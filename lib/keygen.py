"""
Generate fake windows key/mouse events. Supports keyboard events as virtual
key codes or DirectX scancodes (some games work only one of one of these).

Based on various stockexchange answers on "python generate keyboard events".
"""
import ctypes
from ctypes import wintypes
import time

user32 = ctypes.WinDLL('user32', use_last_error=True)

INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_UNICODE     = 0x0004
KEYEVENTF_SCANCODE    = 0x0008

MAPVK_VK_TO_VSC = 0

# Virtual key codes, taken from msdn.microsoft.com/en-us/library/dd375731

VK_BACK = 0x08 # BACKSPACE key
VK_TAB = 0x09 # TAB key
VK_RETURN = 0x0D # ENTER key
VK_SHIFT = 0x10 # SHIFT key
VK_CONTROL = 0x11 # CTRL key
VK_MENU = 0x12 # ALT key
VK_PAUSE = 0x13 # PAUSE key
VK_CAPITAL = 0x14 # CAPS LOCK key
VK_ESCAPE = 0x1B # ESC key
VK_SPACE = 0x20 # SPACEBAR
VK_PRIOR = 0x21 # PAGE UP key
VK_NEXT = 0x22 # PAGE DOWN key
VK_END = 0x23 # END key
VK_HOME = 0x24 # HOME key
VK_LEFT = 0x25 # LEFT ARROW key
VK_UP = 0x26 # UP ARROW key
VK_RIGHT = 0x27 # RIGHT ARROW key
VK_DOWN = 0x28 # DOWN ARROW key
VK_SNAPSHOT = 0x2C # PRINT SCREEN key
VK_INSERT = 0x2D # INS key
VK_DELETE = 0x2E # DEL key
VK_0 = 0x30 # 0 key
VK_1 = 0x31 # 1 key
VK_2 = 0x32 # 2 key
VK_3 = 0x33 # 3 key
VK_4 = 0x34 # 4 key
VK_5 = 0x35 # 5 key
VK_6 = 0x36 # 6 key
VK_7 = 0x37 # 7 key
VK_8 = 0x38 # 8 key
VK_9 = 0x39 # 9 key
VK_A = 0x41 # A key
VK_B = 0x42 # B key
VK_C = 0x43 # C key
VK_D = 0x44 # D key
VK_E = 0x45 # E key
VK_F = 0x46 # F key
VK_G = 0x47 # G key
VK_H = 0x48 # H key
VK_I = 0x49 # I key
VK_J = 0x4A # J key
VK_K = 0x4B # K key
VK_L = 0x4C # L key
VK_M = 0x4D # M key
VK_N = 0x4E # N key
VK_O = 0x4F # O key
VK_P = 0x50 # P key
VK_Q = 0x51 # Q key
VK_R = 0x52 # R key
VK_S = 0x53 # S key
VK_T = 0x54 # T key
VK_U = 0x55 # U key
VK_V = 0x56 # V key
VK_W = 0x57 # W key
VK_X = 0x58 # X key
VK_Y = 0x59 # Y key
VK_Z = 0x5A # Z key
VK_LWIN = 0x5B # Left Windows key (Natural keyboard)
VK_RWIN = 0x5C # Right Windows key (Natural keyboard)
VK_NUMPAD0 = 0x60 # Numeric keypad 0 key
VK_NUMPAD1 = 0x61 # Numeric keypad 1 key
VK_NUMPAD2 = 0x62 # Numeric keypad 2 key
VK_NUMPAD3 = 0x63 # Numeric keypad 3 key
VK_NUMPAD4 = 0x64 # Numeric keypad 4 key
VK_NUMPAD5 = 0x65 # Numeric keypad 5 key
VK_NUMPAD6 = 0x66 # Numeric keypad 6 key
VK_NUMPAD7 = 0x67 # Numeric keypad 7 key
VK_NUMPAD8 = 0x68 # Numeric keypad 8 key
VK_NUMPAD9 = 0x69 # Numeric keypad 9 key
VK_MULTIPLY = 0x6A # Multiply key
VK_ADD = 0x6B # Add key
VK_SEPARATOR = 0x6C # Separator key
VK_SUBTRACT = 0x6D # Subtract key
VK_DECIMAL = 0x6E # Decimal key
VK_DIVIDE = 0x6F # Divide key
VK_F1 = 0x70 # F1 key
VK_F2 = 0x71 # F2 key
VK_F3 = 0x72 # F3 key
VK_F4 = 0x73 # F4 key
VK_F5 = 0x74 # F5 key
VK_F6 = 0x75 # F6 key
VK_F7 = 0x76 # F7 key
VK_F8 = 0x77 # F8 key
VK_F9 = 0x78 # F9 key
VK_F10 = 0x79 # F10 key
VK_F11 = 0x7A # F11 key
VK_F12 = 0x7B # F12 key
VK_NUMLOCK = 0x90 # NUM LOCK key
VK_SCROLL = 0x91 # SCROLL LOCK key
VK_LSHIFT = 0xA0 # Left SHIFT key
VK_RSHIFT = 0xA1 # Right SHIFT key
VK_LCONTROL = 0xA2 # Left CONTROL key
VK_RCONTROL = 0xA3 # Right CONTROL key

# DirectX scan codes, from http://www.gamespp.com/directx/directInputKeyboardScanCodes.html
# Use these values when calling one of the functions to simulate a key.
DIK_ESCAPE        = 0x01
DIK_1             = 0x02
DIK_2             = 0x03
DIK_3             = 0x04
DIK_4             = 0x05
DIK_5             = 0x06
DIK_6             = 0x07
DIK_7             = 0x08
DIK_8             = 0x09
DIK_9             = 0x0A
DIK_0             = 0x0B
DIK_MINUS         = 0x0C    # - on main keyboard
DIK_EQUALS        = 0x0D
DIK_BACK          = 0x0E    # backspace
DIK_TAB           = 0x0F
DIK_Q             = 0x10
DIK_W             = 0x11
DIK_E             = 0x12
DIK_R             = 0x13
DIK_T             = 0x14
DIK_Y             = 0x15
DIK_U             = 0x16
DIK_I             = 0x17
DIK_O             = 0x18
DIK_P             = 0x19
DIK_LBRACKET      = 0x1A
DIK_RBRACKET      = 0x1B
DIK_RETURN        = 0x1C    # Enter on main keyboard
DIK_LCONTROL      = 0x1D
DIK_A             = 0x1E
DIK_S             = 0x1F
DIK_D             = 0x20
DIK_F             = 0x21
DIK_G             = 0x22
DIK_H             = 0x23
DIK_J             = 0x24
DIK_K             = 0x25
DIK_L             = 0x26
DIK_SEMICOLON     = 0x27
DIK_APOSTROPHE    = 0x28
DIK_GRAVE         = 0x29    # accent grave
DIK_LSHIFT        = 0x2A
DIK_BACKSLASH     = 0x2B
DIK_Z             = 0x2C
DIK_X             = 0x2D
DIK_C             = 0x2E
DIK_V             = 0x2F
DIK_B             = 0x30
DIK_N             = 0x31
DIK_M             = 0x32
DIK_COMMA         = 0x33
DIK_PERIOD        = 0x34    # . on main keyboard
DIK_SLASH         = 0x35    # / on main keyboard
DIK_RSHIFT        = 0x36
DIK_MULTIPLY      = 0x37    # * on numeric keypad
DIK_LMENU         = 0x38    # left Alt
DIK_SPACE         = 0x39
DIK_CAPITAL       = 0x3A
DIK_F1            = 0x3B
DIK_F2            = 0x3C
DIK_F3            = 0x3D
DIK_F4            = 0x3E
DIK_F5            = 0x3F
DIK_F6            = 0x40
DIK_F7            = 0x41
DIK_F8            = 0x42
DIK_F9            = 0x43
DIK_F10           = 0x44
DIK_NUMLOCK       = 0x45
DIK_SCROLL        = 0x46    # Scroll Lock
DIK_NUMPAD7       = 0x47
DIK_NUMPAD8       = 0x48
DIK_NUMPAD9       = 0x49
DIK_SUBTRACT      = 0x4A    # - on numeric keypad
DIK_NUMPAD4       = 0x4B
DIK_NUMPAD5       = 0x4C
DIK_NUMPAD6       = 0x4D
DIK_ADD           = 0x4E    # + on numeric keypad
DIK_NUMPAD1       = 0x4F
DIK_NUMPAD2       = 0x50
DIK_NUMPAD3       = 0x51
DIK_NUMPAD0       = 0x52
DIK_DECIMAL       = 0x53    # . on numeric keypad
DIK_F11           = 0x57
DIK_F12           = 0x58

DIK_F13           = 0x64    #                     (NEC PC98)
DIK_F14           = 0x65    #                     (NEC PC98)
DIK_F15           = 0x66    #                     (NEC PC98)

DIK_KANA          = 0x70    # (Japanese keyboard)
DIK_CONVERT       = 0x79    # (Japanese keyboard)
DIK_NOCONVERT     = 0x7B    # (Japanese keyboard)
DIK_YEN           = 0x7D    # (Japanese keyboard)
DIK_NUMPADEQUALS  = 0x8D    # = on numeric keypad (NEC PC98)
DIK_CIRCUMFLEX    = 0x90    # (Japanese keyboard)
DIK_AT            = 0x91    #                     (NEC PC98)
DIK_COLON         = 0x92    #                     (NEC PC98)
DIK_UNDERLINE     = 0x93    #                     (NEC PC98)
DIK_KANJI         = 0x94    # (Japanese keyboard)
DIK_STOP          = 0x95    #                     (NEC PC98)
DIK_AX            = 0x96    #                     (Japan AX)
DIK_UNLABELED     = 0x97    #                        (J3100)
DIK_NUMPADENTER   = 0x9C    # Enter on numeric keypad
DIK_RCONTROL      = 0x9D
DIK_NUMPADCOMMA   = 0xB3    # , on numeric keypad (NEC PC98)
DIK_DIVIDE        = 0xB5    # / on numeric keypad
DIK_SYSRQ         = 0xB7
DIK_RMENU         = 0xB8    # right Alt
DIK_HOME          = 0xC7    # Home on arrow keypad
DIK_UP            = 0xC8    # UpArrow on arrow keypad
DIK_PRIOR         = 0xC9    # PgUp on arrow keypad
DIK_LEFT          = 0xCB    # LeftArrow on arrow keypad
DIK_RIGHT         = 0xCD    # RightArrow on arrow keypad
DIK_END           = 0xCF    # End on arrow keypad
DIK_DOWN          = 0xD0    # DownArrow on arrow keypad
DIK_NEXT          = 0xD1    # PgDn on arrow keypad
DIK_INSERT        = 0xD2    # Insert on arrow keypad
DIK_DELETE        = 0xD3    # Delete on arrow keypad
DIK_LWIN          = 0xDB    # Left Windows key
DIK_RWIN          = 0xDC    # Right Windows key
DIK_APPS          = 0xDD    # AppMenu key

# C struct definitions

wintypes.ULONG_PTR = wintypes.WPARAM

class _MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx",          wintypes.LONG),
                ("dy",          wintypes.LONG),
                ("mouseData",   wintypes.DWORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

class _KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk",         wintypes.WORD),
                ("wScan",       wintypes.WORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

    def __init__(self, *args, **kwds):
        super(_KEYBDINPUT, self).__init__(*args, **kwds)
        # some programs use the scan code even if KEYEVENTF_SCANCODE
        # isn't set in dwFflags, so attempt to map the correct code.
        if not self.dwFlags & (KEYEVENTF_UNICODE | KEYEVENTF_SCANCODE):
            self.wScan = user32.MapVirtualKeyExW(self.wVk,
                                                 MAPVK_VK_TO_VSC, 0)

class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg",    wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))

class _INPUT(ctypes.Structure):
    class _INPUT_UNION(ctypes.Union):
        _fields_ = (("ki", _KEYBDINPUT),
                    ("mi", _MOUSEINPUT),
                    ("hi", _HARDWAREINPUT))
    _anonymous_ = ("_input",)
    _fields_ = (("type",   wintypes.DWORD),
                ("_input", _INPUT_UNION))

_LPINPUT = ctypes.POINTER(_INPUT)

def _check_count(result, func, args):
    if result == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    return args

user32.SendInput.errcheck = _check_count
user32.SendInput.argtypes = (wintypes.UINT, # nInputs
                             _LPINPUT,      # pInputs
                             ctypes.c_int)  # cbSize

def _GetKeyboardInput(key_code):
    if key_code.vk is None:
        kbd_input = _KEYBDINPUT(wScan=key_code.sc, dwFlags=KEYEVENTF_SCANCODE)
    else:
        kbd_input = _KEYBDINPUT(wVk=key_code.vk)
    return kbd_input

def _SendKeyboardInput(kbd_input):
    x = _INPUT(type=INPUT_KEYBOARD, ki=kbd_input)
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

# Public API

class KeyCode:
    """Encapsulate a virtual key or scan code."""

    def __init__(self, vk=None, sc=None):
        """Either vk or sc must be given.

        vk: virtual key code, see VK_* constants above.
        sc: scan code, see DIK_* constants above.
        """
        if vk is None and sc is None:
            raise Exception('Either virtualKey or scanCode must be provided')
        self.vk = vk
        self.sc = sc

def PressKey(key_code):
    """Simulate pressing a key.

    Don't forget to call ReleaseKey too.

    Args:
        key_code: KeyCode instance with the key to press.
    """
    _SendKeyboardInput(_GetKeyboardInput(key_code))

def ReleaseKey(key_code):
    """Simulate releasing a key.

    Either vk or scan must be provided.

    Args:
        key_code: KeyCode instance with the key to release.
    """
    kbd_input = _GetKeyboardInput(key_code)
    kbd_input.dwFlags = kbd_input.dwFlags | KEYEVENTF_KEYUP
    _SendKeyboardInput(kbd_input)

def SendKey(key_code, hold_time=1):
    """Simulate pressing and releasing given key.

    Args:
        key_code: KeyCode instance with the key to press and release.
        hold_time: Time, in seconds, to hold the key pressed.
    """
    PressKey(key_code)
    time.sleep(hold_time)
    ReleaseKey(key_code)

def SendKeys(keys, hold_time=1, wait_time=1):
    """Simulate pressing a sequence of keys.

    Args:
        keys: sequence of KeyCode to simulate in sequence.
        hold_time: how long to keep the keys pressed, in seconds.
        wait_time: how long to wait between key presses, in seconds.
    """
    for key in keys:
        SendKey(key, hold_time=1)
        time.sleep(wait_time)

def SendKeyCombo(keys, hold_time=1):
    """Simulate pressing and releasing multiple keys at once.

    Args:
        keys: sequence of KeyCode to simulate.
        hold_time: how long to keep the keys pressed, in seconds.
    """
    for key in keys:
        PressKey(key)

    time.sleep(hold_time)

    for key in reversed(keys):
        ReleaseKey(key)
