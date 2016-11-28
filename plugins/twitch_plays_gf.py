from lib import keygen
from lib import twitch_plays

class Handler(twitch_plays.Handler):
    """Grim Fandango Twitch Plays command handler."""

    _COMMANDS = {
        'walk': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_W),
                                       hold_time=0.5),
# Not much point in supporting a backstep move.
#       'back': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_S),
#                                      hold_time=0.5),
        # up/down are just like walk/back but are more intuitive for dialogue
        # navigation and they need less time for the key to be pressed.
        'up': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_W),
                                     hold_time=0.2),
        'down': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_S),
                                       hold_time=0.2),
        'left': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_A),
                                       hold_time=0.5),
        'right': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_D),
                                        hold_time=0.5),
        'run': lambda: keygen.SendKeyCombo((keygen.VirtualKey(keygen.VK_LSHIFT),
                                            keygen.VirtualKey(keygen.VK_W)),
                                           hold_time=0.5),
        'look': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_E),
                                       hold_time=0.5),
        'use': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_U),
                                      hold_time=0.5),
        'take': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_P),
                                       hold_time=0.5),
        'inventory': lambda: keygen.SendKey(keygen.VirtualKey(keygen.VK_I),
                                            hold_time=0.5),
    # Key sequence to save the game in the first slot. Doesn't seem to work
    # all the time.
    # WARNING: make sure this is triggered while outside of the inventory
    # screen, otherwise the first "ESCAPE" key simply exits the inventory.
    #    'save': lambda _: keygen.SendKeys((keygen.VirtualKey(keygen.VK_ESCAPE),
    #                                       keygen.VirtualKey(keygen.VK_RETURN),
    #                                       keygen.VirtualKey(keygen.VK_RETURN),
    #                                       keygen.VirtualKey(keygen.VK_RETURN),
    #                                       keygen.VirtualKey(keygen.VK_A),
    #                                       keygen.VirtualKey(keygen.VK_RETURN)),
    #                                      hold_time=0.03, wait_time=0.03),
    }

    def __init__(self, conn, config):
        super().__init__(conn, config, self._COMMANDS)
