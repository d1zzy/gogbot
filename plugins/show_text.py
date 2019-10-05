import logging
import requests
import string
import urllib.parse

from lib import config
from lib import irc


class Handler(irc.HandlerBase):
    """IRC handler to print some text based on configurable template."""

    def __init__(self, conn, conf):
        super().__init__(conn)
        self._channel = conf['CONNECTION']['channel'].lower()

        show_text_section = config.GetSection(conf, 'show_text')
        if 'command' not in show_text_section:
            raise Exception('"command" not found in SHOW_TEXT config section')
        self._command = show_text_section['command']
        if 'template' not in show_text_section:
            raise Exception('"template" not found in SHOW_TEXT config section')
        self._template = show_text_section['template']

    def HandlePRIVMSG(self, msg):
        """The entry point into this plugin, handle a chat message."""
        parts = irc.SplitPRIVMSG(msg)
        if len(parts) < 2 or not parts[1]:
            logging.warning('Got invalid PRIVMSG: %r', msg)
            return False

        command = parts[1].strip().split(' ', maxsplit=1)
        if not command[0]:
            return False

        if command[0] == self._command:
            self._HandleCommand(msg, command[1])
            # The command was handled, even if it might have failed.
            return True

        return False

    def _HandleCommand(self, msg, args):
        """Handle the chat command by printing some formatted text."""
        # Substitution dictionary.
        vars = {
            'args': args,
            'url_args': urllib.parse.quote(args),
            'sender': msg.sender,
        }
        self._conn.SendMessage(
            self._channel,
            string.Template(self._template).substitute(**vars))
