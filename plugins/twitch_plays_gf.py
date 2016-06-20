import logging
import time

from lib import irc
from lib import keygen
from lib import win_mgt

class Handler(irc.HandlerBase):
    """Handles chat commands by passing simulated input to applications."""

    _COMMANDS = {
        'walk': lambda: keygen.SendKey(keygen.KeyCode(vk=keygen.VK_W),
                                       hold_time=0.5),
# Not much point in supporting a backstep move.
#       'back': lambda: keygen.SendKey(keygen.KeyCode(vk=keygen.VK_S),
#                                      hold_time=0.5),
        # up/down are just like walk/back but are more intuitive for dialogue
        # navigation and they need less time for the key to be pressed.
        'up': lambda: keygen.SendKey(keygen.KeyCode(vk=keygen.VK_W),
                                     hold_time=0.2),
        'down': lambda: keygen.SendKey(keygen.KeyCode(vk=keygen.VK_S),
                                       hold_time=0.2),
        'left': lambda: keygen.SendKey(keygen.KeyCode(vk=keygen.VK_A),
                                       hold_time=0.5),
        'right': lambda: keygen.SendKey(keygen.KeyCode(vk=keygen.VK_D),
                                        hold_time=0.5),
        'run': lambda: keygen.SendKeyCombo((keygen.KeyCode(vk=keygen.VK_LSHIFT),
                                            keygen.KeyCode(vk=keygen.VK_W)),
                                           hold_time=0.5),
        'look': lambda: keygen.SendKey(keygen.KeyCode(vk=keygen.VK_E),
                                       hold_time=0.5),
        'use': lambda: keygen.SendKey(keygen.KeyCode(vk=keygen.VK_U),
                                      hold_time=0.5),
        'take': lambda: keygen.SendKey(keygen.KeyCode(vk=keygen.VK_P),
                                       hold_time=0.5),
        'inventory': lambda: keygen.SendKey(keygen.KeyCode(vk=keygen.VK_I),
                                            hold_time=0.5)
    }
    # Key sequence to save the game in the first slot. Doesn't seem to work
    # all the time.
    # WARNING: make sure this is triggered while outside of the inventory
    # screen, otherwise the first "ESCAPE" key simply exits the inventory.
    _SAVE_CMD = lambda _: keygen.SendKeys((keygen.KeyCode(vk=keygen.VK_ESCAPE),
                                           keygen.KeyCode(vk=keygen.VK_RETURN),
                                           keygen.KeyCode(vk=keygen.VK_RETURN),
                                           keygen.KeyCode(vk=keygen.VK_RETURN),
                                           keygen.KeyCode(vk=keygen.VK_A),
                                           keygen.KeyCode(vk=keygen.VK_RETURN)),
                                          hold_time=0.03, wait_time=0.03)

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
            logging.warning('Failed to find window "%s" to focus.', focus_window)
            return
        window.SetForeground()
        # Save the game immediately after focusing it, before taking any new
        # commands.
        #self._SAVE_CMD()

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

        # Special handling for save.
        #if command == 'save':
        #    self._SAVE_CMD()
        #    return True

        key_func = self._COMMANDS.get(command)
        if key_func:
            key_func()
            return True

        return False
