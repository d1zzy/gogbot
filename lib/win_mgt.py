"""
Various window management funtions for Windows. Based on some stackexchange
page on "python windows focus window". Requires pywin32.

TODO: Rewrite this using ctypes to not require pywin32.
"""

import pywintypes
import re
import win32gui

class _Window:
    """Encapsulates some calls to the winapi for window management"""

    def __init__ (self, handle):
        self._handle = handle

    def SetForeground(self):
        """Put the window in the foreground."""
        win32gui.SetForegroundWindow(self._handle)

def FindByName(class_name, window_name=None):
    """Find window by class or name and return it."""
    handle = win32gui.FindWindow(class_name, window_name)
    if handle:
        return _Window(handle)
    return None

def _EnumWindowsCallback(hwnd, state):
    """Passed to win32gui.EnumWindows() to check all the opened windows."""
    if state.pattern_re.match(str(win32gui.GetWindowText(hwnd))) != None:
        state.handle = hwnd
        return False
    return True

def FindByTitleRegexp(pattern_regexp):
    """Find window by matching pattern against title and return it."""
    class State:
        pattern_re = re.compile(pattern_regexp)
        handle = None
    state = State()

    try:
        win32gui.EnumWindows(_EnumWindowsCallback, state)
    except pywintypes.error as err:
        # We have to ignore the no-failure exception raised by win32gui
        # when a boolean function like EnumWindows() returns false.
        if err.args[0] != 0:
            raise
    return _Window(state.handle) if state.handle else None
