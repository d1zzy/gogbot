"""
TwitchPlays IRC command handler for Stardew Valley.

See docs/TwitchPlays_StardewValley.txt.
"""

from lib import keygen
from lib import twitch_plays

class Handler(twitch_plays.Handler):
    """Stardew Valley Twitch Plays command handler."""

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
        super().__init__(conn, config, self._COMMANDS)
