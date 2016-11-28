"""
Twitch Plays IRC command handler.

See docs/TwitchPlays_*.txt.
"""

import logging
import time

from lib import irc
from lib import keygen
from lib import win_mgt

class Handler(irc.HandlerBase):
    """Handles chat commands by passing simulated input to applications."""

    def __init__(self, conn, config, commands):
        """Initialize this instance.

        Args:
            conn: Connection instance.
            config: ConfigParser instance.
            commands: Dictionary associating command strings with callable
                that handles them.
        """
        super().__init__(conn)
        self._nickname = config['CONNECTION']['nickname'].lower()
        self._channel = config['CONNECTION']['channel'].lower()
        self._cfg = config['TWITCH_PLAYS'] if 'TWITCH_PLAYS' in config.sections() else {}
        self._FocusWindow()
        self._commands = commands

    def _FocusWindow(self):
        focus_window = self._cfg.get('focus_window')
        if not focus_window:
            return

        # First try to find the window by full class name or window name match.
        window = win_mgt.FindByName(focus_window)
        # If previous search failed, try to find window by regexp match.
        if not window:
            window = win_mgt.FindByTitleRegexp(focus_window)

        if not window:
            logging.warning('Failed to find window "%s" to focus.',
                            focus_window)
            return
        window.SetForeground()

    def _SkipNickname(self, line):
        require_nickname = self._cfg.getboolean('require_nickname')

        # Split the message into 2 parts, first one should be our nickname
        # if we are to consider it as a command.
        parts = line.strip().lower().split(maxsplit=1)
        if len(parts) < 2:
            # A single word was typed, return it if not requiring a nickname
            # prefix, otherwise return None.
            return None if require_nickname else parts[0]
        # The first word might be a nickname, strip any @ or : that may be at
        # the beginning or end of it.
        nick = parts[0].strip('@:')
        # If first word was our nickname, we always skip it.
        if nick == self._nickname:
            return parts[1]

        # If it wasn't our nickname but we require one, we return None,
        # otherwise return the original line.strip
        return None if require_nickname else line

    def _HandleHelp(self, command):
        if command == 'help':
            self._conn.SendMessage(
                self._channel,
                'Command list: ' + ', '.join(sorted(self._commands)))
            return True

    def HandlePRIVMSG(self, msg):
        parts = irc.SplitPRIVMSG(msg)
        if len(parts) < 2 or not parts[1]:
            logging.warning('Got invalid PRIVMSG: %r', msg)
            return False

        command = self._SkipNickname(parts[1])
        if not command:
            return False

        return self.HandleCommand(command.lower())

    def HandleCommand(self, command):
        if self._HandleHelp(command):
            return True

        key_func = self._commands.get(command)
        if key_func:
            key_func()
            return True

        return False
