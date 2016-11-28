"""
TwitchPlays IRC command handler for Stardew Valley.

See docs/TwitchPlays_StardewValley.txt.
"""

import logging
import time

from lib import irc
from lib import keygen
from lib import win_mgt

class Handler(irc.HandlerBase):
    """Handles chat commands by passing simulated input to applications."""

    _COMMANDS = {
        # For Stardew Valley we use DirectX scancodes as virtual keys don't
        # seem to work for it.
        'up': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_W),
                                     hold_time=0.2),
        'down': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_S),
                                       hold_time=0.2),
        'left': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_A),
                                       hold_time=0.2),
        'right': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_D),
                                        hold_time=0.2),
        'use': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_C),
                                      hold_time=0.2),
        'check': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_X),
                                        hold_time=0.2),
        'slot1': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_1),
                                        hold_time=0.2),
        'slot2': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_2),
                                        hold_time=0.2),
        'slot3': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_3),
                                        hold_time=0.2),
        'slot4': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_4),
                                        hold_time=0.2),
        'slot5': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_5),
                                        hold_time=0.2),
        'slot6': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_6),
                                        hold_time=0.2),
        'slot7': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_7),
                                        hold_time=0.2),
        'slot8': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_8),
                                        hold_time=0.2),
        'slot9': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_9),
                                        hold_time=0.2),
        'slot0': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_0),
                                        hold_time=0.2),
        'slot-': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_MINUS),
                                        hold_time=0.2),
        'slot=': lambda: keygen.SendKey(keygen.ScanCode(keygen.DIK_EQUALS),
                                        hold_time=0.2),
# Menu command disabled as this bot doesn't allow inventory management and
# the menu command makes it easy to troll a stream.
#        'menu':  lambda: keygen.SendKey(keygen.KeyCode(sc=keygen.DIK_E),
#                                        hold_time=0.2),
    }

    def __init__(self, conn, config):
        super().__init__(conn)
        self._nickname = config['CONNECTION']['nickname'].lower()
        self._channel = config['CONNECTION']['channel'].lower()
        self._cfg = config['TWITCH_PLAYS'] if 'TWITCH_PLAYS' in config.sections() else {}
        self._FocusWindow()

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
                'Command list: ' + ', '.join(sorted(self._COMMANDS)))
            return True

    def HandlePRIVMSG(self, msg):
        parts = irc.SplitPRIVMSG(msg)
        if len(parts) < 2 or not parts[1]:
            logging.warning('Got invalid PRIVMSG: %r', msg)
            return False

        command = self._SkipNickname(parts[1])
        if not command:
            return False

        command = command.lower()
        if self._HandleHelp(command):
            return True

        key_func = self._COMMANDS.get(command)
        if key_func:
            key_func()
            return True

        return False
