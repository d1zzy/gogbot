"""
TwitchPlays IRC command handler for Gwent Card Game.

See docs/TwitchPlays_Gwent.txt.
"""

from lib import event_queue
from lib import keygen
from lib import twitch_plays

class Handler(twitch_plays.Handler):
    """Gwent Twitch Plays command handler."""

    # Keep track of all commands issued in the last _MAX_AGE seconds.
    _MAX_AGE = 30
    # Minumum number of "pass" commands required before issuing a pass.
    _MIN_PASS_COMMANDS = 15
    # How many "pass" commands should we get out of all commands in the past
    # _MAX_AGE seconds before issuing a pass.
    _PASS_PERCENT = 0.4  # 40%

    _COMMANDS = {
        'up': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_UP),
                                     hold_time=0.2),
        'down': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_DOWN),
                                       hold_time=0.2),
        'left': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_LEFT),
                                       hold_time=0.2),
        'right': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_RIGHT),
                                        hold_time=0.2),
        'use': lambda: keygen.SendKeys((keygen.VirtualKey(keygen.VK_RETURN),
                                        keygen.VirtualKey(keygen.VK_RETURN)),
                                       hold_time=0.2, wait_time=0.2),
        'stop-redraw': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_X),
                                              hold_time=0.2),
        'change-leader': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_X),
                                                hold_time=0.2),
        # This is just a placeholder, the actual functor is set later.
        'pass': None,
    }

    def __init__(self, conn, config):
        # Need to use an event queue to decide how many times "pass" was issued
        # within a window of time (60 seconds).
        self._cmd_queue = event_queue.Queue(max_age=_MAX_AGE)
        # Make a copy of the command handlers and set the "pass" handler.
        commands = dict(self._COMMANDS)
        commands['pass'] = self._DecideToPass
        super().__init__(conn, config, commands)

    def HandleCommand(self, command):
        # If the command is valid, record it.
        if command in self._COMMANDS:
            self._cmd_queue.RecordEvent(event_queue.Event(command))
        return super().HandleCommand(command)

    def _DecideToPass(self):
        count_all = self._cmd_queue.CountAll()
        # If there are a minimum of 10 commands in the last minute and the
        # number of "pass" commands is at least 80% of them, then do pass.
        if (count_all >= _MIN_PASS_COMMANDS and
            self._cmd_queue.CountByData('pass') / count_all > _PASS_PERCENT):
            keygen.SendKey(keygen.VirtualKey(keygen.VK_SPACE), hold_time=2)
