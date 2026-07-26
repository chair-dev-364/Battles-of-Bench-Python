"""
console_input.py - Windows Console Input Module (production-quality)

Exposes a single function:
    key(timeout=None, mouse=False) -> str | dict | "TIMEOUT"

When mouse=True, mouse events are returned as dictionaries.
When mouse=False (default), only keyboard events are returned.

Uses only `ctypes` and the Windows Console API.
No third-party packages, no msvcrt, no pywin32.
"""

import ctypes
import atexit
import collections
from ctypes import wintypes

# ---------------------------------------------------------------------------
# Win32 constants
# ---------------------------------------------------------------------------
STD_INPUT_HANDLE = -10
INFINITE = 0xFFFFFFFF
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 0x00000102

# Console mode flags
ENABLE_PROCESSED_INPUT = 0x0001
ENABLE_LINE_INPUT      = 0x0002
ENABLE_ECHO_INPUT      = 0x0004
ENABLE_MOUSE_INPUT     = 0x0010
ENABLE_EXTENDED_FLAGS  = 0x0080
ENABLE_QUICK_EDIT_MODE = 0x0040

# Event types
KEY_EVENT          = 0x0001
MOUSE_EVENT        = 0x0002
WINDOW_BUFFER_SIZE_EVENT = 0x0004
MENU_EVENT         = 0x0008
FOCUS_EVENT        = 0x0010

# Mouse event flags
MOUSE_MOVED    = 0x0001
DOUBLE_CLICK   = 0x0002
MOUSE_WHEELED  = 0x0004

# Button state bits
FROM_LEFT_1ST_BUTTON_PRESSED = 0x0001
RIGHTMOST_BUTTON_PRESSED     = 0x0002
FROM_LEFT_2ND_BUTTON_PRESSED = 0x0004   # middle button

# Control key state masks (for dwControlKeyState)
LEFT_CTRL_PRESSED  = 0x0008
RIGHT_CTRL_PRESSED = 0x0004

# Virtual-Key codes we care about
VK_LEFT   = 0x25
VK_UP     = 0x26
VK_RIGHT  = 0x27
VK_DOWN   = 0x28
VK_RETURN = 0x0D
VK_ESCAPE = 0x1B
VK_BACK   = 0x08
VK_SPACE  = 0x20

# ---------------------------------------------------------------------------
# Win32 structures (correctly modelled)
# ---------------------------------------------------------------------------
class COORD(ctypes.Structure):
    _fields_ = [
        ("X", ctypes.c_short),
        ("Y", ctypes.c_short),
    ]

class CHAR_UNION(ctypes.Union):
    _fields_ = [
        ("UnicodeChar", wintypes.WCHAR),
        ("AsciiChar",   ctypes.c_char),
    ]

class KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("bKeyDown",          ctypes.c_int),      # BOOL
        ("wRepeatCount",      wintypes.WORD),
        ("wVirtualKeyCode",   wintypes.WORD),
        ("wVirtualScanCode",  wintypes.WORD),
        ("uChar",             CHAR_UNION),
        ("dwControlKeyState", wintypes.DWORD),
    ]

class MOUSE_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("dwMousePosition",    COORD),
        ("dwButtonState",      wintypes.DWORD),
        ("dwControlKeyState",  wintypes.DWORD),
        ("dwEventFlags",       wintypes.DWORD),
    ]

class WINDOW_BUFFER_SIZE_RECORD(ctypes.Structure):
    _fields_ = [
        ("dwSize", COORD),
    ]

class MENU_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("dwCommandId", wintypes.UINT),
    ]

class FOCUS_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("bSetFocus", ctypes.c_int),  # BOOL
    ]

class EVENT_UNION(ctypes.Union):
    _fields_ = [
        ("KeyEvent",              KEY_EVENT_RECORD),
        ("MouseEvent",            MOUSE_EVENT_RECORD),
        ("WindowBufferSizeEvent", WINDOW_BUFFER_SIZE_RECORD),
        ("MenuEvent",             MENU_EVENT_RECORD),
        ("FocusEvent",            FOCUS_EVENT_RECORD),
    ]

class INPUT_RECORD(ctypes.Structure):
    _fields_ = [
        ("EventType", wintypes.WORD),
        ("Event",     EVENT_UNION),
    ]

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------
_kernel32 = ctypes.windll.kernel32

_stdin_handle = None
_original_mode = None
_base_mode = None              # raw input without mouse, with extended flags
_current_mouse_enabled = None  # True/False/None (unknown)

_event_queue = collections.deque()
_prev_button_state = 0

# ---------------------------------------------------------------------------
# Initialisation / cleanup
# ---------------------------------------------------------------------------
def _init_console():
    """Calculate base console mode and apply it (mouse initially off)."""
    global _stdin_handle, _original_mode, _base_mode, _current_mouse_enabled

    _stdin_handle = _kernel32.GetStdHandle(STD_INPUT_HANDLE)
    if _stdin_handle == wintypes.HANDLE(-1).value:
        raise OSError("GetStdHandle failed")

    mode = wintypes.DWORD()
    if not _kernel32.GetConsoleMode(_stdin_handle, ctypes.byref(mode)):
        raise OSError("GetConsoleMode failed")
    _original_mode = mode.value

    # Build base mode: raw input, extended flags, no line/echo/processed, no quick edit, NO mouse
    _base_mode = _original_mode
    _base_mode &= ~(ENABLE_LINE_INPUT | ENABLE_ECHO_INPUT | ENABLE_PROCESSED_INPUT)
    _base_mode &= ~ENABLE_QUICK_EDIT_MODE
    _base_mode |= ENABLE_EXTENDED_FLAGS
    # ENABLE_MOUSE_INPUT is deliberately omitted

    # Start with mouse disabled
    _kernel32.SetConsoleMode(_stdin_handle, _base_mode)
    _current_mouse_enabled = False

    atexit.register(_restore_console)

def _restore_console():
    if _original_mode is not None and _stdin_handle is not None:
        _kernel32.SetConsoleMode(_stdin_handle, _original_mode)

def _set_mouse_mode(enable):
    """Enable or disable mouse input in console mode."""
    global _current_mouse_enabled
    if _current_mouse_enabled == enable:
        return
    new_mode = _base_mode | (ENABLE_MOUSE_INPUT if enable else 0)
    _kernel32.SetConsoleMode(_stdin_handle, new_mode)
    _current_mouse_enabled = enable

# ---------------------------------------------------------------------------
# Event translation helpers
# ---------------------------------------------------------------------------
def _button_name(state_bits):
    if state_bits & FROM_LEFT_1ST_BUTTON_PRESSED:
        return "left"
    if state_bits & RIGHTMOST_BUTTON_PRESSED:
        return "right"
    if state_bits & FROM_LEFT_2ND_BUTTON_PRESSED:
        return "middle"
    return None

def _process_key_event(rec):
    key = rec.Event.KeyEvent
    vk = key.wVirtualKeyCode
    ctrl_held = key.dwControlKeyState & (LEFT_CTRL_PRESSED | RIGHT_CTRL_PRESSED)

    if ctrl_held and 0x41 <= vk <= 0x5A:
        return "ctrl/" + chr(vk + 32)

    special = {
        VK_LEFT: "left", VK_RIGHT: "right", VK_UP: "up", VK_DOWN: "down",
        VK_RETURN: "enter", VK_ESCAPE: "esc", VK_BACK: "backspace", VK_SPACE: "space",
    }
    if vk in special:
        return special[vk]

    ch = key.uChar.UnicodeChar
    if ch and ch != '\x00' and ch.isprintable():
        return ch

    return None

def _process_mouse_event(rec):
    global _prev_button_state

    mouse = rec.Event.MouseEvent
    flags = mouse.dwEventFlags
    x = mouse.dwMousePosition.X
    y = mouse.dwMousePosition.Y

    if flags & DOUBLE_CLICK:
        btn = _button_name(mouse.dwButtonState)
        if btn:
            _prev_button_state = mouse.dwButtonState
            return {"type": "mouse", "event": "double", "button": btn, "x": x, "y": y}
        return None

    if flags & MOUSE_WHEELED:
        delta = ctypes.c_short(mouse.dwButtonState >> 16).value
        return {"type": "mouse", "event": "wheel", "delta": delta, "x": x, "y": y}

    if flags & MOUSE_MOVED:
        _prev_button_state = mouse.dwButtonState
        return None

    # Button press/release
    curr = mouse.dwButtonState
    prev = _prev_button_state
    _prev_button_state = curr

    events = []
    changed_down = (curr ^ prev) & curr
    if changed_down & FROM_LEFT_1ST_BUTTON_PRESSED:
        events.append({"type": "mouse", "event": "down", "button": "left", "x": x, "y": y})
    if changed_down & RIGHTMOST_BUTTON_PRESSED:
        events.append({"type": "mouse", "event": "down", "button": "right", "x": x, "y": y})
    if changed_down & FROM_LEFT_2ND_BUTTON_PRESSED:
        events.append({"type": "mouse", "event": "down", "button": "middle", "x": x, "y": y})
    changed_up = (curr ^ prev) & prev
    if changed_up & FROM_LEFT_1ST_BUTTON_PRESSED:
        events.append({"type": "mouse", "event": "up", "button": "left", "x": x, "y": y})
    if changed_up & RIGHTMOST_BUTTON_PRESSED:
        events.append({"type": "mouse", "event": "up", "button": "right", "x": x, "y": y})
    if changed_up & FROM_LEFT_2ND_BUTTON_PRESSED:
        events.append({"type": "mouse", "event": "up", "button": "middle", "x": x, "y": y})

    return events if events else None

def _drain_console_events():
    """Read all pending console input records and enqueue parsed events."""
    num_available = wintypes.DWORD(0)
    if not _kernel32.GetNumberOfConsoleInputEvents(_stdin_handle, ctypes.byref(num_available)):
        return
    if num_available.value == 0:
        return

    buf = (INPUT_RECORD * num_available.value)()
    num_read = wintypes.DWORD(0)
    if not _kernel32.ReadConsoleInputW(_stdin_handle, buf, len(buf), ctypes.byref(num_read)):
        raise OSError("ReadConsoleInputW failed")

    for i in range(num_read.value):
        rec = buf[i]
        if rec.EventType == KEY_EVENT:
            if rec.Event.KeyEvent.bKeyDown:
                parsed = _process_key_event(rec)
                if parsed is not None:
                    _event_queue.append(parsed)
        elif rec.EventType == MOUSE_EVENT:
            parsed = _process_mouse_event(rec)
            if parsed is None:
                continue
            if isinstance(parsed, list):
                _event_queue.extend(parsed)
            else:
                _event_queue.append(parsed)
        # ignore other event types

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def key(timeout=None, mouse=False):
    """
    Return the next available input event.

    Parameters:
        timeout: seconds to wait (float/int), 0 for non-blocking, None for infinite.
        mouse:   if True, mouse events are returned. Default False (keyboard only).

    Returns:
        For keyboard: a string (see module docstring).
        For mouse (when mouse=True): a dictionary.
        If no event before timeout: "TIMEOUT".
    """
    global _event_queue, _stdin_handle, _current_mouse_enabled

    if _stdin_handle is None:
        _init_console()

    # Adjust mouse mode if needed
    _set_mouse_mode(mouse)

    # Serve from queue, filtering out mouse events if mouse=False
    while _event_queue:
        ev = _event_queue.popleft()
        if isinstance(ev, dict) and not mouse:
            continue   # discard mouse events when disabled
        return ev

    # Translate timeout
    if timeout is None:
        ms = INFINITE
    elif timeout == 0:
        ms = 0
    else:
        ms = int(timeout * 1000)

    ret = _kernel32.WaitForSingleObject(_stdin_handle, ms)
    if ret == WAIT_TIMEOUT:
        return "TIMEOUT"
    if ret != WAIT_OBJECT_0:
        raise RuntimeError("WaitForSingleObject returned unexpected value")

    # Drain and try again
    _drain_console_events()
    while _event_queue:
        ev = _event_queue.popleft()
        if isinstance(ev, dict) and not mouse:
            continue
        return ev

    return "TIMEOUT"