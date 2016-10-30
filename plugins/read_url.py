import logging
import requests
import string

from lib import config
from lib import irc


class Handler(irc.HandlerBase):
    """IRC handler to print text from a given URL."""

    def __init__(self, conn, conf):
        super().__init__(conn)
        self._channel = conf['CONNECTION']['channel'].lower()

        read_url_section = config.GetSection(conf, 'read_url')
        if 'command' not in read_url_section:
            raise Exception('"command" not found in READ_URL config section')
        self._command = read_url_section['command']
        if 'url' not in read_url_section:
            raise Exception('"url" not found in READ_URL config section')
        self._url = read_url_section['url']

    def HandlePRIVMSG(self, msg):
        """The entry point into this plugin, handle a chat message."""
        parts = irc.SplitPRIVMSG(msg)
        if len(parts) < 2 or not parts[1]:
            logging.warning('Got invalid PRIVMSG: %r', msg)
            return False

        command = parts[1].strip()
        if not command:
            return False

        if command == self._command:
            self._HandleCommand(msg)
            # The command was handled, even if it might have failed.
            return True

        return False

    def _HandleCommand(self, msg):
        """Handle the chat command by reading from an URL."""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) '
                       'Gecko/20100101 Firefox/6.0'}
        req = requests.get(self._url, headers=headers)
        if req.status_code != 200:
            logging.error('URL request failed: %s %s',
                          req.status_code, req.reason)
            return
        text = req.text.strip()
        if not text:
            # No meaningful text, skip.
            return
        if '\n' in text:
            logging.error('got page with newlines, rejecting: %r', text)
            return
        self._conn.SendMessage(
            self._channel,
            string.Template(text).substitute(username=msg.sender))
