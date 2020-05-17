import logging
import re
import requests
import sqlite3
import time
from urllib import parse as url_parse

from lib import config
from lib import irc


class Handler(irc.HandlerBase):
    """IRC handler to support !quote command."""

    # Regular expressions to match against supported commands.
    _GET_QUOTE_RE = re.compile(r'^!quote(?: +#?(\d+)$|$)', flags=re.IGNORECASE)
    _ADD_QUOTE_RE = re.compile(r'^!quote +add +([^ ].*)$', flags=re.IGNORECASE)
    _RAWADD_QUOTE_RE = re.compile(r'^!quote +rawadd +([^ ].*)$',
                                  flags=re.IGNORECASE)
    _UPDATE_QUOTE_RE = re.compile(r'^!quote +update +#?(\d+) +([^ ].*)$',
                                  flags=re.IGNORECASE)
    _DEL_QUOTE_RE = re.compile(r'^!quote +del +#?(\d+)$', flags=re.IGNORECASE)
    _HELP_RE = re.compile(r'^!quote +help$', flags=re.IGNORECASE)

    def __init__(self, conn, conf):
        super().__init__(conn)
        self._client_id = conf['CONNECTION']['client_id'].lower()
        self._channel = conf['CONNECTION']['channel'].lower()
        quote_section = config.GetSection(conf, 'quotes')
        if 'db_file' not in quote_section:
            raise Exception('"db_file" not found in QUOTE config section')
        self._db = sqlite3.connect(quote_section['db_file'])
        self._table = quote_section['db_table']
        self._report_errors = quote_section.getboolean('report_errors')
        self._use_whisper = quote_section.getboolean('use_whisper')

    def _ReportError(self, recipient, fmt, *args, level=logging.WARNING):
        if level is not None:
            logging.log(level, fmt, *args)
        if self._report_errors:
            if self._use_whisper:
                self._conn.SendWhisper(recipient, fmt % args)
            else:
                # Send a nicely formatted chat (public) message with the
                # user as a prefix.
                self._conn.SendMessage(self._channel,
                                       ''.join((recipient, ': ', fmt % args)))

    def HandlePRIVMSG(self, msg):
        """The entry point into this plugin, handle a chat message."""
        parts = irc.SplitPRIVMSG(msg)
        if len(parts) < 2 or not parts[1]:
            logging.warning('Got invalid PRIVMSG: %r', msg)
            return False

        command = parts[1].strip()
        if not command:
            return False

        match = self._GET_QUOTE_RE.match(command)
        if match:
            return self._HandleGetQuote(msg, match)

        match = self._ADD_QUOTE_RE.match(command)
        if match:
            return self._HandleAddQuote(msg, match)

        match = self._RAWADD_QUOTE_RE.match(command)
        if match:
            return self._HandleRawAddQuote(msg, match)

        match = self._UPDATE_QUOTE_RE.match(command)
        if match:
            return self._HandleUpdateQuote(msg, match)

        match = self._DEL_QUOTE_RE.match(command)
        if match:
            return self._HandleDelQuote(msg, match)

        match = self._HELP_RE.match(command)
        if match:
            return self._HandleHelp()

        return False

    def _HandleGetQuote(self, msg, match):
        """Handle "!quote" and "!quote <number>" commands."""
        index = match.group(1)
        cur = self._db.cursor()
        if index:
            cur.execute('SELECT CustomId, Text FROM %s WHERE CustomId = ?' %
                        self._table, (index,))
        else:
            cur.execute(
                'SELECT CustomId, Text FROM %s ORDER BY random() limit 1' %
                self._table)
        row = cur.fetchone()
        if not row:
            self._ReportError(msg.sender, 'Failed to get quote #%s', index)
            return False

        self._conn.SendMessage(self._channel, '#%s: %s' % (row[0], row[1]))
        return True

    def _AuthorizeElevatedCommand(self, sender):
        """Return true/false if "sender" is a moderator."""
        # Twitch takes some time (on the order of minutes) between the bot
        # joining the channel and getting the user list so it's possible that
        # users we don't know about are issuing elevated commands, in that case
        # we don't have much of a choice and just ignore them.
        user = self._conn.GetUserList().get(sender)
        if not user:
            self._ReportError(sender, "User %r tried elevated quotes command "
                              "but we don't know about them from Twitch yet, "
                              "ignoring it.", sender, level=logging.INFO)
            return False
        if not user.IsModerator():
            self._ReportError(sender, 'Unprivileged user %r tried to issue '
                              'elevated quotes command', sender)
            return False
        return True

    def _CallHelix(self, sender, command, args=()):
        url = url_parse.urlunsplit(
            ('https', 'api.twitch.tv', 'helix/%s' % command,
             url_parse.urlencode(args, doseq=True), ''))
        headers = {'Client-ID': self._client_id}
        req = requests.get(url, headers=headers)
        if req.status_code != 200:
            self._ReportError(
                sender, 'Twitch API /helix/%s call failed: %s %s', command,
                req.status_code, req.reason, level=logging.ERROR)
            return None
        result = req.json()
        if not result or 'data' not in result:
            self._ReportError(
                sender, "Twitch API /helix/%s call missing 'data' field",
                level=logging.ERROR)
            return None
        return result['data']

    def _GetCurrentGame(self, sender):
        """Get the current game set on a channel using Twitch API.

            TODO(dizzy): if other code starts using Twitch API, make an internal
            helper library for it.
        """
        # Drop "#" from the start of the channel name, Twitch doesn't need it.
        if len(self._channel) < 2:
            logging.warning('Unexpectadly short channel name: %r',
                            self._channel)
            return None
        data = self._CallHelix(sender, 'streams',
                               {'user_login': self._channel[1:]})
        if data is None:
            return None
        if not data or 'game_id' not in data[0]:
            self._ReportError(
                sender, 'Missing game_id on channel (channel offline?)')
            return None

        data = self._CallHelix(sender, 'games', {'id': data[0]['game_id']})
        if data is None:
            return None
        if not data or 'name' not in data[0]:
            self._ReportError(sender, 'Missing game name in query')
            return None
        return data[0]['name']

    def _AddQuoteToDb(self, quote):
        """Adds the given quote to the database."""
        cur = self._db.cursor()
        cur.execute('INSERT INTO %(table)s (CustomId, Text) '
                    'SELECT max(CustomId) + 1, ? FROM %(table)s' %
                    {'table': self._table}, (quote,))
        cur.execute('SELECT CustomId FROM %s WHERE AutoId = ?' % self._table,
                    (cur.lastrowid,))
        row = cur.fetchone()
        if not row:
            logging.error('Failed to get last added quote')
            self._conn.SendMessage(self._channel, 'Failed to add quote')
            self._db.rollback()
            return None

        idx = row[0]
        self._conn.SendMessage(self._channel, 'Added quote #%s' % idx)
        self._db.commit()
        return idx

    def _HandleAddQuote(self, msg, match):
        """Handle "!quote add ..." command."""
        if not self._AuthorizeElevatedCommand(msg.sender):
            return True

        text = match.group(1).strip()
        date_str = time.strftime('%d.%m.%Y', time.gmtime())
        game = self._GetCurrentGame(msg.sender)
        if not game:
            return True
        text += ' [%s] [%s]' % (game, date_str)
        idx = self._AddQuoteToDb(text)
        if idx:
            logging.info('User %r added quote #%s', msg.sender, idx)
        return True

    def _HandleRawAddQuote(self, msg, match):
        """Handle "!quote rawadd ..." command."""
        if not self._AuthorizeElevatedCommand(msg.sender):
            return True

        text = match.group(1).strip()
        idx = self._AddQuoteToDb(text)
        if idx:
            logging.info('User %r added quote #%s', msg.sender, idx)
        return True

    def _HandleUpdateQuote(self, msg, match):
        """Handle "!quote update ..." command."""
        if not self._AuthorizeElevatedCommand(msg.sender):
            return True

        index = match.group(1)
        text = match.group(2).strip()
        cur = self._db.cursor()
        cur.execute('UPDATE %s SET Text = ? WHERE CustomId = ?' %
                    self._table, (text, index,))
        if cur.rowcount != 1:
            self._ReportError(msg.sender, "Failed to update quote #%s", index)
            return True
        self._db.commit()
        self._conn.SendMessage(self._channel, 'Updated quote #%s' % index)
        logging.info('User %s updated quote #%s to: %s',
                     msg.sender, index, text)
        return True

    def _HandleDelQuote(self, msg, match):
        """Handle "!quote del ..." command."""
        if not self._AuthorizeElevatedCommand(msg.sender):
            return True

        index = match.group(1)
        cur = self._db.cursor()
        cur.execute('DELETE FROM %s WHERE CustomId = ?' % self._table, (index,))
        if cur.rowcount != 1:
            self._ReportError(msg.sender, "Failed to remove quote #%s", index)
            return True
        self._db.commit()
        self._conn.SendMessage(self._channel, 'Deleted quote #%s' % index)
        logging.info('User %r removed quote #%s', msg.sender, index)
        return True

    def _HandleHelp(self):
        """Handle "!quote help"."""
        self._conn.SendMessage(
            self._channel, 'Quotes plugin documentation: https://goo.gl/h7028Q')
        return True
