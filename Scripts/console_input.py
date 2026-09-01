"""Cross-platform single-key and terminal mouse input.

The public API is intentionally unchanged::

    key(timeout=None, mouse=False) -> str | dict | "TIMEOUT"

Windows uses Console Input Records so its established behavior is preserved.
macOS and Linux use the standard POSIX terminal APIs and decode the ANSI input
sequences emitted by terminal emulators.  Mouse coordinates are zero-based on
every platform.
"""

import atexit
import collections
import os
import re
import sys
import time


_event_queue = collections.deque()


# ---------------------------------------------------------------------------
# Pure POSIX-sequence parsing helpers
# ---------------------------------------------------------------------------
# These helpers do not import POSIX-only modules, which keeps the module
# importable and testable on Windows as well.
_NEED_MORE = object()
_IGNORED = object()
_POSIX_MOUSE_RE = re.compile(rb"^\x1b\[<(\d+);(\d+);(\d+)([Mm])")
_posix_input_buffer = bytearray()
_posix_pressed_button = None
_posix_last_click = None


def _posix_modifier_prefix(parameter):
    """Map terminal modifier bits to the public ctrl/alt names.

    CSI modifiers are encoded as one plus a bitmask: Alt/Option is bit 2,
    Ctrl is bit 4, and Super/Command is bit 8.  Command intentionally shares
    the existing Ctrl output name on macOS.
    """
    try:
        modifier_bits = int(parameter) - 1
    except (TypeError, ValueError):
        return ""
    if modifier_bits & (4 | 8):
        return "ctrl/"
    if modifier_bits & 2:
        return "alt/"
    return ""


def _posix_alt_character(buffer):
    """Consume and return an ESC-prefixed printable character, if complete."""
    if len(buffer) < 2:
        return _NEED_MORE
    first = buffer[1]
    if 33 <= first <= 126:
        del buffer[:2]
        return "alt/" + chr(first)

    if 0xC2 <= first <= 0xDF:
        width = 2
    elif 0xE0 <= first <= 0xEF:
        width = 3
    elif 0xF0 <= first <= 0xF4:
        width = 4
    else:
        return _IGNORED
    if len(buffer) < width + 1:
        return _NEED_MORE
    try:
        character = bytes(buffer[1:width + 1]).decode("utf-8")
    except UnicodeDecodeError:
        return _IGNORED
    if not character.isprintable():
        return _IGNORED
    del buffer[:width + 1]
    return "alt/" + character


def _posix_mouse_event(code, x, y, terminator):
    """Translate one SGR mouse report to the Win32-compatible public shape."""
    global _posix_last_click, _posix_pressed_button

    # SGR coordinates are one-based; the existing game API is zero-based.
    x = max(0, x - 1)
    y = max(0, y - 1)
    button_code = code & 0b11
    button = {0: "left", 1: "middle", 2: "right"}.get(button_code)

    if code & 64:  # wheel event (64 = up, 65 = down)
        delta = 120 if button_code == 0 else -120
        return {
            "type": "mouse",
            "event": "wheel",
            "delta": delta,
            "x": x,
            "y": y,
        }

    if terminator == b"m" or button_code == 3:
        released = _posix_pressed_button or button
        _posix_pressed_button = None
        if released:
            return {
                "type": "mouse",
                "event": "up",
                "button": released,
                "x": x,
                "y": y,
            }
        return _IGNORED

    if code & 32:  # motion while a button is held
        _posix_last_click = None
        dragged = button or _posix_pressed_button
        _posix_pressed_button = dragged
        # The Windows implementation intentionally exposes left-button drags
        # only, so do the same on POSIX terminals.
        if dragged == "left":
            return {
                "type": "mouse",
                "event": "drag",
                "button": "left",
                "x": x,
                "y": y,
            }
        return _IGNORED

    if button:
        _posix_pressed_button = button
        now = time.monotonic()
        click = (button, x, y)
        if (
            _posix_last_click is not None
            and _posix_last_click[:3] == click
            and now - _posix_last_click[3] <= 0.5
        ):
            _posix_last_click = None
            return {
                "type": "mouse",
                "event": "double",
                "button": button,
                "x": x,
                "y": y,
            }
        _posix_last_click = (*click, now)
        return {
            "type": "mouse",
            "event": "down",
            "button": button,
            "x": x,
            "y": y,
        }
    return _IGNORED


def _extract_posix_event(buffer):
    """Remove and return one decoded event from a byte buffer."""
    if not buffer:
        return _NEED_MORE

    first = buffer[0]
    if first == 0x1B:
        mouse_match = _POSIX_MOUSE_RE.match(buffer)
        if mouse_match:
            code, x, y = (int(value) for value in mouse_match.groups()[:3])
            terminator = mouse_match.group(4)
            match_end = mouse_match.end()
            del buffer[:match_end]
            return _posix_mouse_event(
                code,
                x,
                y,
                terminator,
            )

        if bytes(buffer).startswith(b"\x1b[<"):
            # An SGR report is still arriving unless its M/m terminator is
            # present.  A malformed completed report is discarded safely.
            terminator_index = next(
                (
                    index
                    for index, value in enumerate(buffer[3:], start=3)
                    if value in (ord("M"), ord("m"))
                ),
                None,
            )
            if terminator_index is None:
                return _NEED_MORE
            del buffer[:terminator_index + 1]
            return _IGNORED

        if bytes(buffer).startswith(b"\x1b["):
            final_index = next(
                (
                    index
                    for index, value in enumerate(buffer[2:], start=2)
                    if 0x40 <= value <= 0x7E
                ),
                None,
            )
            if final_index is None:
                return _NEED_MORE
            final = chr(buffer[final_index])
            parameters = bytes(buffer[2:final_index]).decode("ascii", "ignore")
            del buffer[:final_index + 1]

            # Kitty/CSI-u enhanced keyboard reports expose modifiers that a
            # terminal can distinguish, including macOS Option and Command.
            if final == "u":
                fields = parameters.split(";")
                try:
                    character = chr(int(fields[0].split(":", 1)[0]))
                except (ValueError, OverflowError):
                    return _IGNORED
                prefix = _posix_modifier_prefix(
                    fields[1].split(":", 1)[0] if len(fields) > 1 else 1
                )
                if prefix and character.isprintable():
                    return prefix + character
                return character if character.isprintable() else _IGNORED

            key_name = {
                "A": "up",
                "B": "down",
                "C": "right",
                "D": "left",
            }.get(final)
            if key_name is None:
                return _IGNORED
            fields = parameters.split(";")
            prefix = _posix_modifier_prefix(fields[-1]) if len(fields) > 1 else ""
            return prefix + key_name

        if bytes(buffer).startswith(b"\x1bO"):
            if len(buffer) < 3:
                return _NEED_MORE
            final = chr(buffer[2])
            del buffer[:3]
            return {
                "A": "up",
                "B": "down",
                "C": "right",
                "D": "left",
            }.get(final, _IGNORED)

        if len(buffer) == 1:
            return _NEED_MORE
        alt_character = _posix_alt_character(buffer)
        if alt_character is _NEED_MORE:
            return _NEED_MORE
        if alt_character is not _IGNORED:
            return alt_character
        del buffer[0]
        return "esc"

    if first in (10, 13):
        del buffer[0]
        # Some terminals can produce CRLF. Treat it as one Enter press.
        if first == 13 and buffer[:1] == b"\n":
            del buffer[0]
        return "enter"
    if first in (8, 127):
        del buffer[0]
        return "backspace"
    if first == 32:
        del buffer[0]
        return "space"
    if 1 <= first <= 26:
        del buffer[0]
        return "ctrl/" + chr(first + 96)
    if 33 <= first <= 126:
        del buffer[0]
        return chr(first)

    if 0xC2 <= first <= 0xDF:
        width = 2
    elif 0xE0 <= first <= 0xEF:
        width = 3
    elif 0xF0 <= first <= 0xF4:
        width = 4
    else:
        del buffer[0]
        return _IGNORED

    if len(buffer) < width:
        return _NEED_MORE
    encoded = bytes(buffer[:width])
    del buffer[:width]
    try:
        character = encoded.decode("utf-8")
    except UnicodeDecodeError:
        return _IGNORED
    return character if character.isprintable() else _IGNORED


if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    # -----------------------------------------------------------------------
    # Windows Console Input backend
    # -----------------------------------------------------------------------
    STD_INPUT_HANDLE = -10
    INFINITE = 0xFFFFFFFF
    WAIT_OBJECT_0 = 0
    WAIT_TIMEOUT = 0x00000102

    ENABLE_PROCESSED_INPUT = 0x0001
    ENABLE_LINE_INPUT = 0x0002
    ENABLE_ECHO_INPUT = 0x0004
    ENABLE_MOUSE_INPUT = 0x0010
    ENABLE_EXTENDED_FLAGS = 0x0080
    ENABLE_QUICK_EDIT_MODE = 0x0040

    KEY_EVENT = 0x0001
    MOUSE_EVENT = 0x0002

    MOUSE_MOVED = 0x0001
    DOUBLE_CLICK = 0x0002
    MOUSE_WHEELED = 0x0004

    FROM_LEFT_1ST_BUTTON_PRESSED = 0x0001
    RIGHTMOST_BUTTON_PRESSED = 0x0002
    FROM_LEFT_2ND_BUTTON_PRESSED = 0x0004

    LEFT_CTRL_PRESSED = 0x0008
    RIGHT_CTRL_PRESSED = 0x0004

    VK_LEFT = 0x25
    VK_UP = 0x26
    VK_RIGHT = 0x27
    VK_DOWN = 0x28
    VK_RETURN = 0x0D
    VK_ESCAPE = 0x1B
    VK_BACK = 0x08
    VK_SPACE = 0x20

    class COORD(ctypes.Structure):
        _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

    class CHAR_UNION(ctypes.Union):
        _fields_ = [
            ("UnicodeChar", wintypes.WCHAR),
            ("AsciiChar", ctypes.c_char),
        ]

    class KEY_EVENT_RECORD(ctypes.Structure):
        _fields_ = [
            ("bKeyDown", ctypes.c_int),
            ("wRepeatCount", wintypes.WORD),
            ("wVirtualKeyCode", wintypes.WORD),
            ("wVirtualScanCode", wintypes.WORD),
            ("uChar", CHAR_UNION),
            ("dwControlKeyState", wintypes.DWORD),
        ]

    class MOUSE_EVENT_RECORD(ctypes.Structure):
        _fields_ = [
            ("dwMousePosition", COORD),
            ("dwButtonState", wintypes.DWORD),
            ("dwControlKeyState", wintypes.DWORD),
            ("dwEventFlags", wintypes.DWORD),
        ]

    class WINDOW_BUFFER_SIZE_RECORD(ctypes.Structure):
        _fields_ = [("dwSize", COORD)]

    class MENU_EVENT_RECORD(ctypes.Structure):
        _fields_ = [("dwCommandId", wintypes.UINT)]

    class FOCUS_EVENT_RECORD(ctypes.Structure):
        _fields_ = [("bSetFocus", ctypes.c_int)]

    class EVENT_UNION(ctypes.Union):
        _fields_ = [
            ("KeyEvent", KEY_EVENT_RECORD),
            ("MouseEvent", MOUSE_EVENT_RECORD),
            ("WindowBufferSizeEvent", WINDOW_BUFFER_SIZE_RECORD),
            ("MenuEvent", MENU_EVENT_RECORD),
            ("FocusEvent", FOCUS_EVENT_RECORD),
        ]

    class INPUT_RECORD(ctypes.Structure):
        _fields_ = [("EventType", wintypes.WORD), ("Event", EVENT_UNION)]

    _kernel32 = ctypes.windll.kernel32
    _stdin_handle = None
    _original_mode = None
    _base_mode = None
    _current_mouse_enabled = None
    _prev_button_state = 0

    def _restore_console():
        if _original_mode is not None and _stdin_handle is not None:
            _kernel32.SetConsoleMode(_stdin_handle, _original_mode)

    def _init_console():
        global _stdin_handle, _original_mode, _base_mode
        global _current_mouse_enabled

        _stdin_handle = _kernel32.GetStdHandle(STD_INPUT_HANDLE)
        if _stdin_handle == wintypes.HANDLE(-1).value:
            raise OSError("GetStdHandle failed")

        mode = wintypes.DWORD()
        if not _kernel32.GetConsoleMode(_stdin_handle, ctypes.byref(mode)):
            raise OSError("GetConsoleMode failed")
        _original_mode = mode.value

        _base_mode = _original_mode
        _base_mode &= ~(
            ENABLE_LINE_INPUT | ENABLE_ECHO_INPUT | ENABLE_PROCESSED_INPUT
        )
        _base_mode &= ~ENABLE_QUICK_EDIT_MODE
        _base_mode |= ENABLE_EXTENDED_FLAGS

        _kernel32.SetConsoleMode(_stdin_handle, _base_mode)
        _current_mouse_enabled = False
        atexit.register(_restore_console)

    def _set_mouse_mode(enable):
        global _current_mouse_enabled
        if _current_mouse_enabled == enable:
            return
        new_mode = _base_mode | (ENABLE_MOUSE_INPUT if enable else 0)
        _kernel32.SetConsoleMode(_stdin_handle, new_mode)
        _current_mouse_enabled = enable

    def _button_name(state_bits):
        if state_bits & FROM_LEFT_1ST_BUTTON_PRESSED:
            return "left"
        if state_bits & RIGHTMOST_BUTTON_PRESSED:
            return "right"
        if state_bits & FROM_LEFT_2ND_BUTTON_PRESSED:
            return "middle"
        return None

    def _process_key_event(record):
        event = record.Event.KeyEvent
        virtual_key = event.wVirtualKeyCode
        ctrl_held = event.dwControlKeyState & (
            LEFT_CTRL_PRESSED | RIGHT_CTRL_PRESSED
        )

        if ctrl_held and 0x41 <= virtual_key <= 0x5A:
            return "ctrl/" + chr(virtual_key + 32)

        special = {
            VK_LEFT: "left",
            VK_RIGHT: "right",
            VK_UP: "up",
            VK_DOWN: "down",
            VK_RETURN: "enter",
            VK_ESCAPE: "esc",
            VK_BACK: "backspace",
            VK_SPACE: "space",
        }
        if virtual_key in special:
            return special[virtual_key]

        character = event.uChar.UnicodeChar
        if character and character != "\x00" and character.isprintable():
            return character
        return None

    def _process_mouse_event(record):
        global _prev_button_state

        mouse_event = record.Event.MouseEvent
        flags = mouse_event.dwEventFlags
        x = mouse_event.dwMousePosition.X
        y = mouse_event.dwMousePosition.Y

        if flags & DOUBLE_CLICK:
            button = _button_name(mouse_event.dwButtonState)
            if button:
                _prev_button_state = mouse_event.dwButtonState
                return {
                    "type": "mouse",
                    "event": "double",
                    "button": button,
                    "x": x,
                    "y": y,
                }
            return None

        if flags & MOUSE_WHEELED:
            delta = ctypes.c_short(mouse_event.dwButtonState >> 16).value
            return {
                "type": "mouse",
                "event": "wheel",
                "delta": delta,
                "x": x,
                "y": y,
            }

        if flags & MOUSE_MOVED:
            _prev_button_state = mouse_event.dwButtonState
            if mouse_event.dwButtonState & FROM_LEFT_1ST_BUTTON_PRESSED:
                return {
                    "type": "mouse",
                    "event": "drag",
                    "button": "left",
                    "x": x,
                    "y": y,
                }
            return None

        current = mouse_event.dwButtonState
        previous = _prev_button_state
        _prev_button_state = current
        events = []

        changed_down = (current ^ previous) & current
        for bit, button in (
            (FROM_LEFT_1ST_BUTTON_PRESSED, "left"),
            (RIGHTMOST_BUTTON_PRESSED, "right"),
            (FROM_LEFT_2ND_BUTTON_PRESSED, "middle"),
        ):
            if changed_down & bit:
                events.append(
                    {
                        "type": "mouse",
                        "event": "down",
                        "button": button,
                        "x": x,
                        "y": y,
                    }
                )

        changed_up = (current ^ previous) & previous
        for bit, button in (
            (FROM_LEFT_1ST_BUTTON_PRESSED, "left"),
            (RIGHTMOST_BUTTON_PRESSED, "right"),
            (FROM_LEFT_2ND_BUTTON_PRESSED, "middle"),
        ):
            if changed_up & bit:
                events.append(
                    {
                        "type": "mouse",
                        "event": "up",
                        "button": button,
                        "x": x,
                        "y": y,
                    }
                )
        return events if events else None

    def _drain_console_events():
        available = wintypes.DWORD(0)
        if not _kernel32.GetNumberOfConsoleInputEvents(
            _stdin_handle,
            ctypes.byref(available),
        ):
            return
        if available.value == 0:
            return

        records = (INPUT_RECORD * available.value)()
        read_count = wintypes.DWORD(0)
        if not _kernel32.ReadConsoleInputW(
            _stdin_handle,
            records,
            len(records),
            ctypes.byref(read_count),
        ):
            raise OSError("ReadConsoleInputW failed")

        for index in range(read_count.value):
            record = records[index]
            if record.EventType == KEY_EVENT and record.Event.KeyEvent.bKeyDown:
                parsed = _process_key_event(record)
                if parsed is not None:
                    _event_queue.append(parsed)
            elif record.EventType == MOUSE_EVENT:
                parsed = _process_mouse_event(record)
                if parsed is None:
                    continue
                if isinstance(parsed, list):
                    _event_queue.extend(parsed)
                else:
                    _event_queue.append(parsed)

    def key(timeout=None, mouse=False):
        """Return one key/mouse event, or ``"TIMEOUT"`` when none arrives."""
        global _stdin_handle

        if _stdin_handle is None:
            _init_console()
        _set_mouse_mode(mouse)

        while _event_queue:
            event = _event_queue.popleft()
            if isinstance(event, dict) and not mouse:
                continue
            return event

        if timeout is None:
            milliseconds = INFINITE
        elif timeout == 0:
            milliseconds = 0
        else:
            milliseconds = max(0, int(timeout * 1000))

        result = _kernel32.WaitForSingleObject(_stdin_handle, milliseconds)
        if result == WAIT_TIMEOUT:
            return "TIMEOUT"
        if result != WAIT_OBJECT_0:
            raise RuntimeError("WaitForSingleObject returned unexpected value")

        _drain_console_events()
        while _event_queue:
            event = _event_queue.popleft()
            if isinstance(event, dict) and not mouse:
                continue
            return event
        return "TIMEOUT"

else:
    import select
    import termios
    import tty

    # -----------------------------------------------------------------------
    # macOS/Linux terminal backend
    # -----------------------------------------------------------------------
    _posix_mouse_enabled = None
    _posix_terminal_descriptor = None
    _posix_original_attributes = None

    def _ensure_raw_mode(descriptor):
        """Keep terminal input raw so bytes cannot be echoed between reads."""
        global _posix_terminal_descriptor, _posix_original_attributes

        if not os.isatty(descriptor):
            return
        if (
            _posix_terminal_descriptor == descriptor
            and _posix_original_attributes is not None
        ):
            return

        # There should only be one stdin terminal, but restore a previous
        # descriptor before switching if an embedding application replaces it.
        if (
            _posix_terminal_descriptor is not None
            and _posix_original_attributes is not None
        ):
            try:
                termios.tcsetattr(
                    _posix_terminal_descriptor,
                    termios.TCSANOW,
                    _posix_original_attributes,
                )
            except (OSError, termios.error):
                pass

        _posix_terminal_descriptor = descriptor
        _posix_original_attributes = termios.tcgetattr(descriptor)
        # Cbreak mode provides immediate, no-echo input while preserving the
        # output processing (notably ONLCR) that keeps printed newlines aligned
        # on macOS terminals. Full raw mode disables that output translation.
        tty.setcbreak(descriptor, termios.TCSANOW)

    def _set_mouse_mode(enable):
        """Toggle basic, drag, and SGR-coordinate mouse reporting."""
        global _posix_mouse_enabled
        if _posix_mouse_enabled == enable:
            return
        if _posix_mouse_enabled is None and not enable:
            _posix_mouse_enabled = False
            return
        if getattr(sys.stdout, "isatty", lambda: False)():
            if enable:
                sequence = "\x1b[?1000h\x1b[?1002h\x1b[?1006h"
            else:
                sequence = "\x1b[?1006l\x1b[?1002l\x1b[?1000l"
            try:
                sys.stdout.write(sequence)
                sys.stdout.flush()
            except (OSError, ValueError):
                pass
        _posix_mouse_enabled = enable

    def _restore_console():
        if _posix_mouse_enabled:
            _set_mouse_mode(False)
        if (
            _posix_terminal_descriptor is not None
            and _posix_original_attributes is not None
        ):
            try:
                termios.tcsetattr(
                    _posix_terminal_descriptor,
                    termios.TCSANOW,
                    _posix_original_attributes,
                )
            except (OSError, termios.error):
                pass

    atexit.register(_restore_console)

    def _queued_event(mouse):
        while _event_queue:
            event = _event_queue.popleft()
            if isinstance(event, dict) and not mouse:
                continue
            return event
        return None

    def key(timeout=None, mouse=False):
        """Return one key/mouse event, or ``"TIMEOUT"`` when none arrives."""
        try:
            descriptor = sys.stdin.fileno()
        except (AttributeError, OSError, ValueError) as error:
            raise OSError("Standard input does not expose a terminal handle") from error

        _ensure_raw_mode(descriptor)
        _set_mouse_mode(mouse)

        queued = _queued_event(mouse)
        if queued is not None:
            return queued

        start = time.monotonic()
        deadline = None if timeout is None else start + max(0.0, float(timeout))
        escape_deadline = None
        immediate_poll_pending = timeout is not None and float(timeout) <= 0

        try:
            while True:
                event = _extract_posix_event(_posix_input_buffer)
                if event is not _NEED_MORE:
                    escape_deadline = None
                    if event is _IGNORED:
                        continue
                    if isinstance(event, dict) and not mouse:
                        continue
                    return event

                now = time.monotonic()
                if _posix_input_buffer[:1] == b"\x1b":
                    if escape_deadline is None:
                        escape_deadline = now + 0.03
                    elif now >= escape_deadline:
                        del _posix_input_buffer[0]
                        return "esc"

                if (
                    deadline is not None
                    and now >= deadline
                    and not immediate_poll_pending
                ):
                    if _posix_input_buffer[:1] == b"\x1b":
                        del _posix_input_buffer[0]
                        return "esc"
                    return "TIMEOUT"

                waits = []
                if deadline is not None:
                    waits.append(max(0.0, deadline - now))
                if escape_deadline is not None:
                    waits.append(max(0.0, escape_deadline - now))
                wait_time = min(waits) if waits else None

                readable, _, _ = select.select([descriptor], [], [], wait_time)
                immediate_poll_pending = False
                if not readable:
                    if deadline is not None and time.monotonic() >= deadline:
                        return "TIMEOUT"
                    continue
                incoming = os.read(descriptor, 64)
                if not incoming:
                    return "TIMEOUT"
                _posix_input_buffer.extend(incoming)
        finally:
            # Raw/no-echo mode intentionally remains active between key()
            # calls. Restoring it here creates a window where macOS echoes a
            # key or mouse report at the current cursor position.
            pass
