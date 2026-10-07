"""*******************************************************************************
*                                                                                *
*   ██      ██    ████    ██████    ██    ██  ██████  ██    ██    ██████  ██     *
*   ██      ██  ██    ██  ██    ██  ████  ██    ██    ████  ██  ██        ██     *
*   ██  ██  ██  ████████  ██████    ██  ████    ██    ██  ████  ██  ████  ██     *
*   ██  ██  ██  ██    ██  ██    ██  ██    ██    ██    ██    ██  ██    ██         *
*     ██  ██    ██    ██  ██    ██  ██    ██  ██████  ██    ██    ██████  ██     *
*                                                                                *
**********************************************************************************
*                                                                                *
*   You are about to embark on an adventure through this code.                   *
*   I'm sorry for what your eyes are about to see. Very much.                    *
*                                                                                *
*   Some parts of the code belong to others (or AI). I have no idea which ones.  *
*   I know... shameful. If you created something here, drop me a credit.         *
*                                                                                *                                                                            
**********************************************************************************                                                                            
*                                                                                *
*   In case you actually understand what you're doing, you should be fine.       *
*   However, don't blame yourself if it doesn't work.                            *
*                                                                                *                                                                                
*******************************************************************************"""
import difflib

from Scripts.console_input import key, terminal_background
from Scripts.Settings.editor import (
    SettingEditor,
    back_button_contains,
    boolean_control_contains,
    boolean_slider_parts,
    category_index_at,
    format_setting_value,
    setting_is_off,
    setting_index_at,
    slider_step_count,
    volume_slider_parts,
    volume_value_at_mouse,
)
from Scripts.Settings.schema import (
    KEYBIND_DEFAULTS,
    PERSISTENT_DEFAULTS,
    SETTINGS_BY_ATTR,
    SETTINGS_PAGES,
    CATEGORY_NAMES,
    CATEGORY_ICONS,
    CATEGORY_DESCRIPTIONS,
)
from Scripts.save_backups import backup_before_write, backup_transaction, trim_backups, create_backup
from Scripts.sort import sort_inventory
from Scripts.battle import apply_difficulty, attack_damage, short_action_log
from Scripts.Settings.text import SIMPLE_DESCRIPTIONS
from Scripts.Settings.search import find_settings
import atexit, os, time, sys, ctypes, ast, math, operator as op, subprocess, json, re, random, shlex, shutil, tempfile, stat, urllib.request  # noqa: E401, E402
from pathlib import Path  # noqa: E402
from copy import copy
from functools import wraps
from typing import Literal  # noqa: E402
RGB="[38;2;"

PROJECT_ROOT = Path(__file__).resolve().parent
# use the game folder for saves and sounds, no matter where we launch from
os.chdir(PROJECT_ROOT)


import time
import sys
from Scripts.console_input import key





version=2
subversion=0
subberversion="0-pre3"

CHARACTER_MAX_LEVEL = 100
WEAPON_MAX_LEVEL = 25
ARMOR_MAX_LEVEL = 20
HEADWEAR_MAX_LEVEL = 20
FRAGMENT_MAX_LEVEL = 15
WEAPON_REFINEMENT_MAX = 3
WEAPON_REFINEMENT_CRIT_DAMAGE = 7.5
WEAPON_REFINEMENT_ATK_RATE = 0.10
WEAPON_REFINEMENT_DUST_BASE_COST = 50

FRAGMENT_SLOTS = ("Bracelet", "Necklace", "Ring")
FRAGMENT_MAIN_STATS = {
    "ATK": ((12, 25), 4),
    "ATK %": ((3, 6), 0.8),
    "HP": ((80, 160), 30),
    "HP %": ((4, 7), 1),
    "DEF": ((5, 10), 2),
    "Speed": ((2, 4), 0.5),
    "Crit Rate": ((2, 4), 0.6),
    "Crit Damage": ((5, 10), 1.5),
}
FRAGMENT_SUBSTAT_RANGES = {
    "ATK": (5, 15),
    "ATK %": (1, 4),
    "HP": (25, 80),
    "HP %": (1, 5),
    "DEF": (2, 8),
    "Speed": (1, 3),
    "Crit Rate": (1, 4),
    "Crit Damage": (2, 8),
}
FRAGMENT_PERCENT_STATS = {
    "ATK %",
    "HP %",
    "Crit Rate",
    "Crit Damage",
}
FRAGMENT_OFFENSIVE_SCALE = 0.5
FRAGMENT_BONUS_SCALES = {
    "atk_flat": FRAGMENT_OFFENSIVE_SCALE,
    "atk_percent": FRAGMENT_OFFENSIVE_SCALE,
    "hp_flat": 0.5,
    "hp_percent": 0.75,
    "def_flat": 0.5,
    "def_percent": 0.5,
    "speed": 1.0,
    "crit_rate": FRAGMENT_OFFENSIVE_SCALE,
    "crit_damage": FRAGMENT_OFFENSIVE_SCALE,
}
FRAGMENT_SETS = {
    "Warrior": {
        2: {"atk_percent": 12},
        3: {"speed": 8},
    },
    "Guardian": {
        2: {"def_percent": 15},
        3: {"damage_taken_percent": -8},
    },
    "Assassin": {
        2: {"crit_rate": 10},
        3: {"crit_damage": 25},
    },
    "Titan": {
        2: {"hp_percent": 20},
        3: {"healing_received_percent": 8},
    },
}

ARMOR_LEVEL_POWER_DEFAULTS = {
    "02": 0.035,
    "03": 0.04,
    "07": 0.042,
    "0b": 0.035,
    "0c": 0.037,
    "0d": 0.045,
    "0e": 0.05,
}


if subberversion != 0:
    TITLE = f"Battles of Bench - beta {version}.{subversion}.{subberversion}"
else:
    TITLE = f"Battles of Bench - beta {version}.{subversion}"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8") # actually make it display shit


def _enable_virtual_terminal_output():
    # let Windows use ansi colors too
    if os.name != "nt":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        output_handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint()
        if kernel32.GetConsoleMode(output_handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(output_handle, mode.value | 0x0004)
    except (AttributeError, OSError):
        pass


def _set_terminal_title(title):
    # set the terminal title
    if getattr(sys.stdout, "isatty", lambda: False)():
        sys.stdout.write(f"\x1b]0;{title}\x07")
        sys.stdout.flush()


def _create_windows_kill_job(process):
    # close the sound helper when the game closes on Windows
    if os.name != "nt":
        return None

    from ctypes import wintypes

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        job_handle = kernel32.CreateJobObjectW(None, None)
        if not job_handle:
            return None

        job_info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        job_info.BasicLimitInformation.LimitFlags = 0x00002000
        configured = kernel32.SetInformationJobObject(
            job_handle,
            9,  # JobObjectExtendedLimitInformation
            ctypes.byref(job_info),
            ctypes.sizeof(job_info),
        )
        assigned = configured and kernel32.AssignProcessToJobObject(
            job_handle,
            process._handle,
        )
        if not assigned:
            kernel32.CloseHandle(job_handle)
            return None
        return job_handle
    except (AttributeError, OSError):
        return None


def _stop_sound_process():
    # stop the sound helper when leaving the game
    if sound_process.poll() is None:
        try:
            sound("QUIT")
            sound_process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            try:
                sound_process.kill()
                sound_process.wait(timeout=1)
            except (OSError, subprocess.TimeoutExpired):
                pass
    if _windows_sound_job is not None:
        try:
            ctypes.windll.kernel32.CloseHandle(_windows_sound_job)
        except (AttributeError, OSError):
            pass


_enable_virtual_terminal_output()
_set_terminal_title(TITLE)

# clear old sound commands so they don't all play at startup
if __name__ == "__main__":
    sound_queue_path = PROJECT_ROOT / "General" / "Temp" / "sound_cmd_queue.txt"
    sound_queue_path.parent.mkdir(parents=True, exist_ok=True)
    sound_queue_path.write_text("", encoding="utf-8")

    sound_process = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "Scripts" / "sound_player.py")],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _windows_sound_job = _create_windows_kill_job(sound_process)
    atexit.register(_stop_sound_process)

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
🎯 FUNCTIONS
This section handles (I think) every single backend function designed to keep BoB running... well, as it is.
DISCLAIMER -> Some of these functions are made by AI. Deeply sorry if this sounds disappointing to you.
In a perfect world, I would have hand-crafted everything. But I also want to actually finish the damn thing, so here we are.
Oh well.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

_ALLOWED_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg
}

# well, just see the name. Obvious, right?
def get_item_max_level(category):
    return {
        "Weapons": WEAPON_MAX_LEVEL,
        "Bodywear": ARMOR_MAX_LEVEL,
        "Helmets": HEADWEAR_MAX_LEVEL,
        "Fragments": FRAGMENT_MAX_LEVEL,
    }.get(category)

# same thing, let's go.
def clamp_item_level(level, category):
    try:
        parsed = int(level)
    except Exception:
        parsed = 0

    max_level = get_item_max_level(category)
    if max_level is None:
        return max(0, parsed)
    return max(0, min(parsed, max_level))

# oh wow, again!
def required_player_level_for_item(item_level, category):
    level = clamp_item_level(item_level, category)
    if level <= 1:
        return 0
    if category == "Weapons":
        return level * 4
    if category in ("Bodywear", "Helmets"):
        return level * 5
    if category == "Fragments":
        if level <= 3:
            return 0
        if level <= 6:
            return 20
        if level <= 9:
            return 40
        if level <= 12:
            return 60
        return 80
    return level

# SAFE EVAL -> Used for getx() later. You'll see why. It handles safer calculation.
def safe_eval(expr):
    def _eval(node):
        if isinstance(node, ast.Constant):  # modern number node
            if isinstance(node.value, (int, float)):
                return node.value
            raise TypeError("Invalid constant")

        elif isinstance(node, ast.BinOp):
            if type(node.op) not in _ALLOWED_OPS:
                raise TypeError("Operator not allowed")
            return _ALLOWED_OPS[type(node.op)](
                _eval(node.left),
                _eval(node.right)
            )

        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in _ALLOWED_OPS:
                raise TypeError("Operator not allowed")
            return _ALLOWED_OPS[type(node.op)](
                _eval(node.operand)
            )

        else:
            raise TypeError("Unsupported expression")

    parsed = ast.parse(expr, mode='eval')
    value = _eval(parsed.body)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("Invalid number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Invalid number")
    return value

# woosh, character screen rounding!! DEF is happy with this
def char_round(value):
    return format_number(value)

# Simple. "cursor(True)" to show, "cursor(False)" to hide.
def cursor(x):
    print("\x1b[?25h" if x else "\x1b[?25l", end="", flush=True)

# Move cursor to (row, col). Yes, it's reversed because I got used to ANSI.
def move(row, col):
    print(f"[{row};{col}H", end="")

# Flashes the prompt in red for a moment. Used in getx() when input is invalid.
def flash_prompt(row, col, prompt):
    cursor(False)
    move(row, col)
    print(f"{xlred}{bold}{prompt}{reset}", end="", flush=True)
    animation_sleep(0.12)
    move(row, col)
    print(prompt, end="", flush=True)
    cursor(True)
    
ANSI_PATTERN = re.compile(r'\x1b\[[0-9;?]*[A-Za-z]') # what this does, I have no clue.

# get visible length without ansi codes
def visible_len(text):
    return len(ANSI_PATTERN.sub('', text))


def pad_visible(text, width, fill=" "):
    # pad using the visible width, ansi colors do not count
    return text + fill * max(0, width - visible_len(text))

# FINALLY, getx(). Line input, but actually good.
def getx(
    row, # where the input starts (row)
    col, # same as row but col.
    prompt="", # the prompt, if any, that appears before the input
    max_len=None, # maximum length of input. None for unlimited.
    expect=None, # wanna force a data type? "int", "float", or None for any string.
    min_val=None, # for numbers, set a minimum accepted value. None for no minimum.
    max_val=None, # same with min, but max. Wow!
    allow_none=False, # if True, allows empty input (returns None). If False, empty input is invalid.
    highlight_prefix=None, # if set, this string is prefixed to the input for styling when the input is valid. E.g. set highlight_prefix=x2 to make valid input green.
    highlight_suffix=None, # exactly the same as highlight_prefix but AFTER the thing. Mostly used for resetting color with reset.
    highlight_keywords=None, # dictionary of keywords to highlight in the input. Format: {"keyword": (prefix, suffix), ...}. E.g. {"*": (x4, reset)} would make all asterisks red regardless of validity.
    timeout=None # in case you confuse key() with getx(), this silently passes the timeout to key() - otherwise, it does nothing. so friendly!
):
    if expect == "key":
        return key(timeout=timeout)

    cursor(True)

    ANSI_PATTERN = re.compile(r'\x1b\[[0-9;?]*[A-Za-z]') # again, no clue.
    def visible_len(text):
        return len(ANSI_PATTERN.sub('', text))

    try:
        while True:
            buffer = ""
            last_render_len = 0

            move(row, col)
            print(prompt, end="", flush=True)
            start_col = col + visible_len(prompt)

            while True:

                is_valid = False
                preview_result = None
                is_expression = False

                try:
                    if buffer and expect in ("int", "float"):
                        if any(op in buffer for op in "+-*/%()"):
                            is_expression = True
                            preview_result = safe_eval(buffer)

                            if isinstance(preview_result, float) and preview_result.is_integer():
                                preview_result = int(preview_result)

                            if expect == "int":
                                preview_result = int(preview_result)
                            elif expect == "float":
                                preview_result = float(preview_result)

                            if (min_val is None or preview_result >= min_val) and \
                               (max_val is None or preview_result <= max_val):
                                is_valid = True
                        else:
                            val = float(buffer) if expect == "float" or "." in buffer else int(buffer)
                            if isinstance(val, float) and not math.isfinite(val):
                                raise ValueError("Invalid number")
                            if isinstance(val, float) and val.is_integer():
                                val = int(val)
                            if (min_val is None or val >= min_val) and \
                               (max_val is None or val <= max_val):
                                is_valid = True
                except Exception:
                    pass

                # ----- BUILD DISPLAY -----
                raw_display = buffer

                if highlight_keywords:
                    for word, (pre, post) in highlight_keywords.items():
                        pattern = r'\b' + re.escape(word) + r'\b'
                        raw_display = re.sub(pattern, f"{pre}{word}{post}", raw_display)

                preview_text = ""
                if is_expression and preview_result is not None:
                    if isinstance(preview_result, float):
                    # Covers 3.0, 3., 3.000 etc.
                        if preview_result.is_integer():
                            preview_result = int(preview_result)
                    if is_valid:
                        preview_text = f" {x7}= {round(preview_result,2)}{reset}"
                    else:
                        preview_text = f" {xlred}= {round(preview_result,2)}{reset}"

                if is_valid and highlight_prefix:
                    styled_buffer = f"{highlight_prefix}{raw_display}{highlight_suffix or ''}"
                else:
                    styled_buffer = raw_display

                display = styled_buffer + preview_text

                # ----- CLEAR PREVIOUS -----
                move(row, start_col)
                clear_width = max(last_render_len, max_len or 50)
                print(" " * clear_width, end="", flush=True)

                # ----- PRINT -----
                move(row, start_col)
                print(display, end="", flush=True)

                last_render_len = visible_len(display)

                # ----- CARET FIX -----
                if preview_text:
                    back = visible_len(preview_text)
                    print(f"\x1b[{back}D", end="", flush=True)

                ch = key()

                if ch == "enter":
                    break

                if ch == "backspace":
                    buffer = buffer[:-1]
                    continue

                if ch == "space":
                    ch = " "

                if not isinstance(ch, str) or len(ch) != 1 or not ch.isprintable():
                    continue

                if max_len and len(buffer) >= max_len:
                    continue

                buffer += ch

            # ----- FINAL VALIDATION -----

            if buffer == "":
                if allow_none:
                    move(row + 1, 1)
                    cursor(False)
                    print()
                    return None
                flash_prompt(row, col, prompt)
                continue

            try:
                if expect in ("int", "float"):
                    if any(op in buffer for op in "+-*/%()"):
                        value = safe_eval(buffer)
                    else:
                        value = float(buffer) if expect == "float" or "." in buffer else int(buffer)

                    if isinstance(value, float) and not math.isfinite(value):
                        raise ValueError("Invalid number")
                    if isinstance(value, float) and value.is_integer():
                        value = int(value)

                    if expect == "int":
                        value = int(value)
                    elif expect == "float":
                        value = float(value)

                    if (min_val is not None and value < min_val) or \
                       (max_val is not None and value > max_val):
                        flash_prompt(row, col, prompt)
                        continue
                else:
                    value = buffer
            except Exception:
                flash_prompt(row, col, prompt)
                continue
            move(row + 1, 1)
            cursor(False)
            print()
            if isinstance(value, float):
            # Covers 3.0, 3., 3.000 etc.
                if value.is_integer():
                    value = int(value)
            return value
    finally:
        cursor(False)

# Insane tech literacy required to understand this. Simply... colors text.
def rgb(r, g, b):
    return f"[38;2;{r};{g};{b}m"

# Same as rgb but for background. Yes, I know, the name doesn't make sense. But oh well.
def rgback(r, g, b):
    return f"[48;2;{r};{g};{b}m"

# Finally, actually global variables. Thanks, Batch.
def save_operation(action):
    # one backup for the whole action
    @wraps(action)
    def wrapped(*args, **kwargs):
        with backup_transaction(PROJECT_ROOT):
            return action(*args, **kwargs)
    return wrapped


def write_file(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    owner = globals().get("setting")
    backup_before_write(PROJECT_ROOT, path, value, getattr(owner, "backup_count", 3))
    temp_path = None
    try:
        # finish writing before replacing the old file
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as f:
            temp_path = Path(f.name)
            f.write(str(value))
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


class GeneralVariables:
    pass
d = GeneralVariables()
class PlayerData:
    def __init__(self, filename="data.txt"):
        # ───────────── PATH SETUP ─────────────
        base_dir = os.path.dirname(os.path.abspath(__file__))
        player_dir = os.path.join(base_dir, "Player")
        os.makedirs(player_dir, exist_ok=True)

        self._path = os.path.join(player_dir, filename)

        # ───────────── PERSISTENT SCHEMA ─────────────
        # Only keys here will be saved to file
        self._persistent_fields = {
            "dust": 0,
            "gems": 0,
            "level": 1,
            "money": 0,
            "skill_main": 1,
            "skill_skill": 1,
            "skill_ult": 1,
            "skill_talent": 1,
            "xp": 0,
            "xpneeded": 25,
            "tryd": 0
        }

        player_name_path = os.path.join(os.getcwd(), "General", "playername.txt")
        if os.path.exists(player_name_path):
            with open(player_name_path, "r", encoding="utf-8") as f:
                self.name = f.read().strip() or "Player"
        else:
            self.name = "Player"

        self.load()

    # ───────────── LOAD ─────────────
    def load(self):
        if not os.path.exists(self._path):
            self._create_default_file()

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, UnicodeError):
            data = {}
        if not isinstance(data, dict):
            data = {}

        # Load persistent stats only
        for key, default in self._persistent_fields.items():
            setattr(self, key, self._validated_value(key, data.get(key, default), default))

    def _validated_value(self, key, value, default):
        if not isinstance(value, int) or isinstance(value, bool):
            return default
        minimum = 1 if key == "level" or key == "xpneeded" or key.startswith("skill_") else 0
        if value < minimum:
            return default
        if key == "level":
            return min(value, CHARACTER_MAX_LEVEL)
        if key.startswith("skill_"):
            return min(value, 10)
        return value

    # ───────────── SAVE ─────────────
    def save(self):
        for key, default in self._persistent_fields.items():
            setattr(self, key, self._validated_value(key, getattr(self, key, default), default))
        data = {
            key: getattr(self, key)
            for key in self._persistent_fields.keys()
        }

        write_file(self._path, json.dumps(data, indent=4))

    # ───────────── RESET ─────────────
    def reset(self):
        for key, default in self._persistent_fields.items():
            setattr(self, key, default)
        self.save()

    # ───────────── CREATE DEFAULT FILE ─────────────
    def _create_default_file(self):
        write_file(self._path, json.dumps(self._persistent_fields, indent=4))

player = PlayerData()
class EnemyData:
    def __init__(self, **stats):
        for name, value in stats.items():
            setattr(self, name, value)

enemy = EnemyData()


# Load settings.
class SettingsData:
    _REDUCE_MOTION_OVERRIDES = {
        "animation_speed": 1.0,
        "menu_transitions": False,
        "disable_startup_animation": True,
        "victory_celebration": 0,
    }
    _REDUCE_MOTION_LOCKED_FIELDS = set(_REDUCE_MOTION_OVERRIDES)

    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        settings_dir = os.path.join(base_dir, "Settings")
        os.makedirs(settings_dir, exist_ok=True)

        self._path = os.path.join(settings_dir, "settings.txt")
        self._legacy_keybind_path = os.path.join(settings_dir, "keybinds.txt")
        self._settings_by_attr = SETTINGS_BY_ATTR
        self._keybind_fields = tuple(KEYBIND_DEFAULTS)

        # keep old values, use the settings pages for editable defaults
        legacy_defaults = {
            "difficulty": 0,
            "datatype": 1,
            "sorting": 0,
            "levelup_mode": 0,
            "pronouns": "they/them/their",
            "skipboot": False,
            "skiplevelanim": False,
            "soon": False,
            "_animation_slider_reversed": True,
            "_animation_speed_multiplier": True,
        }
        self._persistent_fields = {
            **legacy_defaults,
            **PERSISTENT_DEFAULTS,
        }

        self.inventory_last_selections = {}
        self.load()

    @staticmethod
    def _read_json(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, UnicodeError):
            return {}
        return loaded if isinstance(loaded, dict) else {}

    def _validated_value(self, key, value, default):
        item = self._settings_by_attr.get(key)
        setting_type = item.get("type") if item else None

        # convert the old animation choices
        if key == "animation_speed" and isinstance(value, str):
            value = {
                "instant": 2.0,
                "fast": 1.5,
                "normal": 1.0,
            }.get(value.casefold(), value)

        if key == "battle_difficulty" and isinstance(value, str):
            value = {
                "very easy": 0,
                "easy": 0,
                "normal": 1,
                "hard": 2,
                "very hard": 2,
                "extreme": 3,
            }.get(value.casefold(), value)

        # convert the old hp display names
        if key == "battle_health_display" and isinstance(value, str):
            value = {
                "hp": "Number",
                "both": "Both number and bar",
                "both bar and hp": "Both number and bar",
            }.get(value.casefold(), value)

        if setting_type == "bool":
            return value if isinstance(value, bool) else default
        if setting_type == "keybind":
            if not isinstance(value, str) or not value.strip():
                return default
            value = value.strip().lower()
            allowed_keys = item.get("allowed_keys")
            return value if not allowed_keys or value in allowed_keys else default
        if setting_type == "choice":
            if value in item.get("choices", ()):
                return value
            if isinstance(value, str):
                for choice in item.get("choices", ()):
                    if value.casefold() == choice.casefold():
                        return choice
            return default
        if setting_type == "slider":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return default
            if not math.isfinite(value):
                return default
            value = max(item["min"], min(item["max"], value))
            step = item.get("step", 1)
            value = item["min"] + round((value - item["min"]) / step) * step
            value = round(value, 6)
            if isinstance(default, int):
                return int(round(value))
            return float(value)

        # check older settings too
        if isinstance(default, bool):
            return value if isinstance(value, bool) else default
        if isinstance(default, int):
            return value if isinstance(value, int) and not isinstance(value, bool) else default
        if isinstance(default, float):
            return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default
        if isinstance(default, str):
            return value if isinstance(value, str) else default
        return value

    def load(self):
        data = self._read_json(self._path)
        if (
            data.get("inventory_sorting") == "Off"
            and "sort_items_automatically" not in data
        ):
            data["sort_items_automatically"] = False
            data["inventory_sorting"] = "Name"
        # old speed used a 0-10 slider; now we save the actual multiplier
        speed_migrated = not data.get("_animation_speed_multiplier", False)
        if speed_migrated:
            old_speed = data.get("animation_speed")
            if isinstance(old_speed, (int, float)) and not isinstance(old_speed, bool):
                if "_animation_slider_reversed" not in data:
                    old_speed = 10 - old_speed
                data["animation_speed"] = max(0.5, min(2.0, 1 + old_speed / 10))
        data["_animation_speed_multiplier"] = True
        # remembered bag positions belong to this run, not the save file
        data.pop("inventory_last_selections", None)
        legacy_keybinds = self._read_json(self._legacy_keybind_path)
        needs_sync = speed_migrated or set(self._persistent_fields) - set(data)
        needs_sync = needs_sync or "battle_preview_outcomes" in data or "show_detailed_action_value" in data

        for key, default in self._persistent_fields.items():
            if key in data:
                value = data[key]
            elif key in self._keybind_fields:
                value = legacy_keybinds.get(key, default)
            else:
                value = default
            value = self._validated_value(key, value, default)
            setattr(self, key, value)

        # save old binds and any new settings
        if needs_sync or not os.path.exists(self._path):
            self.save()

    def save(self):
        for key, default in self._persistent_fields.items():
            value = getattr(self, key, default)
            setattr(self, key, self._validated_value(key, value, default))
        data = {}
        for key, default in self._persistent_fields.items():
            data[key] = getattr(self, key, default)

        write_file(self._path, json.dumps(data, indent=4))
        trim_backups(PROJECT_ROOT, self.backup_count)
        apply_palette = globals().get("apply_display_preferences")
        if apply_palette is not None:
            apply_palette()

    def reset(self):
        for key, default in self._persistent_fields.items():
            setattr(self, key, default)
        self.save()

    def reset_fields(self, fields):
        for key in fields:
            if key in self._persistent_fields:
                setattr(self, key, self._persistent_fields[key])
        self.save()

    def setting_is_locked(self, attr):
        reduce_motion_lock = (
            bool(getattr(self, "reduce_motion", False))
            and attr in self._REDUCE_MOTION_LOCKED_FIELDS
        )
        sorting_lock = (
            attr in {"inventory_sorting", "inventory_sort_order"}
            and not getattr(self, "sort_items_automatically", True)
        )
        audio_lock = (
            attr in {"master", "sound", "ambient", "sfx", "dialogue", "music"}
            and getattr(self, "disable_audio_completely", False)
        )
        return reduce_motion_lock or sorting_lock or audio_lock

    def setting_lock_reason(self, attr):
        if (
            attr in {"master", "sound", "ambient", "sfx", "dialogue", "music"}
            and getattr(self, "disable_audio_completely", False)
        ):
            return "audio disabled"
        if (
            attr in {"inventory_sorting", "inventory_sort_order"}
            and not getattr(self, "sort_items_automatically", True)
        ):
            return "sorting disabled"
        if (
            bool(getattr(self, "reduce_motion", False))
            and attr in self._REDUCE_MOTION_LOCKED_FIELDS
        ):
            return "reduce motion"
        return ""

    def setting_lock_message(self, attr):
        if self.setting_lock_reason(attr) == "audio disabled":
            return "Turn Mute all audio off to edit this setting."
        if self.setting_lock_reason(attr) == "sorting disabled":
            return "Turn Sort items automatically on to edit this setting."
        return "Turn Reduce motion off to edit this setting."

    def effective_setting(self, attr):
        # use the override here, keep the saved choice
        if (
            attr in {"master", "sound", "ambient", "sfx", "dialogue", "music"}
            and getattr(self, "disable_audio_completely", False)
        ):
            return 0
        if (
            bool(getattr(self, "reduce_motion", False))
            and attr in self._REDUCE_MOTION_OVERRIDES
        ):
            return self._REDUCE_MOTION_OVERRIDES[attr]
        return getattr(self, attr)

# Create global instance
setting = SettingsData()
class ItemData:
    pass
item = ItemData()
class FragmentData:
    pass
fragment = FragmentData()
fragment_bracelet = FragmentData()
fragment_necklace = FragmentData()
fragment_ring = FragmentData()
FRAGMENT_EQUIPPED_OBJECTS = {
    "Bracelet": fragment_bracelet,
    "Necklace": fragment_necklace,
    "Ring": fragment_ring,
}
class ArmorData:
    pass
armor = ArmorData()
class HeadwearData:
    pass
head = HeadwearData()
class SystemData:
    pass

game = SystemData()


class KeyBinds:
    # binds are saved with settings now

    def __init__(self, owner):
        object.__setattr__(self, "_owner", owner)
        object.__setattr__(self, "_path", owner._path)
        object.__setattr__(self, "_persistent_fields", dict(KEYBIND_DEFAULTS))

    def __getattr__(self, name):
        if name in self._persistent_fields:
            return getattr(self._owner, name)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        fields = self.__dict__.get("_persistent_fields", {})
        if name in fields:
            value = self._owner._validated_value(name, value, fields[name])
            setattr(self._owner, name, value)
            return
        object.__setattr__(self, name, value)

    def load(self):
        self._owner.load()

    def save(self):
        self._owner.save()

    def reset(self):
        self._owner.reset_fields(self._persistent_fields)

bind = KeyBinds(setting)
settings_editor = SettingEditor()

d.frombattle = False
d.character_view = 1
# Oh yeah, here comes the RGB COLOR MESS!! Let's go!!
bind.load()
player.load()
game.goto = "main"
x0 = rgb(12, 12, 12)
x1 = rgb(0, 74, 171)
x2 = rgb(15, 138, 12)
x3 = rgb(59, 149, 219)
x4 = rgb(255, 56, 59)
x5 = rgb(207, 92, 230)
x6 = rgb(207, 154, 72)
x7 = rgb(148, 148, 148)
x8 = rgb(94, 94, 94)
x9 = rgb(81, 96, 224)
xa = rgb(70, 198, 107)
xb = rgb(122, 195, 230)
xc = rgb(255, 102, 105)
xd = rgb(214, 138, 230)
xe = rgb(240, 232, 158)
xf = rgb(242, 242, 242)
xlred = rgb(255, 143, 116)
xlorange = rgb(255, 222, 167)
xlbrown = rgb(213, 126, 65)
xbrown = rgb(137, 81, 42)
xg = rgb(137, 81, 42)
xh = rgb(137, 81, 42)
xlyellow = rgb(255, 202, 102)
xb0 = rgback(12, 12, 12)
xb1 = rgback(0, 74, 171)
xb2 = rgback(15, 138, 12)
xb3 = rgback(59, 149, 219)
xb4 = rgback(255, 56, 59)
xb5 = rgback(207, 92, 230)
xb6 = rgback(207, 154, 72)
xb7 = rgback(148, 148, 148)
xb8 = rgback(94, 94, 94)
xb9 = rgback(81, 96, 224)
xba = rgback(70, 198, 107)
xbb = rgback(122, 195, 230)
xbc = rgback(255, 102, 105)
xbd = rgback(214, 138, 230)
xbe = rgback(240, 232, 158)
xbf = rgback(242, 242, 242)
xblred = rgback(255, 143, 116)
xblorange = rgback(255, 222, 167)
xblyellow = rgback(255, 202, 102)
reset = "[0m"
ESC = "\x1b["
reset = ESC + "0m"
bold = ESC + "1m"
unbold = ESC + "22m"
dim = ESC + "2m"
undim = ESC + "22m"
italic = ESC + "3m"
unitalic = ESC + "23m"
underline = ESC + "4m"
nounderline = ESC + "24m"
strikethrough = ESC + "9m"
unstrike = ESC + "29m"
uncolor = ESC + "39m"
unbg = ESC + "49m"
# ...but at least they work.
_DEFAULT_READABILITY_PALETTE = {name: globals()[name] for name in ("x0", "x1", "x2", "x7", "x8", "x9")}


def apply_display_preferences():
    globals().update(_DEFAULT_READABILITY_PALETTE)
    if setting.high_contrast_colors:
        globals().update(x0=rgb(180, 180, 180), x1=rgb(110, 185, 255),
                         x2=rgb(100, 230, 130), x7=rgb(242, 242, 242),
                         x8=rgb(195, 195, 195), x9=rgb(150, 170, 255))


apply_display_preferences()


# clear needs extra commands on some terminals to remove scrollback too
_terminal_clear_cache_key = None
_terminal_clear_payload_cache = None


def _terminal_command_output(command, *arguments):
    # run the terminal command and get its output
    try:
        result = subprocess.run(
            [command, *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except (OSError, ValueError):
        return b""

    if result.returncode != 0:
        return b""
    output = result.stdout or b""
    if isinstance(output, str):
        return output.encode("utf-8", errors="replace")
    return bytes(output)


def _safe_terminal_fragment(output):
    # skip clear commands that would add new lines
    if not output:
        return b""
    # keep escape codes, reject other control characters that could add rows
    if any(byte < 0x20 and byte != 0x1B for byte in output):
        return b""
    return output


def _get_terminal_clear_payload():
    # prepare the commands to clear the screen and scrollback
    global _terminal_clear_cache_key, _terminal_clear_payload_cache

    cache_key = (
        sys.platform,
        os.environ.get("TERM", ""),
        os.environ.get("TERM_PROGRAM", ""),
    )
    if (
        cache_key == _terminal_clear_cache_key
        and _terminal_clear_payload_cache is not None
    ):
        return _terminal_clear_payload_cache

    parts = []

    # use the terminal's clear command first, it may only clear the screen
    clear = shutil.which("clear")
    if clear:
        parts.append(_safe_terminal_fragment(_terminal_command_output(clear)))

    # E3 clears saved lines on terminals that support it
    tput = shutil.which("tput")
    if tput:
        parts.append(_safe_terminal_fragment(_terminal_command_output(tput, "E3")))

    # clear the screen, clear scrollback, move back to top left
    parts.append(b"\x1b[2J\x1b[3J\x1b[1;1H")

    # iTerm2 has its own scrollback command too
    if os.environ.get("TERM_PROGRAM") == "iTerm.app":
        parts.append(b"\x1b]1337;ClearScrollback\x1b\\")

    _terminal_clear_cache_key = cache_key
    _terminal_clear_payload_cache = b"".join(part for part in parts if part)
    return _terminal_clear_payload_cache


def _write_terminal_bytes(payload):
    # write terminal commands without adding a newline
    if not payload:
        return

    try:
        sys.stdout.flush()
    except (AttributeError, OSError, ValueError):
        pass

    remaining = memoryview(payload)
    try:
        descriptor = sys.stdout.fileno()
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("terminal write made no progress")
            remaining = remaining[written:]
        return
    except (AttributeError, OSError, TypeError, ValueError):
        # if direct terminal output fails, try normal stdout
        try:
            sys.stdout.write(payload.decode("utf-8", errors="replace"))
            sys.stdout.flush()
        except (AttributeError, OSError, ValueError):
            pass


# clear the screen and old scrollback too
def cls():
    _write_terminal_bytes(_get_terminal_clear_payload())

# animation configs!! for accessibility settings.

def animation_speed_name():
    return format_setting_value(
        SETTINGS_BY_ATTR["animation_speed"],
        setting.effective_setting("animation_speed"),
    )


def animation_rate():
    return setting.effective_setting("animation_speed")


def animations_enabled():
    return not getattr(setting, "reduce_motion", False)


def animation_sleep(seconds):
    if not animations_enabled():
        return
    time.sleep(max(0.0, seconds) / animation_rate())

# -- end prev.

# cls but another cls.
def screen_wipe(mode, delay_ms):
    transitions_enabled = setting.effective_setting("menu_transitions")
    if (
        getattr(setting, "reduce_motion", False)
        or not transitions_enabled
        or not animations_enabled()
    ):
        cls()
        return

    wipe_path = PROJECT_ROOT / "Scripts" / "wipe.py"
    subprocess.run([sys.executable, str(wipe_path), mode, str(delay_ms)])


def open_text_file(path):
    # open the file in a text editor, wait if the editor allows it
    resolved_path = Path(path)
    if not resolved_path.is_absolute():
        resolved_path = PROJECT_ROOT / resolved_path
    resolved_path = resolved_path.resolve()

    if os.name == "nt":
        command = ["notepad.exe", str(resolved_path)]
    else:
        configured_editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
        if configured_editor:
            command = shlex.split(configured_editor) + [str(resolved_path)]
        elif sys.platform == "darwin":
            command = ["open", "-W", str(resolved_path)]
        else:
            opener = shutil.which("xdg-open")
            if opener:
                command = [opener, str(resolved_path)]
            else:
                fallback_editor = shutil.which("nano") or shutil.which("vi")
                if not fallback_editor:
                    return False
                command = [fallback_editor, str(resolved_path)]

    try:
        return subprocess.run(command, check=False).returncode == 0
    except OSError:
        return False


# Key. As simple as that. Press a key, and... that's the return. With some specials.
#[[removed and replaced by a key-mouse detect from imports!]]

# INTERACTIVITY TIME! Sound() plays a sound effect. It does this by writing the command to a text file, which is then read by the sound player.
def sound(cmd, channel="sound", pan=0.0):
    navigation_sounds = {"switch", "woosh", "setting_battles", "settings_graphics",
                         "settings_music", "setting_keybinds", "setting_accessibility"}
    if (channel == "sound" and not getattr(setting, "menu_feedback_sounds", True)
            and (str(cmd).partition(" ")[0] in navigation_sounds or str(cmd).startswith("map_"))):
        return
    if channel not in ("sound", "ambient", "sfx", "dialogue", "music"): # set your type!
        raise ValueError(f"Unknown audio channel: {channel}")
    pan = max(-1.0, min(1.0, float(pan)))
    command = str(cmd)
    if channel != "sound" or pan:
        command = f"@{channel},{pan:.2f}|{command}"
    path = PROJECT_ROOT / "General" / "Temp" / "sound_cmd_queue.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(command + "\n")

# file operations!
def update(path, value):
    # Normalize path
    full_path = os.path.join(os.getcwd(), path + ".txt")
    write_file(full_path, value)
        
def read(path, default=None):
    full_path = os.path.join(os.getcwd(), path + ".txt")
    if not os.path.exists(full_path):
        return default
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    # --- Auto type detection ---
    try:
        if "." in content:
            value = float(content)
            if value.is_integer():
                return int(value)
            return value
        return int(content)
    except Exception:
        return content
       
def _clear_object(obj):
    for attr in list(vars(obj).keys()):
        delattr(obj, attr)


def _reset_object(obj, defaults):
    _clear_object(obj)
    for key, value in defaults.items():
        setattr(obj, key, value)

# item stat loading time!
def _load_armor_item_fields(target, parts, category):
    target.type_raw = parts[0] if len(parts) > 0 else None
    target.rarity = parts[1] if len(parts) > 1 else None
    target.name = parts[2] if len(parts) > 2 else None
    raw_level = int(parts[3]) if len(parts) > 3 and parts[3] else 0
    target.level = clamp_item_level(raw_level, category)
    stored_defense = float(parts[4]) if len(parts) > 4 and parts[4] else 0.0
    target.description = parts[5] if len(parts) > 5 else ""
    target.ability = parts[6] if len(parts) > 6 else ""
    target.locked = int(parts[7]) if len(parts) > 7 and parts[7] != "" else 0

    if len(parts) > 8 and parts[8] != "":
        target.defense = stored_defense
        target.level_power = float(parts[8])
    else:
        # old armor files stored scaled defense in field five
        target.level_power = ARMOR_LEVEL_POWER_DEFAULTS.get(target.rarity, 0.035)
        target.defense = get_base_equipment_stat(
            stored_defense,
            target.level,
            target.level_power,
        )
    return target


def _armor_item_parts(target, category):
    target.level = clamp_item_level(getattr(target, "level", 0), category)
    return [
        str(getattr(target, "type_raw", "") or ""),
        str(getattr(target, "rarity", "") or ""),
        str(getattr(target, "name", "") or ""),
        str(getattr(target, "level", 0)),
        str(getattr(target, "defense", 0)),
        str(getattr(target, "description", "") or ""),
        str(getattr(target, "ability", "") or ""),
        str(getattr(target, "locked", 0)),
        str(getattr(target, "level_power", 0.0)),
    ]


def normalize_fragment_stat(stat_name):
    aliases = {
        "ATKP": "ATK %",
        "HP P": "HP %",
        "HPP": "HP %",
        "SPD": "Speed",
        "CRIT": "Crit Rate",
        "CRIT RATE": "Crit Rate",
        "CRIT DMG": "Crit Damage",
        "CRIT DAMAGE": "Crit Damage",
    }
    text = str(stat_name or "").strip()
    if not text or text.lower() == "none":
        return None
    return aliases.get(text.upper(), text)


def compact_number(value):
    value = round(float(value), 2)
    return int(value) if value.is_integer() else value


def format_number(value):
    # format the displayed number, keep the actual value unchanged
    numeric = float(value)
    if getattr(globals().get("setting"), "number_format", "Full") == "Compact":
        for scale, suffix in ((1_000_000_000, "b"), (1_000_000, "m"), (1_000, "k")):
            if abs(numeric) >= scale:
                # 999.95k rounds to 1m
                scaled = round(numeric / scale, 1)
                if abs(scaled) >= 1000 and scale < 1_000_000_000:
                    larger = {1_000: (1_000_000, "m"), 1_000_000: (1_000_000_000, "b")}
                    scale, suffix = larger[scale]
                    scaled = round(numeric / scale, 1)
                return f"{scaled:g}{suffix}"
    if numeric.is_integer():
        return f"{int(numeric):,}"
    return f"{numeric:,.2f}".rstrip("0").rstrip(".")


def menu_navigation_key(pressed):
    # turn custom movement keys into up/down/left/right
    if not isinstance(pressed, str):
        return pressed
    lowered = pressed.lower()
    if lowered in {"up", "down", "left", "right"}:
        return lowered
    for direction in ("up", "down", "left", "right"):
        if lowered == getattr(setting, "menu_" + direction):
            return direction
    return lowered


def format_fragment_stat(stat_name, value, signed=False):
    stat_name = normalize_fragment_stat(stat_name) or "Unknown"
    value = compact_number(value)
    sign = "+" if signed and float(value) >= 0 else ""
    value = format_number(value)
    if stat_name in FRAGMENT_PERCENT_STATS:
        label = stat_name[:-2] if stat_name.endswith(" %") else stat_name
        return f"{sign}{value}% {label}"
    return f"{sign}{value} {stat_name}"


def format_fragment_set_effect(effect_name, value):
    labels = {
        "atk_percent": ("ATK", True),
        "def_percent": ("DEF", True),
        "hp_percent": ("HP", True),
        "speed": ("Speed", False),
        "crit_rate": ("Crit Rate", True),
        "crit_damage": ("Crit Damage", True),
        "damage_taken_percent": ("Damage Taken", True),
        "healing_received_percent": ("Healing Received", True),
    }
    label, percent = labels.get(
        effect_name,
        (effect_name.replace("_", " ").title(), False),
    )
    value = compact_number(value)
    sign = "+" if float(value) >= 0 else ""
    value = format_number(value)
    suffix = "%" if percent else ""
    return f"{sign}{value}{suffix} {label}"


def get_fragment_main_stat_value(fragment_obj, level=None):
    stat_name = normalize_fragment_stat(getattr(fragment_obj, "main_stat", None))
    if stat_name not in FRAGMENT_MAIN_STATS:
        return 0
    if level is None:
        level = getattr(fragment_obj, "level", 1)
    level = clamp_item_level(level, "Fragments")
    per_level = FRAGMENT_MAIN_STATS[stat_name][1]
    base_value = float(getattr(fragment_obj, "main_stat_value", 0))
    return compact_number(base_value + per_level * max(0, level - 1))


def get_fragment_main_stat_base(final_value, stat_name, level):
    stat_name = normalize_fragment_stat(stat_name)
    per_level = FRAGMENT_MAIN_STATS.get(stat_name, ((0, 0), 0))[1]
    return compact_number(float(final_value) - per_level * max(0, int(level) - 1))


def generate_fragment_main_stat(stat_name=None):
    if stat_name is None:
        stat_name = random.choice(tuple(FRAGMENT_MAIN_STATS))
    stat_name = normalize_fragment_stat(stat_name)
    if stat_name not in FRAGMENT_MAIN_STATS:
        raise ValueError(f"Unknown fragment main stat: {stat_name}")
    value_range = FRAGMENT_MAIN_STATS[stat_name][0]
    if isinstance(value_range[0], int) and isinstance(value_range[1], int):
        value = random.randint(*value_range)
    else:
        value = random.uniform(*value_range)
    return stat_name, compact_number(value)


def get_fragment_substats(fragment_obj):
    substats = []
    index = 1
    while hasattr(fragment_obj, f"substat{index}"):
        stat_name = normalize_fragment_stat(getattr(fragment_obj, f"substat{index}", None))
        if stat_name:
            substats.append((
                stat_name,
                compact_number(getattr(fragment_obj, f"substat{index}_value", 0)),
            ))
        index += 1
    return substats


def generate_fragment_substat(excluded_stats=()):
    excluded = {normalize_fragment_stat(stat) for stat in excluded_stats}
    available = [stat for stat in FRAGMENT_SUBSTAT_RANGES if stat not in excluded]
    if not available:
        return None
    stat_name = random.choice(available)
    minimum, maximum = FRAGMENT_SUBSTAT_RANGES[stat_name]
    return stat_name, random.randint(minimum, maximum)


def apply_fragment_substats(fragment_obj, target_level):
    existing = get_fragment_substats(fragment_obj)
    needed = min(3, clamp_item_level(target_level, "Fragments") // 5) - len(existing)
    additions = []
    while len(additions) < needed:
        excluded = [getattr(fragment_obj, "main_stat", None)]
        excluded.extend(stat for stat, _ in existing + additions)
        generated = generate_fragment_substat(excluded)
        if generated is None:
            break
        additions.append(generated)
    for stat_name, value in additions:
        index = len(existing) + 1
        setattr(fragment_obj, f"substat{index}", stat_name)
        setattr(fragment_obj, f"substat{index}_value", value)
        existing.append((stat_name, value))
    return additions


def fragment_item_parts(fragment_obj):
    parts = [
        str(getattr(fragment_obj, "slot", "Bracelet")),
        str(getattr(fragment_obj, "name", "Unnamed Fragment")),
        str(clamp_item_level(getattr(fragment_obj, "level", 1), "Fragments")),
        str(normalize_fragment_stat(getattr(fragment_obj, "main_stat", "ATK"))),
        str(getattr(fragment_obj, "main_stat_value", 0)),
        str(
            getattr(
                fragment_obj,
                "set_name",
                getattr(fragment_obj, "set", "Warrior"),
            )
        ),
        str(int(getattr(fragment_obj, "locked", 0))),
    ]
    for stat_name, value in get_fragment_substats(fragment_obj):
        parts.extend((str(stat_name), str(value)))
    return parts


def load_fragment_item_fields(target, parts):
    _clear_object(target)
    if parts and parts[0] in FRAGMENT_SLOTS:
        target.slot = parts[0]
        target.name = parts[1] if len(parts) > 1 else f"Unnamed {target.slot}"
        target.level = clamp_item_level(parts[2] if len(parts) > 2 else 1, "Fragments")
        target.main_stat = normalize_fragment_stat(parts[3] if len(parts) > 3 else "ATK")
        target.main_stat_value = float(parts[4]) if len(parts) > 4 and parts[4] else 0
        target.set_name = parts[5] if len(parts) > 5 and parts[5] in FRAGMENT_SETS else "Warrior"
        target.set = target.set_name
        target.locked = int(parts[6]) if len(parts) > 6 and parts[6] else 0
        stat_parts = parts[7:]
    else:
        target.name = parts[0] if parts else "Legacy Fragment"
        target.slot = next(
            (slot for slot in FRAGMENT_SLOTS if slot.lower() in target.name.lower()),
            "Bracelet",
        )
        target.level = clamp_item_level(parts[1] if len(parts) > 1 else 1, "Fragments")
        target.main_stat = normalize_fragment_stat(parts[2] if len(parts) > 2 else "ATK")
        final_value = float(parts[3]) if len(parts) > 3 and parts[3] else 0
        target.main_stat_value = get_fragment_main_stat_base(
            final_value,
            target.main_stat,
            target.level,
        )
        target.set_name = "Warrior"
        target.set = target.set_name
        target.locked = 0
        stat_parts = parts[4:]

    target.type_raw = target.slot.lower()
    target.rarity = None
    target.description = f"{target.set_name} set {target.slot.lower()} fragment."
    target.ability = ""
    index = 1
    for offset in range(0, len(stat_parts) - 1, 2):
        stat_name = normalize_fragment_stat(stat_parts[offset])
        if not stat_name or stat_name == target.main_stat:
            continue
        if stat_name in {
            normalize_fragment_stat(getattr(target, f"substat{i}", None))
            for i in range(1, index)
        }:
            continue
        try:
            value = compact_number(stat_parts[offset + 1])
        except (TypeError, ValueError):
            continue
        setattr(target, f"substat{index}", stat_name)
        setattr(target, f"substat{index}_value", value)
        index += 1
        if index > 3:
            break
    return target

# dev tools
def create_fragment(slot=None, main_stat=None, set_name=None, level=1):
    slot = slot if slot in FRAGMENT_SLOTS else random.choice(FRAGMENT_SLOTS)
    set_name = set_name if set_name in FRAGMENT_SETS else random.choice(tuple(FRAGMENT_SETS))
    main_stat, main_value = generate_fragment_main_stat(main_stat)
    created = FragmentData()
    created.slot = slot
    created.type_raw = slot.lower()
    created.rarity = None
    created.name = f"{set_name} {slot}"
    created.level = clamp_item_level(level, "Fragments")
    created.main_stat = main_stat
    created.main_stat_value = main_value
    created.set_name = set_name
    created.set = created.set_name
    created.locked = 0
    created.description = f"{set_name} set {slot.lower()} fragment."
    created.ability = ""
    apply_fragment_substats(created, created.level)
    return created


def spawn_fragment(fragment_obj):
    fragments_dir = Path("Items/Fragments")
    fragments_dir.mkdir(parents=True, exist_ok=True)
    item_ids = []
    for path in fragments_dir.glob("item*.txt"):
        match = re.fullmatch(r"item(\d+)\.txt", path.name)
        if match:
            item_ids.append(int(match.group(1)))
    existing_ids = set(item_ids)
    item_id = 1
    while item_id in existing_ids:
        item_id += 1
    path = fragments_dir / f"item{item_id}.txt"
    path.write_text(";;".join(fragment_item_parts(fragment_obj)), encoding="utf-8")
    return item_id


def fragment_slot_path(slot):
    if slot not in FRAGMENT_SLOTS:
        return None
    return f"Items/active_fragment_{slot.lower()}"

# for your old guys:
def migrate_legacy_fragment_slot():
    for slot in FRAGMENT_SLOTS:
        path = fragment_slot_path(slot)
        if read(path, default=None) is None:
            update(path, "none")
    legacy_id = read("Items/active_fragment", default="none")
    if str(legacy_id).lower() in ("", "none", "0"):
        return
    if any(str(read(fragment_slot_path(slot), default="none")).lower() != "none"
           for slot in FRAGMENT_SLOTS):
        return
    try:
        legacy_fragment = load_item(int(legacy_id), "Fragments")
    except (OSError, ValueError):
        return
    update(fragment_slot_path(legacy_fragment.slot), legacy_id)
    update("Items/active_fragment", "none")


# Loads an item by ID and category. If ID is 0, loads equipped items from the "active_*.txt" files.
# Otherwise, loads from the corresponding item file.
def load_item(item_id, category="Weapons"):
    base_dir = os.getcwd()
    items_dir = os.path.join(base_dir, "Items")

    # ─────────────────────────────────────────────
    # UNIVERSAL EQUIPPED LOADER (ID = 0)
    # ─────────────────────────────────────────────
    if str(item_id) == "0":
        migrate_legacy_fragment_slot()
        slot_map = {
            "active_weapon.txt": (
                "Weapons",
                item,
                {
                    "type_raw": None,
                    "type": "❌",
                    "rarity": None,
                    "name": None,
                    "level": 0,
                    "atk": 0,
                    "atkcrit": 0.0,
                    "substat": None,
                    "substat_value": 0,
                    "description": None,
                    "level_power": 0.0,
                    "ability": None,
                    "locked": 0,
                    "refine": 0,
                    "special": None,
                    "specialvalue": 0,
                },
            ),
            "active_body.txt": (
                "Bodywear",
                armor,
                {
                    "type_raw": None,
                    "rarity": None,
                    "name": None,
                    "level": 0,
                    "defense": 0,
                    "level_power": 0.0,
                    "description": None,
                    "ability": None,
                    "locked": 0,
                },
            ),
            "active_head.txt": (
                "Helmets",
                head,
                {
                    "type_raw": None,
                    "rarity": None,
                    "name": None,
                    "level": 0,
                    "defense": 0,
                    "level_power": 0.0,
                    "description": None,
                    "ability": None,
                    "locked": 0,
                },
            ),
            "active_fragment_bracelet.txt": (
                "Fragments",
                fragment_bracelet,
                {"name": None, "slot": "Bracelet", "level": 0, "locked": 0},
            ),
            "active_fragment_necklace.txt": (
                "Fragments",
                fragment_necklace,
                {"name": None, "slot": "Necklace", "level": 0, "locked": 0},
            ),
            "active_fragment_ring.txt": (
                "Fragments",
                fragment_ring,
                {"name": None, "slot": "Ring", "level": 0, "locked": 0},
            ),
        }

        for filename, (cat, obj, defaults) in slot_map.items():
            path = os.path.join(items_dir, filename)

            _reset_object(obj, defaults)

            if not os.path.exists(path):
                continue

            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.readline().strip()
                if content.lower() == "none" or content == "":
                    continue
                active_id = int(content)
                if active_id <= 0:
                    raise ValueError("Invalid item ID")
                loaded = load_item(active_id, cat)
                if cat == "Fragments" and loaded.slot != defaults["slot"]:
                    raise ValueError("Wrong fragment slot")
            except (FileNotFoundError, ValueError, TypeError, IndexError, UnicodeError):
                _reset_object(obj, defaults)
                update(
                    os.path.splitext(os.path.join("Items", filename))[0],
                    "none",
                )
                continue
            if cat == "Fragments":
                _reset_object(obj, vars(loaded))

        return

    # ─────────────────────────────────────────────
    # NORMAL ITEM LOADING
    # ─────────────────────────────────────────────
    path = os.path.join(
        items_dir,
        category,
        f"item{item_id}.txt"
    )

    with open(path, "r", encoding="utf-8") as f:
        line = f.readline().strip()

    parts = line.split(";;")

    # ───────────── WEAPONS ─────────────
    if category == "Weapons":
        _clear_object(item)

        fields = [
        "type_raw",
        "rarity",
        "name",
        "level",
        "atk",
        "atkcrit",
        "substat",
        "substat_value",
        "description",
        "level_power",
        "ability",
        "locked",
        "refine"
    ]
        for i, field in enumerate(fields):
            setattr(item, field, parts[i] if i < len(parts) else None)

        # Type conversions
        item.level = clamp_item_level(item.level, "Weapons")
        item.atk = int(item.atk)
        item.atkcrit = float(item.atkcrit)
        item.substat_value = int(item.substat_value)
        item.level_power = float(item.level_power)
        item.locked = int(item.locked)
        item.refine = max(
            0,
            min(WEAPON_REFINEMENT_MAX, int(item.refine or 0)),
        )

        type_map = {
            None: "❌",
            "None": "❌",
            "bow": "🏹",
            "sword": "⚔️",
            "knife": "🔪",
            "dagger": "🗡️",
            "helmet": "⛑️",
            "bodywear": "👗",
            "book": "📖",
            "wand": "🪄",
            "axe": "🪓",
            "hammer": "⚒️",
            "pistol": "🔫",
            "flower": "🌹",
        }

        item.type = type_map.get(item.type_raw, item.type_raw)
        return item

    # ───────────── HELMETS ─────────────
    elif category == "Helmets":
        _clear_object(head)
        return _load_armor_item_fields(head, parts, "Helmets")

    # ───────────── BODYWEAR ─────────────
    elif category == "Bodywear":
        _clear_object(armor)
        return _load_armor_item_fields(armor, parts, "Bodywear")

    # ───────────── FRAGMENTS ─────────────
    elif category == "Fragments":
        return load_fragment_item_fields(fragment, parts)

    else:
        raise ValueError(f"Unknown category: {category}")
        
def save_item(item_id, category="Weapons"):
    path = os.path.join(
        os.getcwd(),
        "Items",
        category,
        f"item{item_id}.txt"
    )

    # ───────────── WEAPONS ─────────────
    if category == "Weapons":
        item.level = clamp_item_level(getattr(item, "level", 0), "Weapons")
        parts = [
            str(getattr(item, "type_raw", "") or ""),
            str(getattr(item, "rarity", "") or ""),
            str(getattr(item, "name", "") or ""),
            str(getattr(item, "level", 0)),
            str(getattr(item, "atk", 0)),
            str(getattr(item, "atkcrit", 0)),
            str(getattr(item, "substat", "") or ""),
            str(getattr(item, "substat_value", 0)),
            str(getattr(item, "description", "") or ""),
            str(getattr(item, "level_power", 0.0)),
            str(getattr(item, "ability", "") or ""),
            str(getattr(item, "locked", 0)),
            str(getattr(item, "refine", 0))
        ]

    # ───────────── HELMETS ─────────────
    elif category == "Helmets":
        parts = _armor_item_parts(head, "Helmets")

    # ───────────── BODYWEAR ─────────────
    elif category == "Bodywear":
        parts = _armor_item_parts(armor, "Bodywear")

    # ───────────── FRAGMENTS ─────────────
    elif category == "Fragments":
        fragment.level = clamp_item_level(getattr(fragment, "level", 1), "Fragments")
        parts = fragment_item_parts(fragment)

    else:
        raise ValueError(f"Unknown category: {category}")

    line = ";;".join(parts)

    write_file(path, line)

def load_binds():
    bind.load()

    actions = [
        "attack",
        "heal",
        "skill",
        "ult",
        "forfeit",
        "confirm",
        "back",
        "deny",
        "custom1",
        "custom2",
    ]

    display_map = {
        "space": "␣",
        "enter": "↵",
        "esc": "⎋",
        "backspace": "⌫",
    }

    for action in actions:
        raw = str(getattr(bind, action, "")).strip()
        setattr(bind, action, raw)

        display = display_map.get(raw.lower(), raw.upper())
        setattr(bind, f"{action}_display", display)
load_binds()

def draw_text(x, y, text):
    print(f"\x1b[{y};{x}H{text}\x1b[0m", end="",flush=True)
    
def blank(y1, x1, y2, x2):
    if y2 < y1 or x2 < x1:
        return

    width = x2 - x1 + 1
    spaces = " " * width

    for y in range(y1, y2 + 1):
        # Reset style BEFORE drawing spaces
        print(f"\x1b[0m\x1b[{y};{x1}H{spaces}", end="", flush=True)
        
def draw_box_border(
    y1: int,
    x1: int,
    y2: int,
    x2: int,
    text: str = "",
    bold: bool = False,
    text_color: str = "",
    border_color: str = x7,
    align: Literal["left", "center", "right"] = "left"
):

    width  = x2 - x1 + 1
    height = y2 - y1 + 1

    if width < 2 or height < 2:
        return

    inner_width = width - 2

    TL = "╭"
    TR = "╮"
    BL = "╰"
    BR = "╯"
    H  = "─"
    V  = "│"

    # Draw full top border
    draw_text(x1, y1, border_color + TL + H*(width-2) + TR)

    # Draw vertical borders
    for y in range(y1+1, y2):
        draw_text(x1, y, border_color + V)
        draw_text(x2, y, border_color + V)

    # Bottom border
    draw_text(x1, y2, border_color + BL + H*(width-2) + BR)

    if not text:
        return

    # Add breathing room
    padded_text = f" {text} "
    text_len = visible_len(padded_text)

    # Clamp if too wide
    if text_len > inner_width - 2:
        padded_text = padded_text[:inner_width - 2]
        text_len = visible_len(padded_text)

    # Alignment
    if align == "left":
        text_x = x1 + 2

    elif align == "center":
        text_x = x1 + 1 + (inner_width - text_len)//2

    elif align == "right":
        text_x = x2 - text_len - 1

    else:
        text_x = x1 + 2

    left_connector_x  = text_x - 1
    right_connector_x = text_x + text_len

    # Safety clamp
    if left_connector_x <= x1:
        left_connector_x = x1 + 1
    if right_connector_x >= x2:
        right_connector_x = x2 - 1

    # Draw connectors
    draw_text(left_connector_x, y1, border_color + "┤")
    draw_text(right_connector_x, y1, border_color + "├")

    # Draw text
    style = text_color
    if bold:
        style += "\x1b[1m"

    draw_text(text_x, y1, style + padded_text)
    
def get_scaled_equipment_stat(target, base_stat, level=None):
    base = float(getattr(target, base_stat, 0))
    if level is None:
        level = int(getattr(target, "level", 0))
    else:
        level = int(level)
    growth = float(getattr(target, "level_power", 0))

    return round(base * ((1 + growth) ** level))


def get_base_equipment_stat(scaled_value, level, level_power):
    growth = (1 + float(level_power)) ** max(0, int(level))
    if not growth:
        return float(scaled_value)
    return round(float(scaled_value) / growth, 6)


def get_actual_atk(item_obj=None, level=None):
    target = item_obj if item_obj is not None else item
    return get_scaled_equipment_stat(target, "atk", level)


def get_actual_defense(item_obj, level=None):
    return get_scaled_equipment_stat(item_obj, "defense", level)


def scale_fragment_bonus(key, value):
    # calculate the bonus from a fragment stat or set
    scaled = float(value) * FRAGMENT_BONUS_SCALES.get(key, 1.0)
    if key == "hp_percent":
        return round(scaled)
    return compact_number(scaled)


def scale_fragment_stat(stat_name, value):
    stat_keys = {
        "ATK": "atk_flat",
        "ATK %": "atk_percent",
        "HP": "hp_flat",
        "HP %": "hp_percent",
        "DEF": "def_flat",
        "Speed": "speed",
        "Crit Rate": "crit_rate",
        "Crit Damage": "crit_damage",
    }
    normalized = normalize_fragment_stat(stat_name)
    return scale_fragment_bonus(stat_keys.get(normalized, ""), value)


def fragment_stat_icon(stat_name):
    return {
        "ATK": "⚔",
        "ATK %": "⚔",
        "HP": "♥",
        "HP %": "♥",
        "DEF": "🛡",
        "Speed": "➟",
        "Crit Rate": "✦",
        "Crit Damage": "✴",
    }.get(normalize_fragment_stat(stat_name), "•")


def get_fragment_bonuses():
    bonuses = {
        "atk_flat": 0,
        "atk_percent": 0,
        "hp_flat": 0,
        "hp_percent": 0,
        "def_flat": 0,
        "def_percent": 0,
        "speed": 0,
        "crit_rate": 0,
        "crit_damage": 0,
        "damage_taken_percent": 0,
        "healing_received_percent": 0,
    }
    stat_keys = {
        "ATK": "atk_flat",
        "ATK %": "atk_percent",
        "HP": "hp_flat",
        "HP %": "hp_percent",
        "DEF": "def_flat",
        "Speed": "speed",
        "Crit Rate": "crit_rate",
        "Crit Damage": "crit_damage",
    }
    equipped = [
        FRAGMENT_EQUIPPED_OBJECTS[slot]
        for slot in FRAGMENT_SLOTS
        if getattr(FRAGMENT_EQUIPPED_OBJECTS[slot], "name", None)
    ]
    for equipped_fragment in equipped:
        main_key = stat_keys.get(normalize_fragment_stat(equipped_fragment.main_stat))
        if main_key:
            bonuses[main_key] += scale_fragment_bonus(
                main_key,
                get_fragment_main_stat_value(equipped_fragment),
            )
        for stat_name, value in get_fragment_substats(equipped_fragment):
            key = stat_keys.get(stat_name)
            if key:
                bonuses[key] += scale_fragment_bonus(key, value)

    set_counts = {}
    for equipped_fragment in equipped:
        set_name = getattr(
            equipped_fragment,
            "set_name",
            getattr(equipped_fragment, "set", None),
        )
        if set_name in FRAGMENT_SETS:
            set_counts[set_name] = set_counts.get(set_name, 0) + 1
    active_sets = []
    active_set_details = []
    for set_name, count in set_counts.items():
        for pieces in (2, 3):
            if count >= pieces:
                label = f"{set_name} {pieces}pc"
                effects = FRAGMENT_SETS[set_name][pieces]
                active_sets.append(label)
                active_set_details.append((
                    label,
                    ", ".join(
                        format_fragment_set_effect(
                            key,
                            scale_fragment_bonus(key, value),
                        )
                        for key, value in effects.items()
                    ),
                ))
                for key, value in effects.items():
                    bonuses[key] += scale_fragment_bonus(key, value)
    bonuses["active_sets"] = active_sets
    bonuses["active_set_details"] = active_set_details
    return bonuses


def draw_box_text(text: str, y1: int, x1: int, y2: int, x2: int):

    width = x2 - x1 + 1
    height = y2 - y1 + 1

    if width <= 0 or height <= 0:
        return []

    # split into tokens of whitespace and non-whitespace so we can wrap by words
    tokens = re.split(r'(\s+)', text)

    def split_token_chunks(tok, maxw):
        # split a token (which may contain ANSI sequences) into raw chunks
        # each with at most maxw visible characters
        chunks = []
        cur_raw = ''
        cur_vis = 0
        i = 0
        L = len(tok)
        while i < L:
            m = ANSI_PATTERN.match(tok, i)
            if m:
                seq = m.group()
                cur_raw += seq
                i = m.end()
                continue
            # normal char
            cur_raw += tok[i]
            i += 1
            cur_vis += 1
            if cur_vis >= maxw:
                chunks.append(cur_raw)
                cur_raw = ''
                cur_vis = 0
        if cur_raw != '':
            chunks.append(cur_raw)
        return chunks

    lines = []
    cur_raw = ''
    cur_vis = 0

    def flush():
        nonlocal cur_raw, cur_vis
        lines.append(cur_raw)
        cur_raw = ''
        cur_vis = 0

    for tok in tokens:
        if tok == '':
            continue
        tok_vis = visible_len(tok)

        # treat whitespace tokens as a single space when wrapping, but preserve surrounding ANSI
        if tok.isspace():
            space_raw = ' '
            # collapse to one visible space
            space_vis = 1
            if cur_vis == 0:
                # skip leading space at line start
                continue
            if cur_vis + space_vis <= width:
                cur_raw += space_raw
                cur_vis += space_vis
            else:
                flush()
            if len(lines) >= height:
                break
            continue

        # non-space token (a word)
        if tok_vis <= (width - cur_vis):
            cur_raw += tok
            cur_vis += tok_vis
        else:
            # doesn't fit as-is
            if tok_vis > width:
                # token itself must be split
                first_chunk_space = width - cur_vis
                if first_chunk_space > 0:
                    chunks = split_token_chunks(tok, first_chunk_space)
                    # append first chunk to current line
                    cur_raw += chunks[0]
                    flush()
                    # append remaining chunks as full lines
                    remaining = ''.join(chunks[1:])
                    for c in split_token_chunks(remaining, width):
                        if len(lines) >= height:
                            break
                        lines.append(c)
                    cur_raw = ''
                    cur_vis = 0
                else:
                    # start fresh lines with token chunks
                    chunks = split_token_chunks(tok, width)
                    for c in chunks:
                        if len(lines) >= height:
                            break
                        lines.append(c)
                    cur_raw = ''
                    cur_vis = 0
            else:
                # move word to next line
                flush()
                if len(lines) >= height:
                    break
                cur_raw += tok
                cur_vis += tok_vis

        if len(lines) >= height:
            break

    if len(lines) < height and cur_raw != '':
        lines.append(cur_raw)

    overflow = False
    # Check if original text (visible) fits into produced lines
    visible_total = len(re.sub(r'\s+', '', ANSI_PATTERN.sub('', text)))
    produced_vis = sum(len(re.sub(r'\s+', '', ANSI_PATTERN.sub('', l))) for l in lines)
    if produced_vis < visible_total or len(lines) > height:
        overflow = True

    # Truncate/pad to height
    if len(lines) > height:
        lines = lines[:height]
        overflow = True

    if overflow and height > 0:
        last_idx = min(height, len(lines)) - 1
        last = lines[last_idx]
        # compute allowed visible space for ellipsis
        if width <= 3:
            ell = '.' * width
            lines[last_idx] = ell
        else:
            allowed = width - 3
            # strip ANSI for measuring, but keep raw prefixes/suffixes
            # build a truncated raw string up to allowed visible chars
            raw = last
            cur = ''
            cur_vis = 0
            i = 0
            L = len(raw)
            while i < L and cur_vis < allowed:
                m = ANSI_PATTERN.match(raw, i)
                if m:
                    seq = m.group()
                    cur += seq
                    i = m.end()
                    continue
                cur += raw[i]
                i += 1
                cur_vis += 1
            cur = cur.rstrip()
            lines[last_idx] = cur + '...'

    # pad with empty lines if necessary
    while len(lines) < height:
        lines.append('')

    # print lines at given coordinates (do not start at column 1)
    for idx, raw_line in enumerate(lines):
        row = y1 + idx
        draw_text(x1, row, raw_line)

    return lines

def center(text, row):
    cols = shutil.get_terminal_size(fallback=(128, 36)).columns
    text_len = visible_len(text)
    col = max(1, (cols - text_len) // 2 + 1)
    draw_text(col, row, text)

# why? Don't ask. Just... rainbow text. That's all.
def rainbow(text, offset=0, bold=False, italic=False, preview=False, speed=None):
    if not preview and not getattr(setting, "rainbow_text", True):
        style = ("\033[1m" if bold else "") + ("\033[3m" if italic else "")
        return f"\033[38;2;255;255;255m{style}{text}\033[0m"
    rate = animation_rate() if speed is None else speed
    offset = offset * rate if animations_enabled() else 0
    colors = [
        (255, 100, 100),
        (255, 180, 100),
        (255, 255, 120),
        (120, 255, 120),
        (120, 180, 255),
        (180, 120, 255),
        (255, 100, 100),
    ]

    style = ("\033[1m" if bold else "") + ("\033[3m" if italic else "")
    result = style
    length = max(len(text), 1)

    for i, char in enumerate(text):
        t = (i / (length - 1) if length > 1 else 0)
        t = (t + offset) % 1.0

        idx = int(t * (len(colors) - 1))
        t_local = (t * (len(colors) - 1)) - idx

        r1, g1, b1 = colors[idx]
        r2, g2, b2 = colors[idx + 1]

        r = int(r1 + (r2 - r1) * t_local)
        g = int(g1 + (g2 - g1) * t_local)
        b = int(b1 + (b2 - b1) * t_local)

        result += f"\033[38;2;{r};{g};{b}m{char}"

    return result + "\033[0m"

# Now THIS is the MVP function. Amazing for animations.
# Unlike rainbow, which just cycles through colors, this creates a "shine" effect that travels across the text. You can customize the color, width, intensity, and speed of the shine.
def shine(text, offset=0, color=(255, 255, 0), bold=False, start_color=None, italics=False, underline=False, fade_out=False, preview=False, speed=None):
    style = ("\033[1m" if bold else "") + ("\033[3m" if italics else "") + ("\033[4m" if underline else "")
    if start_color is None:
        start_color = (255, 255, 255)
    if not animations_enabled() or (not preview and not getattr(setting, "text_shine", True)):
        r, g, b = color
        return f"\033[38;2;{r};{g};{b}m{style}{text}\033[0m"

    rate = animation_rate() if speed is None else speed
    offset *= rate if not fade_out else 1
    result = ""
    length = max(len(text), 1)

    # 🔁 cycle
    cycle = max(0, min(1, offset)) if fade_out else offset % 1.0

    # ⚙️ tuning
    active_window = 0.75   # how long shine is active
    width = 0.6           # how wide the shine is
    intensity = 3         # intensity falloff (higher = sharper shine, lower = more spread out)

    for i, char in enumerate(text):
        t = i / (length - 1) if length > 1 else 0

        if fade_out:
            strength = max(0, min(1, (cycle * (1 + width) - t) / width))
            r = int(start_color[0] * (1 - strength) + color[0] * strength)
            g = int(start_color[1] * (1 - strength) + color[1] * strength)
            b = int(start_color[2] * (1 - strength) + color[2] * strength)
        elif cycle > active_window:
            # 💤 fully idle (no shine at all)
            r, g, b = start_color

        else:
            # normalize 0 → 1 within active window
            t_cycle = cycle / active_window

            # 👇 IMPORTANT: extend travel range
            center = -width + t_cycle * (1 + 2 * width)

            dist = abs(t - center)

            # smooth falloff
            strength = max(0, 1 - dist * intensity)

            r = int(start_color[0] * (1 - strength) + color[0] * strength)
            g = int(start_color[1] * (1 - strength) + color[1] * strength)
            b = int(start_color[2] * (1 - strength) + color[2] * strength)
        result += f"\033[38;2;{r};{g};{b}m{style}{char}"
    return result + "\033[0m"

def flipboard(text, offset=0, color=(255, 255, 0), bold=False, italics=False, underline=False, start_text=None, quick=False, preview=False):
    style = ("\033[1m" if bold else "") + ("\033[3m" if italics else "") + ("\033[4m" if underline else "")
    if isinstance(color, str):
        text_color = color
    else:
        r, g, b = color
        text_color = f"\033[38;2;{r};{g};{b}m"
    if not animations_enabled() or (not preview and not getattr(setting, "flipboard_animations", True)) or offset >= 1:
        return f"{text_color}{style}{text}\033[0m"
    if offset <= 0:
        if start_text is not None:
            return f"{text_color}{style}{start_text[:len(text)].ljust(len(text))}\033[0m"
        return " " * len(text)

    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    if start_text is not None:
        start_text = start_text[:len(text)].ljust(len(text))
        result = ""
        for i, char in enumerate(text):
            start = alphabet.find(start_text[i].lower())
            if start < 0:
                start = (i * 11 + 7) % len(alphabet)
            target = alphabet.find(char.lower())
            progress = min(1, offset / (0.65 + (i % 4) * 0.08))
            if progress >= 1 or start_text[i] == char:
                result += char
            elif quick:
                source = start_text[i]
                if source.isascii() and source.isdigit() and char.isascii() and char.isdigit():
                    distance = (int(char) - int(source)) % 10
                    if distance > 5:
                        distance -= 10
                    result += str((int(source) + round(progress * distance)) % 10)
                else:
                    letters = source + char
                    result += letters[1 if progress >= 0.5 else 0]
            else:
                distance = (target - start) % len(alphabet)
                step = int(progress * (len(alphabet) * 2 + distance))
                if step == 0:
                    result += start_text[i]
                else:
                    letter = alphabet[(start + step) % len(alphabet)]
                    result += letter.upper() if char.isupper() else letter
        return f"{text_color}{style}{result}\033[0m"
    step = min(len(alphabet) - 1, int(offset * len(alphabet)))
    result = ""
    for char in text:
        if char.isspace():
            result += char
            continue
        target = alphabet.find(char.lower())
        if target < 0:
            result += alphabet[step]
        else:
            letter = alphabet[min(step, target)]
            result += letter.upper() if char.isupper() else letter
    return f"{text_color}{style}{result}\033[0m"


# colored spaces fill the whole cell, blocks can leave gaps depending on the font
_SGR_PATTERN = re.compile(r"\x1b\[([0-9;]*)m")


def background_blocks(text, default_background=None):
    # use colored spaces instead of blocks; keep the text color as the background
    if not text or "█" not in text:
        return text

    result = []
    foreground = None
    cursor = 0

    def append_cells(chunk):
        for char in chunk:
            if char != "█":
                result.append(char)
                continue
            if foreground is None:
                if default_background is None:
                    result.append(" ")
                else:
                    result.extend((default_background, " ", unbg))
            else:
                result.extend((rgback(*foreground), " ", unbg))

    for match in _SGR_PATTERN.finditer(text):
        append_cells(text[cursor:match.start()])
        sequence = match.group(0)
        params = match.group(1)
        values = [part for part in params.split(";") if part]
        if params in ("0", "39") or "39" in values:
            foreground = None
        elif (
            len(values) >= 5
            and values[0] == "38"
            and values[1] == "2"
        ):
            try:
                foreground = tuple(int(value) for value in values[2:5])
            except ValueError:
                foreground = None
        result.append(sequence)
        cursor = match.end()

    append_cells(text[cursor:])
    return "".join(result)


# big numbers for easier access!
def bignumber_db(digit):
    art = {
        '0': [
            "  ████  ",
            "██    ██",
            "██    ██",
            "██    ██",
            "  ████  "
        ],
        '1': [
            "  ██  ",
            "████  ",
            "  ██  ",
            "  ██  ",
            "██████"
        ],
        '2': [
            "  ████  ",
            "██    ██",
            "    ██  ",
            "  ██    ",
            "████████"
        ],
        '3': [
            "  ████  ",
            "██    ██",
            "   ███  ",
            "██    ██",
            "  ████  "
        ],
        '4': [
            "██    ██",
            "██    ██",
            "████████",
            "      ██",
            "      ██"
        ],
        '5': [
            "████████",
            "██      ",
            "██████  ",
            "      ██",
            "██████  "
        ],
        '6': [
            "  █████ ",
            "██      ",
            "██████  ",
            "██    ██",
            "  ████  "
        ],
        '7': [
            "████████",
            "      ██",
            "    ██  ",
            "  ██    ",
            "  ██    "
        ],
        '8': [
            "  ████  ",
            "██    ██",
            "  ████  ",
            "██    ██",
            "  ████  "
        ],
        '9': [
            "  ████  ",
            "██    ██",
            "  ██████",
            "      ██",
            " █████  "
        ]
    }
    return art.get(digit, ["        "] * 5)

def bignumber(number_str, display=False, background=None):
    if not number_str.isdigit() or len(number_str) < 1 or len(number_str) > 3:
        return None

    # white by default, other screens can choose their own background
    if background is None:
        background = globals().get(
            "xbf",
            "\x1b[48;2;242;242;242m",
        )

    digit_arts = [bignumber_db(digit) for digit in number_str]
    
    result_lines = []
    for line_idx in range(5):
        line_parts = [art[line_idx] for art in digit_arts]
        line = "  ".join(line_parts)
        result_lines.append(background_blocks(line, background))

    if display:
        print("\n".join(result_lines))
    
    return result_lines

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
INTERFACE
Here's where... you really don't want to look. This is the absolute mess of hardcoded coordinates, colors, and styles that
creates the actual game interface. It's a nightmare to maintain, but it works, so good luck.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def reward_number_art(value, background):
    art = bignumber(str(value), background=background)
    if art is not None:
        return art
    label = format_number(value)
    width = max(17, len(label))
    return [" " * width, " " * width, f"{xf}{bold}{label:^{width}}{reset}", " " * width, " " * width]


def levelup():
    # don't overflow :c
    max_level = 100
    if player.level >= max_level or player.xp < player.xpneeded:
        game.goto = mainmenu
        return

    # calculate how many times we can level up based on current XP and required XP for next level
    level = player.level
    levels_gained = 0
    xp_for_next = player.xpneeded
    player.xp -= xp_for_next
    level += 1
    levels_gained += 1
    while level < max_level:
        xp_for_next = round(xp_for_next + 15 + level / 4) # determines curve
        if player.xp >= xp_for_next:
            player.xp -= xp_for_next
            level += 1
            levels_gained += 1
        else:
            break

    player.level = level
    player.xpneeded = round(xp_for_next)
    player.save()
    
    # if that's done, "level" should show the new level
    # (player.level only updates when we save)
    
    
    
    # get how you look!
    player.load() # just for safety
    thresholds = [
        (0, x8), (5, x7), (10, xf),(15, x3),(20, x9),(25, xb),(30, x2),(35, xa),(40, xlorange),(45, xlyellow),(50, xe),(55, x5),(60, xd),(65, xlred),(70, xc),(75, x4),(80, rgb(184, 172, 246)),(85, rgb(254, 163, 98)),(90, rgb(186, 243, 219)),(95, rgb(255, 131, 101)),(100, rgb(227, 62, 57)),
    ]
    player.color = None
    for req_level, color in thresholds:
        if player.level >= req_level:
            player.color = color
    sound("celebration")
    sound("swish")
    screen_wipe("center", 15)
    cls()
    delay = 0.05
    print(f"[10;1H{xf}                                  | |   _ / /__\\\\[ \\ [  ]/ /__\\\\ | |  [  | | |[ '/'`\\ \\| | ")
    animation_sleep(delay)
    print(f"[10;1H{xf}{player.color}                                  | |   _ / /__\\\\[ \\ [  ]/ /__\\\\ | |  [  | | |[ '/'`\\ \\| | ")
    print(f"[9;1H{xf}                                  | |      .---.  _   __  .---.  | |   __   _  _ .--.  | | ")
    print(f"[11;1H{xf}                                 _| |__/ || \\__., \\ \\/ / | \\__., | |   | \\_/ |,| \\__/ ||_| ")
    animation_sleep(delay)
    print(f"[9;1H{xf}{player.color}                                  | |      .---.  _   __  .---.  | |   __   _  _ .--.  | | ")
    print(f"[11;1H{xf}{player.color}                                 _| |__/ || \\__., \\ \\/ / | \\__., | |   | \\_/ |,| \\__/ ||_| ")
    animation_sleep(delay)
    print(f"[8;1H{xf}                                |_   _|                         [  |                   | | ")
    print(f"[12;1H{xf}                                |________| '.__.'  \\__/   '.__.'[___]  '.__.'_/| ;.__/ (_) ")
    animation_sleep(delay)
    print(f"[8;1H{xf}{player.color}                                |_   _|                         [  |                   | | ")
    print(f"[12;1H{xf}{player.color}                                |________| '.__.'  \\__/   '.__.'[___]  '.__.'_/| ;.__/ (_) ")
    print(f"[7;1H{xf}{bold}                                 _____                           __                     _  ")
    print(f"[13;1H{xf}                                                                              [__|         {reset}")
    animation_sleep(delay)
    print(f"[7;1H{xf}{bold}{player.color}                                 _____                           __                     _  ")
    print(f"[13;1H{xf}{player.color}                                                                              [__|         {reset}")
    
    added_attack = levels_gained * 10
    added_defense = levels_gained * 5
    x = player.level
    basehp = round(50 + (x-1)*20 + ((x-1)*(x+2))/4)
    a = player.level
    b = level
    added_health=round((b - a)*20 + ((b - 1)*(b + 2) - (a - 1)*(a + 2)) / 4)
    
    added_defense = levels_gained * 0.3
    
    # keep level-up numbers white
    graph = bignumber(str(level), display=False, background=xbf)

    print(background_blocks(f"""
{player.color}[15;1H                                                  ██████
{player.color}                                                ██      ██  
{player.color}                                                ██ •  • ██  
{player.color}                                                ██      ██  
{player.color}                                                  ██████      {xf}{graph[0]}
{player.color}                                                    ██        {xf}{graph[1]}                                     
{player.color}                                                    ██    ██  {xf}{graph[2]}   
{player.color}                                                    ██  ██    {xf}{graph[3]}                                        
{player.color}                                                 ███████      {xf}{graph[4]}
{player.color}                                               ██   ██       
{player.color}                                                    ██      
{player.color}                                                    ██      
{player.color}                                                  ██  ██    
{player.color}                                                ██      ██  
""").strip(), end="")
    center(f"{xf}› press any key to confirm ‹", 31)
    pause = key()
    game.goto = mainmenu
    return
    
    






















def startup_animation():
    if setting.effective_setting("disable_startup_animation"):
        game.goto = mainmenu
        return

    # Quick fade in.
    cls()
    fade_duration = 1.25
    steps = 15 if animations_enabled() else 1
    step_delay = fade_duration / steps
    
    art = f"""
    [2;4H{xb}{bold}                         ____        _   _   _             {x8}    {xe}{bold} ____                  _     {reset}
    [3;4H{xb}{bold}                        | __ )  __ _| |_| |_| | ___  ___   {x8}    {xe}{bold}| __ )  ___ _ __   ___| |__  {reset}
    [4;4H{xb}{bold}                        |  _ \\ / _` | __| __| |/ _ \\/ __|  {x7}o   {xe}{bold}|  _ \\ / _ \\ '_ \\ / __| '_ \\ {reset} 
    [5;4H{xb}{bold}                        | |_) | (_| | |_| |_| |  __/\\__ \\  {x7} f  {xe}{bold}| |_) |  __/ | | | (__| | | |{reset}
    [6;4H{xb}{bold}                        |____/ \\__,_|\\__|\\__|_|\\___||___/  {x8}    {xe}{bold}|____/ \\___|_| |_|\\___|_| |_|{reset}
    [10;4H{xlorange}                                                      _│=│__________
    [11;4H{xlorange}                                                     /              \\
    [12;4H                            {x9}{italic}{bold}[2]{unbold}{x9}⤵️{unbold}                   {xlorange}/ {rgb(255,202,102)}{bold}{italic}[1]{reset}{rgb(255,202,102)}{italic} Your House{unbold}{xlorange} \\   {xd}      │>>>
    [13;4H{x9}                         {italic}Blacksmith{unbold}{xlorange}                /__________________\\{unbold}  {xd}      │ 
    [14;4H{x3}                        ____________ .' '.   {xlorange}       ││  ││ /--\\ ││  ││ {unbold}      {xd} / \\     {x5}{bold}{italic}[3]{unbold}{x5}⤵️{reset}         
    [15;4H{x3}                       //// ////// /V_.-._\\  {xlorange}       ││[]││ │ .│ ││[]││ {unbold}      {xd}/___\\ {x5}{italic}Viewpoint{reset}             
    [16;4H{x3}                      // /// // ///==\\ u │.  {xlorange}       ││__││_│__│_││__││ {unbold}      {xd}│ u │_ _ _ _ _ _    
    [17;4H{x3}                     ///////-\\////====\\==│{x7}:::::::::::::::::::::::::::::::::::{xd}│u u│ U U U U U     
    [18;4H{x3}                     │----/\\u │--│++++│..│{x7}'''''''''''{x7}::::::::::::::{x7}''''''''''{xd}│+++│+-+-+-+-+-+    
    [19;4H{x3}                     │u u│u │ │u ││││││..│     {xa}\\│/{x7}      {x7}'::::::::'   {xa}\\│/{x7}     {xd}│===│>=== _ _ ==    
    [20;4H{x3}                     │===│  │u│==│++++│==│ {xa}\\│/          {x7}.::::::::.{xa}\\│/{x7}        {xd}│ T │....│ V │..    
    [21;4H{x3}                     │u u│u │ │u ││HH││         {xa}\\│/{x7}    {x7}.::::::::::.            {xa}\\│/                       
    [22;4H{x3}                     │===│_.│u│_.│+HH+│{x8}_              {x7}.::::::::::::.       {xa}\\│/{x7}   {x8} _                  
    [23;4H{xe}                                    {x8}__(_)___  {xa}\\│/{x7}    {x7}.::::::::::::::.        {x8} ___(_)__               
    [24;1H{x8}--------------------------------------/  / \\  /│       {x7}.:::::;;;:::;;:::.       {x8}│\\  / \\  \\------------------------------------   
    [25;1H{x8}_____________________________________/_______/ │      {x7}.::::::;;:::::;;:::.      {x8}│ \\_______\\___________________________________{x7}   
    [26;1H{x8}   │     │       │     │       │     [===  =] /│    {x7} .:::::;;;::::::;;;:::.     {x8}│\\ [==  = ]   │       │       │       │   │   {x7}   
    [27;1H{x8}___│_____│_______│_____│_______│_____[ = == ]/ │    {x7}.:::::;;;:::::::;;;::::.    {x8}│ \\[ ===  ]___│_______│_______│_______│___│___{x7}   
    [28;1H{x8}│       │     │       │     │       │[  === ] /│   {x7}.:::::;;;::::::::;;;:::::.   {x8}│\\ [=  ===] │       │       │       │   │     {x7}   
    [29;1H{x8}│_______│_____│_______│_____│_______│[== = =]/ │  {x7}.:::::;;;::::::::::;;;:::::.  {x8}│ \\[ ==  =]_│_______│_______│_______│___│_____{x7}   
    [30;1H{x8}    │     │       │     │       │    [ == = ] /│ {x7}.::::::;;:::::::::::;;;::::::. {x8}│\\ [== == ]      │       │       │           │{x7}   
    [31;1H{x8}____│_____│_______│_____│_______│____[=  == ]/ │{x7}.::::::;;:::::::::::::;;;::::::.{x8}│ \\[  === ]______│_______│_______│___________│{x7}   
    [32;1H{x8}      │     │       │     │       │  [ === =] /{x7}.::::::;;::::::::::::::;;;:::::::.{x8}\\ [===  =]   │       │       │       │   │   {x9}
    [33;1H{x8}______│_____│_______│_____│_______│__[ == ==]/{x7}.::::::;;; {xf}{bold}[B] to battle{reset}{x7} ;;;:::::::.{x8}\\[=  == ]___│_______│_______│_______│___│__{reset}
    """
    
    with open("Scripts/tips.txt", "r", encoding="utf-8") as f:
        tips = [line.strip() for line in f if line.strip()]
    tip_text = f"{xf}{italic}{random.choice(tips)}{reset}"
    
    cursor(False)
    for step in range(1, steps + 1):
        t = step / steps
        def shift_color(match):
            r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return f"\x1b[38;2;{int(r * t)};{int(g * t)};{int(b * t)}m"
        
        frame = re.sub(r'\x1b\[38;2;(\d+);(\d+);(\d+)m', shift_color, art)
        
        move(1, 1)
        print(frame, end="", flush=True)
        center(re.sub(r'\x1b\[38;2;(\d+);(\d+);(\d+)m', shift_color, tip_text), 8)
        sys.stdout.flush()
        animation_sleep(step_delay)

    game.skip_mainmenu_cls = True
    game.goto = mainmenu
    return


def mainmenu():
    if not getattr(game, "skip_mainmenu_cls", False):
        cls()
        # if it's nighttime (between 8pm and 6am), display stars in the background (but only if there is space and isn't already being occupied)
        current_hour = time.localtime().tm_hour
        if setting.menu_background_decoration and (current_hour >= 20 or current_hour < 6):
            for _ in range(random.randint(30, 100)):
                x = random.randint(1, shutil.get_terminal_size(fallback=(128, 36)).columns)
                y = random.randint(1, 15)
                # make the stars more random in shape
                star_shape = random.choice(["⁺", "⋆", "₊"])
                # and variable in color with randint RGB values to keep them gray-to-white
                star_color = rgb(random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
                print(f"\033[{y};{x}H{star_color}{star_shape}\x1b[0m", end="", flush=True)
        print(f"""
        [2;4H{xb}{bold}                         ____        _   _   _             {x8}    {xe}{bold} ____                  _     {reset}
        [3;4H{xb}{bold}                        | __ )  __ _| |_| |_| | ___  ___   {x8}    {xe}{bold}| __ )  ___ _ __   ___| |__  {reset}
        [4;4H{xb}{bold}                        |  _ \\ / _` | __| __| |/ _ \\/ __|  {x7}o   {xe}{bold}|  _ \\ / _ \\ '_ \\ / __| '_ \\ {reset} 
        [5;4H{xb}{bold}                        | |_) | (_| | |_| |_| |  __/\\__ \\  {x7} f  {xe}{bold}| |_) |  __/ | | | (__| | | |{reset}
        [6;4H{xb}{bold}                        |____/ \\__,_|\\__|\\__|_|\\___||___/  {x8}    {xe}{bold}|____/ \\___|_| |_|\\___|_| |_|{reset}
        [10;4H{xlorange}                                                      _│=│__________
        [11;4H{xlorange}                                                     /              \\
        [12;4H                            {x9}{italic}{bold}[2]{unbold}{x9}⤵️{unbold}                   {xlorange}/ {rgb(255,202,102)}{bold}{italic}[1]{reset}{rgb(255,202,102)}{italic} Your House{unbold}{xlorange} \\   {xd}      │>>>
        [13;4H{x9}                         {italic}Blacksmith{unbold}{xlorange}                /__________________\\{unbold}  {xd}      │ 
        [14;4H{x3}                        ____________ .' '.   {xlorange}       ││  ││ /--\\ ││  ││ {unbold}      {xd} / \\     {x5}{bold}{italic}[3]{unbold}{x5}⤵️{reset}         
        [15;4H{x3}                       //// ////// /V_.-._\\  {xlorange}       ││[]││ │ .│ ││[]││ {unbold}      {xd}/___\\ {x5}{italic}Viewpoint{reset}             
        [16;4H{x3}                      // /// // ///==\\ u │.  {xlorange}       ││__││_│__│_││__││ {unbold}      {xd}│ u │_ _ _ _ _ _    
        [17;4H{x3}                     ///////-\\////====\\==│{x7}:::::::::::::::::::::::::::::::::::{xd}│u u│ U U U U U     
        [18;4H{x3}                     │----/\\u │--│++++│..│{x7}'''''''''''{x7}::::::::::::::{x7}''''''''''{xd}│+++│+-+-+-+-+-+    
        [19;4H{x3}                     │u u│u │ │u ││││││..│     {xa}\\│/{x7}      {x7}'::::::::'   {xa}\\│/{x7}     {xd}│===│>=== _ _ ==    
        [20;4H{x3}                     │===│  │u│==│++++│==│ {xa}\\│/          {x7}.::::::::.{xa}\\│/{x7}        {xd}│ T │....│ V │..    
        [21;4H{x3}                     │u u│u │ │u ││HH││         {xa}\\│/{x7}    {x7}.::::::::::.            {xa}\\│/                       
        [22;4H{x3}                     │===│_.│u│_.│+HH+│{x8}_              {x7}.::::::::::::.       {xa}\\│/{x7}   {x8} _                  
        [23;4H{xe}                                    {x8}__(_)___  {xa}\\│/{x7}    {x7}.::::::::::::::.        {x8} ___(_)__               
        [24;1H{x8}--------------------------------------/  / \\  /│       {x7}.:::::;;;:::;;:::.       {x8}│\\  / \\  \\------------------------------------   
        [25;1H{x8}_____________________________________/_______/ │      {x7}.::::::;;:::::;;:::.      {x8}│ \\_______\\___________________________________{x7}   
        [26;1H{x8}   │     │       │     │       │     [===  =] /│    {x7} .:::::;;;::::::;;;:::.     {x8}│\\ [==  = ]   │       │       │       │   │   {x7}   
        [27;1H{x8}___│_____│_______│_____│_______│_____[ = == ]/ │    {x7}.:::::;;;:::::::;;;::::.    {x8}│ \\[ ===  ]___│_______│_______│_______│___│___{x7}   
        [28;1H{x8}│       │     │       │     │       │[  === ] /│   {x7}.:::::;;;::::::::;;;:::::.   {x8}│\\ [=  ===] │       │       │       │   │     {x7}   
        [29;1H{x8}│_______│_____│_______│_____│_______│[== = =]/ │  {x7}.:::::;;;::::::::::;;;:::::.  {x8}│ \\[ ==  =]_│_______│_______│_______│___│_____{x7}   
        [30;1H{x8}    │     │       │     │       │    [ == = ] /│ {x7}.::::::;;:::::::::::;;;::::::. {x8}│\\ [== == ]      │       │       │           │{x7}   
        [31;1H{x8}____│_____│_______│_____│_______│____[=  == ]/ │{x7}.::::::;;:::::::::::::;;;::::::.{x8}│ \\[  === ]______│_______│_______│___________│{x7}   
        [32;1H{x8}      │     │       │     │       │  [ === =] /{x7}.::::::;;::::::::::::::;;;:::::::.{x8}\\ [===  =]   │       │       │       │   │   {x9}
        [33;1H{x8}______│_____│_______│_____│_______│__[ == ==]/{x7}.::::::;;; {xf}{bold}[B] to battle{reset}{x7} ;;;:::::::.{x8}\\[=  == ]___│_______│_______│_______│___│__{reset}
        """)
        with open("Scripts/tips.txt", "r", encoding="utf-8") as f:
            tips = [line.strip() for line in f if line.strip()]
        center(f"{xf}{italic}{random.choice(tips)}{reset}", 8)
    else:
        game.skip_mainmenu_cls = False    

    offset = 0
    animate_menu_effects = animations_enabled()
    
    # check if you can level up
    if player.xp >= player.xpneeded and player.level < 100:
        game.goto = levelup
        return
    
    while True:
        if animate_menu_effects:
            offset += 0.005
        print(f"[33;1H{x8}______│_____│_______│_____│_______│__[ == ==]/{x7}.::::::;;; {xlred}{bold}{shine('[B] to battle',offset=offset, color=(255, 71, 76), bold=True)}{reset}{x7} ;;;:::::::.{x8}\\[=  == ]___│_______│_______│_______│___│__{reset}")
        shortcut_hint = f"[{setting.open_inventory.upper()}] Inventory  [{setting.open_character.upper()}] Character  [{setting.open_settings.upper()}] Settings"
        draw_text(2, 35, f"{xf}{shortcut_hint[:47]:<47}{reset}")
        if setting.debug_shortcuts:
            print(f"[35;53H{reset}{shine('[Ctrl+T] to modify data', offset=offset, bold=True,color=(132, 224, 133))}",end="",flush=True)
        k = key(timeout=0 if animate_menu_effects else None)
        if k.lower() == "b":
            sound("woosh")
            screen_wipe("normal", 10)
            game.goto = battle
            return
        if k.lower() == "1":
            game.goto = house
            return
        if k.lower() == setting.open_inventory:
            game.goto = inventory
            return
        if k.lower() == setting.open_character:
            game.goto = character
            return
        if k.lower() == setting.open_settings:
            game.goto = settings
            return
        # cheats interface (terminal) => Ctrl+T
        if setting.debug_shortcuts and k.lower() in ("ctrl/t", "t"):
            game.goto = internal_modify
            return
        if setting.debug_shortcuts and k.lower() == "k":
            game.goto = internal_modify_beta
            return
        if animate_menu_effects:
            time.sleep(0.01)
        # play sound: ctrl+R
        if setting.debug_shortcuts and k.lower() == "ctrl/r":
            game.goto = testsounds
            return
        # force levelup: ctrl+L
        if setting.debug_shortcuts and k.lower() == "ctrl/l":
            player.xp = player.xpneeded
            player.save()
            game.goto = mainmenu
            return

def testsounds():
    while True:
        # enter sound
        cls()
        name = (getx(1, 1, prompt="Enter sound name: ", allow_none=True) or "").strip()
        # if name is back, go back to main menu
        if name.lower() == "back":
            game.goto = mainmenu
            return
        pitch = getx(
            2,
            1,
            prompt="Enter pitch: ",
            expect="float",
            allow_none=True,
        )
        if pitch is None:
            pitch = 1.0
        sound(f"{name} {pitch}")



def internal_modify_beta():
    console_height = 31
    terminal_row = 34
    statusbar_row = 36
    lines = [""] * 36
    rendered_console = [None] * console_height
    autocomplete_rows = {}
    command_input = ""

    command_colors = {
        "exit": xlred,
        "experience": xlyellow,
        "xp": xlyellow,
        "quit": xlred,
        "help": xlyellow,
        "?": xlyellow,
        "commands": xlyellow,
    }

    command_descriptions = {
        "exit": "Exit the console and return to the main menu.",
        "quit": "Exit the console and return to the main menu.",
        "help": "Display a list of available commands.",
        "?": "Display a list of available commands.",
        "commands": "Display a list of available commands.",
        "experience": "Modify your in-game XP.",
        "xp": "Modify your in-game XP.",
    }

    def terminal_width():
        return max(20, shutil.get_terminal_size(fallback=(80, 36)).columns)

    def fit_line(line, width=None, background=""):
        width = width or terminal_width()
        line_width = width if background else width - 1
        padding = " " * max(0, line_width - visible_len(line))
        return f"{line}{background}{padding}{reset}"

    def write_frame(*parts):
        sys.stdout.write("".join(parts))
        sys.stdout.flush()

    def redraw_console(force=False):
        # only redraw rows that changed
        width = terminal_width()
        frame = []
        for index in range(console_height):
            is_autocomplete_row = index in autocomplete_rows
            line = autocomplete_rows.get(index, lines[index])
            background = xb8 if is_autocomplete_row else ""
            rendered = fit_line(line, width, background)
            if force or rendered != rendered_console[index]:
                frame.append(f"\x1b[{index + 1};1H\x1b[2K{rendered}")
                rendered_console[index] = rendered
        if frame:
            write_frame(*frame)

    def redraw_statusbar():
        write_frame(f"\x1b[{statusbar_row};1H{xf}{fit_line(lines[35])}")

    def redraw_terminal():
        write_frame(f"\x1b[{terminal_row};1H{fit_line(lines[33])}")

    def add_line(line):
        lines[:30] = lines[1:31]
        lines[30] = line

    def autocomplete(command):
        # show suggestions without adding them to command history
        nonlocal autocomplete_rows
        matches = sorted(
            name for name in command_colors
            if command and name.startswith(command)
        )
        overlay = {}
        if matches:
            longest = max(map(len, matches))
            overlay[0] = ""
            for index, match in enumerate(matches, start=1):
                spacing = " " * (longest + 2 - len(match))
                overlay[index] = (
                    f"{xb8}  {xe}· {bold}{match}{unbold}{spacing}"
                    f"{xf}- {italic}{command_descriptions[match]}{reset}"
                )
            overlay[len(matches) + 1] = ""

        if overlay != autocomplete_rows:
            changed_rows = set(autocomplete_rows) | set(overlay)
            for index in changed_rows:
                rendered_console[index] = None
            autocomplete_rows = overlay
            redraw_console()

    def check_command_validity(command):
        exact_match = command in command_colors
        possible_match = any(name.startswith(command) for name in command_colors)
        lines[35] = default_statusbar
        if exact_match:
            lines[33] = f"{xb8}{xa}› {xf}{command}{reset}"
            lines[35] = f"{xa}✓ {default_statusbar}"
        elif possible_match:
            lines[33] = f"{xb8}{xlyellow}› {xf}{command}{reset}"
        else:
            lines[33] = f"{xb8}{xc}› {xf}{command}{reset}"
            lines[35] = (
                f"{xc}⚠ {xlred}{bold}syntax error{reset} · {default_statusbar}"
            )

    def stylize_command(command, cursor_character="|"):
        if not command:
            hint = shine(
                text="type your command...",
                offset=time.time() / 4,
                color=(148, 148, 148),
                bold=False,
            )
            return f"{xb8}{xlyellow}› {xf}{xb8}{hint}"

        match = re.match(r"^(\S+)(.*)$", command.replace("\t", "    "))
        stylized = command
        if match:
            name, arguments = match.groups()
            if name in command_colors:
                stylized = f"{command_colors[name]}{bold}{name}{xf}{arguments}"
        return (
            f"{xb8}{xlyellow}› {xf}{xb8}{stylized}{reset}"
            f"{xlyellow}{xb8}{cursor_character}{reset}{xb8}"
        )

    def execute(command):
        lines[35] = default_statusbar
        add_line("")
        if command in {"exit", "quit"}:
            game.goto = mainmenu
        elif command in {"help", "?", "commands"}:
            add_line(f"{xa}{bold}· {reset}{xf}{bold}Executed {xa}{command}{reset}")
            add_line(f"{xa}╰{xf} Available commands: {', '.join(command_colors)}")
        else:
            closest = difflib.get_close_matches(
                command,
                command_colors,
                n=1,
                cutoff=0.6,
            )
            if closest:
                message = f"Did you mean to type '{closest[0]}'?"
            else:
                message = "Type 'help' for a list of available commands."
            add_line(
                f"{xc}{bold}· {reset}{xf}{command} - command not found! "
                f"{message}{reset}"
            )

    default_statusbar = (
        f"{xe}Battles of Bench {xf}· {x7}"
        f"v{version}.{subversion}.{subberversion} {xf}·{xb} "
        f"{unbold}{os.getcwd()}{reset}"
    )
    lines[35] = default_statusbar
    lines[33] = stylize_command(command_input)

    cls()
    redraw_console(force=True)
    redraw_statusbar()
    redraw_terminal()

    cursor_character = "|"
    last_cursor_change = time.monotonic()
    last_hint_frame = last_cursor_change

    while game.goto != mainmenu:
        pressed = key(timeout=0.05)
        now = time.monotonic()

        if pressed.lower() == "timeout":
            needs_redraw = False
            if command_input and now - last_cursor_change >= 0.5:
                cursor_character = " " if cursor_character == "|" else "|"
                last_cursor_change = now
                needs_redraw = True
            elif not command_input and now - last_hint_frame >= 0.1:
                last_hint_frame = now
                needs_redraw = True
            if needs_redraw:
                lines[33] = stylize_command(command_input, cursor_character)
                redraw_terminal()
            continue

        if pressed == "backspace":
            command_input = command_input[:-1]
        elif pressed == "space":
            command_input += " "
        elif pressed == "enter":
            execute(command_input)
            if game.goto == mainmenu:
                return
            command_input = ""
            autocomplete(command_input)
            redraw_console()
        elif pressed == "ctrl/c":
            command_input = ""
        elif pressed in {"esc", "escape"}:
            if not command_input:
                game.goto = mainmenu
                return
            command_input = ""
            lines[35] = (
                f"{xlred}{bold}Press esc again to exit{unbold} {xf}· "
                f"{default_statusbar}"
            )
            autocomplete(command_input)
            lines[33] = f"{xb8}{xc}› {xf}{reset}"
            redraw_terminal()
            redraw_statusbar()
            continue
        else:
            command_input += pressed

        cursor_character = "|"
        last_cursor_change = now
        check_command_validity(command_input)
        autocomplete(command_input)
        lines[33] = stylize_command(command_input, cursor_character)
        redraw_terminal()
        redraw_statusbar()

def internal_modify():
    def pause(message):
        print(message, end="", flush=True)
        getx(0, 0, expect="key")

    def parse_override_value(raw):
        text = raw.strip()
        lowered = text.lower()

        if lowered == "none":
            return None
        if lowered == "true":
            return True
        if lowered == "false":
            return False

        try:
            return ast.literal_eval(text)
        except Exception:
            pass

        try:
            return int(text)
        except Exception:
            pass

        try:
            return float(text)
        except Exception:
            return text

    def read_key_choice(valid_choices):
        valid = {c.lower() for c in valid_choices}
        while True:
            k = getx(0, 0, expect="key")
            if not isinstance(k, str):
                continue
            k = k.lower()
            if k in valid:
                return k

    def obj_full_preview(obj, limit=24):
        attrs = sorted(vars(obj).items())
        if not attrs:
            return f"  {xa}(no attributes yet){xf}"

        lines = []
        for name, value in attrs[:limit]:
            lines.append(f"  {xa}{name}{xf}: {value!r}")

        if len(attrs) > limit:
            lines.append(f"  {x8}... and {len(attrs) - limit} more{xf}")

        return "\n".join(lines)

    def confirm_destructive(action_text):
        cls()
        print(f"""
{x4}{bold}=== CONFIRM DESTRUCTIVE ACTION ==={reset}
{xf}{action_text}

{x2}[Y]{xf} Yes, proceed
{xc}[N]{xf} No, cancel
{reset}
""")
        return read_key_choice({"y", "n"}) == "y"

    player.load()
    setting.load()
    bind.load()
    load_binds()
    load_item(0)

    targets = {
        "p": ("player", player),
        "w": ("weapon", item),
        "h": ("head", head),
        "a": ("armor", armor),
        "g": ("general", d),
        "y": ("system", game),
        "s": ("settings", setting),
    }

    slot_paths = {
        "w": ("Weapon", "Items/active_weapon"),
        "h": ("Head", "Items/active_head"),
        "a": ("Armor", "Items/active_body"),
        "1": ("Bracelet", "Items/active_fragment_bracelet"),
        "2": ("Necklace", "Items/active_fragment_necklace"),
        "3": ("Ring", "Items/active_fragment_ring"),
    }

    reset_candidates = {
        "Player data": player,
        "Keybinds": bind,
        "Settings": setting,
        "System": game,
        "General": d,
        "Weapon": item,
        "Head": head,
        "Armor": armor,
        "Fragment": fragment,
    }

    reset_targets = [
        (name, obj)
        for name, obj in reset_candidates.items()
        if callable(getattr(obj, "reset", None))
    ]

    cursor(True)
    try:
        while True:
            cls()
            print(f"""
{xb}{bold}=== OVERRIDE INTERNAL DATA ==={reset}
{xf}Choose an area to modify. Press the [keys]:
{xf}--------------------------------------------
{xa}[P]{xf} 👤 Player fields
{xa}[N]{xf} 🏷️ Player name
{xf}--------------------------------------------
{xa}[W]{xf} ⚔️ Equipped weapon
{xa}[H]{xf} 🪖 Equipped head
{xa}[A]{xf} 🛡️ Equipped armor
{xa}[F]{xf} 🧩 Equipped fragment
{xf}--------------------------------------------
{xa}[G]{xf} 📦 Other variables
{xa}[Y]{xf} 🧠 System data
{xa}[S]{xf} ⚙️ Settings
{xf}--------------------------------------------
{x3}[E]{xf} 🎯 Equipped items
{xf}--------------------------------------------
{x3}[K]{xf} ⌨️ Keybinds
{xf}--------------------------------------------
{x2}[R]{xf} Spawn random fragments
{x2}[C]{xf} Spawn custom fragment
{xf}--------------------------------------------
{x4}[+]{xf} 💥 Clear or reset...
{xf}--------------------------------------------
{xc}[B]{xf} Back to main menu
{reset}
""")

            choice = read_key_choice({"p", "n", "w", "h", "a", "f", "g", "y", "s", "e", "k", "r", "c", "+", "b"})

            if choice == "b":
                game.goto = mainmenu
                return

            if choice == "r":
                cls()
                print(f"{xb}{bold}=== SPAWN RANDOM FRAGMENTS ==={reset}")
                amount = getx(
                    4,
                    1,
                    prompt=f"{x3}Amount (1-999){xf}: ",
                    expect="int",
                    min_val=1,
                    max_val=999,
                )
                first_id = None
                for _ in range(amount):
                    spawned_id = spawn_fragment(create_fragment())
                    if first_id is None:
                        first_id = spawned_id
                print(
                    f"\n{xa}Spawned {bold}{amount}{unbold} fragments "
                    f"(items {first_id}-{spawned_id}).{reset}"
                )
                print(f"{x7}Press any key to continue.{reset}")
                getx(0, 0, expect="key")
                continue

            if choice == "c":
                cls()
                print(f"""
{xb}{bold}=== SPAWN CUSTOM FRAGMENT ==={reset}
{xf}Slot: {xa}[1]{xf} Bracelet  {xa}[2]{xf} Necklace  {xa}[3]{xf} Ring
{reset}
""")
                slot = FRAGMENT_SLOTS[int(read_key_choice({"1", "2", "3"})) - 1]

                cls()
                print(f"{xb}{bold}=== SELECT MAIN STAT ==={reset}")
                main_stats = tuple(FRAGMENT_MAIN_STATS)
                for index, stat_name in enumerate(main_stats, start=1):
                    print(f"{xa}[{index}]{xf} {stat_name}")
                main_stat = main_stats[
                    int(read_key_choice({str(i) for i in range(1, 9)})) - 1
                ]

                cls()
                print(f"{xb}{bold}=== SELECT SET ==={reset}")
                set_names = tuple(FRAGMENT_SETS)
                for index, set_name in enumerate(set_names, start=1):
                    print(f"{xa}[{index}]{xf} {set_name}")
                set_name = set_names[
                    int(read_key_choice({str(i) for i in range(1, 5)})) - 1
                ]
                level = getx(
                    10,
                    1,
                    prompt=f"{x3}Starting level (1-{FRAGMENT_MAX_LEVEL}){xf}: ",
                    expect="int",
                    min_val=1,
                    max_val=FRAGMENT_MAX_LEVEL,
                )
                created = create_fragment(slot, main_stat, set_name, level)
                spawned_id = spawn_fragment(created)
                print(
                    f"\n{xa}Spawned item {bold}{spawned_id}{unbold}: "
                    f"{created.name}, Lv {created.level}, "
                    f"{format_fragment_stat(created.main_stat, get_fragment_main_stat_value(created))}.{reset}"
                )
                print(f"{x7}Press any key to continue.{reset}")
                getx(0, 0, expect="key")
                continue

            if choice == "+":
                while True:
                    cls()
                    reset_lines = []
                    for idx, (label, _) in enumerate(reset_targets, start=1):
                        reset_lines.append(f"    {xa}[{idx}]{xf} Reset {label}")

                    reset_block = "\n".join(reset_lines) if reset_lines else f"    {x8}(no reset-capable targets found){xf}"
                    delete_screen_path = os.path.join(os.getcwd(), "General", "screensetup.txt")
                    delete_setup_path = os.path.join(os.getcwd(), "General", "setup.txt")

                    print(f"""
{x4}{bold}=== ADVANCED FUNCTIONS ==={reset}
{xf}Destructive actions (confirmation required):

{reset_block}

    {x4}[C]{xf} Clear screen setup ({delete_screen_path})
    {x4}[U]{xf} Reset setup ({delete_setup_path})

{xc}[B]{xf} Back
{reset}
""")

                    valid_adv = {"b", "c", "u"}
                    valid_adv.update({str(i) for i in range(1, len(reset_targets) + 1)})
                    adv_choice = read_key_choice(valid_adv)

                    if adv_choice == "b":
                        break

                    if adv_choice == "c":
                        if not confirm_destructive("Delete General/screensetup.txt?"):
                            pause(f"{x8}Cancelled.{xf} Press any key to continue...")
                            continue
                        if os.path.exists(delete_screen_path):
                            os.remove(delete_screen_path)
                            pause(f"{xa}Deleted.{xf} Press any key to continue...")
                        else:
                            pause(f"{x8}File not found, nothing to delete.{xf} Press any key to continue...")
                        continue

                    if adv_choice == "u":
                        if not confirm_destructive("Delete General/setup.txt?"):
                            pause(f"{x8}Cancelled.{xf} Press any key to continue...")
                            continue
                        if os.path.exists(delete_setup_path):
                            os.remove(delete_setup_path)
                            pause(f"{xa}Deleted.{xf} Press any key to continue...")
                        else:
                            pause(f"{x8}File not found, nothing to delete.{xf} Press any key to continue...")
                        continue

                    target_idx = int(adv_choice) - 1
                    target_label, target_obj = reset_targets[target_idx]
                    if not confirm_destructive(f"Reset {target_label}?"):
                        pause(f"{x8}Cancelled.{xf} Press any key to continue...")
                        continue

                    try:
                        target_obj.reset()
                        if target_obj is bind:
                            load_binds()
                        if target_obj is setting:
                            setting.load()
                        if target_obj is player:
                            player.load()
                        pause(f"{xa}Reset complete:{xf} {target_label}. Press any key to continue...")
                    except Exception as exc:
                        pause(f"{xlred}Reset failed:{xf} {exc}. Press any key to continue...")
                continue

            if choice == "n":
                cls()
                current_name = read("General/playername", default="")
                print(f"""
{xb}{bold}=== PLAYER NAME ==={reset}
{xf}Current name: {xa}{current_name!r}{xf}

{xf}Enter a new player name.
{xc}Type [B] to cancel.{xf}
{reset}
""")
                new_name = (
                    getx(10, 1, prompt=f"{x3}New name{xf}: ", allow_none=True)
                    or ""
                ).strip()
                if new_name.lower() == "b":
                    continue
                if len(new_name) < 2 or len(new_name) > 15:
                    pause(f"{xlred}Name must be between 2 and 15 characters.{xf} Press any key to continue...")
                    continue

                update("General/playername", new_name)
                player.name = new_name
                pause(f"{xa}Saved{xf} player name as {new_name!r}. Press any key to continue...")
                continue

            if choice == "e":
                while True:
                    cls()
                    print(f"""
{xb}{bold}=== EQUIPPED SLOT IDS ==={reset}
{xf}Current IDs:
    {xa}Weapon{xf}: {read('Items/active_weapon', default='none')}
    {xa}Head{xf}:   {read('Items/active_head', default='none')}
    {xa}Armor{xf}:  {read('Items/active_body', default='none')}
    {xa}Bracelet{xf}: {read('Items/active_fragment_bracelet', default='none')}
    {xa}Necklace{xf}: {read('Items/active_fragment_necklace', default='none')}
    {xa}Ring{xf}:     {read('Items/active_fragment_ring', default='none')}

{xf}Choose slot:
    {xa}[W]{xf} Weapon
    {xa}[H]{xf} Head
    {xa}[A]{xf} Armor
    {xa}[1]{xf} Bracelet
    {xa}[2]{xf} Necklace
    {xa}[3]{xf} Ring

{xc}[B]{xf} Back
{reset}
""")

                    slot_choice = read_key_choice({"w", "h", "a", "1", "2", "3", "b"})
                    if slot_choice == "b":
                        break

                    slot_name, slot_path = slot_paths[slot_choice]
                    raw_id = (
                        getx(
                            25,
                            1,
                            prompt=f"{x3}New item ID for {slot_name}{xf} ({xc}B{xf}=back, Enter=none): ",
                            allow_none=True,
                        )
                        or ""
                    ).strip()
                    if raw_id.lower() == "b":
                        continue

                    if raw_id == "" or raw_id.lower() == "none":
                        update(slot_path, "none")
                        try:
                            load_item(0)
                            msg = f"{x2}Updated{xf} {slot_name} slot to {xa}'none'{xf}."
                        except Exception as exc:
                            msg = f"{xlorange}Updated file to 'none', but loading failed:{xf} {exc}"
                        pause(msg + " Press any key to continue...")
                        continue

                    try:
                        new_id = int(raw_id)
                        if new_id < 0:
                            raise ValueError()
                    except ValueError:
                        pause(f"{xlred}Please enter a valid non-negative number.{xf} Press any key to continue...")
                        continue

                    update(slot_path, new_id)
                    try:
                        load_item(0)
                        msg = f"{x2}Updated{xf} {slot_name} slot to item ID {new_id}."
                    except Exception as exc:
                        msg = f"{xlorange}Updated file, but loading failed:{xf} {exc}"
                    pause(msg + " Press any key to continue...")
                continue

            if choice == "k":
                while True:
                    cls()
                    fields = sorted(bind._persistent_fields.keys())
                    current = "\n".join([f"  {xa}{name}{xf}: {getattr(bind, name, '')}" for name in fields])

                    print(f"""
{xb}{bold}=== KEYBINDS ==={reset}
{xf}Current binds:
{current}

{xf}Type a keybind name to edit.
{xc}Type [B] to go back.{xf}
{reset}
""")

                    field = (
                        getx(17, 1, prompt=f"{x3}Keybind{xf}: ", allow_none=True)
                        or ""
                    ).strip().lower()
                    if field == "b":
                        break
                    if field not in bind._persistent_fields:
                        pause(f"{xlred}Unknown keybind.{xf} Press any key to continue...")
                        continue

                    raw_value = (
                        getx(
                            18,
                            1,
                            prompt=f"{x3}New value for {field}{xf} (current={getattr(bind, field)!r}) [{xc}B{xf}=back]: ",
                            allow_none=True,
                        )
                        or ""
                    ).strip()
                    if raw_value.lower() == "b":
                        continue
                    if raw_value == "":
                        pause(f"{xlred}Keybind cannot be empty.{xf} Press any key to continue...")
                        continue

                    setattr(bind, field, raw_value.lower())
                    bind.save()
                    load_binds()
                    pause(f"{x2}Saved{xf} keybind {field} = {raw_value.lower()!r}. Press any key to continue...")
                continue

            if choice == "f":
                cls()
                print(f"""
{xb}{bold}=== SELECT EQUIPPED FRAGMENT ==={reset}
{xa}[1]{xf} Bracelet
{xa}[2]{xf} Necklace
{xa}[3]{xf} Ring
{xc}[B]{xf} Back
{reset}
""")
                fragment_choice = read_key_choice({"1", "2", "3", "b"})
                if fragment_choice == "b":
                    continue
                slot = FRAGMENT_SLOTS[int(fragment_choice) - 1]
                target_name = f"{slot.lower()} fragment"
                target_obj = FRAGMENT_EQUIPPED_OBJECTS[slot]
            else:
                if choice not in targets:
                    pause(f"{xlred}Invalid option.{xf} Press any key to continue...")
                    continue
                target_name, target_obj = targets[choice]

            while True:
                cls()
                preview = obj_full_preview(target_obj)

                print(f"""
{xb}{bold}Editing: {target_name}{reset}

{xf}Current attributes preview:
{preview}

Type an attribute name to override.
{xc}Type [B] to go back.{xf}
{reset}
""")

                prompt_row = 10 + len(preview.splitlines())
                field = (
                    getx(prompt_row, 1, prompt=f"{x3}Attribute{xf}: ", allow_none=True)
                    or ""
                ).strip()

                if field.lower() == "b":
                    break

                current_value = getattr(target_obj, field, "<missing>")
                raw_value = (
                    getx(
                        prompt_row + 1,
                        1,
                        prompt=f"{x3}New value for {field}{xf} (current={current_value!r}) [{xc}B{xf}=back]: ",
                        allow_none=True,
                    )
                    or ""
                ).strip()

                if raw_value.lower() == "b":
                    continue

                new_value = parse_override_value(raw_value)
                setattr(target_obj, field, new_value)

                # save changed player values and settings
                if target_obj is player and field in getattr(player, "_persistent_fields", {}):
                    player.save()
                    save_note = " (saved to Player/data.txt)"
                elif target_obj is setting and field in getattr(setting, "_persistent_fields", {}):
                    setting.save()
                    save_note = " (saved to Settings/settings.txt)"
                elif target_obj in (
                    item,
                    head,
                    armor,
                    fragment_bracelet,
                    fragment_necklace,
                    fragment_ring,
                ):
                    category_map = {
                        item: ("Items/active_weapon", "Weapons"),
                        head: ("Items/active_head", "Helmets"),
                        armor: ("Items/active_body", "Bodywear"),
                        fragment_bracelet: (
                            "Items/active_fragment_bracelet",
                            "Fragments",
                        ),
                        fragment_necklace: (
                            "Items/active_fragment_necklace",
                            "Fragments",
                        ),
                        fragment_ring: (
                            "Items/active_fragment_ring",
                            "Fragments",
                        ),
                    }
                    active_path, category_name = category_map[target_obj]
                    active_id = read(active_path, default=0)
                    try:
                        active_id = int(active_id)
                    except Exception:
                        active_id = 0

                    if active_id > 0:
                        if category_name == "Fragments":
                            _reset_object(fragment, vars(target_obj))
                        save_item(active_id, category_name)
                        if category_name == "Fragments":
                            load_item(0)
                        save_note = f" (saved to Items/{category_name}/item{active_id}.txt)"
                    else:
                        save_note = " (runtime only: no active item id to save)"
                else:
                    save_note = ""

                print(f"{xa}Set{xf} {target_name}.{field} = {new_value!r}{save_note}")
                pause("Press any key to continue...")
    finally:
        cursor(False)

def battle():
    d.frombattle = True
    d.first_turn = True
    d.latest_action = ""
    d.battle_action_history = []
    cls()
    game.goto = character # load stuff then immediately jump to battle2() from there
    return

def whose_turn():
    if player.av >= 100 and player.av >= enemy.av:
        return "player" # player
    if enemy.av >= 100 and enemy.av > player.av:
        return "enemy" # enemy
    return "none" # regen

def simple_text(text, short_text):
    return short_text if setting.simplify_tutorials else text


def setting_description(item):
    if setting.simplify_tutorials:
        return SIMPLE_DESCRIPTIONS.get(item["attr"], item["description"])
    return item["description"]


def player_turn():
    d.latest_action += f"\n  {xf}→ Your turn, waiting for key..."
    battle_show_data()
    k = key()
    if k == "2" and setting.debug_shortcuts:
        player.hp = max(1, round(player.total_hp * 0.2))
        d.latest_action = f"{xlyellow}⚙  HP set to 20%{reset}"
        battle_show_data()
        return
    elif k == "6" and setting.debug_shortcuts:
        player.hp = max(1, round(player.total_hp * 0.6))
        d.latest_action = f"{xlyellow}⚙  HP set to 60%{reset}"
        battle_show_data()
        return
    elif k == "0" and setting.debug_shortcuts:
        enemy.hp = 0
        game.goto = battle_win
        return
    elif k.lower() == bind.attack:
        game.goto = battle_attack
        return
    elif k.lower() == bind.skill:
        game.goto = battle_skill
        return
    elif k.lower() == bind.ult:
        game.goto = battle_ult
        return
    elif k.lower() == bind.heal:
        game.goto = battle_heal
        return
    elif k.lower() == bind.forfeit:
        print(f"{xlred}Forfeit this battle? {bind.confirm.upper()} / {bind.deny.upper()}{reset}")
        while True:
            answer = key().lower()
            if answer in (bind.confirm, "enter"):
                game.goto = mainmenu
                return
            if answer in (bind.deny, bind.back, "esc"):
                game.goto = player_turn
                return

def enemy_turn():
    d.latest_action += f"\n  {xf}→ Enemy's turn, attacking..."
    game.goto = enemy_attack
    return

def new_turn():
    d.latest_action += f"\n  {xf}→ New turn started!"
    if not d.first_turn:
         if player.regen > 0:
             heal_amount = round(
                 player.total_hp
                 * (player.regen / 100)
                 * getattr(player, "healing_received_multiplier", 1)
             )
             player.hp = min(player.total_hp, player.hp + heal_amount)
             d.latest_action += f"\n  {xb}💧  Regenerated {format_number(heal_amount)} HP{reset}"
    d.first_turn = False
    
    # if player hp is above max, set it to max
    if player.hp >= player.total_hp:
        player.hp = player.total_hp
        
    # regen action values
    player.av += player.speed
    enemy.av += enemy.speed

    d.av_difference = player.av - enemy.av

    # check for whose turn it is
    turn = whose_turn()
    if turn == "player":
        game.goto = player_turn
        return
    elif turn == "enemy":
        game.goto = enemy_turn
        return
    else:
        game.goto = new_turn # keep regenerating until someone can act
        return
    
def battle_lose():
    cls()
    print(f"{xb}{bold}=== YOU LOSE ==={reset}")
    print(f"{xf}You have been defeated by the {enemy.name}.")
    print(f"{x8}Press any key to return to the main menu.{reset}")
    key()
    game.goto = mainmenu
    return

def battle_win_title(text, start_row):
    # draw the victory box
    print(f"""
[{start_row+1};1H#3{xlyellow}                 ╭────────────────────────╮
[{start_row+2};1H#4{xlyellow}                 ╭────────────────────────╮
[{start_row+3};1H#3{xlyellow}                 │{" " * ((24 - len(text)) // 2)}{xa}{bold}{shine(text=text,offset=time.time(),bold=True,color=(240, 232, 158))}{reset}{xlyellow}{" " * ((24 - len(text)) // 2)}│
[{start_row+4};1H#4{xlyellow}                 │{" " * ((24 - len(text)) // 2)}{xa}{bold}{shine(text=text,offset=time.time(),bold=True,color=(240, 232, 158))}{reset}{xlyellow}{" " * ((24 - len(text)) // 2)}│
[{start_row+5};1H#3{xlyellow}                 ╰────────────────────────╯
[{start_row+6};1H#4{xlyellow}                 ╰────────────────────────╯
""",flush=False)


def battle_win_progress(text_row, progress_text, bar, xp_bar_length,
                        xp_notification_column, levelup_notice_frame, color_notice_frame):
    # xp bar and the two notices beside it
    print(f"""
[{text_row+5};1H#5{xlyellow}{" "*(shutil.get_terminal_size(fallback=(128, 36)).columns - 1)}
[{text_row+6};1H#5{xlyellow}{" " * ((shutil.get_terminal_size(fallback=(128, 36)).columns - visible_len(progress_text)) // 2 - 3)}{progress_text}
[{text_row+7};1H#5{xlyellow}{" "*(shutil.get_terminal_size(fallback=(128, 36)).columns - 1)}
[{text_row+8};1H#5{xlyellow}{" "*33}{f"{xb0} "*(xp_bar_length+4)}{reset}
[{text_row+9};1H#5{xlyellow}{" "*33}{xb0}  {bar}{xb0}  {reset}
[{text_row+10};1H#5{xlyellow}{" "*33}{xb0}  {bar}{xb0}  {reset}
[{text_row+11};1H#5{xlyellow}{" "*33}{f"{xb0} "*(xp_bar_length+4)}{reset}
[{text_row+9};{xp_notification_column}H#5{levelup_notice_frame}
[{text_row+10};{xp_notification_column}H#5{color_notice_frame}
""",flush=True)


def battle_win_notice(text, started, width, duration, strong=True):
    if not text:
        return " " * width
    elapsed = time.perf_counter() - started
    if elapsed >= duration:
        return " " * width

    # fade from light to dark
    progress = max(0.0, min(1.0, elapsed / duration))
    shade = round(242 + (55 - 242) * progress)
    style = bold if strong else unbold
    return f"{rgb(shade, shade, shade)}{style}{text.ljust(width)}{reset}"


def battle_win_xp_bar(level, xp, xpneeded, length, color, dark_color):
    if level >= CHARACTER_MAX_LEVEL:
        progress = 1.0
    else:
        progress = max(0.0, min(max(0, xp) / max(1, xpneeded), 1.0))

    # filled cells, then the dark part
    filled = round(progress * length)
    bar = f"{reset}{color} " * filled
    bar += f"{dark_color} " * (length - filled)
    return bar + reset


def battle_win_stars(star_tier, celebration_mode):
    # star groups for the three fills
    star_groups = (
        ((2, 24, 25), (3, 22, 27), (4, 20, 29), (5, 22, 27), (6, 24, 25)),
        ((1, 40, 41), (2, 38, 43), (3, 36, 45), (4, 34, 47),
         (5, 36, 45), (6, 38, 43), (7, 40, 41)),
        ((0, 60, 61), (1, 58, 63), (2, 56, 65), (3, 54, 67),
         (4, 52, 69), (5, 54, 67), (6, 56, 65), (7, 58, 63),
         (8, 60, 61)),
        ((1, 80, 81), (2, 78, 83), (3, 76, 85), (4, 74, 87),
         (5, 76, 85), (6, 78, 83), (7, 80, 81)),
        ((2, 96, 97), (3, 94, 99), (4, 92, 101), (5, 94, 99),
         (6, 96, 97)),
    )
    star_stages = ((2,), (1, 3), (0, 4))
    star_stage_colours = (xb6, xblyellow, xbe)

    star_tier = max(1, min(3, int(star_tier)))
    print(
        "".join(
            f"[{row};1H#5[2K"
            for row in range(2, 11)
        ),
        end="",
    )
    star_rows = {}
    for star_group in range(len(star_groups)):
        for row, start_col, end_col in star_groups[star_group]:
            star_rows.setdefault(row, []).append((start_col, end_col))
    for row in star_rows:
        star_rows[row].sort()
    # paint the gray star catalog once
    for row in sorted(star_rows):
        for start_col, end_col in star_rows[row]:
            print(
                f"[{2 + row};{start_col}H#5"
                f"{xb7}{' ' * (end_col - start_col + 1)}{unbg}",
                end="",
                flush=False,
            )
    sys.stdout.flush()
    total_star_duration = {1: 0.0, 2: 0.3, 3: 0.7}[star_tier]
    star_stage_duration = total_star_duration / star_tier
    stage_delays = (0, 0.3, 0.4)

    # fill the middle star first, then the pairs beside it
    for star_stage in range(star_tier):
        if celebration_mode > 0 and celebration_mode < 3:
            time.sleep(stage_delays[star_stage])

        star_stage_rows = {}
        for star_group in star_stages[star_stage]:
            for row, start_col, end_col in star_groups[star_group]:
                star_stage_rows.setdefault(row, []).append((start_col, end_col))
        for row in star_stage_rows:
            star_stage_rows[row].sort()
        rows = sorted(star_stage_rows)
        stage_start = time.perf_counter()

        for row_index, row in enumerate(rows, start=1):
            if celebration_mode >= 3:
                # extreme: flash the row white before filling it
                for start_col, end_col in star_stage_rows[row]:
                    print(f"\x1b[{2 + row};{start_col}H\x1b#5{xbf}{' ' * (end_col - start_col + 1)}{unbg}", end="")
                sys.stdout.flush()
                star_hold = min(0.04, star_stage_duration / len(rows) * 0.45)
                if star_hold > 0:
                    time.sleep(star_hold)

            for start_col, end_col in star_stage_rows[row]:
                color = star_stage_colours[star_stage]
                print(f"\x1b[{2 + row};{start_col}H\x1b#5{color}{' ' * (end_col - start_col + 1)}{unbg}", end="")
            if celebration_mode >= 3:
                sys.stdout.flush()
                deadline = stage_start + star_stage_duration * row_index / len(rows)
                time.sleep(max(0, deadline - time.perf_counter()))
        sys.stdout.flush()



def battle_win_number_lines(number):
    lines = []
    for row in range(5):
        digits = []
        for digit in str(number):
            digits.append(bignumber_db(digit)[row])
        lines.append("  ".join(digits))
    return lines


def battle_win_gold(amount, balance, row, counting=False):
    amount_text = format_number(amount)
    balance_text = format_number(balance + amount)
    plain_text = f"¤ +{amount_text} gold → {balance_text}"
    # double-size text uses twice the cells
    column = max(1, (shutil.get_terminal_size(fallback=(128, 36)).columns - visible_len(plain_text) * 2) // 4)
    plus = f"{xlyellow}{bold}+{reset}"
    number = f"{xlyellow}{bold}{amount_text}{reset}"
    text = f"{xf}¤ {reset}{plus}{number}{xlyellow} gold{reset}{xf} → {reset}{x7}{balance_text}{reset}"
    color = xlyellow if counting else ""
    ending = reset if counting else ""
    print(f"""
\x1b[{row};1H\x1b[2K\x1b#3{color}{" " * (column - 1)}{text}{ending}
\x1b[{row + 1};1H\x1b[2K\x1b#4{color}{" " * (column - 1)}{text}{ending}
""", end="", flush=True)


def battle_win_colors(level, colors):
    color = x8
    values = (94, 94, 94)
    for required_level, text_color, rgb_values in colors:
        if level >= required_level:
            color = text_color
            values = rgb_values

    dark_values = []
    for value in values:
        dark_values.append(max(0, round(value * 0.22)))
    return color, rgback(*values), rgback(*dark_values)


def battle_win_count_gold(totalgold, gold_balance_start, gold_row, celebration_mode):
    # timing and sound controls for the gold count
    gold_animation_duration = 0.675
    gold_animation_tick_amount = 25
    gold_animation_max_ticks = 10
    gold_animation_acceleration = 1.20
    gold_animation_pitch_rise = 0.16
    gold_animation_delay = 0.3
    confirmation_fade_duration = 0.5
    gold_animation_tick_amount = max(1, int(gold_animation_tick_amount))

    if totalgold > 0 and celebration_mode >= 2:
        gold_animation_tick_count = max(1, math.ceil(totalgold / gold_animation_tick_amount))
        gold_animation_tick_count = min(gold_animation_max_ticks, gold_animation_tick_count)
    else:
        gold_animation_tick_count = 0
    gold_animation_pitches = []

    gold_animation_started = False
    gold_animation_start = 0.0
    gold_animation_tick = 0
    gold_count = 0
    # gold next, then the continue prompt
    confirmation_prompt_text = "› press any key to continue ‹"
    confirmation_prompt = f"{xf}{confirmation_prompt_text}"
    confirmation_column = max(1, (shutil.get_terminal_size(fallback=(128, 36)).columns - visible_len(confirmation_prompt)) // 2 - 2)
    confirmation_prompt_frame = " " * visible_len(confirmation_prompt)
    draw_text(confirmation_column, 34, confirmation_prompt_frame)
    if totalgold > 0 and celebration_mode >= 2:
        # precache after the stars so the opening animation stays responsive
        for gold_tick in range(gold_animation_tick_count):
            gold_progress = (gold_tick + 1) / gold_animation_tick_count
            if gold_tick == 0:
                gold_pitch = 1.0
            else:
                gold_pitch = 1.0 + gold_animation_pitch_rise * (gold_progress ** 1.15)
            gold_animation_pitches.append(gold_pitch)
            sound(f"PRECACHE pickup_silver {gold_pitch:.4f}")
        time.sleep(gold_animation_delay)
        gold_animation_started = True
        gold_animation_start = time.perf_counter()

    # finish remaining gold ticks
    if totalgold > 0 and gold_animation_started:
        while gold_animation_tick < gold_animation_tick_count:
            gold_animation_tick += 1
            gold_progress = gold_animation_tick / gold_animation_tick_count
            gold_target = (
                gold_animation_start
                + gold_progress * gold_animation_duration
            )
            time.sleep(max(0, gold_target - time.perf_counter()))
            gold_count = min(totalgold, max(gold_count, 1, round(totalgold * gold_progress ** gold_animation_acceleration)))
            sound(
                f"pickup_silver "
                f"{gold_animation_pitches[gold_animation_tick - 1]:.4f}"
            )
            battle_win_gold(gold_count, gold_balance_start, gold_row, counting=True)
            confirmation_shade = round(55 + (242 - 55) * gold_progress)
            confirmation_prompt_frame = f"{rgb(confirmation_shade, confirmation_shade, confirmation_shade)}{confirmation_prompt_text}{reset}"
            print(f"\x1b[34;{confirmation_column}H\x1b#5{confirmation_prompt_frame}", end="", flush=True)

    battle_win_gold(totalgold, gold_balance_start, gold_row)

    if not gold_animation_started:
        if animations_enabled():
            for confirmation_step in range(1, 11):
                confirmation_progress = confirmation_step / 10
                confirmation_shade = round(55 + (242 - 55) * confirmation_progress)
                confirmation_prompt_frame = f"{rgb(confirmation_shade, confirmation_shade, confirmation_shade)}{confirmation_prompt_text}{reset}"
                draw_text(confirmation_column, 34, confirmation_prompt_frame)
                time.sleep(confirmation_fade_duration / 10)
        else:
            confirmation_prompt_frame = f"{xf}{confirmation_prompt_text}{reset}"
            draw_text(confirmation_column, 34, confirmation_prompt_frame)



def battle_win_draw_number(lines, row, column, width, color, bonus_text, highlight_rows=()):
    frame = []
    for offset, raw_line in enumerate(lines):
        background = color
        if offset in highlight_rows:
            background = xbf
        rendered = pad_visible(background_blocks(raw_line, background), width)
        suffix = ""
        if offset == 4:
            suffix = f" {bonus_text}{reset}"
        frame.append(f"\x1b[{row + offset};{column}H\x1b#5{rendered}{suffix}")
    print("\n".join(frame), end="", flush=False)


def battle_win():
    # check remaining hp percentage
    remaining_hp_pct = (player.hp / player.total_hp) * 100
    if remaining_hp_pct >= 80:
        text = random.choice(["Excellent!", "Stellar performance!", "Outstanding!", "Perfect!", "Battle over!", "Well done!", "Nice work!", "You win!", "Victory!"])
        sound("end_excellent")
    elif remaining_hp_pct >= 50:
        text = random.choice(["Great job!", "Quick victory!", "Well played!", "Great performance!", "Battle over!", "Well done!", "Nice work!", "You win!", "Victory!"])
        sound("end_great")
    else:
        sound("end_good")
        text = random.choice(["Battle over!", "Well done!", "Nice work!", "You win!", "Victory!"])

    # celebration levels: 0 = minimal, 1 = small, 2 = regular, 3 = extreme
    celebration_mode = getattr(setting, "victory_celebration", 2)
    effective_setting = getattr(setting, "effective_setting", None)
    if callable(effective_setting):
        celebration_mode = effective_setting("victory_celebration")
    try:
        celebration_mode = max(0, min(3, int(celebration_mode)))
    except (TypeError, ValueError):
        celebration_mode = 2
    # keep reduced motion local to this animation
    if getattr(setting, "reduce_motion", False) or not animations_enabled():
        celebration_mode = 0
    
    # scale the xp reward from remaining health
    level_progress = max(0.0, (float(player.level) - 1.0) / 89.0)
    full_health_bonus = 8.0 * (150.0 / 8.0) ** (level_progress ** 1.33)
    health_ratio = max(0.0, min(1.0, remaining_hp_pct / 100.0))
    health_xp_bonus = round(full_health_bonus * health_ratio ** 0.75)
    if celebration_mode == 0:
        cls()
    else:
        screen_wipe("normal",10)
    
    totalxp = round(enemy.xp_reward + health_xp_bonus)
    gold_reward = max(0, int(enemy.gold_reward))
    totalgold = max(0, round(gold_reward * health_ratio ** 0.75))

    # local animation controls
    xp_animation_duration = 1.8
    xp_animation_tick_amount = 1
    star_to_number_delay = 0.2
    notice_fade_duration = 0.5
    title_animation_timeout = 0.05

    xp_animation_tick_amount = max(1, int(xp_animation_tick_amount))

    # keep live xp separate from the reward number
    animated_level = min(CHARACTER_MAX_LEVEL, max(1, int(getattr(player, "level", 1))))
    animated_xp = max(0, int(getattr(player, "xp", 0)))
    animated_xpneeded = max(1, int(getattr(player, "xpneeded", 1)))
    earned_xp = 0
    xp_required_for_next = animated_xpneeded
    if animated_level >= CHARACTER_MAX_LEVEL:
        xp_required_for_next = 0

    thresholds = [
        (0, x8), (5, x7), (10, xf), (15, x3), (20, x9), (25, xb),
        (30, x2), (35, xa), (40, xlorange), (45, xlyellow), (50, xe),
        (55, x5), (60, xd), (65, xlred), (70, xc), (75, x4),
        (80, rgb(184, 172, 246)), (85, rgb(254, 163, 98)),
        (90, rgb(186, 243, 219)), (95, rgb(255, 131, 101)),
        (100, rgb(227, 62, 57)),
    ]
    # remember rgb values too, no need to read ansi codes at every level-up
    level_colors = []
    color_milestones = []
    for required_level, color in thresholds:
        match = re.search(r"38;2;(\d+);(\d+);(\d+)m", color)
        if match:
            values = tuple(int(value) for value in match.groups())
        else:
            values = (94, 94, 94)
        level_colors.append((required_level, color, values))
        if required_level > 0:
            color_milestones.append(required_level)
    player_color, xp_color, xp_dark_color = battle_win_colors(animated_level, level_colors)
    levelup_notice = ""
    color_notice = ""
    levelup_notice_start = 0.0
    color_notice_start = 0.0
    notice_width = len("New color unlocked!")
    levelup_notice_frame = " " * notice_width
    color_notice_frame = " " * notice_width

    def battle_add_xp(amount):
        nonlocal animated_xp, animated_level, animated_xpneeded
        nonlocal levelup_notice, levelup_notice_start, color_notice, color_notice_start
        nonlocal player_color, xp_color, xp_dark_color

        # add xp, keep leveling until we don't have enough anymore
        animated_xp += amount
        while (
            animated_level < CHARACTER_MAX_LEVEL
            and animated_xp >= animated_xpneeded
        ):
            xp_for_next = animated_xpneeded
            animated_xp -= xp_for_next
            animated_level += 1
            sound("inside_levelup")
            levelup_notice = "Level up!"
            levelup_notice_start = time.perf_counter()
            if animated_level in color_milestones:
                color_notice = "New color unlocked!"
                color_notice_start = time.perf_counter()
            if animated_level < CHARACTER_MAX_LEVEL:
                xp_for_next = round(xp_for_next + 15 + animated_level / 4)
            animated_xpneeded = round(xp_for_next)
            player_color, xp_color, xp_dark_color = battle_win_colors(animated_level, level_colors)

    gold_balance_start = int(getattr(player, "money", 0))
    gold_row = 31

    title_text = random.choice([
        "your progress to level",
        "your advancement to level",
        "here's your progress to level",
        "your journey to level",
        "your path to level",
        "your quest to level",
    ])
    
    if celebration_mode > 0:
        move(4,1)

        print(f"""
#5{" "*120}
#3{xlyellow}                 ╭────────────────────────╮
#4{xlyellow}                 ╭────────────────────────╮
#3{xlyellow}                 │{" " * ((24 - len(text)) // 2)}{xa}{bold}{shine(text=text,offset=time.time(),bold=True,color=(240, 232, 158))}{reset}{xlyellow}{" " * ((24 - len(text)) // 2)}│
#4{xlyellow}                 │{" " * ((24 - len(text)) // 2)}{xa}{bold}{shine(text=text,offset=time.time(),bold=True,color=(240, 232, 158))}{reset}{xlyellow}{" " * ((24 - len(text)) // 2)}│
#3{xlyellow}                 ╰────────────────────────╯
#4{xlyellow}                 ╰────────────────────────╯
""")
    
    move(15,30)

    # minimal uses the final animated layout
    start_row = 5
    text_row = 13
    milestone_shifts = 0
    max_title_shifts = 5
    max_number_shifts = 5
    xp_bar_length = 50
    xp_notification_column = 33 + xp_bar_length + 6
    next_level = str(animated_level + 1) if animated_level < CHARACTER_MAX_LEVEL else "MAX"
    progress_text = f"{bold}{player_color}XP earned{unbold} {xf}· {title_text} {bold}{player_color}{next_level}:{reset}"
    xp_animation_tick_count = max(1, math.ceil(totalxp / xp_animation_tick_amount)) if totalxp > 0 else 1
    xp_animation_start = time.perf_counter()

    milestone_values = sorted(set(
        round(totalxp * milestone_ratio) for milestone_ratio in (0.8, 0.85, 0.9, 0.95, 0.98, 0.99, 1)
    )) if totalxp > 0 else []
    xp_milestones = milestone_values if celebration_mode > 0 else []
    milestone_index = 0
    if celebration_mode == 0:
        # match the animated resting coordinates
        milestone_count = min(max_title_shifts, len(set(milestone_values)))
        start_row += milestone_count
        text_row += min(max_number_shifts, milestone_count)
    if celebration_mode > 0:
        count_values = range(xp_animation_tick_count)
    else:
        count_values = range(1)
    extra_xp = 0
    bonus_label = ""
    bonus_text = " "

    # count the earned xp
    for xp_tick in count_values:
        if totalxp > 0:
            if celebration_mode == 0:
                xp_tick_start = 0
                xp_tick_end = totalxp
            else:
                xp_tick_start = xp_tick * xp_animation_tick_amount
                xp_tick_end = min(totalxp, (xp_tick + 1) * xp_animation_tick_amount)
            xp_tick_amount = max(0, xp_tick_end - xp_tick_start)
        else:
            xp_tick_amount = 0
        earned_xp = min(totalxp, earned_xp + xp_tick_amount)
        battle_add_xp(xp_tick_amount)

        while (
            milestone_index < len(xp_milestones)
            and earned_xp >= xp_milestones[milestone_index]
            and milestone_shifts < max_title_shifts
        ):
            print(
                "".join(
                    f"[{start_row + 1 + offset};1H[2K#5"
                    for offset in range(6)
                ),
                end="",
            )
            start_row += 1
            if milestone_shifts < max_number_shifts:
                print(
                    "".join(
                        f"[{row};1H#5[2K"
                        for row in range(text_row, text_row + 12)
                    ),
                    end="",
                )
                text_row += 1
            milestone_shifts += 1
            milestone_index += 1

        levelup_notice_frame = battle_win_notice(levelup_notice, levelup_notice_start, notice_width, notice_fade_duration)
        color_notice_frame = battle_win_notice(color_notice, color_notice_start, notice_width, notice_fade_duration)
        bonus_text = shine(text=bonus_label, offset=time.time(), bold=True, color=(242, 242, 242)) if bonus_label else " "
        art = reward_number_art(earned_xp, background=xp_color)
        length = max(visible_len(art[0]), visible_len(art[1]), visible_len(art[2]), visible_len(art[3]), visible_len(art[4]))
        text_column = max(1, shutil.get_terminal_size(fallback=(128, 36)).columns // 2 - (length // 2) - 3)
        next_level = str(animated_level + 1) if animated_level < CHARACTER_MAX_LEVEL else "MAX"
        progress_text = f"{bold}{player_color}XP earned{unbold} {xf}· {title_text} {bold}{player_color}{next_level}:{reset}"
        print(f"""
[{text_row};1H#5[2K[{text_row};{text_column}H{pad_visible(art[0], length)}
[{text_row+1};1H#5[2K[{text_row+1};{text_column}H{pad_visible(art[1], length)}
[{text_row+2};1H#5[2K[{text_row+2};{text_column}H{pad_visible(art[2], length)}
[{text_row+3};1H#5[2K[{text_row+3};{text_column}H{pad_visible(art[3], length)}
[{text_row+4};1H#5[2K[{text_row+4};{text_column}H{pad_visible(art[4], length)}{reset}
""",flush=False)
        
        battle_win_title(text, start_row)
        
        # xp bar - fill in the bar based on the current xp
        bar = battle_win_xp_bar(animated_level, animated_xp, animated_xpneeded,
                                xp_bar_length, xp_color, xp_dark_color)
        
        battle_win_progress(text_row, progress_text, bar, xp_bar_length,
                            xp_notification_column, levelup_notice_frame, color_notice_frame)
        
        
        if celebration_mode > 0 and totalxp > 0:
            target = xp_animation_start + (xp_tick + 1) * xp_animation_duration / xp_animation_tick_count
            time.sleep(max(0, target - time.perf_counter()))
    next_level = str(animated_level + 1) if animated_level < CHARACTER_MAX_LEVEL else "MAX"
    progress_text = f"{bold}{player_color}XP earned{unbold} {xf}· {title_text} {bold}{player_color}{next_level}:{reset}"
    print(f"""
    [{start_row+3};1H#3{xlyellow}                 │{" " * ((24 - len(text)) // 2)}{shine(text=text,offset=time.time(),bold=True,color=(240, 232, 158))}{xlyellow}{" " * ((24 - len(text)) // 2)}│
    [{start_row+4};1H#4{xlyellow}                 │{" " * ((24 - len(text)) // 2)}{shine(text=text,offset=time.time(),bold=True,color=(240, 232, 158))}{xlyellow}{" " * ((24 - len(text)) // 2)}│
    """,flush=True)
    extra_xp = 0
    bonus_label = ""
    bonus_text = " "
    if remaining_hp_pct >= 80:
        star_tier = 3
        extra_xp = 100 if animated_level >= CHARACTER_MAX_LEVEL else round(xp_required_for_next * 0.10)
        bonus_label = f"[+{format_number(extra_xp)} XP - excellent!]"
    elif remaining_hp_pct >= 50:
        star_tier = 2
        extra_xp = 50 if animated_level >= CHARACTER_MAX_LEVEL else round(xp_required_for_next * 0.05)
        bonus_label = f"[+{format_number(extra_xp)} XP - great!]"
    else:
        star_tier = 1
    if bonus_label:
        bonus_text = f"{reset}{bold}{xf}{bonus_label}{reset}"

    # show how well we did
    battle_win_stars(star_tier, celebration_mode)
    levelup_notice_frame = battle_win_notice(levelup_notice, levelup_notice_start, notice_width, notice_fade_duration)
    color_notice_frame = battle_win_notice(color_notice, color_notice_start, notice_width, notice_fade_duration)
    bonus_text = shine(text=bonus_label, offset=time.time(), bold=True, color=(242, 242, 242)) if bonus_label else " "
    final_art = reward_number_art(totalxp + extra_xp, background=xp_color)
    raw_number_lines = battle_win_number_lines(earned_xp)
    length = max(visible_len(line) for line in final_art)
    text_column = max(1, shutil.get_terminal_size(fallback=(128, 36)).columns // 2 - (length // 2) - 3)

    print(
        "".join(
            f"[{row};1H#5[2K"
            for row in range(text_row, text_row + 5)
        ),
        end="",
    )
    battle_win_draw_number(raw_number_lines, text_row, text_column, length, xp_color, bonus_text)
    bar = battle_win_xp_bar(animated_level, animated_xp, animated_xpneeded,
                            xp_bar_length, xp_color, xp_dark_color)
    battle_win_title(text, start_row)
    battle_win_progress(text_row, progress_text, bar, xp_bar_length,
                        xp_notification_column, levelup_notice_frame, color_notice_frame)

    if remaining_hp_pct >= 50 and celebration_mode >= 2:
        extra_xp_applied = False
        # sweep the big number
        shine_frames = (
            (0,),
            (0, 1),
            (0, 1, 2),
            (1, 2, 3),
            (2, 3, 4),
            (3, 4),
            (4,),
            (),
        )
        # keep the shine quick
        number_shine_delay = 0.04896
        number_shine_target = time.perf_counter() + (star_to_number_delay if celebration_mode >= 3 else number_shine_delay)
        for shine_index, highlight_rows in enumerate(shine_frames):
            if shine_index == 0:
                time.sleep(max(0, number_shine_target - time.perf_counter()))
            else:
                time.sleep(number_shine_delay)

            # apply the bonus when the shine begins
            if not extra_xp_applied:
                earned_xp = totalxp + extra_xp
                battle_add_xp(extra_xp)
                next_level = str(animated_level + 1) if animated_level < CHARACTER_MAX_LEVEL else "MAX"
                progress_text = f"{bold}{player_color}XP earned{unbold} {xf}· {title_text} {bold}{player_color}{next_level}:{reset}"
                raw_number_lines = battle_win_number_lines(earned_xp)
                extra_xp_applied = True
            levelup_notice_frame = battle_win_notice(levelup_notice, levelup_notice_start, notice_width, notice_fade_duration)
            color_notice_frame = battle_win_notice(color_notice, color_notice_start, notice_width, notice_fade_duration)
            bonus_text = shine(text=bonus_label, offset=time.time(), bold=True, color=(242, 242, 242)) if bonus_label else " "
            battle_win_draw_number(raw_number_lines, text_row, text_column, length, xp_color, bonus_text, highlight_rows)
            next_level = str(animated_level + 1) if animated_level < CHARACTER_MAX_LEVEL else "MAX"
            progress_text = f"{bold}{player_color}XP earned{unbold} {xf}· {title_text} {bold}{player_color}{next_level}:{reset}"
            bar = battle_win_xp_bar(animated_level, animated_xp, animated_xpneeded,
                                    xp_bar_length, xp_color, xp_dark_color)
            battle_win_title(text, start_row)
            battle_win_progress(text_row, progress_text, bar, xp_bar_length,
                                xp_notification_column, levelup_notice_frame, color_notice_frame)

    else:
        # apply the bonus after the stars
        earned_xp = totalxp + extra_xp
        battle_add_xp(extra_xp)
        levelup_notice_frame = battle_win_notice(levelup_notice, levelup_notice_start, notice_width, notice_fade_duration)
        color_notice_frame = battle_win_notice(color_notice, color_notice_start, notice_width, notice_fade_duration)
        bonus_text = shine(text=bonus_label, offset=time.time(), bold=True, color=(242, 242, 242)) if bonus_label else " "
        next_level = str(animated_level + 1) if animated_level < CHARACTER_MAX_LEVEL else "MAX"
        progress_text = f"{bold}{player_color}XP earned{unbold} {xf}· {title_text} {bold}{player_color}{next_level}:{reset}"
        raw_number_lines = battle_win_number_lines(earned_xp)
        battle_win_draw_number(raw_number_lines, text_row, text_column, length, xp_color, bonus_text)
        next_level = str(animated_level + 1) if animated_level < CHARACTER_MAX_LEVEL else "MAX"
        progress_text = f"{bold}{player_color}XP earned{unbold} {xf}· {title_text} {bold}{player_color}{next_level}:{reset}"
        bar = battle_win_xp_bar(animated_level, animated_xp, animated_xpneeded,
                                xp_bar_length, xp_color, xp_dark_color)
        battle_win_title(text, start_row)
        battle_win_progress(text_row, progress_text, bar, xp_bar_length,
                            xp_notification_column, levelup_notice_frame, color_notice_frame)
    # gold next, then the continue prompt
    battle_win_count_gold(totalgold, gold_balance_start, gold_row, celebration_mode)

    # fade the notices when needed
    if celebration_mode >= 1 and (bonus_label or levelup_notice or color_notice):
        bonus_column = text_column + length + 1
        fade_duration = notice_fade_duration
        fade_steps = 10
        for fade_step in range(1, fade_steps + 1):
            fade_progress = fade_step / fade_steps
            shade = round(242 + (55 - 242) * fade_progress)
            if bonus_label:
                print(f"[{text_row+4};{bonus_column}H#5{rgb(shade, shade, shade)}{unbold}{bonus_label}{reset}",end="",flush=True)
            levelup_notice_frame = battle_win_notice(levelup_notice, levelup_notice_start, notice_width, notice_fade_duration, strong=False)
            color_notice_frame = battle_win_notice(color_notice, color_notice_start, notice_width, notice_fade_duration, strong=False)
            print(f"[{text_row+9};{xp_notification_column}H#5{levelup_notice_frame}[{text_row+10};{xp_notification_column}H#5{color_notice_frame}",end="",flush=True)
            time.sleep(fade_duration / fade_steps)
        if bonus_label:
            print(f"[{text_row+4};{bonus_column}H#5{' ' * len(bonus_label)}{reset}",end="",flush=True)
        print(f"[{text_row+9};{xp_notification_column}H#5{' ' * notice_width}[{text_row+10};{xp_notification_column}H#5{' ' * notice_width}",end="",flush=True)

    # save xp and gold
    player.level = animated_level
    player.xp = animated_xp
    player.xpneeded = animated_xpneeded
    player.color = player_color
    player.money += totalgold
    player.save()

    # keep the title animated while waiting
    while True:
        print(f"""
[{start_row+3};1H#3{xlyellow}                 │{" " * ((24 - len(text)) // 2)}{shine(text=text,offset=time.time(),bold=True,color=(240, 232, 158))}{xlyellow}{" " * ((24 - len(text)) // 2)}│
[{start_row+4};1H#4{xlyellow}                 │{" " * ((24 - len(text)) // 2)}{shine(text=text,offset=time.time(),bold=True,color=(240, 232, 158))}{xlyellow}{" " * ((24 - len(text)) // 2)}│
""", flush=True)
        if celebration_mode >= 3 and totalgold > 0:
            battle_win_gold(totalgold, gold_balance_start, gold_row)
        if celebration_mode > 0 and animations_enabled():
            pressed_key = key(timeout=title_animation_timeout)
            if pressed_key == "TIMEOUT":
                continue
        else:
            pressed_key = key()
        break
    game.goto = mainmenu
    return

def after_attack():
    # if dead:
    if player.hp <= 0:
        game.goto = battle_lose
        return
    elif enemy.hp <= 0:
        game.goto = battle_win
        return
    battle_show_data()
    time.sleep(setting.battle_turn_delay)
    if player.av >= 100 or enemy.av >= 100:
        # someone can still act
        turn = whose_turn()
        if turn == "player":
            battle_show_data()
            game.goto = player_turn
            return
        elif turn == "enemy":
            battle_show_data()
            game.goto = enemy_turn
            return
    else:
        game.goto = new_turn
        return

def battle_preparation():
    d.frombattle = False
    player.load()
    global enemy

    # test for now, nothing special:
    player.hp = player.total_hp
    cls()
    print("Entering battle...")

    # enemy data for testing:
    
    #
    enemies_list = [
        EnemyData(name="Goblin", hp=7000, attack=1000, defense=10, xp_reward=20, gold_reward=100, speed=110),
        EnemyData(name="Orc", hp=5000, attack=2, defense=1, xp_reward=50, gold_reward=250, speed=80),
        EnemyData(name="Troll", hp=8000, attack=3, defense=2, xp_reward=100, gold_reward=500, speed=60),
        EnemyData(name="Dragon", hp=15000, attack=5, defense=3, xp_reward=200, gold_reward=1000, speed=40),
        EnemyData(name="Dark Knight", hp=12000, attack=4, defense=4, xp_reward=150, gold_reward=750, speed=50),
        EnemyData(name="Necromancer", hp=10000, attack=3, defense=2, xp_reward=120, gold_reward=600, speed=70),
        EnemyData(name="Ancient Dragon", hp=20000, attack=6, defense=5, xp_reward=500, gold_reward=250, speed=30),
    ]    
    for enemy_data in enemies_list:
        apply_difficulty(enemy_data, setting.battle_difficulty)

    # give the player the option to choose an enemy to fight
    cls()
    difficulty = ("Easy", "Normal", "Hard", "Extreme")[setting.battle_difficulty]
    if setting.battle_difficulty == 3:
        difficulty = f"{unbold}{xlred}{difficulty}{xb}{bold}"
    print(f"{xb}{bold}=== CHOOSE AN ENEMY ({difficulty}) ==={reset}")
    for idx, enemy_data in enumerate(enemies_list, start=1):
        print(f"{xa}[{idx}]{xf} {enemy_data.name} (HP: {format_number(enemy_data.hp)}, ATK: {format_number(enemy_data.attack)}, DEF: {format_number(enemy_data.defense)}, SPD: {format_number(enemy_data.speed)})")
    print(f"{xc}[{bind.back.upper()}]{xf} Back to main menu")
    while True:
        k = key()
        if k.lower() in (bind.back, "esc"):
            game.goto = mainmenu
            return
        try:
            choice = int(k)
            if 1 <= choice <= len(enemies_list):
                enemy = enemies_list[choice - 1]
                break
        except ValueError:
            pass
        
    # and load!
    enemy.max_hp = enemy.hp
    # prepare action values
    player.av = 0
    enemy.av = 0
    d.av_difference = player.av - enemy.av
    av_required = 100
    d.av_required = av_required
    # simulate battle
    game.goto = battle_loop
    return

def record_battle_action(actor):
    lines = short_action_log(d.latest_action)
    if not lines:
        return
    history = list(getattr(d, "battle_action_history", []))
    history.append((actor, "  •  ".join(lines)))
    d.battle_action_history = history[-5:]


def battle_show_data():
    cls()

    def hp_bar(current, maximum, width=20):
        if maximum <= 0:
            pct = 0.0
        else:
            pct = max(0.0, min(1.0, current / maximum))
        fill = int(width * pct)
        empty = width - fill
        return f"{xa}{'█' * fill}{x8}{'░' * empty}{reset}"

    enemy_max_hp = max(getattr(enemy, "max_hp", getattr(enemy, "hp", 1)), 1)
    player_max_hp = max(getattr(player, "total_hp", getattr(player, "hp", 1)), 1)

    # status indicator of turns
    # get console width
    console_width = shutil.get_terminal_size(fallback=(128, 36)).columns//2
    if player.av >= enemy.av:
        # your turn
        turn_indicator = f"{xf}{xbb}{bold}→ Your turn! →"
        d.temp_player_turn_indicator = turn_indicator
        fill = f"{xbb} "
    else:
        turn_indicator = f"{xf}{xbc}{bold}← Enemy's turn! ←"
        d.temp_enemy_turn_indicator = turn_indicator
        fill = f"{xbc} "
    length = visible_len(turn_indicator)
    side = max(0, (console_width - length) // 2)
    extra = max(0, console_width - length - side)
    turn_text = fill * side + turn_indicator + fill * extra
    print(f"[1;1H#3{turn_text}")
    print(f"[2;1H#4{turn_text}")
    
    print()
    print()
    print(f"{reset}{bold}{xf}  → Battle ←{reset}")
    print()

    print(f"{bold}{xlred}{enemy.name}{reset}")
    print(f"  {xb4}⚔️ Enemy 1 of 1{reset}")
    health_display = setting.battle_health_display
    enemy_health = []
    if health_display in ("Bar", "Both number and bar"):
        enemy_health.append(hp_bar(enemy.hp, enemy_max_hp))
    if health_display in ("Number", "Both number and bar"):
        enemy_health.append(f"{xf}{format_number(enemy.hp)}/{format_number(enemy_max_hp)}{reset}")
    print(f"  {x7}HP{reset}  {'  '.join(enemy_health)}")
    if setting.battle_details == "Detailed":
        print(f"  {x7}{simple_text('ATK', 'Damage')}{reset} {xf}{format_number(enemy.attack)}{reset}  |  {x7}{simple_text('DEF', 'Block %')}{reset} {xf}{format_number(enemy.defense)}{reset}  |  {x7}{simple_text('SPD', 'Speed')}{reset} {xf}{format_number(enemy.speed)}{reset}")
    if setting.battle_details == "Detailed":
        print(f"  {x7}{simple_text('Action Value', 'Action points')}{reset}  {xb}{format_number(enemy.av)}{reset}  ({xf}{"+" if d.av_difference >= 0 else ""}{format_number(d.av_difference)}{reset})")
    print(f"  {x7}Reward:{reset} {xa}{format_number(enemy.xp_reward)} XP{reset} and {xe}{format_number(max(0, int(enemy.gold_reward)))} gold coins{reset}")
    print()

    print(f"{bold}{xa}▸ {player.name}{reset}")
    player_health = []
    if setting.player_health_display in ("Bar", "Both number and bar"):
        player_health.append(hp_bar(player.hp, player_max_hp))
    if setting.player_health_display in ("Number", "Both number and bar"):
        player_health.append(f"{xf}{format_number(player.hp)}/{format_number(player_max_hp)}{reset}")
    print(f"  {x7}HP{reset}  {'  '.join(player_health)}")
    av_label = simple_text("Action Value", "Action points")
    if setting.battle_details == "Detailed":
        print(f"  {x7}{av_label}{reset}  {xb}{format_number(player.av)}{reset}")
    if setting.battle_details == "Detailed":
        print(f"  {x7}{simple_text('ATK', 'Damage')}{reset} {xf}{format_number(player.total_dmg)}{reset}  |  {x7}{simple_text('DEF', 'Block %')}{reset} {xf}{format_number(player.total_def)}{reset}  |  {x7}{simple_text('SPD', 'Speed')}{reset} {xf}{format_number(player.speed)}{reset}")
    if setting.battle_details == "Detailed":
        print(f"  {x7}Regen{reset} {xf}{format_number(player.regen)}%{reset}  |  {x7}Lifesteal{reset} {xf}{format_number(player.life_steal)}%{reset}  |  {x7}Crit{reset} {xf}{format_number(player.crit_rate)}%{reset}")
    print()

    print(f"{bold}{xb}⚙️ {simple_text('Keybinds you can use:', 'Battle controls:')}{reset}")
    print(f"  {xf}{bind.attack.upper()}{reset} {x7}Attack{reset}  •  {xf}{bind.skill.upper()}{reset} {x7}Skill{reset}  •  {xf}{bind.ult.upper()}{reset} {x7}Ultimate{reset}  •  {xf}{bind.heal.upper()}{reset} {x7}Heal{reset}  •  {xf}{bind.forfeit.upper()}{reset} {x7}Forfeit{reset}")
    if setting.debug_shortcuts:
        print(f"  {xf}2{reset} {x7}Set HP to 20%{reset}  •  {xf}6{reset} {x7}Set HP to 60%{reset}  •  {xf}0{reset} {x7}Win battle{reset}")
    print()
    # if it's your turn or not,
    if player.av >= enemy.av:
        turn_indicator = f"{xa} Your turn!{reset}"
    else:
        turn_indicator = f"{xlred} Enemy's turn!{reset}"
    print(f"{bold}{x7}● Last action:{reset}{turn_indicator}")
    history_length = setting.battle_action_history_length
    history = getattr(d, "battle_action_history", [])
    if history_length > 1 and history:
        print(f"  {x7}Recent actions (last {history_length}):{reset}")
        for actor, action in history[-history_length:]:
            summary = re.sub(r"\x1b\[[0-9;]*m", "", action)
            print(f"  {xf}{actor}: {summary[:95]}{reset}")
    elif getattr(d, "latest_action", "").strip():
        lines = (short_action_log(d.latest_action) if setting.battle_short_action_log
                 else [line.strip() for line in d.latest_action.splitlines() if line.strip()][:4])
        for line in lines:
            print(f"  {line[:95]}")
        if not lines:
            print(f"  {x7}No action yet.{reset}")
    else:
        print(f"  {x7}Still nothing! Maybe try pressing some of the keys above, hmm?{reset}")

def enemy_attack():
    d.latest_action = ""
    sound("shield", channel="sfx", pan=0.35)
    dmgdealt = max(
        0,
        round(
            enemy.attack
            * (100 - player.total_def)
            / 100
            * getattr(player, "damage_taken_multiplier", 1)
        ),
    )
    player.hp -= dmgdealt
    if dmgdealt > 0:
        d.latest_action += f"{xlred}⚔  {format_number(dmgdealt)}{xa} DMG RCV{reset}"
    else:
        d.latest_action += f"{x7}⚔  Blocked{reset}"
    
    # if player hp is above max, set it to max
    if player.hp >= player.total_hp:
        player.hp = player.total_hp
    
    # add separator to latest action
    d.latest_action += f"\n{x7}{'─' * 60}{reset}\n"
    # action value decrease
    enemy.av -= 100
    d.av_difference = player.av - enemy.av
    record_battle_action("Enemy")
    battle_show_data()
    game.goto = after_attack
    return

# functions for actions
def battle_attack():
    
    # add action value to enemy based on his speed
    player.av -= 100
    d.av_difference = player.av - enemy.av
    
    # normal hits (enemy.defense is a % reduction to damage, so 5 defense means 5% damage reduction):
    normal_damage, critical_damage = attack_damage(player, enemy)
    dmgdealt = normal_damage
    
    # if critical (chance triggers: random int 0-100, if it's less than player's crit chance, it's a crit):
    is_crit = random.random() * 100 < player.crit_rate
    if is_crit:
        dmgdealt = critical_damage
        d.latest_action = f"{rgb(255, 215, 0)}✴  CRIT!{reset} {format_number(dmgdealt)}{xa} DMG{reset}"
    else:
        d.latest_action = f"{xf}⚔  {format_number(dmgdealt)}{xa} DMG{reset}"
    
    enemy.hp -= dmgdealt
    sound("sword2", channel="sfx", pan=-0.35)
    
    # then, life steal (steal is float = % of damage dealt that is returned to you as HP):
    if player.life_steal > 0:
        steal_amount = round(
            dmgdealt
            * (player.life_steal / 100)
            * getattr(player, "healing_received_multiplier", 1)
        )
        player.hp = min(player.total_hp, player.hp + steal_amount)
        d.latest_action += f"\n{xlred}🩸 Life steal: {format_number(steal_amount)} HP stolen!{reset}"
        
    # if player hp is above max, set it to max
    if player.hp >= player.total_hp:
        player.hp = player.total_hp
    
    # add separator to latest action
    d.latest_action += f"\n{x7}{chr(9472) * 60}{reset}\n"
    record_battle_action("You")
    battle_show_data()
    game.goto = after_attack
    return

def battle_skill():
    d.latest_action = f"{x7}Skills are not available yet.{reset}"
    game.goto = player_turn
    return

def battle_ult():
    d.latest_action = f"{x7}Ultimates are not available yet.{reset}"
    game.goto = player_turn
    return

def battle_heal():
    d.latest_action = f"{x7}Healing items are not available yet.{reset}"
    game.goto = player_turn
    return

# battle loop incoming:
def battle_loop():
    game.goto = new_turn
    return
    

def house():
    gear_column = 67 if sys.platform == "darwin" else 66
    cls()
    player.load()
    thresholds = [
        (0, x8), (5, x7), (10, xf),(15, x3),(20, x9),(25, xb),(30, x2),(35, xa),(40, xlorange),(45, xlyellow),(50, xe),(55, x5),(60, xd),(65, xlred),(70, xc),(75, x4),(80, rgb(184, 172, 246)),(85, rgb(254, 163, 98)),(90, rgb(186, 243, 219)),(95, rgb(255, 131, 101)),(100, rgb(227, 62, 57)),
    ]
    player.color = None
    for req_level, color in thresholds:
        if player.level >= req_level:
            player.color = color
    print(f"""
 
                                                   {xlyellow}_│=│__________
                                                  /              \\
                                                 /                \\
                                                /__________________\\
                                                 ││  ││ /--\\ ││  ││
                                                 ││[]││ │ .│ ││[]││
                                                 ││__││_│__│_││__││{reset}

#3{xlorange}                ╭────────────────────────╮
#4{xlorange}                ╭────────────────────────╮
#3{xlorange}                │       {xlyellow}{bold}Your House{reset}{xlorange}       │
#4{xlorange}                │       {xlyellow}{bold}Your House{reset}{xlorange}       │
#3{xlorange}                ╰────────────────────────╯
#4{xlorange}                ╰────────────────────────╯
{player.color}       ██████                                                            
{player.color}     ██      ██     {x8}     ╭───────────────────────────╮         ╭───────────────────────────╮   
{player.color}     ██ •  • ██     {x8}╭────╯    {x7}{italic}Home, sweet home...{reset}{x8}    ╰────┬────╯    {x7}{underline}{italic} Available Options {reset}{x8}    ╰────╮     
{player.color}     ██      ██     {x8}│{x9}                                {x8}     │                                    {x8} │ 
{player.color}       ██████       {x8}│{player.color}{bold}  This is your house, welcome in!  {reset}{x8}  │  {xlyellow}{bold}[{setting.open_character.upper()}]{reset}{xe} 🚶 Manage character          {x8}  \033[97G│ 
{player.color}         ██         {x8}│{x9}                                    {x8} │   ╰─ {x2}{bold}[{setting.open_inventory.upper()}]{reset}{xa} 💼 Enter inventory       {x8}  \033[97G│           

{player.color}         ██  ██     {x8}│{xlyellow}  character or personalization will {x8} │{x1}                                   {x8}  │ 
{player.color}      ███████       {x8}│{xlyellow}  be displayed here on the right!   {x8} │  {x7}{bold}[{setting.open_settings.upper()}]{reset}{xf} \033[{gear_column}G⚙️\033[69GSettings & info           {x8}  \033[97G│ 
{player.color}    ██   ██         {x8}│{x9}                                    {x8} │{x1}                                   {x8}  │  
{player.color}         ██         {x8}│{xlorange}  To access any option on the right,{x8} │  {x5}{bold}[R]{reset}{xd} 🎧 Refresh game music       {x8}   \033[97G│ 
{player.color}         ██         {x8}│{xlorange}  simply press the keys that are{x8}     │                                   {x8}  │    
{player.color}       ██  ██       {x8}│{xlorange}  shown next to them!            {x8}    │  {xc}{bold}[{bind.back.upper()}] {reset}🏡 {xlred}{italic}<- Return to the main menu{x8}{x8}  \033[97G│ 
{player.color}     ██      ██     {x8}│{x9}                                    {x8} │                                     │              
{player.color}                    {x8}╰{x8}────────────────────────────────────{x8}─┴─────────────────────────────────────╯         
    """)
    if player.level >= 100:
        print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x3}{bold}[E]{reset}{xb} 💎 Convert excess XP     {x8}  \033[97G│ ")
    else:
        print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x3}{bold}[G]{reset}{xb} 🦮 Level guide/Builder   {x8}  \033[97G│ ")
    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            game.goto = mainmenu
            return
        if k.lower() == setting.open_settings:
            sound("map_switch2")
            game.goto = settings
            return
        if k.lower() == setting.open_inventory:
            sound("map_switch2")
            game.goto = inventory
            return
        if k.lower() == setting.open_character:
            sound("map_switch2")
            game.goto = character
            return
        # xp time
        if setting.debug_shortcuts and k.lower() == "x":
            # move to 1;1 and ask how much xp you wanna earn
            move(1, 1)
            x = getx(1, 1, prompt="Enter XP to earn: ", expect="int")
            player.xp += x
            player.save()
            blank(1,1,1,30)
            
        # convert excess XP into coins
        if k.lower() == "e" and player.level >= 100:
            player.load()
            # stuff goes here
            excess_xp = player.xp
            if excess_xp <= 5000:
                gold = excess_xp * 4

            elif excess_xp <= 15000:
                gold = (5000 * 4) + ((excess_xp - 5000) * 2)

            else:
                gold = (5000 * 4) + (10000 * 2) + ((excess_xp - 15000) * 1)
            # if there's nothing to convert:
            if gold <= 0:
                sound("ultimatehit")
                print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x4}{bold}[E]{reset}{xc}                {x7}          {reset}")
                print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x4}{bold}[E]{reset}{x4} 🚫 No XP to convert! {reset}")
                animation_sleep(0.025)
                print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x4}{bold}[E]{reset}{xc} 🚫 No XP to convert!{reset}")
            else:
                # determine reward sound from 1 to 5 based on xp amount (max 25,000)
                if excess_xp <= 1500:
                    reward_sound = "reward_1"
                elif excess_xp <= 2500:
                    reward_sound = "reward_2"
                elif excess_xp <= 5000:
                    reward_sound = "reward_3"
                elif excess_xp <= 7500:
                    reward_sound = "reward_4"
                else:
                    reward_sound = "reward_5"
                #sound("pop_2")
                #time.sleep(0.15)
                print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x6}{bold}[E]{reset}{xe} ⏳ Working          ")
                #time.sleep(0.4)
                update("Player/xp", 0)
                player.xp = 0
                player.money += gold
                player.save()
                pitch = 1
                dotsdisplay = "..."
                
                counts = (
                    min(20, int(math.sqrt(excess_xp / 1000) * 4))
                    if animations_enabled()
                    else 0
                )
                for i in range(counts):
                    # change dots
                    if dotsdisplay == ".  ":
                        dotsdisplay = ".. "
                    elif dotsdisplay == ".. ":
                        dotsdisplay = "..."
                    else:
                        dotsdisplay = ".  "
                    sound(f"pickup_coin {pitch}")
                    if gold/counts*(i+1) < 100000:
                        print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x6}{bold}[E]{reset}{xe} ⏳ Working{dotsdisplay} {xlyellow}({bold}+{format_number(round(gold/counts*(i+1)))}{reset}🪙{xlyellow}) {reset}")
                    else:
                        # normalize to "k"
                        print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x6}{bold}[E]{reset}{xlred} 🔥 Working{dotsdisplay} {xlyellow}({bold}+{format_number(round(gold/counts*(i+1)))}{reset}🪙{xlyellow}) {reset}")
                    progress = i / counts
                    pitch = 1 + (progress ** 1.5) * 1.5
                    delay = max(
                        0.012,
                        0.18 * (0.92 ** i)
                    )
                    # must make sure delay is not small...
                    # and that pitch is not excessively high
                    if pitch > 2.5:
                        pitch = 2.5
                    if delay < 0.001:
                        delay = 0.001
                    animation_sleep(delay)
                
                sound("map_right")
            
                sound(reward_sound)
                animation_sleep(0.1)
                if gold < 100000:
                    print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} \033[97G│{x8}   ╰─ {x3}{bold}[E]{reset}{xb} 💎 Converted! {xlyellow}({bold}+{format_number(round(gold))}{reset}🪙{xlyellow})   {reset}")
                else:
                    # normalize to k
                    print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} \033[97G│{x8}   ╰─ {x3}{bold}[E]{reset}{xb} 💎 Converted! {xlyellow}({bold}+{format_number(round(gold))}{reset}🪙{xlyellow})  {reset}")
                
        # this is the pitch testing code!
        if setting.debug_shortcuts and k.lower() == "o":
            draw_box_border(32,20,34,60,text="Enter an int 1 to 50:",bold=True,text_color=xlyellow)
            a = getx(33,22,prompt="› ",expect="int",max_len=25,min_val=1,max_val=50,highlight_prefix=f"{xlorange}{bold}",highlight_suffix=reset)
            blank(32,20,34,60)
            pitch = 1
            for i in range(a):
                sound(f"exp {pitch}")
                # write out i at [1;1]
                pitch = 1 + 0.005 * i ** 1.1
                delay = 0.3-(i**2*0.00035)
                # must make sure delay is not small
                if delay < 0.025:
                    delay = 0.025
                # and that pitch is not excessively high
                if pitch > 2.2:
                    pitch = 2.2
                time.sleep(delay)
                print(f"[1;1HPlaying sound {i+1:3}/{a:3} ({pitch:.3f}x; {delay:.3f}s)   ", end="", flush=True)
            # clear sound command queue (set file contents to empty)
            # file: General / Temp / sound_cmd_queue.txt
            sound(f"big_level {pitch}")


def effective_def(totaldef):
    if totaldef <= 40:
        return totaldef

    totaldef -= 40
    eff = 40

    # 41-50% (2 DEF each)
    gain = min(totaldef, 20)
    eff += gain // 2
    totaldef -= gain

    # 51-60% (4 DEF each)
    gain = min(totaldef, 40)
    eff += gain // 4
    totaldef -= gain

    # 61-65% (6 DEF each)
    gain = min(totaldef, 30)
    eff += gain // 6
    totaldef -= gain

    # 66-70% (10 DEF each)
    gain = min(totaldef, 50)
    eff += gain // 10
    totaldef -= gain

    # 71-75% (15 DEF each)
    gain = min(totaldef, 75)
    eff += gain // 15

    return min(eff, 75)


def refresh_player_core_stats(reload_equipment=True):
    if reload_equipment:
        load_item(0)

    level = int(player.level)
    base_hp = round(50 + (level - 1) * 20 + ((level - 1) * (level + 2)) / 4)
    base_atk = level * 10
    base_def = round(level * 0.3, 1)

    item.actual_atk = get_actual_atk()
    fragment_bonuses = get_fragment_bonuses()
    player.fragment_bonuses = fragment_bonuses

    damage_before_weapon = round(
        (base_atk + fragment_bonuses["atk_flat"])
        * (1 + fragment_bonuses["atk_percent"] / 100)
    )
    total_dmg = damage_before_weapon + item.actual_atk
    damage_without_fragments = base_atk + item.actual_atk

    raw_def = base_def
    if getattr(item, "substat", None) == "Defence":
        raw_def += item.substat_value
    if getattr(armor, "name", None):
        armor.actual_defense = get_actual_defense(armor)
        raw_def += armor.actual_defense
    if getattr(head, "name", None):
        head.actual_defense = get_actual_defense(head)
        raw_def += head.actual_defense

    defense_without_fragments = effective_def(raw_def)
    raw_def = (
        raw_def + fragment_bonuses["def_flat"]
    ) * (1 + fragment_bonuses["def_percent"] / 100)

    hp_without_fragments = base_hp
    if getattr(item, "substat", None) == "Health":
        hp_without_fragments += item.substat_value
    total_hp = round(
        (hp_without_fragments + fragment_bonuses["hp_flat"])
        * (1 + fragment_bonuses["hp_percent"] / 100)
    )

    player.total_dmg = total_dmg
    player.total_def = effective_def(raw_def)
    player.total_hp = total_hp
    player.bonus_atk = player.total_dmg - base_atk - item.actual_atk
    player.bonus_def = round(
        player.total_def - effective_def(base_def),
        1,
    )
    player.bonus_hp = player.total_hp - base_hp
    player.fragment_atk_bonus = player.total_dmg - damage_without_fragments
    player.fragment_def_bonus = round(
        player.total_def - defense_without_fragments,
        1,
    )
    player.fragment_hp_bonus = player.total_hp - hp_without_fragments
    player.damage_taken_multiplier = max(
        0,
        1 + fragment_bonuses["damage_taken_percent"] / 100,
    )
    player.healing_received_multiplier = max(
        0,
        1 + fragment_bonuses["healing_received_percent"] / 100,
    )
    player.crit_damage = (
        float(getattr(item, "atkcrit", 0))
        + fragment_bonuses["crit_damage"]
    )
    refresh_player_secondary_stats()
    return {
        "base_hp": base_hp,
        "base_atk": base_atk,
        "base_def": base_def,
        "total_dmg": player.total_dmg,
        "total_def": player.total_def,
        "total_hp": player.total_hp,
        "fragment_bonuses": fragment_bonuses,
    }


def refresh_player_secondary_stats():
    bonuses = getattr(player, "fragment_bonuses", None)
    if bonuses is None:
        bonuses = get_fragment_bonuses()

    weapon_crit_rate = (
        getattr(item, "substat_value", 0)
        if getattr(item, "substat", None) == "Crit Rate"
        else 0
    )
    crit_without_fragments = (
        15 + weapon_crit_rate + (int(player.level) // 10)
    )
    player.fragment_crit_rate_bonus = bonuses["crit_rate"]
    player.crit_rate = crit_without_fragments + bonuses["crit_rate"]

    weapon_speed = (
        getattr(item, "substat_value", 0)
        if getattr(item, "substat", None) == "Speed"
        else 0
    )
    level_speed = (int(player.level) // 10) * 5
    level_speed += sum(
        int(player.level) >= breakpoint
        for breakpoint in (20, 40, 60, 80, 100)
    )
    player.fragment_speed_bonus = bonuses["speed"]
    player.speed = 100 + weapon_speed + level_speed + bonuses["speed"]
    player.fragment_crit_damage_bonus = bonuses["crit_damage"]


def character_exp_progress(level, xp, xp_needed, bar_length=30):
    # no xp bar after reaching max level
    if int(level) >= CHARACTER_MAX_LEVEL:
        return None
    if xp_needed <= 0:
        return 0, 0
    percent = min(100, max(0, round((xp / xp_needed) * 100)))
    filled = min(bar_length, max(0, (xp * bar_length) // xp_needed))
    return percent, filled


# (i'm sorry)
def character():
    player.load()
    load_binds()
    load_item(0)
    cls()
    thresholds = [
        (0, x8), (5, x7), (10, xf),(15, x3),(20, x9),(25, xb),(30, x2),(35, xa),(40, xlorange),(45, xlyellow),(50, xe),(55, x5),(60, xd),(65, xlred),(70, xc),(75, x4),(80, rgb(184, 172, 246)),(85, rgb(254, 163, 98)),(90, rgb(186, 243, 219)),(95, rgb(255, 131, 101)),(100, rgb(227, 62, 57)),
    ]
    player.color = None
    for req_level, color in thresholds:
        if player.level >= req_level:
            player.color = color
    
    # get skill levels
    lvl_main = player.skill_main
    lvl_skill = player.skill_skill
    lvl_ult = player.skill_ult
    player.playerclass = "warrior" # for now, only one, hardcode but hope it works
    
    if player.playerclass == "warrior":
        from Scripts.Classes import warrior as playerclass
        d.classicon = f"{xlyellow}🪖{reset}"
        player.main_dmg = playerclass.main_damage[lvl_main - 1]
        player.skill_dmg = playerclass.skill_damage[lvl_skill - 1]
        player.ult_dmg = playerclass.ult_damage[lvl_ult - 1]
        
        player.main_name = playerclass.main_name
        player.skill_name = playerclass.skill_name
        player.ult_name = playerclass.ult_name

        player.main_cost = playerclass.main_cost[lvl_main - 1]
        player.skill_cost = playerclass.skill_cost[lvl_skill - 1]
        player.ult_cost = playerclass.ult_cost[lvl_ult - 1]

        player.double_tap = playerclass.double_tap[lvl_main - 1]
        player.stronger_skill = playerclass.stronger_skill[lvl_skill - 1]
        player.stronger_ult = playerclass.stronger_ult[lvl_ult - 1]

        player.double_tap_cost = playerclass.double_tap_cost[lvl_main - 1]
        player.mastery = max(1, (lvl_main + lvl_skill + lvl_ult) // 3) # average of all skill levels, rounded down

        player.double_tap_crit = playerclass.double_tap_crit[player.mastery - 1]
        player.skill_atk_decrease = playerclass.skill_atk_decrease[player.mastery - 1]
        player.ult_crit_percent = playerclass.ult_crit_percent[player.mastery - 1]

    boxwidth = 25
    playername=read("General/playername")
    playernamd = f"{playername} › Attributes"
    length = visible_len(playernamd)
    pad = (boxwidth - length) // 2 + 1
    spaces = " " * max(pad, 0)
    centered = spaces + playernamd
    core_stats = refresh_player_core_stats(reload_equipment=False)
    basehp = core_stats["base_hp"]
    baseatk = core_stats["base_atk"]
    basedef = core_stats["base_def"]

    atksymbol1=f"    {x6}██████{xlyellow}"
    atksymbol2=f"  {x6}██{xlyellow}██{xe}██{xlyellow}██{x6}██{xlyellow}"
    atksymbol3=f"{x6}██{xlyellow}██████{xe}██{xlyellow}██{x6}██{xlyellow}"
    atksymbol4=f"{x6}██{xlyellow}{xe}██████████{xlyellow}{x6}██{xlyellow}"
    atksymbol5=f"{x6}██{xlyellow}██████{xe}██{xlyellow}██{x6}██{xlyellow}"
    atksymbol6=f"  {x6}██{xlyellow}██{xe}██{xlyellow}██{x6}██{xlyellow}"
    atksymbol7=f"    {x6}██████{xlyellow}"

    defsymbol1=f"{x3}██████████████        "
    defsymbol2=f"{x3}██{xb}██████████{x3}██"
    defsymbol3=f"{x3}██{xb}██████████{x3}██"
    defsymbol4=f"{x3} ██{xb}████████{x3}██ "
    defsymbol5=f" {x3} ██{xb}██████{x3}██  "
    defsymbol6=f"   {x3} ██{xb}██{x3}██    "
    defsymbol7=f"      {x3}██              "


    hpsymbol1=f"  {x4}██{x4}██  {x4}██{x4}██"
    hpsymbol2=f"{x4}██{xc}██{xc}██{x4}██{xc}██{xc}██{x4}██"
    hpsymbol3=f"{x4}██{xc}████{xc}██{xc}██{xc}██{x4}██"
    hpsymbol4=f"{x4}██{xc}██████████{x4}██  "
    hpsymbol5=f"  {x4}██{xc}██████{x4}██    "
    hpsymbol6=f"   {x4} ██{xc}██{x4}██      "
    hpsymbol7=f"      {x4}██  "

    lvsymbol1=f"{RGB}195;255;253m  {RGB}192;253;248m  {RGB}190;251;242m  {RGB}189;249;237m  {RGB}187;247;231m  {RGB}186;245;225m  {RGB}186;243;219m██"
    lvsymbol2=f"{RGB}195;255;253m  {RGB}192;253;248m  {RGB}190;251;242m  {RGB}189;249;237m  {RGB}187;247;231m  {RGB}186;245;225m██{RGB}186;243;219m██"
    lvsymbol3=f"{RGB}195;255;253m  {RGB}192;253;248m  {RGB}190;251;242m  {RGB}189;249;237m  {RGB}187;247;231m██{RGB}186;245;225m██{RGB}186;243;219m██"
    lvsymbol4=f"{RGB}195;255;253m  {RGB}192;253;248m  {RGB}190;251;242m  {RGB}189;249;237m██{RGB}187;247;231m██{RGB}186;245;225m██{RGB}186;243;219m██"
    lvsymbol5=f"{RGB}195;255;253m  {RGB}192;253;248m  {RGB}190;251;242m██{RGB}189;249;237m██{RGB}187;247;231m██{RGB}186;245;225m██{RGB}186;243;219m██"
    lvsymbol6=f"{RGB}195;255;253m  {RGB}192;253;248m██{RGB}190;251;242m██{RGB}189;249;237m██{RGB}187;247;231m██{RGB}186;245;225m██{RGB}186;243;219m██"
    lvsymbol7=f"{RGB}195;255;253m██{RGB}192;253;248m██{RGB}190;251;242m██{RGB}189;249;237m██{RGB}187;247;231m██{RGB}186;245;225m██{RGB}186;243;219m██"
    abilityatk=0
    abilitydef=0
    abilityhp=0
    totaldmg = core_stats["total_dmg"]
    totalcritdmg=round(totaldmg*(1+player.crit_damage/100))
    critrate = round(player.crit_rate)
    expected = round(totaldmg * (1 + (critrate / 100) * (player.crit_damage / 100)))
    number = 1
    totaldef = core_stats["total_def"]
    totalhp = core_stats["total_hp"]
    # ===== INPUTS =====
    EXP = player.xp
    EXP_NEEDED = player.xpneeded

    # ===== CONFIG =====
    BAR_LENGTH = 30
    FILLED_SEG = f"{xba} "
    EMPTY_SEG = f"{xb0} "

    # ===== CALCULATE FILLED SEGMENTS =====
    if EXP_NEEDED > 0:
        FILLED = (EXP * BAR_LENGTH) // EXP_NEEDED
    else:
        FILLED = 0

    if FILLED > BAR_LENGTH:
        FILLED = BAR_LENGTH
    if FILLED < 0:
        FILLED = 0

    # ===== BUILD BAR =====
    EXP_BAR = ""

    for i in range(1, BAR_LENGTH + 1):
        if i <= FILLED:
            EXP_BAR += FILLED_SEG
        else:
            EXP_BAR += EMPTY_SEG

    # make dodge, effect res, life steal and regen work normally
    
    # dodge rate = base dodge + (dodge from item) - (enemy accuracy debuff)
    # base dodge rate is 2% and 0.1% per player level
    base_dodge = 2 + (player.level * 0.1)
    # for every 10 levels in armor, +0.3% dodge rate
    armor_dodge = (getattr(armor, "level", 0) // 10) * 0.3
    # weapon if substat if dodge, add the same
    weapon_dodge = 0
    if getattr(item, "substat", None) == "Dodge":
        weapon_dodge = item.substat_value
    # headwear dodge functions exactly like armor
    head_dodge = (getattr(head, "level", 0) // 10) * 0.3
    player.dodge = base_dodge + armor_dodge + weapon_dodge + head_dodge
    player.dodge = round(player.dodge, 1)
    del base_dodge, armor_dodge, weapon_dodge, head_dodge
    
    # now, let's do effect res
    # effect res has a x% chance to negate enemy debuffs (if negation FAILS, its POTENCY is reduced by x% instead)
    # for every 1 player level => 0.2% effect res
    base_effect_res = player.level * 0.2
    # armor gives 1% effect res per 20 levels
    armor_effect_res = (getattr(armor, "level", 0) // 20) * 1
    # headwear gives 1% effect res per 20 levels
    head_effect_res = (getattr(head, "level", 0) // 20) * 1
    # bonus effect res, random stuff
    bonus_effect_res = 0
    # so finally,
    player.effect_res = base_effect_res + armor_effect_res + head_effect_res + bonus_effect_res
    del base_effect_res, armor_effect_res, head_effect_res, bonus_effect_res
    
    # now, life steal
    # base life steal is 0
    base_life_steal = 0
    # for every 10 levels in weapon, +0.05% life steal
    weapon_life_steal = (getattr(item, "level", 0) // 10) * 0.05
    # weapon life steal multiplier based on rarity of weapon
    rarity_multiplier = {
        "08": 1.0, # common
        "02": 1.5, # uncommon
        "03": 2.0, # rare
        "0d": 2.5, # epic
        "0e": 3.0, # legendary
    }
    weapon_life_steal *= rarity_multiplier.get(getattr(item, "rarity", "08"), 1.0)
    # round it to at most one decimal place
    weapon_life_steal = round(weapon_life_steal, 1)
    # if weapon substat, add the same
    if getattr(item, "substat", None) == "Life Steal":
        weapon_life_steal += item.substat_value    
    # if any bonuses:
    bonus_life_steal = 0
    player.life_steal = base_life_steal + weapon_life_steal + bonus_life_steal
    
    # regeneration is the percentage of your max HP you heal back after each battle round 
    # base is 0.2% max HP regen after each battle round
    base_regen = 0.2
    # if weapon substat is regen, add the same
    weapon_regen = 0
    if getattr(item, "substat", None) == "Regeneration":
        weapon_regen = item.substat_value
    # any bonuses:
    bonus_regen = 0
    player.regen = base_regen + weapon_regen + bonus_regen
    del base_regen, weapon_regen, bonus_regen
    
    # now, make total ATK, DEF and Hp actually global
    player.total_dmg = totaldmg
    player.total_def = totaldef
    player.total_hp = totalhp
    
    # if "from battle" is defined, jump straight to battle (easier loading; no need to write a separate battle loading function)
    if d.frombattle == True:
        game.goto = battle_preparation
        return
    
    # now comes the insane part: page switching!
    if d.character_view == 1:
        pass # attributes
    elif d.character_view == 2:
        game.goto = character2
        return # equipment
    elif d.character_view == 3:
        game.goto = character3
        return # skills & classes
    
    print(background_blocks(f"""
[1;{number}H{reset}
[2;17H#3{x7}╭───────────────────────────╮
[3;17H#4{x7}╭───────────────────────────╮
[4;17H#3{x7}│ {xf}{bold}{centered}       {reset}
[5;17H#4{x7}│ {xf}{bold}{centered}       {reset}
[6;17H#3{x7}╰───────────────────────────╯
[7;17H#4{x7}╰───────────────────────────╯
[4;45H#3{x7}│ {reset}{x7}{bold}{reset}
[5;45H#4{x7}│ {reset}{x7}{bold}{reset}
[08;3H{xf}{bold}╭────────────────────────────────────╮{reset}
[09;3H{xf}{bold}│                                    │{reset}
[10;3H{xf}{bold}│ {player.color}   ██████                        {xf}  │{reset}
[11;3H{xf}{bold}│ {player.color} ██      ██                      {xf}  │{reset}
[12;3H{xf}{bold}│ {player.color} ██ •  • ██                      {xf}  │{reset}
[13;3H{xf}{bold}│ {player.color} ██      ██                      {xf}  │{reset}
[14;3H{xf}{bold}│ {player.color}   ██████                        {xf}  │{reset}
[15;3H{xf}{bold}│ {player.color}     ██                          {xf}  │{reset}
[16;3H{xf}{bold}│ {player.color}     ██    ██                    {xf}  │{reset}
[17;3H{xf}{bold}│ {player.color}     ██  ██                      {xf}  │{reset}
[18;3H{xf}{bold}│ {player.color}  ███████                        {xf}  │{reset}
[19;3H{xf}{bold}│ {player.color}██   ██                          {xf}  │{reset}
[20;3H{xf}{bold}│ {player.color}     ██                          {xf}  │{reset}
[21;3H{xf}{bold}│ {player.color}     ██                          {xf}  │{reset}
[22;3H{xf}{bold}│ {player.color}   ██  ██                        {xf}  │{reset}
[23;3H{xf}{bold}│ {player.color} ██      ██                      {xf}  │{reset}
[24;3H{xf}{bold}│                                    │{reset}
[25;3H{xf}{bold}╰────────────────────────────────────╯{reset}
[26;3H{x7}{bold}╭────────────────────────────────────╮
[27;3H{x7}{bold}│ {reset}{xf}✅ {rgb(197, 229, 200)}{bold}[1] {reset}{xf}-{xa} Attributes               {xf}{x7}{bold} │
[28;3H{x7}{bold}│                                    │
[29;3H{x7}{bold}│ {reset}{xf}{item.type} {xlyellow}{bold}[2]{reset}{xe} {xf}-{xe} Equipment & fragments     {x7}{bold}│
[30;3H{x7}{bold}│                                    │{reset}
[31;3H{x7}{bold}│ {reset}{xf}{d.classicon} {xlyellow}{bold}[3]{reset}{xe} {xf}-{xe} Classes & skill tree      {x7}{bold}│
[32;3H{x7}{bold}│                                    │
[33;3H{x7}{bold}│ {reset}{xf}🎨 {xlyellow}{bold}[4]{reset}{xe} {xf}-{xe} Character personalization {x7}{bold}│
[34;3H{x7}{bold}│                                    │
[35;3H{x7}{bold}│ {reset}{xf}🔢 {xlyellow}{bold}[5] {reset}{xe}{xf}-{xe} Lifetime stats{reset}{x7}{bold}            │
[15;20H{item.type} {xlyellow}Attack{reset}{x8}.....{bold}{xe}{char_round(round(totaldmg))}{reset}
[16;20H🛡️ {x3}Defence{reset}{x8}....{bold}{xb}{char_round(round(totaldef,1))}%{reset}
[17;20H❤️ {xc}Health{reset}{x8}.....{bold}{xlred}{char_round(round(totalhp))}{reset}
[08;42H{xf}{bold}{RGB}255;219;187m╭───────────────────────────────────────╮ {RGB}186;243;219m╭─────────────────────────────────────────╮
[09;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[10;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[11;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[12;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[13;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[14;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[15;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[16;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[17;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[18;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[19;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[20;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[21;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[22;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[23;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[24;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[25;42H{xf}{bold}{RGB}255;219;187m╰───────────────────────────────────────╯ {RGB}186;243;219m╰─────────────────────────────────────────╯
[08;43H{RGB}255;219;187m{bold}┤ Attack ├
[08;85H{RGB}186;243;219m{bold}┤ Levelling ├
[26;42H{RGB}173;216;225m╭───────────────────────────────────────╮ {RGB}255;203;204m╭─────────────────────────────────────────╮
[27;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[28;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[29;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[30;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[31;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[32;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[33;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[34;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[35;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[26;43H{RGB}173;216;225m{bold}┤ Defence ├
[26;85H{RGB}255;203;204m{bold}┤ Health ├
[28;45H{defsymbol1}
[29;45H{defsymbol2}
[30;45H{defsymbol3}
[31;45H{defsymbol4}
[32;45H{defsymbol5}
[33;45H{defsymbol6}
[34;45H{defsymbol7}
[28;86H{hpsymbol1}
[29;86H{hpsymbol2}
[30;86H{hpsymbol3}
[31;86H{hpsymbol4}
[32;86H{hpsymbol5}
[33;86H{hpsymbol6}
[34;86H{hpsymbol7}
[10;45H{atksymbol1}
[11;45H{atksymbol2}
[12;45H{atksymbol3}
[13;45H{atksymbol4}
[14;45H{atksymbol5}
[15;45H{atksymbol6}
[16;45H{atksymbol7}
[10;86H{lvsymbol1}
[11;86H{lvsymbol2}
[12;86H{lvsymbol3}
[13;86H{lvsymbol4}
[14;86H{lvsymbol5}
[15;86H{lvsymbol6}
[16;86H{lvsymbol7}
[11;60H{reset}☺ 
[11;62H{RGB}255;219;187mBase ATK{x8}------{xlyellow}{bold}{char_round(baseatk)}{reset}
[12;60H{reset}† 
[12;62H{RGB}255;219;187mWeapon{x8}--------{xlyellow}{bold}{char_round(item.actual_atk)}{reset}
[13;60H{reset}✸ 
[13;62H{RGB}255;219;187mCrit Rate{x8}-----{xlyellow}{bold}{char_round(player.crit_rate)}%{reset}
[14;60H{reset}※ 
[14;62H{RGB}255;219;187mCrit DMG{x8}------{xlyellow}{bold}{char_round(player.crit_damage)}%{reset}
[15;60H{reset}⟐ 
[15;62H{RGB}255;219;187mSpeed{x8}---------{xlyellow}{bold}{char_round(player.speed)}{reset}
[16;60H{reset}+
[16;62H{RGB}255;219;187mBonus ATK{x8}-----{xlyellow}{bold}{char_round(player.bonus_atk + abilityatk)}{reset}
[18;44H{reset}{RGB}255;219;187m⇝{xf} 
[13;101H{reset}⌬ 
[13;103H{RGB}186;243;219mSkill Lv.{x8}-----{xa}{bold}soon!{reset}{RGB}186;243;219m/15{reset}
[14;101H{reset}⇋ 
[14;103H{RGB}186;243;219mWeapon Lv.{x8}----{xa}{bold}{item_level_display(item, "Weapons")}{reset}{RGB}186;243;219m{reset}
[21;86H{reset}{RGB}186;243;219m⇝{xf} 
[21;88HHigher levels provide upgrades to {reset}
[22;86H{reset}{RGB}255;219;187m {xf} 
[22;88Hhealth, defence and power. Moreover{reset}
[23;86H{reset}{RGB}255;219;187m {xf} 
[23;88Hthey also unlock skill tree items.{reset}
[21;44H{reset}{RGB}255;219;187m•{xf} 
[21;46HDamage every normal hit: {RGB}255;219;187m{bold}{char_round(totaldmg)}{reset}

[29;60H{reset}◇ 
[29;62H{RGB}173;216;225mBase DEF{x8}------{xb}{bold}{char_round(basedef)}%{reset}
[30;60H{reset}∆ 
[30;62H{RGB}173;216;225mArmour DEF{x8}----{xb}{bold}{char_round(getattr(armor, "actual_defense", 0))}%{reset}
[31;60H{reset}⦿ 
[31;62H{RGB}173;216;225mHelmet DEF{x8}----{xb}{bold}{char_round(getattr(head, "actual_defense", 0))}%{reset}
[32;60H{reset}★ 
[32;62H{RGB}173;216;225mBonus DEF{x8}-----{xb}{bold}{char_round(abilitydef + player.bonus_def)}{reset}
[33;60H{reset}⊗ 
[33;62H{RGB}173;216;225mDodge Rate{x8}----{xb}{bold}{char_round(player.dodge)}%{reset}
[29;101H{reset}♥ 
[29;103H{RGB}255;203;204mBase HP{x8}---------{xlred}{bold}{char_round(basehp)}{reset}
[30;101H{reset}♡ 
[30;103H{RGB}255;203;204mBonus HP{x8}--------{xlred}{bold}{char_round(abilityhp + player.bonus_hp)}{reset}
[31;101H{reset}⬣ 
[31;103H{RGB}255;203;204mEffect RES{x8}------{xlred}{bold}{char_round(round(player.effect_res))}%{reset}
[32;101H{reset}↺ 
[32;103H{RGB}255;203;204mRegeneration{x8}----{xlred}{bold}{char_round(round(player.regen,1))}%{reset}
[33;101H{reset}⸕ 
[33;103H{RGB}255;203;204mLife Steal{x8}------{xlred}{bold}{char_round(round(player.life_steal,1))}%{reset}
[36;42H{RGB}173;216;225m╰───────────────────────────────────────╯ {RGB}255;203;204m╰─────────────────────────────────────────╯
[36;3H{x7}╰────────────────────────────────────╯{reset}
""").strip().replace("\n", ""),end="",flush=True)
    if item.type_raw is not None: print(f"""
[18;46HYour {item.type_raw} {bold}crits {RGB}255;219;187m{char_round(player.crit_rate)}%{reset} of the time,{reset}
[19;46H{reset}in which case you deal {RGB}255;219;187m{bold}+{char_round(player.crit_damage)}%{reset} DMG:
[22;44H{reset}{RGB}255;219;187m•{xf} 
[22;46HDamage every critical hit: {RGB}255;219;187m{bold}{char_round(totalcritdmg)}{reset}
[23;44H{reset}{RGB}255;219;187m•{xf} 
[23;46HExpected average damage: {RGB}255;219;187m{bold}{char_round(expected)}{reset}
""".strip().replace("\n",""),end="",flush=True)  # noqa: E701
    if item.type_raw is None or item.type_raw == "None": print(f"""
[18;46HYour fists are {xlred}too weak{reset} to crit,{reset}
[19;46H{reset}so all your hits perform the same:
""".strip().replace("\n",""),end="",flush=True)  # noqa: E701
        # ===== RESULT =====
    print(f"[12;101H{reset}✧ [12;103H{RGB}186;243;219mLevel{x8}---------{xa}{bold}{player.level}{reset}{RGB}186;243;219m/100{reset}")
    EXP = player.xp
    EXP_NEEDED = player.xpneeded

    BAR_LENGTH = 30
    FILLED_SEG = f"{xba} "
    EMPTY_SEG = f"{xb0} "

    exp_progress = character_exp_progress(
        player.level,
        EXP,
        EXP_NEEDED,
        BAR_LENGTH,
    )
    if exp_progress is None:
        print(f"\033[18;86H{reset}{rgb(186,243,219)}✦ \033[18;88H{bold}MAX LEVEL{reset}")
        print(f"\033[19;88H{reset}{x7}Level cap reached.{reset}")
    else:
        percent, FILLED = exp_progress
        EXP_BAR = (FILLED_SEG * FILLED) + (EMPTY_SEG * (BAR_LENGTH - FILLED))
        print(f"\033[18;86H{reset}{rgb(255,219,187)}{rgb(186,243,219)}✚{xf}\033[18;88H{bold}EXP: {EXP_BAR}{reset} ", end="")
        if percent < 10:
            print(f"{xf}{bold}{rgback(0,0,1)}\033[18;94H{percent}%")
        else:
            print(f"{xba}{xf}{bold}\033[18;94H{percent}%")
        print(f"\033[19;93H{reset}{x7}{rgb(186,243,219)}↑ {bold}{format_number(EXP)}/{format_number(EXP_NEEDED)} {reset}XP to get level {player.level+1}{reset} ")
    print(f"""
[15;20H{item.type} {xlyellow}Attack{reset}{x8}.....{bold}{xe}{char_round(round(totaldmg))}{reset}
[16;20H🛡️ {x3}Defence{reset}{x8}....{bold}{xb}{char_round(round(totaldef,1))}%{reset}
[17;20H❤️ {xc}Health{reset}{x8}.....{bold}{xlred}{char_round(round(totalhp))}{reset}
""".strip().replace("\n",""),end="",flush=True)
    del hpsymbol1,hpsymbol2,hpsymbol3,hpsymbol4,hpsymbol5,hpsymbol6,hpsymbol7, atksymbol1,atksymbol2,atksymbol3,atksymbol4,atksymbol5,atksymbol6,atksymbol7,defsymbol1,defsymbol2,defsymbol3,defsymbol4,defsymbol5,defsymbol6,defsymbol7,lvsymbol1,lvsymbol2,lvsymbol3,lvsymbol4,lvsymbol5,lvsymbol6,lvsymbol7
    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            game.goto = house
            return
        if k.lower() == bind.back or k.lower() == "2":
            d.character_view = 2
            sound("map_switch2")
            game.goto = character
            return
        if k.lower() == bind.back or k.lower() == "3":
            d.character_view = 3
            sound("map_switch2")
            game.goto = character
            return
        
        
        
        
        
        
        
        
        
def settings():
    d.settings_difficulty_value = setting.battle_difficulty
    d.settings_extreme_started = None
    d.settings_value_texts = {}
    d.settings_value_changes = {}
    d.settings_audio_test_until = 0
    d.settings_unavailable_until = 0
    d.settings_selection = "category"
    d.settings_cursor = 1
    d.settings_category = 1
    d.settings_category_scroll = 0
    d.settings_category_manual_scroll = False
    d.settings_category_scrollbar_dragging = False
    d.settings_edit_flash = False
    d.settings_slider_dragging = False
    d.settings_scrollbar_dragging = False
    d.settings_click_sound = False
    d.settings_hover_attr = None
    d.settings_scroll = 0
    settings_editor.clear()
    cls()
    move(1,1)
    print(f"""
#3{x1}                  ╭────────────────────────╮
#4{x1}                  ╭────────────────────────╮
#3{x1}                  │   {reset}{xb}⚙ {bold} Options & info {reset}{x1}   │
#4{x1}                  │   {reset}{xb}⚙ {bold} Options & info {reset}{x1}   │
#3{x1}                  ╰────────────────────────╯
#4{x1}                  ╰────────────────────────╯{x7}
╭───────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   │                                                                                                        │
│                   ├──────────────────────────────────────────────────────────────────────────┬─────────────────────────────┤
{xlred}│                   {x7}│                                                                          │                             │
{xlred}│  {xc}{bold} Back to house  {unbold} {xlred}{x7}│{x7}                                                                          │                             │
{xlred}│  {xc}[press {bold}{setting.back.upper()}{unbold} | {bold}ESC{unbold}]  {xlred}{x7}│{x7}                                                                          │                             │
{xlred}│                   {x7}│{x7}                                                                          │                             │
{xlred}╰───────────────────{x7}┴{x7}──────────────────────────────────────────────────────────────────────────┴─────────────────────────────╯
""".strip(),end="",flush=True)
    
    game.goto = settings2
    return

def run_settings_action(item):
    settings_editor.clear()
    blank(32, 23, 35, 94)
    if item["attr"] == "reset_settings":
        draw_box_text(f"{xf}Reset all settings and keybinds? Type YES to confirm.{reset}", 32, 23, 33, 94)
        answer = getx(34, 23, prompt="Confirm: ", max_len=3, allow_none=True)
        if (answer or "").strip().lower() != "yes":
            settings_editor.message = "Reset cancelled."
            return
        setting.reset()
        setting.inventory_last_selections = {}
        d.settings_value_texts = {}
        d.settings_value_changes = {}
        settings_editor.message = "All settings reset to defaults."
        sound("REFRESH_AUDIO")
        sound("map_switch3")
    elif item["attr"] == "manual_backup":
        draw_box_text(f"{xf}Name this backup, or leave it empty. Manual backups are always kept.{reset}", 32, 23, 33, 94)
        name = getx(34, 23, prompt="Name: ", max_len=55, allow_none=True)
        try:
            create_backup(PROJECT_ROOT, name=name or "", manual=True)
        except OSError as error:
            settings_editor.message = f"Backup failed: {error}"
            sound("error2")
            return
        settings_editor.message = "Backup saved!"
        sound("map_switch2")


def open_settings_search():
    if settings_editor.active:
        settings_editor.commit()
    settings_editor.clear()
    if d.settings_selection == "setting":
        d.settings_search_return = (d.settings_category, d.settings_cursor, d.settings_scroll, "setting")
    else:
        d.settings_search_return = getattr(d, "settings_last_visited", (d.settings_category, d.settings_cursor, d.settings_scroll, "setting"))
    d.settings_slider_dragging = False
    d.settings_scrollbar_dragging = False
    d.settings_category_scrollbar_dragging = False
    if not hasattr(d, "settings_search_query"):
        d.settings_search_query = ""
        d.settings_search_caret = 0
        d.settings_search_focus = 0
        d.settings_search_scroll = 0

    # fade the tabs, leave the sidebar where it was
    first = getattr(d, "settings_category_scroll", 0)
    steps = 5 if animations_enabled() else 1
    for step in range(steps):
        # finish at x7, keep the same gray as the other tabs
        shade = round(186 + (148 - 186) * (step + 1) / steps)
        color = x7 if step == steps - 1 else rgb(shade, shade, shade)
        for index in range(6):
            category = first + index
            if category >= len(CATEGORY_NAMES):
                break
            label = CATEGORY_ICONS[category] + " " + CATEGORY_NAMES[category]
            row = 8 + index * 4
            for offset, text in ((0, " " * 19), (1, f"{label:^19}"), (2, " " * 19)):
                move(row + offset, 1)
                print(f"{reset}{unbold}{color}│{text}│{reset}", end="")
            # same divider as normal settings; the footer shares this frame
            move(row + 3, 1)
            ending = "┼" if index == 5 else "┤"
            print(f"{x7}├{'─' * 19}{ending}{reset}", end="")
        sys.stdout.flush()
        if steps > 1:
            animation_sleep(0.025)
    game.goto = settings_search


def settings_search_visit(category, index):
    # open the tab, highlight the result without toggling it
    cursor(False)
    settings_editor.clear()
    d.settings_hover_attr = None
    d.settings_category = category + 1
    d.settings_category_manual_scroll = False
    d.settings_selection = "setting"
    d.settings_cursor = index + 1
    d.settings_scroll = max(0, index - 3)
    sound("map_right")
    game.goto = settings2


def settings_search():
    col = 23
    width = 100
    result_count = 6
    input_col = col + 10
    input_width = width - 12
    query = d.settings_search_query
    caret = min(len(query), d.settings_search_caret)
    focus = d.settings_search_focus
    scroll = d.settings_search_scroll

    try:
        while True:
            results = find_settings(query)
            focus = max(0, min(focus, len(results)))
            max_scroll = max(0, len(results) - result_count)
            scroll = max(0, min(scroll, max_scroll))
            if focus > 0:
                if focus - 1 < scroll:
                    scroll = focus - 1
                elif focus - 1 >= scroll + result_count:
                    scroll = focus - result_count
            visible = results[scroll:scroll + result_count]

            # keep this window for the next Ctrl/Cmd+F
            d.settings_search_query = query
            d.settings_search_caret = caret
            d.settings_search_focus = focus
            d.settings_search_scroll = scroll
            cursor(False)
            # stop before the outer border, draw it back if search cleared it
            blank(8, col, 30, col + width + 2)
            for row in range(8, 31):
                move(row, col + width + 3)
                print(f"{x7}│{reset}", end="")
            blank(32, col, 35, 94)
            move(33, 2)
            print(f"{xc}{bold}{'Back to settings':^19}{reset}", end="")
            move(34, 2)
            back_hint = "[click | Esc]" if setting.mouse_controls else "[Esc]"
            print(f"{xc}{back_hint:^19}{reset}", end="")

            # query field, same size as a setting
            color = xlyellow if focus == 0 else x7
            move(8, col)
            print(f"{color}╭{'─' * width}╮{reset}", end="")
            move(9, col)
            print(f"{color}│{reset} {xf}Search: {reset}", end="")
            # slide the text when the cursor reaches the edge
            text_start = max(0, caret - input_width + 1)
            text = query[text_start:text_start + input_width]
            move(9, input_col)
            print(f"{xf}{pad_visible(text, input_width)}{reset}", end="")
            move(9, col + width + 1)
            print(f"{color}│{reset}", end="")
            move(10, col)
            print(f"{color}╰{'─' * width}╯{reset}", end="")

            # top matches below, use gray boxes for all of them
            for index, result in enumerate(visible):
                score, category, setting_index, item = result
                selected = focus == scroll + index + 1
                row = 11 + index * 3
                move(row, col)
                print(f"{x7}╭{'─' * width}╮{reset}", end="")
                move(row + 1, col)
                print(f"{x7}│{reset}", end="")
                move(row + 1, col + 2)
                prefix = "→ " if selected else "  "
                name_color = xa if selected else xf
                print(f"{name_color}{bold if selected else unbold}{prefix}{item['name']}{reset}", end="")
                category_name = CATEGORY_ICONS[category] + " " + CATEGORY_NAMES[category]
                move(row + 1, col + width - len(category_name))
                print(f"{x7}{category_name}{reset}", end="")
                move(row + 1, col + width + 1)
                print(f"{x7}│{reset}", end="")
                move(row + 2, col)
                print(f"{x7}╰{'─' * width}╯{reset}", end="")

            if not results:
                message = "Nothing found yet — try a different word!" if query.strip() else "Looking for something? Try a name, an effect, or whatever you remember!"
                draw_box_text(f"{x7}{message}{reset}", 12, col + 2, 14, col + width - 2)
            if len(results) > result_count:
                move(30, col + 2)
                print(f"{x7}{scroll + 1}–{scroll + len(visible)} of {len(results)} results{reset}", end="")

            if focus > 0:
                item = results[focus - 1][3]
                title = item['name']
                description = setting_description(item)
            else:
                title = "What would you like to change?"
                description = "Type whatever comes to mind — it doesn't have to be the exact name! Use ↑/↓ to pick a result, then ⏎ or click to open it."
            move(32, col)
            print(f"{xlorange}{bold}{title}{reset}", end="")
            draw_box_text(f"{xf}{unbold}{description}{reset}", 33, col, 34, 94)
            hint = "Want to start over? Esc clears your search." if query else "All done? Esc takes you back to where you left off."
            draw_box_text(f"{x7}{hint}{reset}", 35, col, 35, 94)
            help_lines = [("←/→", "move text cursor"), ("↑/↓", "choose result"), ("⏎", "open result"), ("Esc", "clear / return")]
            for index, (control, action) in enumerate(help_lines):
                move(32 + index, 96)
                line = f"{xlyellow}{bold}{control}{unbold}{x7} - {xf}{action}"
                print(f"{reset}{x7}│ {reset}", end="")
                draw_box_text(line, 32 + index, 98, 32 + index, 124)
                move(32 + index, 125)
                print(f"{reset}{x7} │{reset}", end="")
            move(36, 1)
            print(f"{xlred}╰{'─' * 19}{x7}┴{reset}", end="")

            if focus == 0:
                move(9, input_col + caret - text_start)
                cursor(True)
            sys.stdout.flush()
            k = key(mouse=setting.mouse_controls, shortcuts=True)
            if isinstance(k, dict):
                if k.get("event") == "wheel" and results:
                    if k.get("delta", 0) > 0:
                        focus = max(0, focus - 1)
                    else:
                        focus = min(len(results), focus + 1)
                    continue
                if k.get("event") != "down" or k.get("button") != "left":
                    continue
                if back_button_contains(k["x"], k["y"]):
                    category, selected, position, selection = d.settings_search_return
                    d.settings_category = category
                    d.settings_cursor = selected
                    d.settings_scroll = position
                    d.settings_selection = selection
                    d.settings_category_manual_scroll = False
                    d.settings_hover_attr = None
                    game.goto = settings2
                    return
                if col - 1 <= k.get("x", -1) <= col + width and 7 <= k.get("y", -1) <= 9:
                    focus = 0
                    caret = max(0, min(len(query), text_start + k["x"] + 1 - input_col))
                    continue
                index = setting_index_at(k["x"], k["y"], len(visible), col, 11, width, 3)
                if index is not None:
                    focus = scroll + index + 1
                    d.settings_search_focus = focus
                    category = visible[index][1]
                    setting_index = visible[index][2]
                    settings_search_visit(category, setting_index)
                    return
                continue

            if k in ("ctrl/f", "cmd/f", "command/f", "super/f", "meta/f"):
                focus = 0
            elif k == "esc":
                if query:
                    query = ""
                    caret = 0
                    focus = 0
                    scroll = 0
                else:
                    category, selected, position, selection = d.settings_search_return
                    d.settings_category = category
                    d.settings_cursor = selected
                    d.settings_scroll = position
                    d.settings_selection = selection
                    d.settings_category_manual_scroll = False
                    d.settings_hover_attr = None
                    game.goto = settings2
                    return
            elif k == "down":
                focus = min(len(results), focus + 1)
            elif k == "up":
                focus = max(0, focus - 1)
            elif k == "enter":
                if focus > 0:
                    settings_search_visit(results[focus - 1][1], results[focus - 1][2])
                    return
            elif focus == 0:
                changed = False
                if k == "left":
                    caret = max(0, caret - 1)
                elif k == "right":
                    caret = min(len(query), caret + 1)
                elif k == "home":
                    caret = 0
                elif k == "end":
                    caret = len(query)
                elif k == "backspace" and caret > 0:
                    query = query[:caret - 1] + query[caret:]
                    caret -= 1
                    changed = True
                elif k == "delete" and caret < len(query):
                    query = query[:caret] + query[caret + 1:]
                    changed = True
                else:
                    text = " " if k == "space" else k
                    if len(text) == 1 and text.isprintable() and len(query) < 256:
                        query = query[:caret] + text + query[caret:]
                        caret += 1
                        changed = True
                if changed:
                    scroll = 0
    finally:
        cursor(False)


def settings2():

    category_height = 4
    category_view_size = 6
    category_track_height = category_view_size * category_height - 1
    category_scrollbar_col = 21
    category_max_scroll = max(0, len(CATEGORY_NAMES) - category_view_size)
    # prepare category names with their icons
    CATEGORY_LABELS = []
    for icon, name in zip(CATEGORY_ICONS, CATEGORY_NAMES):
        label = icon + " " + name
        CATEGORY_LABELS.append(f"{label:^19}")
    d.settings_category_scroll = max(0, min(getattr(d, "settings_category_scroll", 0), category_max_scroll))
    if not getattr(d, "settings_category_manual_scroll", False):
        focused_index = d.settings_category - 1
        if focused_index < d.settings_category_scroll:
            d.settings_category_scroll = focused_index
        elif focused_index >= d.settings_category_scroll + category_view_size:
            d.settings_category_scroll = focused_index - category_view_size + 1
    visible_categories = CATEGORY_LABELS[d.settings_category_scroll:d.settings_category_scroll + category_view_size]
    for local_index, label in enumerate(visible_categories):
        selected = d.settings_category == d.settings_category_scroll + local_index + 1
        if selected and d.settings_selection == "category":
            color = rgb(186, 243, 219)
        elif selected:
            color = x3
        else:
            color = x7
        style = bold if selected else unbold
        top = 8 + local_index * category_height
        for row, text in ((top, " " * 19), (top + 1, label), (top + 2, " " * 19)):
            move(row, 1)
            print(f"{reset}{color}{style}│{text}│{reset}", end="")
        move(top + 3, 1)
        print(f"{reset}{x7}├{'─' * 19}{'┼' if local_index == category_view_size - 1 else '┤'}{reset}", end="")
    category_thumb_height = max(2, round(category_track_height * category_view_size / len(CATEGORY_NAMES)))
    category_thumb_travel = category_track_height - category_thumb_height
    category_thumb_offset = round(category_thumb_travel * d.settings_category_scroll / max(1, category_max_scroll))
    for index in range(category_track_height):
        move(8 + index, category_scrollbar_col)
        thumb = category_thumb_offset <= index < category_thumb_offset + category_thumb_height
        print(f"{xlorange}{bold}┃{reset}" if thumb else f"{x8}{unbold}│{reset}", end="")

    page_list = SETTINGS_PAGES
    max_settings = [len(p) for p in page_list] # max settings per category
    max_settings[2] += 1  # Test audio is a button, but participates in navigation.

    

    page = page_list[d.settings_category - 1]

    SETTINGS_COL = 23
    SETTINGS_ROW = 8
    BOX_WIDTH = 100
    BOX_HEIGHT = 3
    SETTINGS_VIEW_SIZE = 7
    SETTINGS_SCROLLBAR_COL = SETTINGS_COL + BOX_WIDTH + 2
    SLIDER_DISPLAYS = (
        "volume",
        "animation_speed",
        "duration",
        "difficulty",
        "victory_celebration",
        "number",
    )
    CATEGORY_SELECTED_RGB = (186, 243, 219)
    scroll_item_count = len(page) + (1 if d.settings_category == 3 else 0)
    d.settings_cursor = max(1, min(d.settings_cursor, scroll_item_count))
    max_scroll = max(0, scroll_item_count - SETTINGS_VIEW_SIZE)
    d.settings_scroll = max(0, min(getattr(d, "settings_scroll", 0), max_scroll))
    if d.settings_selection == "setting":
        cursor_index = d.settings_cursor - 1
        if cursor_index < d.settings_scroll:
            d.settings_scroll = cursor_index
        elif cursor_index >= d.settings_scroll + SETTINGS_VIEW_SIZE:
            d.settings_scroll = cursor_index - SETTINGS_VIEW_SIZE + 1
    visible_page = page[
        d.settings_scroll:d.settings_scroll + SETTINGS_VIEW_SIZE
    ]
    test_audio_visible = (
        d.settings_category == 3
        and d.settings_scroll == max_scroll
        and len(visible_page) < SETTINGS_VIEW_SIZE
    )
    if d.settings_selection == "setting":
        d.settings_last_visited = (d.settings_category, d.settings_cursor, d.settings_scroll, "setting")
    test_audio_row = SETTINGS_ROW + len(visible_page) * BOX_HEIGHT
    category_focused = d.settings_selection == "category"
    visually_editing = (
        settings_editor.active
        and not getattr(d, "settings_slider_dragging", False)
    )

    slider_label_width = 3
    for slider_item in page:
        if slider_item["type"] != "slider":
            continue
        for index in range(slider_step_count(slider_item) + 1):
            possible = slider_item["min"] + index * slider_item.get("step", 1)
            if isinstance(possible, float):
                possible = round(possible, 6)
            slider_label_width = max(slider_label_width, len(format_setting_value(slider_item, possible)))

    def draw_description_line(row, text, color=xf, strong=False):
        text = str(text).replace("\n", " ")
        if len(text) > 72:
            text = text[:69].rstrip() + "..."
        move(row, 23)
        print(f"{reset}{color}{bold if strong else unbold}{text:<72}{reset}", end="")

    def inventory_sort_order_label(value):
        sorting = getattr(setting, "inventory_sorting", "Name")
        if not getattr(setting, "sort_items_automatically", True):
            return "Sorting off"
        labels = {
            "Level": {
                "Ascending": "Lowest first",
                "Descending": "Highest first",
            },
            "Name": {
                "Ascending": "A to Z",
                "Descending": "Z to A",
            },
            "Rarity": {
                "Ascending": "Common first",
                "Descending": "Divine first",
            },
        }
        return labels.get(sorting, {}).get(value, str(value))

    def choice_options(item):
        options = []
        for choice in item.get("choices", []):
            if item["attr"] == "inventory_sort_order":
                label = inventory_sort_order_label(choice)
            else:
                label = format_setting_value(item, choice)
            options.append((choice, label))
        return options

    def choice_regions(item):
        options = choice_options(item)
        start = SETTINGS_COL + BOX_WIDTH - (sum(len(label) + 2 for _, label in options) + max(0, len(options) - 1))
        regions = []
        for choice, label in options:
            regions.append((choice, label, start - 1, len(label)))
            start += len(label) + 3
        return regions

    def unavailable_active(item):
        return item["attr"] == getattr(d, "settings_unavailable_attr", None) and time.monotonic() < getattr(d, "settings_unavailable_until", 0)

    def show_unavailable(item):
        d.settings_unavailable_attr = item["attr"]
        d.settings_unavailable_until = time.monotonic() + 0.8
        if settings_editor.active:
            settings_editor.commit()
        settings_editor.clear()
        settings_editor.message = "Coming soon — this option is not available yet."
        sound("error2")

    def extreme_animating():
        started = getattr(d, "settings_extreme_started", None)
        return (
            d.settings_category == 1
            and started is not None
            and animations_enabled()
            and getattr(setting, "flipboard_animations", True)
            and (time.monotonic() - started) * animation_rate() < 0.45
        )

    def animated_setting_value(item, label, color, selected=False):
        if not hasattr(d, "settings_value_texts"):
            d.settings_value_texts = {}
            d.settings_value_changes = {}
        attr = item["attr"]
        old = d.settings_value_texts.get(attr, label)
        d.settings_value_texts[attr] = label
        # on/off and numbers should never flipboard in settings
        can_flip = (
            animations_enabled()
            and getattr(setting, "flipboard_animations", True)
            and item["type"] != "bool"
            and label.strip().casefold() not in {"on", "off", "off / on"}
            and not any(char.isdigit() for char in label + old)
        )
        if old != label:
            if can_flip and label != "[press a key]":
                duration = 0.42 if item["type"] == "keybind" else 0.22
                d.settings_value_changes[attr] = (old, label, time.monotonic(), duration)
            else:
                d.settings_value_changes.pop(attr, None)
        change = d.settings_value_changes.get(attr)
        if change is None or not can_flip:
            d.settings_value_changes.pop(attr, None)
            if label == "[press a key]":
                return f"{reset}{rgb(255, 255, 255)}{label}{reset}", len(label)
            return f"{reset}{color}{bold if selected else ''}{label}{reset}", len(label)
        old, label, started, duration = change
        offset = min(1, (time.monotonic() - started) * animation_rate() / duration)
        width = max(len(old), len(label))
        if offset >= 1:
            d.settings_value_changes.pop(attr, None)
            return f"{color}{bold if selected else ''}{label.rjust(width)}{reset}", width
        if item["type"] == "keybind" and old == "[press a key]":
            old = old.rjust(width)
            prefix = old[:-len(label)]
            prefix = "".join(" " if offset * 1.6 - index / max(1, len(prefix) - 1) >= 0.6 else char for index, char in enumerate(prefix))
            background = terminal_background()
            faded = shine(prefix, offset=offset, color=background if background is not None else (128, 128, 128), start_color=(255, 255, 255), fade_out=True)
            ending = flipboard(label, offset=offset, color=(255, 255, 255), start_text=old[-len(label):], quick=True)
            return reset + faded + ending, width
        if old.endswith(" first") and label.endswith(" first"):
            prefix = flipboard(label[:-6].rjust(width - 6), offset=offset, color=color, bold=selected, start_text=old[:-6].rjust(width - 6), quick=True)
            return prefix + f"{color}{bold if selected else ''} first{reset}", width
        return flipboard(label.rjust(width), offset=offset, color=color, bold=selected, start_text=old.rjust(width), quick=item.get("display") != "victory_celebration"), width

    def value_animations_active():
        return any(
            item["attr"] in getattr(d, "settings_value_changes", {})
            for item in visible_page
        )

    def audio_test_active():
        return test_audio_visible and time.monotonic() < getattr(d, "settings_audio_test_until", 0)

    def draw_slider_setting_value(item, raw_value, row, selected, flash=False):
        before_dot, dot, after_dot, _ = volume_slider_parts(item, raw_value)
        label_width = slider_label_width
        formatted_value = format_setting_value(item, raw_value)
        label = f"{formatted_value:>{label_width}}"
        slider_width = slider_step_count(item) + 1 + 1 + label_width
        move(row + 1, SETTINGS_COL + BOX_WIDTH - slider_width)
        state_color = (
            xlred
            if flash or setting_is_off(item, raw_value)
            else xa
        )
        label_style = f"{state_color}{bold}" if selected else xf
        if item.get("display") == "difficulty":
            previous = getattr(d, "settings_difficulty_value", raw_value)
            if raw_value != previous:
                d.settings_extreme_started = time.monotonic() if raw_value == 3 else None
            d.settings_difficulty_value = raw_value
            if raw_value == 3:
                if hasattr(d, "settings_value_texts"):
                    d.settings_value_texts[item["attr"]] = label
                    d.settings_value_changes.pop(item["attr"], None)
                started = getattr(d, "settings_extreme_started", None)
                offset = 1 if started is None else min(1, (time.monotonic() - started) * animation_rate() / 0.45)
                label_style = ""
                label = unbold + flipboard(label, offset=offset, color=xlred, bold=False, start_text="Hard".rjust(label_width))
                if offset >= 1:
                    d.settings_extreme_started = None
            else:
                label, _ = animated_setting_value(item, label, state_color if selected else xf, selected)
        else:
            label, _ = animated_setting_value(item, label, state_color if selected else xf, selected)
        print(
            f"{x8}{before_dot}{state_color}{dot}{x8}{after_dot} "
            f"{label_style}{label}{reset}",
            end="",
            flush=True,
        )

    preview_attrs = {"text_shine", "rainbow_text", "flipboard_animations", "animation_speed"}

    def name_preview_active(item):
        selected = d.settings_selection == "setting" and d.settings_cursor - 1 == page.index(item)
        return item["attr"] in preview_attrs and (selected or item["attr"] == getattr(d, "settings_hover_attr", None))

    def draw_setting_name(item, row, selected=False, editing=False, flash=False, locked=False):
        move(row + 1, SETTINGS_COL + 2)
        prefix = "✎ " if editing else "→ " if selected else ""
        color = xlred if flash else x7 if locked else xlyellow if editing else xa if selected else xf
        name = f"{color}{bold if selected or editing else unbold}{item['name']}{reset}"
        if not flash and not locked and name_preview_active(item):
            # preview the effect on its name, leave on/off and numbers alone
            offset = time.monotonic()
            if item["attr"] == "rainbow_text":
                name = rainbow(item["name"], offset=offset * 0.3, bold=True, preview=True)
            elif item["attr"] == "flipboard_animations":
                offset = (offset * animation_rate()) % 2
                name = flipboard(item["name"], offset=min(1, offset), color=(186, 243, 219), bold=True, preview=True)
            else:
                rate = animation_rate()
                if item["attr"] == "animation_speed" and settings_editor.active and settings_editor.item is item:
                    rate = settings_editor.value
                name = shine(item["name"], offset=offset * 0.65, color=(186, 243, 219), bold=True, preview=True, speed=rate)
        elif editing and not flash:
            name = shine(item["name"], offset=(time.monotonic() * 0.65) % 1, color=(255, 202, 102), bold=True)
        lock_icon = "🔒 " if locked and selected else ""
        print(f"{color}{prefix}{lock_icon}{name}{reset}" + "  ", end="", flush=True)

    def draw_editing_setting_name(item, row, flash=False):
        draw_setting_name(item, row, selected=True, editing=True, flash=flash)

    def play_boolean_toggle_sound(value):
        sound("map_switch2" if value else "map_switch3")

    def setting_value_contains(x, item, value):
        if item.get("display") in SLIDER_DISPLAYS:
            label_width = slider_label_width
            width = slider_step_count(item) + 2 + label_width
        elif item["type"] == "bool":
            return boolean_control_contains(x, SETTINGS_COL, BOX_WIDTH, slider_label_width)
        elif item["type"] == "choice":
            return any(left <= x < left + width + 2 for _, _, left, width in choice_regions(item))
        else:
            display_value = format_setting_value(item, value)
            if item["attr"] == "inventory_sort_order":
                display_value = inventory_sort_order_label(value)
            width = max(3, len(str(display_value)))
        return x >= SETTINGS_COL + BOX_WIDTH - width - 1

    def draw_setting_value(item, raw_value, value, row, is_selected, is_editing, is_edit_flash, is_locked):
        if is_locked or item.get("disabled"):
            getattr(d, "settings_value_changes", {}).pop(item["attr"], None)
        if is_locked:
            value = f"🔒 {value}"
            move(row + 1, SETTINGS_COL + BOX_WIDTH - len(value) - 1)
            print(f"{x7}{bold if is_selected else ''}{value}{reset}", end="")
        elif item.get("disabled"):
            active = unavailable_active(item)
            value = "Coming soon!" if active else "Coming soon"
            move(row + 1, SETTINGS_COL + BOX_WIDTH - 12)
            print(f"{xlyellow if active else x7}{bold if active else ''}{value:>12}{reset}", end="", flush=True)
        elif item.get("display") in SLIDER_DISPLAYS:
            draw_slider_setting_value(
                item,
                raw_value,
                row,
                selected=is_selected,
                flash=is_edit_flash,
            )
        elif item["type"] == "bool":
            before_dot, dot, after_dot, label = boolean_slider_parts(raw_value)
            label = f"{label:>{slider_label_width}}"
            slider_width = 3 + 1 + slider_label_width
            move(row + 1, SETTINGS_COL + BOX_WIDTH - slider_width)
            state_color = (
                xlred
                if is_edit_flash or setting_is_off(item, raw_value)
                else xa
            )
            label_style = f"{state_color}{bold}" if is_selected else xf
            label, _ = animated_setting_value(item, label, state_color if is_selected else xf, is_selected)
            print(
                f"{x8}{before_dot}{state_color}{dot}{x8}{after_dot} "
                f"{label_style}{label}{reset}",
                end="",
                flush=True,
            )
        elif item["type"] == "choice":
            getattr(d, "settings_value_changes", {}).pop(item["attr"], None)
            for choice, label, left, width in choice_regions(item):
                move(row + 1, left + 1)
                color = xa if choice == raw_value else x7
                print(f"{reset}{color}{bold if choice == raw_value and is_selected else ''}[{label}]{reset}", end="", flush=True)
        else:
            value_color = xlred if is_edit_flash else xa if is_selected else xf
            rendered, width = animated_setting_value(item, value, value_color, is_selected and not is_editing)
            move(row + 1, SETTINGS_COL + BOX_WIDTH - width)
            print(rendered, end="", flush=True)


    # blanks from top left to bottom right (row, col style)
    blank(SETTINGS_ROW, SETTINGS_COL,  30, SETTINGS_COL + BOX_WIDTH + 2)
    
    for visible_index, item in enumerate(visible_page):
        item_index = d.settings_scroll + visible_index

        try:
            obj = setting

            value = getattr(obj, item["attr"], item.get("default"))
        except Exception as e:
            move(10, 40)
            print(f"ERROR: {e}", end="")
            return

        if (
            settings_editor.active
            and item_index == d.settings_cursor - 1
            and settings_editor.item is item
        ):
            value = settings_editor.value
        is_locked = setting.setting_is_locked(item["attr"])
        if is_locked:
            value = setting.effective_setting(item["attr"])
        raw_value = value
        value = format_setting_value(item, value)
        if (
            is_locked
            and item["attr"] in {"inventory_sorting", "inventory_sort_order"}
        ):
            value = "Sorting off"
        if item["attr"] == "inventory_sort_order":
            value = inventory_sort_order_label(raw_value)

        row = SETTINGS_ROW + visible_index * BOX_HEIGHT
        is_selected = (
            item_index == d.settings_cursor - 1
            and d.settings_selection == "setting"
        )
        is_editing = is_selected and (visually_editing or unavailable_active(item))
        is_edit_flash = is_editing and getattr(d, "settings_edit_flash", False)
        edit_border_color = xc if is_edit_flash else xlyellow

        # Top
        print(reset, end="")
        move(row, SETTINGS_COL)
        if is_editing:
            print(f"{edit_border_color}{bold}╔" + "═" * BOX_WIDTH + f"╗{reset}", end="")
        elif is_selected:
            print(f"{RGB}186;243;219m╭" + "─" * BOX_WIDTH + "╮", end="")
        else:
            print("╭" + "─" * BOX_WIDTH + "╮", end="")

        # Middle
        move(row + 1, SETTINGS_COL)
        if is_editing:
            print(f"{edit_border_color}{bold}║{reset}", end="")
        elif is_selected:
            print(f"{RGB}186;243;219m│", end="")
        else:
            print("│", end="")

        move(row + 1, SETTINGS_COL + 2)

        draw_setting_name(item, row, selected=is_selected, editing=is_editing, flash=is_edit_flash, locked=is_locked)

        if is_editing and item["type"] == "keybind":
            value = "[press a key]"
        value = str(value)
        draw_setting_value(item, raw_value, value, row, is_selected, is_editing, is_edit_flash, is_locked)

        move(row + 1, SETTINGS_COL + BOX_WIDTH + 1)
        if is_editing:
            print(f"{edit_border_color}{bold}║{reset}", end="")
        elif is_selected:
            print(f"{RGB}186;243;219m│", end="")
        else:
            print("│", end="")

        # Bottom
        if visible_index != 7:
            move(row + 2, SETTINGS_COL)
            if is_editing:
                print(f"{edit_border_color}{bold}╚" + "═" * BOX_WIDTH + f"╝{reset}", end="")
            elif is_selected:
                print(f"{RGB}186;243;219m╰" + "─" * BOX_WIDTH + "╯", end="")
            else:
                print("╰" + "─" * BOX_WIDTH + "╯", end="")
        if visible_index != len(visible_page) - 1:
            continue

        current_is_test_audio = (
            d.settings_category == 3
            and d.settings_cursor == len(page) + 1
        )
        if current_is_test_audio:
            current = {
                "name": "Test audio",
                "attr": "test_audio",
                "description": "Play the configured audio test sound.",
                "accepted": ["Enter", "Click"],
            }
            current_is_locked = False
        else:
            current = page[d.settings_cursor - 1]
            current_is_locked = setting.setting_is_locked(current["attr"])
        # Description
        blank(32,22, 35,95)
        if d.settings_selection == "setting":
            title = "Editing" if visually_editing else "Currently selected"
            draw_description_line(32, f"{title}: {current['name']}", xlyellow if visually_editing else xlorange, True)
            description = setting_description(current)
            if current_is_locked:
                description = setting.setting_lock_message(current["attr"]) + " " + description
            elif settings_editor.message and not settings_editor.message.startswith(("Press a new key.", "Press Enter to toggle.", "Use left/right,")):
                message = settings_editor.message
                if d.settings_category in (4, 7):
                    for key_item in page:
                        message = message.replace(f"assigned to {key_item['attr']}.", f"assigned to {key_item['name']}.")
                description = message + " " + description
            draw_box_text(f"{reset}{unbold}{xf}{description}{reset}", 33, 23, 34, 94)
            accepted = current["accepted"]
            if current.get("disabled"):
                accepted = "Coming soon"
            elif current_is_locked:
                accepted = "Locked — " + setting.setting_lock_reason(current["attr"])
            elif current.get("type") == "choice":
                accepted = [label for _, label in choice_options(current)]
            if isinstance(accepted, list):
                accepted = " / ".join(accepted)
            accepted = str(accepted).replace("Enter", "⏎")
            draw_box_text(f"{reset}{xa}✓ {bold}Accepted values{unbold}{xa}: {xf}{accepted}{reset}", 35, 23, 35, 94)
        else:
            settings_category = CATEGORY_NAMES
            settings_category_descriptions = CATEGORY_DESCRIPTIONS
            draw_description_line(32, f"Currently selected: {settings_category[d.settings_category - 1]}", xlorange, True)
            draw_box_text(f"{reset}{unbold}{xf}{settings_category_descriptions[d.settings_category - 1]}{reset}", 33, 23, 34, 94)

    def draw_test_audio():
        selected = d.settings_selection == "setting" and d.settings_cursor == len(page) + 1
        active = audio_test_active()
        color = (xlred if setting.disable_audio_completely else xlyellow) if active else RGB + "186;243;219m" if selected else xf
        move(test_audio_row, SETTINGS_COL)
        print(f"{color}{bold if active else ''}╭" + "─" * BOX_WIDTH + f"╮{reset}", end="")
        move(test_audio_row + 1, SETTINGS_COL)
        print(f"{color}│{reset}", end="")
        move(test_audio_row + 1, SETTINGS_COL + 2)
        name = "✓ Test audio" if active else "→ Test audio" if selected else "Test audio"
        print(f"{color}{bold if active or selected else ''}{name.ljust(13)}{reset}", end="")
        status = 'Muted' if active and setting.disable_audio_completely else 'Sound played!' if active else 'Click'
        move(test_audio_row + 1, SETTINGS_COL + BOX_WIDTH - 13)
        print(f"{color}{status:>13}{reset}", end="")
        move(test_audio_row + 1, SETTINGS_COL + BOX_WIDTH + 1)
        print(f"{color}│{reset}", end="")
        move(test_audio_row + 2, SETTINGS_COL)
        print(f"{color}╰" + "─" * BOX_WIDTH + f"╯{reset}", end="", flush=True)

    if test_audio_visible:
        draw_test_audio()

    if scroll_item_count > SETTINGS_VIEW_SIZE:
        track_height = SETTINGS_VIEW_SIZE * BOX_HEIGHT
        thumb_height = max(
            2,
            round(track_height * SETTINGS_VIEW_SIZE / scroll_item_count),
        )
        thumb_offset = round(
            (track_height - thumb_height)
            * d.settings_scroll
            / max(1, max_scroll)
        )
        scrollbar_col = SETTINGS_SCROLLBAR_COL
        for track_index in range(track_height):
            move(SETTINGS_ROW + track_index, scrollbar_col)
            if thumb_offset <= track_index < thumb_offset + thumb_height:
                print(f"{xlorange}{bold}┃{reset}", end="")
            else:
                print(f"{x8}│{reset}", end="")
    else:
        track_height = SETTINGS_VIEW_SIZE * BOX_HEIGHT
        for track_index in range(track_height):
            move(SETTINGS_ROW + track_index, SETTINGS_SCROLLBAR_COL)
            print(" ", end="")

    if visually_editing:
        if settings_editor.item["type"] == "keybind":
            help_lines = [("Key", "save binding"), ("Esc", "discard changes"), ("Ctrl+R", "reset all keys"), ("↑/↓", "save & move")]
        else:
            help_lines = [("↑/↓", "save & move"), ("←/→", "change value"), ("⏎", "save changes"), ("Esc", "discard changes")]
    elif d.settings_selection == "setting":
        help_lines = [("↑/↓", "switch setting"), ("←/Esc", "categories")]
        action = "see help on left" if current_is_locked else "test audio" if current_is_test_audio else "coming soon" if current.get("disabled") else "run action" if current["type"] == "action" else "toggle switch" if current["type"] == "bool" else "edit setting"
        help_lines.append(("Locked" if current_is_locked else "⏎", action))
        help_lines.append(("Ctrl/Cmd+F", "search"))
    else:
        help_lines = [("↑/↓", "switch category"), ("→", "enter category"), ("⏎", "enter category"), ("Esc", "exit settings")]
    for index, (control, action) in enumerate(help_lines):
        text = f"{xlyellow}{bold}{control}{unbold}{x7} - {xf}{unbold}{action}"
        # keep long controls inside the box, never wrap into the bottom border
        move(32 + index, 96)
        print(f"{reset}{x7}│ {reset}", end="")
        draw_box_text(text, 32 + index, 98, 32 + index, 124)
        move(32 + index, 125)
        print(f"{reset}{x7} │{reset}", end="")
    move(36, 1)
    print(f"{xlred}╰{'─' * 19}{x7}┴{reset}", end="")

    move(33, 2)
    print(f"{reset}{xc}{bold}{'Back to house':^19}{reset}", end="")
    move(34, 2)
    if not setting.mouse_controls:
        back_hint = "[ESC - cancel edit]" if visually_editing else "[ESC twice]" if d.settings_selection == "setting" else f"[{bind.back.upper()} | ESC]"
    else:
        back_hint = "[click to go back]" if visually_editing else "[click | ESC twice]" if d.settings_selection == "setting" else f"[{bind.back.upper()} | ESC]"
    print(f"{reset}{xc}{back_hint:^19}{reset}", end="")

    print("", end="", flush=True)
    if getattr(d, "settings_edit_flash", False):
        d.settings_edit_flash = False
        time.sleep(0.18)
        game.goto = settings2
        return

    while True:
            k = key(
                timeout=(
                    0.04
                    if (animations_enabled() and (visually_editing or category_focused or extreme_animating() or value_animations_active() or any(name_preview_active(item) for item in visible_page)))
                    or (test_audio_visible and getattr(d, "settings_audio_test_until", 0))
                    or getattr(d, "settings_unavailable_until", 0)
                    else None
                ),
                mouse=setting.mouse_controls,
                hover=True,
                shortcuts=True,
            )

            if k == "TIMEOUT":
                for index, item in enumerate(visible_page):
                    if name_preview_active(item):
                        selected = d.settings_selection == "setting" and d.settings_cursor - 1 == d.settings_scroll + index
                        editing = visually_editing and selected
                        draw_setting_name(item, SETTINGS_ROW + index * BOX_HEIGHT, selected=selected, editing=editing, locked=setting.setting_is_locked(item["attr"]))
                if getattr(d, "settings_unavailable_until", 0):
                    if time.monotonic() >= d.settings_unavailable_until:
                        d.settings_unavailable_until = 0
                    game.goto = settings2
                    return
                if test_audio_visible and getattr(d, "settings_audio_test_until", 0):
                    draw_test_audio()
                    if not audio_test_active():
                        d.settings_audio_test_until = 0
                if value_animations_active():
                    for index, animated_item in enumerate(visible_page):
                        if animated_item["attr"] not in d.settings_value_changes:
                            continue
                        raw = getattr(setting, animated_item["attr"])
                        editing = settings_editor.active and settings_editor.item is animated_item
                        if editing:
                            raw = settings_editor.value
                        locked = setting.setting_is_locked(animated_item["attr"])
                        if locked:
                            raw = setting.effective_setting(animated_item["attr"])
                        label = format_setting_value(animated_item, raw)
                        if animated_item["attr"] == "inventory_sort_order":
                            label = inventory_sort_order_label(raw)
                        draw_setting_value(animated_item, raw, str(label), SETTINGS_ROW + index * BOX_HEIGHT,
                            d.settings_selection == "setting" and d.settings_cursor - 1 == d.settings_scroll + index,
                            editing, False, locked)
                sys.stdout.flush()
                if d.settings_category == 1 and getattr(d, "settings_extreme_started", None) is not None:
                    difficulty_item = page[0]
                    difficulty_value = (
                        settings_editor.value
                        if settings_editor.active and settings_editor.item["attr"] == "battle_difficulty"
                        else setting.battle_difficulty
                    )
                    draw_slider_setting_value(
                        difficulty_item, difficulty_value, SETTINGS_ROW,
                        selected=d.settings_selection == "setting" and d.settings_cursor == 1,
                    )
                if visually_editing:
                    focused_item = page[d.settings_cursor - 1]
                    focused_row = (
                        SETTINGS_ROW
                        + (d.settings_cursor - 1 - d.settings_scroll) * BOX_HEIGHT
                    )
                    draw_editing_setting_name(focused_item, focused_row)
                    continue
                if category_focused:
                    category_index = d.settings_category - 1
                    if not d.settings_category_scroll <= category_index < d.settings_category_scroll + category_view_size:
                        continue
                    move(9 + (category_index - d.settings_category_scroll) * category_height, 2)
                    label = shine(
                        CATEGORY_LABELS[category_index],
                        offset=(time.monotonic() * 0.65) % 1.0,
                        color=CATEGORY_SELECTED_RGB,
                        bold=True,
                    )
                    print(label, end="", flush=True)
                    continue
                continue

            if isinstance(k, str) and k.lower() in ("ctrl/f", "cmd/f", "command/f", "super/f", "meta/f"):
                open_settings_search()
                return

            if isinstance(k, dict):
                mouse_event = k.get("event")
                if mouse_event == "move":
                    index = setting_index_at(k["x"], k["y"], len(visible_page), SETTINGS_COL, SETTINGS_ROW, BOX_WIDTH, BOX_HEIGHT)
                    hovered = visible_page[index]["attr"] if index is not None else None
                    if hovered != getattr(d, "settings_hover_attr", None):
                        d.settings_hover_attr = hovered
                        game.goto = settings2
                        return
                    continue
                if mouse_event == "up" and k.get("button") == "left":
                    d.settings_category_scrollbar_dragging = False
                    d.settings_scrollbar_dragging = False
                over_category_sidebar = 0 <= k.get("x", -1) <= category_scrollbar_col - 1 and 7 <= k.get("y", -1) < 7 + category_track_height
                if mouse_event == "wheel" and over_category_sidebar:
                    direction = -1 if k.get("delta", 0) > 0 else 1
                    new_scroll = max(0, min(category_max_scroll, d.settings_category_scroll + direction))
                    if new_scroll != d.settings_category_scroll:
                        d.settings_category_scroll = new_scroll
                        d.settings_category_manual_scroll = True
                        sound("map_switch3" if direction < 0 else "map_switch2")
                        game.goto = settings2
                        return
                    continue
                dragging_categories = getattr(d, "settings_category_scrollbar_dragging", False)
                on_category_scrollbar = over_category_sidebar and k.get("x") == category_scrollbar_col - 1
                if k.get("button") == "left" and ((mouse_event == "down" and on_category_scrollbar) or (mouse_event == "drag" and dragging_categories)):
                    position = max(0, min(category_track_height - 1, k["y"] - 7))
                    if mouse_event == "down":
                        on_thumb = category_thumb_offset <= position < category_thumb_offset + category_thumb_height
                        d.settings_category_scrollbar_grab = position - category_thumb_offset if on_thumb else category_thumb_height // 2
                    grab = getattr(d, "settings_category_scrollbar_grab", category_thumb_height // 2)
                    d.settings_category_scroll = max(0, min(category_max_scroll, round((position - grab) * category_max_scroll / max(1, category_thumb_travel))))
                    d.settings_category_manual_scroll = True
                    d.settings_category_scrollbar_dragging = True
                    game.goto = settings2
                    return
                if mouse_event == "down":
                    d.settings_category_scrollbar_dragging = False
                if mouse_event in ("down", "drag") and k.get("button") == "left" and max_scroll and (
                    (mouse_event == "drag" and getattr(d, "settings_scrollbar_dragging", False))
                    or (mouse_event == "down" and k.get("x") == SETTINGS_SCROLLBAR_COL - 1 and SETTINGS_ROW - 1 <= k.get("y", -1) < SETTINGS_ROW - 1 + SETTINGS_VIEW_SIZE * BOX_HEIGHT)
                ):
                    if settings_editor.active:
                        settings_editor.commit()
                        if d.settings_category == 3:
                            sound("REFRESH_AUDIO")
                    settings_editor.clear()
                    d.settings_slider_dragging = False
                    d.settings_scrollbar_dragging = True
                    position = max(0, min(SETTINGS_VIEW_SIZE * BOX_HEIGHT - 1, k["y"] - SETTINGS_ROW + 1))
                    d.settings_scroll = round(position * max_scroll / (SETTINGS_VIEW_SIZE * BOX_HEIGHT - 1))
                    d.settings_cursor = max(d.settings_scroll + 1, min(d.settings_cursor, d.settings_scroll + SETTINGS_VIEW_SIZE))
                    game.goto = settings2
                    return
                if mouse_event == "down":
                    d.settings_scrollbar_dragging = False
                if mouse_event == "drag" and k.get("button") == "left":
                    if getattr(d, "settings_slider_dragging", False) and settings_editor.active:
                        item = settings_editor.item
                        value = volume_value_at_mouse(k["x"], item, SETTINGS_COL, BOX_WIDTH, clamp=True, label_width=slider_label_width)
                        if value != settings_editor.value:
                            settings_editor.value = value
                            row = SETTINGS_ROW + (d.settings_cursor - 1 - d.settings_scroll) * BOX_HEIGHT
                            draw_slider_setting_value(item, value, row, selected=True)
                    continue
                if mouse_event == "wheel" and (getattr(d, "settings_slider_dragging", False) or getattr(d, "settings_scrollbar_dragging", False)):
                    continue
                if (
                    mouse_event == "down"
                    and k.get("button") == "left"
                    and test_audio_visible
                    and SETTINGS_COL - 1 <= k.get("x", -1) <= SETTINGS_COL + BOX_WIDTH
                    and test_audio_row - 1 <= k.get("y", -1) <= test_audio_row + 1
                ):
                    if settings_editor.active:
                        settings_editor.commit()
                        sound("REFRESH_AUDIO")
                    settings_editor.clear()
                    d.settings_slider_dragging = False
                    d.settings_selection = "setting"
                    d.settings_cursor = len(page) + 1
                    d.settings_audio_test_until = time.monotonic() + 0.45
                    sound("sound_test")
                    game.goto = settings2
                    return
                if (
                    mouse_event == "down"
                    and k.get("button") == "left"
                    and back_button_contains(k["x"], k["y"])
                ):
                    settings_editor.clear()
                    d.settings_slider_dragging = False
                    sound("map_left")
                    game.goto = house
                    return

                if mouse_event == "wheel":
                    local_hovered_index = setting_index_at(
                        k["x"],
                        k["y"],
                        len(visible_page),
                        SETTINGS_COL,
                        SETTINGS_ROW,
                        BOX_WIDTH,
                        BOX_HEIGHT,
                    )
                    on_scrollbar = (
                        max_scroll > 0
                        and k.get("x", -1) == SETTINGS_SCROLLBAR_COL - 1
                        and SETTINGS_ROW - 1
                        <= k.get("y", -1)
                        < SETTINGS_ROW - 1 + SETTINGS_VIEW_SIZE * BOX_HEIGHT
                    )
                    wheel_up = k.get("delta", 0) > 0
                    hovered_index = None
                    hovered = None
                    current_value = None
                    over_value = False
                    if local_hovered_index is not None:
                        hovered_index = d.settings_scroll + local_hovered_index
                        hovered = page[hovered_index]
                        current_value = getattr(setting, hovered["attr"], hovered.get("default"))
                        over_value = (
                            k.get("y")
                            == SETTINGS_ROW
                            + local_hovered_index * BOX_HEIGHT
                            and setting_value_contains(
                                k.get("x", -1),
                                hovered,
                                current_value,
                            )
                        )

                    inside_settings_area = (
                        SETTINGS_COL - 1
                        <= k.get("x", -1)
                        <= SETTINGS_SCROLLBAR_COL
                        and SETTINGS_ROW - 1 <= k.get("y", -1) < 31
                    )

                    if on_scrollbar or (inside_settings_area and not over_value):
                        scroll_direction = -1 if wheel_up else 1
                        new_scroll = max(
                            0,
                            min(max_scroll, d.settings_scroll + scroll_direction),
                        )
                        if new_scroll != d.settings_scroll:
                            if settings_editor.active:
                                settings_editor.commit()
                                if d.settings_category == 3:
                                    sound("REFRESH_AUDIO")
                            d.settings_scroll = new_scroll
                            d.settings_cursor = max(
                                new_scroll + 1,
                                min(
                                    d.settings_cursor,
                                    new_scroll + SETTINGS_VIEW_SIZE,
                                ),
                            )
                            settings_editor.clear()
                            sound("map_switch3" if wheel_up else "map_switch2")
                            game.goto = settings2
                            return
                        continue

                    if hovered is None:
                        continue

                    if (
                        hovered.get("disabled")
                        or setting.setting_is_locked(hovered["attr"])
                        or hovered["type"] in ("keybind", "action")
                    ):
                        sound("error2")
                        continue

                    if settings_editor.active:
                        settings_editor.commit()
                    direction = 1 if wheel_up else -1

                    if hovered["type"] == "bool":
                        new_value = not current_value
                    elif hovered["type"] == "choice":
                        choices = hovered.get("choices", ())
                        if not choices:
                            continue
                        try:
                            current_index = choices.index(current_value)
                        except ValueError:
                            current_index = 0
                        new_value = choices[
                            (current_index + direction) % len(choices)
                        ]
                    elif hovered["type"] == "slider":
                        step = hovered.get("step", 1)
                        new_value = max(
                            hovered.get("min", current_value),
                            min(
                                hovered.get("max", current_value),
                                current_value + direction * step,
                            ),
                        )
                        if isinstance(step, float):
                            decimals = max(
                                0,
                                len(str(step).partition(".")[2]),
                            )
                            new_value = round(new_value, decimals)
                    else:
                        continue

                    if new_value == current_value:
                        continue
                    setattr(setting, hovered["attr"], new_value)
                    setting.save()
                    settings_editor.clear()
                    d.settings_selection = "setting"
                    d.settings_cursor = hovered_index + 1
                    if d.settings_category == 3:
                        sound("REFRESH_AUDIO")
                    if hovered["type"] == "bool":
                        play_boolean_toggle_sound(new_value)
                    else:
                        sound("map_switch2" if direction > 0 else "map_switch3")
                    game.goto = settings2
                    return

                if mouse_event == "up" and k.get("button") in ("left", "right"):
                    # the click sound already played on mouse down
                    d.settings_click_sound = False
                    if k.get("button") == "left" and getattr(d, "settings_slider_dragging", False):
                        d.settings_slider_dragging = False
                        if (
                            settings_editor.active
                            and settings_editor.item.get("display")
                            in SLIDER_DISPLAYS
                        ):
                            settings_editor.commit()
                            if d.settings_category == 3:
                                sound("REFRESH_AUDIO")
                            game.goto = settings2
                            return
                    continue

                if mouse_event == "down" and k.get("button") == "right":
                    if (
                        test_audio_visible
                        and SETTINGS_COL - 1 <= k.get("x", -1) <= SETTINGS_COL + BOX_WIDTH
                        and test_audio_row - 1 <= k.get("y", -1) <= test_audio_row + 1
                    ):
                        if settings_editor.active:
                            settings_editor.commit()
                            sound("REFRESH_AUDIO")
                        settings_editor.clear()
                        d.settings_slider_dragging = False
                        d.settings_selection = "setting"
                        d.settings_cursor = len(page) + 1
                        game.goto = settings2
                        return
                    right_clicked_index = setting_index_at(
                        k["x"], k["y"], len(visible_page),
                        SETTINGS_COL, SETTINGS_ROW, BOX_WIDTH, BOX_HEIGHT,
                    )
                    if right_clicked_index is not None:
                        if settings_editor.active:
                            settings_editor.commit()
                            if d.settings_category == 3:
                                sound("REFRESH_AUDIO")
                        settings_editor.clear()
                        d.settings_slider_dragging = False
                        d.settings_selection = "setting"
                        d.settings_cursor = d.settings_scroll + right_clicked_index + 1
                        game.goto = settings2
                        return
                    continue

                if mouse_event == "down" and k.get("button") == "left":
                    # mouse starts at 0, drawing starts at 1
                    clicked_index = setting_index_at(
                        k["x"],
                        k["y"],
                        len(visible_page),
                        SETTINGS_COL,
                        SETTINGS_ROW,
                        BOX_WIDTH,
                        BOX_HEIGHT,
                    )

                    if clicked_index is not None:
                        local_clicked_index = clicked_index
                        clicked_index = d.settings_scroll + local_clicked_index
                        clicked = page[clicked_index]
                        owner = setting
                        if clicked["type"] == "action":
                            if settings_editor.active:
                                settings_editor.commit()
                            d.settings_selection = "setting"
                            d.settings_cursor = clicked_index + 1
                            run_settings_action(clicked)
                            game.goto = settings2
                            return
                        same_active_setting = (
                            settings_editor.active
                            and clicked_index == d.settings_cursor - 1
                            and settings_editor.item is clicked
                        )
                        value_row = SETTINGS_ROW + local_clicked_index * BOX_HEIGHT
                        over_value_row = k["y"] == value_row

                        if mouse_event == "down" and clicked.get("disabled"):
                            d.settings_selection = "setting"
                            d.settings_cursor = clicked_index + 1
                            show_unavailable(clicked)
                            game.goto = settings2
                            return

                        if mouse_event == "down" and clicked["type"] == "choice" and over_value_row and not owner.setting_is_locked(clicked["attr"]):
                            for choice, _, left, width in choice_regions(clicked):
                                if not left <= k["x"] < left + width + 2:
                                    continue
                                if settings_editor.active:
                                    settings_editor.commit()
                                previous = getattr(owner, clicked["attr"])
                                setattr(owner, clicked["attr"], choice)
                                owner.save()
                                settings_editor.clear()
                                d.settings_selection = "setting"
                                d.settings_cursor = clicked_index + 1
                                if previous != choice:
                                    sound("map_switch2" if clicked["choices"].index(choice) > clicked["choices"].index(previous) else "map_switch3")
                                    d.settings_click_sound = True
                                game.goto = settings2
                                return

                        if (
                            clicked.get("display") in SLIDER_DISPLAYS
                            and over_value_row
                            and not clicked.get("disabled")
                            and not owner.setting_is_locked(clicked["attr"])
                        ):
                            clicked_value = volume_value_at_mouse(
                                k["x"],
                                clicked,
                                SETTINGS_COL,
                                BOX_WIDTH,
                                label_width=slider_label_width,
                            )
                            if clicked_value is not None:
                                was_same_active_setting = same_active_setting
                                if settings_editor.active and not same_active_setting:
                                    settings_editor.commit()
                                    if d.settings_category == 3:
                                        sound("REFRESH_AUDIO")

                                d.settings_selection = "setting"
                                d.settings_cursor = clicked_index + 1
                                if not same_active_setting:
                                    settings_editor.begin(clicked, owner)
                                previous_value = settings_editor.value
                                settings_editor.value = clicked_value
                                settings_editor.message = (
                                    "Drag the slider; release to save."
                                )
                                d.settings_slider_dragging = True
                                if mouse_event == "down":
                                    d.settings_click_sound = True
                                    sound("map_switch3" if clicked_value < previous_value else "map_switch2")
                                if was_same_active_setting and not visually_editing:
                                    draw_slider_setting_value(
                                        clicked,
                                        clicked_value,
                                        value_row,
                                        selected=True,
                                    )
                                    continue
                                game.goto = settings2
                                return

                        if (
                            mouse_event == "down"
                            and clicked["type"] == "bool"
                            and over_value_row
                            and boolean_control_contains(k["x"], SETTINGS_COL, BOX_WIDTH, slider_label_width)
                            and not clicked.get("disabled")
                            and not owner.setting_is_locked(clicked["attr"])
                        ):
                            settings_editor.message = ""
                            if settings_editor.active:
                                if same_active_setting:
                                    settings_editor.clear()
                                else:
                                    settings_editor.commit()
                            d.settings_selection = "setting"
                            d.settings_cursor = clicked_index + 1
                            new_value = not getattr(owner, clicked["attr"])
                            setattr(
                                owner,
                                clicked["attr"],
                                new_value,
                            )
                            owner.save()
                            if d.settings_category == 3:
                                sound("REFRESH_AUDIO")
                            play_boolean_toggle_sound(new_value)
                            d.settings_click_sound = True
                            game.goto = settings2
                            return

                        if (
                            settings_editor.active and same_active_setting
                        ):
                            continue

                        if settings_editor.active:
                            settings_editor.commit()
                            if d.settings_category == 3:
                                sound("REFRESH_AUDIO")

                        d.settings_selection = "setting"
                        d.settings_cursor = clicked_index + 1
                        if clicked["type"] in ("slider", "bool", "choice") and not owner.setting_is_locked(clicked["attr"]):
                            settings_editor.clear()
                            game.goto = settings2
                            return
                        result = settings_editor.begin(clicked, owner)
                        sound(
                            "error2"
                            if result in ("disabled", "locked")
                            else "map_right"
                        )
                        game.goto = settings2
                        return

                    if mouse_event == "down":
                        clicked_category = category_index_at(k["x"], k["y"], count=len(visible_categories), height=category_height, offset=d.settings_category_scroll)
                        if clicked_category is not None:
                            if settings_editor.active:
                                settings_editor.message = "Save or cancel before switching categories."
                                d.settings_edit_flash = True
                                sound("error2")
                                game.goto = settings2
                                return

                            previous_category = d.settings_category
                            d.settings_category = clicked_category + 1
                            d.settings_category_manual_scroll = False
                            d.settings_selection = "category"
                            d.settings_cursor = 1
                            d.settings_scroll = 0
                            settings_editor.clear()
                            sounds_list = [
                                "setting_battles",
                                "settings_graphics",
                                "settings_music",
                                "setting_keybinds",
                                "setting_accessibility",
                                "switch", "switch", "switch", "switch",
                            ]
                            direction_sound = (
                                "map_switch3"
                                if d.settings_category < previous_category
                                else "map_switch2"
                            )
                            sound(direction_sound)
                            sound(sounds_list[d.settings_category - 1])
                            game.goto = settings2
                            return
                continue
            else:
                if not (settings_editor.active and settings_editor.item["type"] == "keybind"):
                    k = menu_navigation_key(k)
                d.settings_scrollbar_dragging = False
                d.settings_category_scrollbar_dragging = False
                if d.settings_category in (4, 7) and k.lower() == "ctrl/r":
                    # add this back when the reset confirmation screen is ready
                    # if not confirm_keybind_reset():
                    #     continue
                    bind.reset()
                    settings_editor.clear()
                    settings_editor.message = "All keybinds reset to defaults."
                    sound("map_switch3")
                    game.goto = settings2
                    return

                if settings_editor.active:
                    if k.lower() in ("up", "down"):
                        d.settings_slider_dragging = False
                        settings_editor.commit()
                        sound("map_switch3")
                        if d.settings_category == 3:
                            sound("REFRESH_AUDIO")

                        if k.lower() == "up":
                            d.settings_cursor = max(1, d.settings_cursor - 1)
                        else:
                            d.settings_cursor = min(
                                max_settings[d.settings_category - 1],
                                d.settings_cursor + 1,
                            )
                        d.settings_selection = "setting"
                        game.goto = settings2
                        return

                    edit_key = k
                    if settings_editor.item["type"] != "keybind":
                        if k.lower() == bind.confirm.lower():
                            edit_key = "enter"
                        elif k.lower() == bind.deny.lower():
                            edit_key = "esc"
                    result = settings_editor.handle_key(edit_key)
                    if result == "saved":
                        d.settings_slider_dragging = False
                        if d.settings_category == 3:
                            sound("REFRESH_AUDIO")
                        if settings_editor.item["type"] == "bool":
                            play_boolean_toggle_sound(settings_editor.value)
                        else:
                            sound("map_switch3")
                    elif result == "cancelled":
                        d.settings_slider_dragging = False
                        getattr(d, "settings_value_texts", {}).pop(settings_editor.item["attr"], None)
                        getattr(d, "settings_value_changes", {}).pop(settings_editor.item["attr"], None)
                        sound("map_left")
                    elif result == "error":
                        d.settings_edit_flash = True
                        sound("error2")
                    elif result == "changed":
                        sound("map_switch3" if edit_key.lower() in ("left", "a") else "map_switch2")
                        if settings_editor.item.get("display") in SLIDER_DISPLAYS:
                            focused_row = (
                                SETTINGS_ROW
                                + (d.settings_cursor - 1 - d.settings_scroll)
                                * BOX_HEIGHT
                            )
                            draw_slider_setting_value(
                                settings_editor.item,
                                settings_editor.value,
                                focused_row,
                                selected=True,
                            )
                            continue
                    elif result == "ignored":
                        continue
                    game.goto = settings2
                    return
                if k.lower() == "down":
                    settings_editor.message = ""
                    if d.settings_selection == "category":
                        d.settings_category_manual_scroll = False
                        d.settings_category += 1
                        d.settings_scroll = 0
                        if d.settings_category > len(CATEGORY_NAMES):
                            d.settings_category = len(CATEGORY_NAMES)
                            sound("map_switch2_end")
                        else:
                            sounds_list = ["setting_battles", "settings_graphics", "settings_music", "setting_keybinds", "setting_accessibility", "switch", "switch", "switch", "switch"]
                            sound("map_switch2")
                            sound(sounds_list[d.settings_category - 1])
                    elif d.settings_selection == "setting":
                        d.settings_cursor += 1
                        if d.settings_cursor > max_settings[d.settings_category - 1]:
                            d.settings_cursor = max_settings[d.settings_category - 1]
                            if (
                                d.settings_category == 3
                                and d.settings_scroll < max_scroll
                            ):
                                d.settings_scroll = max_scroll
                                sound("map_switch2")
                            else:
                                sound("map_switch2_end")
                        else:
                            sound("map_switch2")
                    game.goto = settings2
                    return
                if k.lower() == "up":
                    settings_editor.message = ""
                    if d.settings_selection == "category":
                        d.settings_category_manual_scroll = False
                        d.settings_category -= 1
                        d.settings_scroll = 0
                        if d.settings_category < 1:
                            d.settings_category = 1
                            sound("map_switch1_end")
                        else:
                            sounds_list = ["setting_battles", "settings_graphics", "settings_music", "setting_keybinds", "setting_accessibility", "switch", "switch", "switch", "switch"]
                            sound("map_switch3")
                            sound(sounds_list[d.settings_category - 1])
                    elif d.settings_selection == "setting":
                        d.settings_cursor -= 1
                        if d.settings_cursor < 1:
                            d.settings_cursor = 1
                            sound("map_switch1_end")
                        else:
                            sound("map_switch3")
                    game.goto = settings2
                    return    
                if d.settings_selection == "category" and k.lower() in (
                    "enter", bind.confirm.lower(), "right"
                ):
                    settings_editor.message = ""
                    d.settings_selection = "setting"
                    d.settings_cursor = d.settings_scroll + 1
                    sound("map_right")
                    game.goto = settings2
                    return
                if d.settings_selection == "setting" and k.lower() in (
                    "enter", bind.confirm.lower()
                ):
                    if (
                        d.settings_category == 3
                        and d.settings_cursor == len(page) + 1
                    ):
                        d.settings_audio_test_until = time.monotonic() + 0.45
                        sound("sound_test")
                        game.goto = settings2
                        return
                    current = page[d.settings_cursor - 1]
                    owner = setting
                    if current["type"] == "action":
                        run_settings_action(current)
                        game.goto = settings2
                        return
                    if current.get("disabled"):
                        show_unavailable(current)
                        game.goto = settings2
                        return
                    result = settings_editor.begin(current, owner)
                    if result == "focused" and current["type"] == "bool":
                        result = settings_editor.handle_key("enter")
                        if result == "saved" and d.settings_category == 3:
                            sound("REFRESH_AUDIO")
                        play_boolean_toggle_sound(settings_editor.value)
                    else:
                        sound(
                            "error2"
                            if result in ("disabled", "locked")
                            else "map_right"
                        )
                    game.goto = settings2
                    return
                if d.settings_selection == "setting" and k.lower() in (
                    "esc", "left", "a", bind.back.lower(), bind.deny.lower()
                ): # go left
                    settings_editor.message = ""
                    d.settings_selection = "category"
                    d.settings_cursor = 1
                    sound("map_left")
                    game.goto = settings2
                    return
                if d.settings_selection == "category" and k.lower() in (
                    bind.back.lower(), bind.deny.lower(), "esc"
                ):
                    game.goto = house
                    return

def settings_old():
    cls()
    print(f"""
[3;1H                                            {xb}              ██          
                                            {xb}            ██            
                                            {xb}  ██      ██  {xlred} ██      {xlred}██ 
                                            {xb}    ██  ██     {xlred}  ██  ██   
                                            {xb}      ██     {xlred}      ██     
                                                            {xlred} ██  ██   
                                                          {xlred} ██     {xlred} ██  

#3{x7}                ╭────────────────────────╮
#4{x7}                ╭────────────────────────╮
#3{x7}                │    {reset}{xf}{bold} Options & info {reset}{x7}    │
#4{x7}                │    {reset}{xf}{bold} Options & info {reset}{x7}    │
#3{x7}                ╰────────────────────────╯
#4{x7}                ╰────────────────────────╯
{player.color}       ██████                                                         
{player.color}     ██      ██     {x8}     ╭───────────────────────────╮         ╭───────────────────────────╮   
{player.color}     ██ •  • ██     {x8}╭────╯     {x7}{italic}Configure things!{reset}{x8}     ╰────┬────╯    {x7}{underline}{italic} Available Options {reset}{x8}    ╰────╮     
{player.color}     ██      ██     {x8}│{x9}                                {x8}     │                                    {x8} │ 
{player.color}       ██████       {x8}│{player.color}{bold}  You've landed in the settings!   {reset}{x8}  │  {x7}{bold}[G]{reset}{xf} 💡 Graphics and performance   {x8} │ 
{player.color}              {x8}{italic}arm2⇣{reset} {x8}│{x9}                                    {x8} │                                   {x8}  │           
{player.color}         ██      ██ {x8}│{xf}  Here is where you can find every   {x8}│  {x6}{bold}[S]{reset}{xlyellow} 📣 Sound and music options   {x8}  │ 
{player.color}  {x8}{italic}arm1⇣{reset}{player.color}  ██    ██   {x8}│{xf}  single setting currently available {x8}│                                   {x8}  │ 
{player.color}    ███  ██  ██     {x8}│{xf}  in the game. Check them out here! {x8} │  {x2}{bold}[K]{reset}{xa} ⌨️ Key bindings and shortcuts{x8}  │ 
{player.color}  ██     ██         {x8}│{x9}                                    {x8} │                                   {x8}  │  
{player.color}         ██ {x8}{italic}‹"body"{reset} {x8}│{xf}  To access a category on the right,{x8} │  {x5}{bold}[A]{reset}{RGB}255;222;167m{xd} 📺 Interface and gameplay{x8}      │ 
{player.color}                    {x8}│{xf}  simply {bold}press the keys {reset}that are{x8}     │                                   {x8}  │    
{player.color}       ██  ██       {x8}│{xf}  shown next to them!            {x8}    │  {x3}{bold}[R]{reset}{xb} 📬 Profiles and data backup{x8}    │ 
{player.color}     ██      ██     {x8}│{x9}                                    {x8} │                                     │              
{player.color}                    {x8}│{xf}  So go on - {italic}customize and conquer!{reset}{x8}  │  {x3}{bold}{RGB}190;81;70m{xbrown}[C]{reset}{xb}{RGB}213;126;65m{xlbrown} ⚙️ System core and game info{x8}   │ 
{player.color}  {x8}{italic}leg1⇡      ⇡leg2  {reset}{x8}│{x9}                                    {x8} │                                     │              
{player.color}                    {x8}│{xf}  {xlorange}🔎 {bold}Press space to search...    {reset}{x8}    │  {xc}{bold}[{bind.back.upper()}] {reset}🏡 {xlred}{italic}<- Return to your house{x8}{x8}     │ 
{player.color}  {x8}{italic}                  {reset}{x8}│{x9}                                    {x8} │                                     │              
{player.color} {x8}{italic}     {reset}        {x8}{italic}      {reset}{x8}╰{x8}────────────────────────────────────{x8}─┴─────────────────────────────────────╯   
    """,end="")
    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            sound("map_switch3")
            game.goto = house
            return
            
@save_operation
def inventory():
    player.color = getattr(player, "color", xa)
    sorting = setting.inventory_sorting if setting.sort_items_automatically else "Off"
    id_maps = sort_inventory(
        PROJECT_ROOT / "Items", sorting, setting.inventory_sort_order,
        before_change=lambda path: backup_before_write(PROJECT_ROOT, path, "", setting.backup_count),
    )
    selections = dict(setting.inventory_last_selections)
    for category, id_map in id_maps.items():
        if category in selections:
            selections[category] = id_map.get(selections[category], selections[category])
    if selections != setting.inventory_last_selections:
        setting.inventory_last_selections = selections
    cls()
    print(f"""
{reset}
{x5}{bold}                                                       __________ 
                                                     /\\_________\\ 
                                                    │ /         / 
                                                    `. ())oo() . 
                                                     │\\(*()*.,()o\\
                                                     │ │--------_│
                                                      \\│-________│{reset}

#3{xd}                 ╭───────────────────────╮
#4{xd}                 ╭───────────────────────╮
#3{xd}                 │       {bold}{x5}Inventory{reset}{xd}       │
#4{xd}                 │       {bold}{x5}Inventory{reset}{xd}       │
#3{xd}                 ╰───────────────────────╯
#4{xd}                 ╰───────────────────────╯
{player.color}       ██████                                                            
{player.color}     ██      ██     {x8}     ╭───────────────────────────╮         ╭───────────────────────────╮   
{player.color}     ██ •  • ██     {x8}╭────╯ {x7}{italic}Oh, shiny! Ooh, sparkly! {reset}{x8} ╰────┬────╯    {x7}{underline}{italic} Available Options {reset}{x8}    ╰────╮     
{player.color}     ██      ██     {x8}│{x9}                                {x8}     │                                    {x8} │ 
{player.color}       ██████       {x8}│{player.color}{bold}  Welcome to your inventory!      {reset}{x8}   │  {x2}{bold}[1]{reset}{xa} 🏹 View all weapons          {x8}  │ 
{player.color}         ██         {x8}│{x9}                                    {x8} │                                   {x8}  │           
{player.color}   ██    ██    ██   {x8}│{xlorange}  Every single weapon, bodypiece,   {x8} │  {x3}{bold}[2]{reset}{xb} 🤺 View all armour           {x8}  │ 
{player.color}     ██  ██  ██     {x8}│{xlorange}  helmet or material you've gotten {x8}  │                                   {x8}  │ 
{player.color}       ██████       {x8}│{xlorange}  will be stored right here!        {x8} │  {x5}{bold}[3]{reset}{xd} 🪖 View all helmets          {x8}  │ 
{player.color}         ██         {x8}│{x9}                                    {x8} │                                   {x8}  │  
{player.color}         ██         {x8}│{xe}  Your inventory has an unlimited   {x8} │  {xlyellow}{bold}[E]{reset}{xe} 🧩 View all fragments        {x8}  │
{player.color}         ██         {x8}│{xe}  capacity - store as many things as {x8}│                                   {x8}  │    
{player.color}       ██  ██       {x8}│{xe}  you need! Now, select an option:  {x8} │  {xc}{bold}[{bind.back.upper()}] {reset}🏡 {xlred}{italic}<- Return to your house{x8}{x8}     │ 
{player.color}     ██      ██     {x8}│{x9}                                    {x8} │                                     │              
{player.color}                    {x8}╰{x8}────────────────────────────────────{x8}─┴─────────────────────────────────────╯   
    """)
    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            sound("map_switch3")
            game.goto = house
            return
        if k.lower() == "1":
            game.sel = "Weapons"
            game.goto = inventory_prep
            return
        if k.lower() == "2":
            game.sel = "Bodywear"
            game.goto = inventory_prep
            return
        if k.lower() == "3":
            game.sel = "Helmets"
            game.goto = inventory_prep
            return
        if k.lower() == "e":
            game.sel = "Fragments"
            game.goto = inventory_prep
            return

def get_ability(iname):
    if setting.simplify_tutorials:
        if not iname:
            return "No item ability."
        if iname.lower() == "krita user manual":
            return "Hits add permanent dizziness. The effect stacks."
        if iname.lower() == "befriend a shark in 30 days":
            return "A shark attacks after you. It cannot be killed."
        return "No ability available for this item."
    if not iname:
        return f"{xlyellow}{bold}No ability{reset} is associated with this item."
    if iname.lower() == "Krita User Manual".lower():
        return f"Hitting an enemy makes it panic about color theory → it gets {xlyellow}{bold}dizzy {reset}permanently (stackable)."
    elif iname.lower() == "Befriend a Shark in 30 Days".lower():
        return f"A cute shark will attack after you do! He's considered a {xlyellow}{bold}phantom {reset} and so can't be killed."
    else:
        return f"{xlyellow}{bold}No ability{reset} is associated with this item yet. Hold tight for more info in a later update!"


def draw_equipment_title_bar():
    boxwidth = 25
    playername = read("General/playername", default="Player")
    playernamd = f"{playername} › Equipment "
    length = visible_len(playernamd)
    pad = (boxwidth - length) // 2 + 1
    spaces = " " * max(pad, 0)
    centered = spaces + playernamd
    print(f"""
[1;1H{reset}
[2;17H#3{x7}╭───────────────────────────╮
[3;17H#4{x7}╭───────────────────────────╮
[4;17H#3{x7}│ {xf}{bold}{centered}       {reset}
[5;17H#4{x7}│ {xf}{bold}{centered}       {reset}
[6;17H#3{x7}╰───────────────────────────╯
[7;17H#4{x7}╰───────────────────────────╯
[4;45H#3{x7}│ {reset}{x7}{bold}{reset}
[5;45H#4{x7}│ {reset}{x7}{bold}{reset}
""".strip().replace("\n", ""), end="", flush=True)


def equipped_fragment_summary_lines():
    slot_lines = []
    for slot in FRAGMENT_SLOTS:
        equipped_fragment = FRAGMENT_EQUIPPED_OBJECTS[slot]
        if getattr(equipped_fragment, "name", None):
            slot_lines.append(
                f"{slot}: {equipped_fragment.name} "
                f"(Lv {equipped_fragment.level})"
            )
        else:
            slot_lines.append(f"{slot}: Empty")
    bonuses = get_fragment_bonuses()
    set_lines = [
        f"{label}: {effect}"
        for label, effect in bonuses["active_set_details"]
    ]
    if not set_lines:
        set_lines = ["No active set bonuses"]
    return slot_lines, set_lines


def character2():
    if getattr(item, "rarity", None) == "08":
        rarity_indicator = f"{reset}{x7}★ {xf}Common"
    elif getattr(item, "rarity", None) == "02":
        rarity_indicator = f"{reset}{xa}★★ {xf}Rare"
    elif getattr(item, "rarity", None) == "03":
        rarity_indicator = f"{reset}{xb}★★★ {xf}Special"
    elif getattr(item, "rarity", None) == "0d":
        rarity_indicator = f"{reset}{xd}★★★★ {xf}Legendary"
    else:
        rarity_indicator = f"{reset}{xe}★★★★★ {xf}Divine"

    draw_equipment_title_bar()
    print(background_blocks(f"""
[08;3H{xf}{bold}╭────────────────────────────────────╮{reset}
[09;3H{xf}{bold}│                                    │{reset}
[10;3H{xf}{bold}│ {player.color}   ██████                        {xf}  │{reset}
[11;3H{xf}{bold}│ {player.color} ██      ██                      {xf}  │{reset}
[12;3H{xf}{bold}│ {player.color} ██ •  • ██                      {xf}  │{reset}
[13;3H{xf}{bold}│ {player.color} ██      ██                      {xf}  │{reset}
[14;3H{xf}{bold}│ {player.color}   ██████                        {xf}  │{reset}
[15;3H{xf}{bold}│ {player.color}     ██                          {xf}  │{reset}
[16;3H{xf}{bold}│ {player.color}     ██    ██                    {xf}  │{reset}
[17;3H{xf}{bold}│ {player.color}     ██  ██                      {xf}  │{reset}
[18;3H{xf}{bold}│ {player.color}  ███████                        {xf}  │{reset}
[19;3H{xf}{bold}│ {player.color}██   ██                          {xf}  │{reset}
[20;3H{xf}{bold}│ {player.color}     ██                          {xf}  │{reset}
[21;3H{xf}{bold}│ {player.color}     ██                          {xf}  │{reset}
[22;3H{xf}{bold}│ {player.color}   ██  ██                        {xf}  │{reset}
[23;3H{xf}{bold}│ {player.color} ██      ██                      {xf}  │{reset}
[24;3H{xf}{bold}│                                    │{reset}
[25;3H{xf}{bold}╰────────────────────────────────────╯{reset}
[26;3H{x7}{bold}╭────────────────────────────────────╮
[27;3H{x7}{bold}│ {reset}{xf}📊 {xlyellow}{bold}[1] {reset}{xf}-{xe} Attributes               {xf}{x7}{bold} │
[28;3H{x7}{bold}│                                    │
[29;3H{x7}{bold}│ {reset}{xf}✅ {rgb(197, 229, 200)}{bold}[2]{reset}{xe} {xf}-{xa} Equipment & fragments     {x7}{bold}│
[30;3H{x7}{bold}│                                    │{reset}
[31;3H{x7}{bold}│ {reset}{xf}{d.classicon} {xlyellow}{bold}[3]{reset}{xe} {xf}-{xe} Classes & skill tree      {x7}{bold}│
[32;3H{x7}{bold}│                                    │
[33;3H{x7}{bold}│ {reset}{xf}🎨 {xlyellow}{bold}[4]{reset}{xe} {xf}-{xe} Character personalization {x7}{bold}│
[34;3H{x7}{bold}│                                    │
[35;3H{x7}{bold}│ {reset}{xf}🔢 {xlyellow}{bold}[5] {reset}{xe}{xf}-{xe} Lifetime stats{reset}{x7}{bold}            │

[08;42H{xf}{bold}{RGB}255;219;187m╭───────────────────────────────────────╮ {RGB}186;243;219m╭─────────────────────────────────────────╮
[09;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[10;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[11;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[12;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[13;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[14;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[15;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[16;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[17;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[18;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[19;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[20;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[21;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[22;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[23;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[24;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[25;42H{xf}{bold}{RGB}255;219;187m╰───────────────────────────────────────╯ {RGB}186;243;219m╰─────────────────────────────────────────╯
[08;43H{RGB}255;219;187m{bold}┤ {item.type} {item.name if item.name is not None else "Weapon"} ├
[08;85H{RGB}186;243;219m{bold}┤ 🧩 Fragments ├
[26;42H{RGB}173;216;225m╭───────────────────────────────────────╮ {RGB}255;203;204m╭─────────────────────────────────────────╮
[27;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[28;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[29;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[30;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[31;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[32;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[33;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[34;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[35;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[26;43H{RGB}173;216;225m{bold}┤ 🪖 {head.name if head.name is not None else "Head"} ├
[26;85H{RGB}255;203;204m{bold}┤ 👘 {armor.name if armor.name is not None else "Armor"} ├
[36;42H{RGB}173;216;225m╰───────────────────────────────────────╯ {RGB}255;203;204m╰─────────────────────────────────────────╯
[36;3H{x7}╰────────────────────────────────────╯{reset}


[10;45H{reset}☆ 
[10;47H{RGB}255;219;187mRarity: {x8}{xlyellow}{bold}{rarity_indicator}{reset}

[11;45H{reset}⇝ 
[11;47H{RGB}255;219;187m{italic}"{item.description}"{reset}

[13;45H{reset}⇲ 
[13;47H{RGB}255;219;187mBase ATK{x8}-------------{xlyellow}{bold}{item.atk}{reset}
[14;45H{reset}𐫰 
[14;47H{RGB}255;219;187mCrit DMG{x8}-------------{xlyellow}{bold}{item.atkcrit}%{reset}
[15;45H{reset}🟃 
[15;47H{RGB}255;219;187mSubstat{x8}--------------{xlyellow}{bold}{item.substat_value}{"% Regen" if item.substat == "Regeneration" else f" {item.substat}"}{reset}

[17;45H{reset}⌬ 
[17;47H{RGB}255;219;187mLevel{x8}----------------{xlyellow}{bold}{item.level}{reset}{RGB}255;219;187m/{max(1,player.level//4)}{reset}
[18;45H{reset}♆ 
[18;47H{RGB}255;219;187mLevel Power{x8}----------{xlyellow}{bold}{100*item.level_power}×{reset}
[19;45H{reset}♅ 
[19;47H{RGB}255;219;187mRefinement{x8}-----------{xlyellow}{bold}Tier {item.refine}{reset}{RGB}255;219;187m/3{reset}

[10;87H{reset}⌬ 
[10;89H{RGB}186;243;219mSkill Lv.{x8}-----{xa}{bold}woo!{reset}


[28;45H{reset}◇ 
[28;47H{RGB}173;216;225mBase DEF{x8}------{xb}{bold}again{reset}

[28;87H{reset}↺ 
[28;89H{RGB}255;203;204mRegeneration{x8}----{xlred}{bold}random text{reset}




""").strip().replace("\n",""),end="",flush=True)
    slot_lines, set_lines = equipped_fragment_summary_lines()
    for row, text in zip((10, 12, 14), slot_lines):
        print(f"\033[{row};87H{reset}{RGB}186;243;219m{text[:38]:<38}{reset}")
    for row, text in enumerate(set_lines[:2], start=17):
        print(f"\033[{row};87H{reset}{x7}{text[:38]:<38}{reset}")
    full_ability = get_ability(getattr(item, "name", None))
    draw_box_text(f"→ {full_ability}", 21,45, 23,79)
    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            sound("map_switch3")
            game.goto = house
            return
        if k.lower() == bind.back or k.lower() == "1":
            d.character_view = 1
            sound("map_switch3")
            game.goto = character
            return
        if k.lower() == bind.back or k.lower() == "3":
            d.character_view = 3
            sound("map_switch2")
            game.goto = character
            return

def character3():
    boxwidth = 25
    playername=read("General/playername")
    playernamd = f"{playername} › Abilities "
    length = visible_len(playernamd)
    pad = (boxwidth - length) // 2 + 1
    spaces = " " * max(pad, 0)
    centered = spaces + playernamd
    number = 1
    print(background_blocks(f"""
[1;{number}H{reset}
[2;17H#3{x7}╭───────────────────────────╮
[3;17H#4{x7}╭───────────────────────────╮
[4;17H#3{x7}│ {xf}{bold}{centered}       {reset}
[5;17H#4{x7}│ {xf}{bold}{centered}       {reset}
[6;17H#3{x7}╰───────────────────────────╯
[7;17H#4{x7}╰───────────────────────────╯
[4;45H#3{x7}│ {reset}{x7}{bold}{reset}
[5;45H#4{x7}│ {reset}{x7}{bold}{reset}
[08;3H{xf}{bold}╭────────────────────────────────────╮{reset}
[09;3H{xf}{bold}│                                    │{reset}
[10;3H{xf}{bold}│ {player.color}   ██████                        {xf}  │{reset}
[11;3H{xf}{bold}│ {player.color} ██      ██                      {xf}  │{reset}
[12;3H{xf}{bold}│ {player.color} ██ •  • ██                      {xf}  │{reset}
[13;3H{xf}{bold}│ {player.color} ██      ██                      {xf}  │{reset}
[14;3H{xf}{bold}│ {player.color}   ██████                        {xf}  │{reset}
[15;3H{xf}{bold}│ {player.color}     ██                          {xf}  │{reset}
[16;3H{xf}{bold}│ {player.color}     ██    ██                    {xf}  │{reset}
[17;3H{xf}{bold}│ {player.color}     ██  ██                      {xf}  │{reset}
[18;3H{xf}{bold}│ {player.color}  ███████                        {xf}  │{reset}
[19;3H{xf}{bold}│ {player.color}██   ██                          {xf}  │{reset}
[20;3H{xf}{bold}│ {player.color}     ██                          {xf}  │{reset}
[21;3H{xf}{bold}│ {player.color}     ██                          {xf}  │{reset}
[22;3H{xf}{bold}│ {player.color}   ██  ██                        {xf}  │{reset}
[23;3H{xf}{bold}│ {player.color} ██      ██                      {xf}  │{reset}
[24;3H{xf}{bold}│                                    │{reset}
[25;3H{xf}{bold}╰────────────────────────────────────╯{reset}
[26;3H{x7}{bold}╭────────────────────────────────────╮
[27;3H{x7}{bold}│ {reset}{xf}📊 {xlyellow}{bold}[1] {reset}{xf}-{xe} Attributes               {xf}{x7}{bold} │
[28;3H{x7}{bold}│                                    │
[29;3H{x7}{bold}│ {reset}{xf}{item.type} {xlyellow}{bold}[2]{reset}{xe} {xf}-{xe} Equipment & fragments     {x7}{bold}│
[30;3H{x7}{bold}│                                    │{reset}
[31;3H{x7}{bold}│ {reset}{xf}✅ {rgb(197, 229, 200)}{bold}[3]{reset}{xe} {xf}-{xa} Classes & skill tree      {x7}{bold}│
[32;3H{x7}{bold}│                                    │
[33;3H{x7}{bold}│ {reset}{xf}🎨 {xlyellow}{bold}[4]{reset}{xe} {xf}-{xe} Character personalization {x7}{bold}│
[34;3H{x7}{bold}│                                    │
[35;3H{x7}{bold}│ {reset}{xf}🔢 {xlyellow}{bold}[5] {reset}{xe}{xf}-{xe} Lifetime stats{reset}{x7}{bold}            │

[08;42H{xf}{bold}{RGB}255;219;187m╭───────────────────────────────────────╮ {RGB}186;243;219m╭─────────────────────────────────────────╮
[09;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[10;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[11;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[12;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[13;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[14;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[15;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[16;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[17;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[18;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[19;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[20;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[21;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[22;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[23;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[24;42H{xf}{bold}{RGB}255;219;187m│                                       │ {RGB}186;243;219m│                                         │
[25;42H{xf}{bold}{RGB}255;219;187m╰───────────────────────────────────────╯ {RGB}186;243;219m╰─────────────────────────────────────────╯
[08;43H{RGB}255;219;187m{bold}┤ {item.type} Main Attack - {player.main_name if player.main_name is not None else "Unnamed"} ├
[08;85H{RGB}186;243;219m{bold}┤ ⚒️ Skill Mastery ├
[26;42H{RGB}173;216;225m╭───────────────────────────────────────╮ {RGB}255;203;204m╭─────────────────────────────────────────╮
[27;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[28;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[29;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[30;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[31;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[32;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[33;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[34;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[35;42H{RGB}173;216;225m│                                       │ {RGB}255;203;204m│                                         │
[26;43H{RGB}173;216;225m{bold}┤ 💥 Skill - {player.skill_name if player.skill_name is not None else "Unnamed"} ├
[26;85H{RGB}255;203;204m{bold}┤ 🔥 Ultimate - {player.ult_name if player.ult_name is not None else "Unnamed"} ├
[36;42H{RGB}173;216;225m╰───────────────────────────────────────╯ {RGB}255;203;204m╰─────────────────────────────────────────╯
[36;3H{x7}╰────────────────────────────────────╯{reset}
""").strip().replace("\n",""),end="",flush=True)
    

    if player.playerclass.lower() == "warrior":
        pass
    
    
    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            sound("map_switch3")
            game.goto = house
            return
        if k.lower() == bind.back or k.lower() == "1":
            d.character_view = 1
            sound("map_switch3")
            game.goto = character
            return
        if k.lower() == bind.back or k.lower() == "2":
            d.character_view = 2
            sound("map_switch3")
            game.goto = character
            return










def screensetup():
    cls()
    if setting.simplify_tutorials:
        print(f"{xb}{bold}Check your screen{reset}")
        print("Use a terminal at least 128 columns wide and 36 rows tall.")
        print("Maximize the window or make the font smaller if the game does not fit.")
        print("Wait two seconds after resizing, then check again.")
        print(f"{xf}Press Y to continue.{reset}")
        if key().lower() == "y":
            write_file("General/screensetup.txt", "okay")
            game.goto = startup
        else:
            game.goto = screensetup
        return
    print(f"""
[01;1H{xa}██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████
[02;1H{xa}██                                                                                                                          ██
[03;1H{xa}██  {xb}{bold}--- DISPLAY AREA TESTING ---{reset}               {xa}                                                                             ██
[04;1H{xa}██  {x3}The entire area of the box must fit your window          {xa}                                                               ██
[05;1H{xa}██  {x3}for the game to display things properly.                 {xa}                                                               ██
[06;1H{xa}██  {xf}                                                         {xa}                                                               ██
[07;1H{xa}██  {xf}If the outer box is not displayed well, please:          {xa}                                                               ██
[08;1H{xa}██  {xf}   1. maximise the window of your terminal;              {xa}                                                               ██
[09;1H{xa}██  {xf}   2. if needed, adjust the zoom level with Ctrl+scroll; {xa}                                                               ██
[10;1H{xa}██  {xf}                                                         {xa}                                                               ██
[11;1H{xa}██  {xf}For the best viewing experience, please follow the       {xa}                                                               ██
[12;1H{xa}██  {xf}recommendations found in the readme file.                {xa}                                                               ██
[13;1H{xa}██  {xf}                                                         {xa}                                                               ██
[14;1H{xa}██  {x2}If you see the entire box well, press Y to continue.     {xa}                                                               ██
[15;1H{xa}██                                                                                                                          ██
[16;1H{xa}██  {bold}{xc}Wait one or two seconds after zooming to let the game redraw the UI!{reset}{xa}                                                    ██
[17;1H{xa}██                                                                                                                          ██
[18;1H{xa}██                                                                                                                          ██
[19;1H{xa}██                                                                                                                          ██
[20;1H{xa}██                                                                                                                          ██
[21;1H{xa}██                                                                                                                          ██
[22;1H{xa}██                                                                                                                          ██
[23;1H{xa}██                                                                                                                          ██
[24;1H{xa}██                                                                                                                          ██
[25;1H{xa}██                                                                                                                          ██
[26;1H{xa}██                                                                                                                          ██
[27;1H{xa}██                                                                                                                          ██
[28;1H{xa}██                                                                                                                          ██
[29;1H{xa}██                                                                                                                          ██
[30;1H{xa}██                                                                                                                          ██
[31;1H{xa}██                                                                                                                          ██
[32;1H{xa}██                                                                                                                          ██
[33;1H{xa}██                                                                                                                          ██
[34;1H{xa}██                                                                                                                          ██
[35;1H{xa}██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████[01;1H
    """.strip().replace("\n",""),end="",flush=True)
    while True:
        k = key(timeout=1)
        if k.lower() == "y":
            # create screensetup.txt with contents "okay"
            with open("General/screensetup.txt", "w") as f:
                f.write("okay")
            game.goto = startup
            return
        else:
            game.goto = screensetup
            return

def first_time_setup():
    cls()
    print(f"""
[10;1H
{x6}                                                       
{x6}           ████████████                ████████████                  ██████████████                  ██████████████    
{x6}         ██            ██            ██            ██              ██              ██              ██              ██  
{x6}       ██                ████████████                ██████████████                  ██████████████                  ██


{xe}                                       ██    ██    ████    ██  ██            ██
{xe}                                       ██    ██  ██    ██  ██  ██    ████    ██
{xe}                                       ████████  ██████    ██  ██  ██    ██  ██
{xe}                                       ██    ██  ██        ██  ██  ██    ██  
{xe}                                       ██    ██    █████   ██  ██    ████    ██


{x6}       ██                ████████████                ██████████████                  ██████████████                  ██
{x6}         ██            ██            ██            ██              ██              ██              ██              ██  
{x6}           ████████████                ████████████                  ██████████████                  ██████████████    
""".strip(),end="",flush=True)
    setup_prompt = simple_text("press A on your keyboard to start setup", "Press A to choose your name")
    center(f"{xlorange}🔸 {setup_prompt} 🔸",row=29)
    while True:
        k = key()
        if k.lower() == "a":
            break
    # Time for the name input:
    cls()
    sound("map_right")
    print(f"""
{reset}

{xe}                                              (\\ 
{xe}                                              \\'\\ 
{xe}                                               \\'\\     __________  
{xe}                                               / '|   ()_________)
{xe}                                               \\ '/    \\ ~~~~~~~~ \\
{xe}                                                 \\       \\ ~~~~~~   \\
{xe}                                                 ==).      \\__________\\
{xe}                                                (__)       ()__________)

 #3{xlyellow}                ╭─────────────────────────╮
 #4{xlyellow}                ╭─────────────────────────╮
 #3{xlyellow}                │ {bold}{xf}   What's your name?   {reset}{xlyellow} │
 #4{xlyellow}                │ {bold}{xf}   What's your name?   {reset}{xlyellow} │
 #3{xlyellow}                ╰─────────────────────────╯
 #4{xlyellow}                ╰─────────────────────────╯

                  {xlorange}{simple_text("Change the course of history! Enter what you'd want to be called, then hit", "Type the name you want to use. Press")} {bold}Enter {reset}{xlorange}to confirm.
                 {xlorange}⚠️ Your new name must be between {bold}{xlred}2 and 15 {reset}{xlorange}{simple_text("characters. Try not to become the next Picasso here!", "characters.")}

                                {x7}╭┤ {xb}Enter your new name here...{x7} ├─────────────────────╮
                                {x7}│ {xb}{bold}› {x7}                                                 │
                                {x7}╰────────────────────────────────────────────────────╯{reset}
""".strip(),end="",flush=True)
    while True:
        player.name = getx(23,35,f"{xb}{bold}› {xf}{bold}",max_len=15).strip()
        if 2 <= len(player.name) <= 15:
            break
        flash_prompt(23,35,f"{xb}{bold}› {xf}{bold}")
    # save player name into settings (General/playername.txt)
    with open("General/playername.txt", "w", encoding="utf-8") as f:
        f.write(player.name)
    # setup confirmed! write into setup
    with open("General/setup.txt", "w") as f:
        f.write("okay")
    sound("payment_success")
    # wipe screen with animation (using Scripts/wipe.py)
    screen_wipe("normal", 20)
    game.goto = startup
    return

def noitems():
    cls()
    cursor(False)
    print()

    category_title = inv_category_title(game.sel)

    # top symbols for stuff
    if game.sel in ("Bodywear", "Helmets"):
        print("                                                      \033[38;5;4m██████████████        ")
        print("                                                      \033[38;5;4m██\033[38;5;6m██████████\033[38;5;4m██")
        print("                                                      \033[38;5;4m██\033[38;5;6m██████████\033[38;5;4m██")
        print("                                                      \033[38;5;4m ██\033[38;5;6m████████\033[38;5;4m██ ")
        print("                                                       \033[38;5;4m ██\033[38;5;6m██████\033[38;5;4m██  ")
        print("                                                         \033[38;5;4m ██\033[38;5;6m██\033[38;5;4m██    ")
        print("                                                            \033[38;5;4m██              ")
    elif game.sel == "Weapons":
        atksymbol1=f"{x6}██████{xlyellow}"
        atksymbol2=f"{x6}██{xlyellow}██{xe}██{xlyellow}██{x6}██{xlyellow}"
        atksymbol3=f"{x6}██{xlyellow}██████{xe}██{xlyellow}██{x6}██{xlyellow}"
        atksymbol4=f"{x6}██{xlyellow}{xe}██████████{xlyellow}{x6}██{xlyellow}"
        atksymbol5=f"{x6}██{xlyellow}██████{xe}██{xlyellow}██{x6}██{xlyellow}"
        atksymbol6=f"{x6}██{xlyellow}██{xe}██{xlyellow}██{x6}██{xlyellow}"
        atksymbol7=f"{x6}██████{xlyellow}"
        print(f"                                                          \033[38;2;2;74;48m{atksymbol1}")
        print(f"                                                        \033[38;2;2;74;48m{atksymbol2}")
        print(f"                                                      \033[38;2;2;74;48m{atksymbol3}")
        print(f"                                                      \033[38;2;2;74;48m{atksymbol4}")
        print(f"                                                      \033[38;2;2;74;48m{atksymbol5}")
        print(f"                                                        \033[38;2;2;74;48m{atksymbol6}")
        print(f"                                                          \033[38;2;2;74;48m{atksymbol7}")
    else:
        for _ in range(7):
            print()

    print(f"\033#3{reset}                  {xlorange}╭───────────────────────{xlorange}╮")
    print(f"\033#4                  {xlorange}╭───────────────────────{xlorange}╮")
    print(f"\033#3                  {xlorange}│        {bold}{xlyellow}{category_title}        {xlorange}│")
    print(f"\033#4                  {xlorange}│        {bold}{xlyellow}{category_title}        {xlorange}│")
    print(f"\033#3                  {xlorange}╰───────────────────────{xlorange}╯")
    print(f"\033#4                  {xlorange}╰───────────────────────{xlorange}╯")

    print(f"{x8}",end="")
    print(f"{player.color}               {x8} ╭───────────────────────────────────────────┬─────────────────────────────────────────────────╮")
    print(f"{player.color}               {x8} │                                           │                                                 │")
    print(f"{player.color}      ██████   {x8} ├───────────────────────────────────────────┼─────────────────────────────────────────────────┤")
    print(f"{player.color}    ██      ██ {x8} │                                           │                                                 │")
    print(f"{player.color}    ██ •  • ██ {x8} │                                           │                                                 │")
    print(f"{player.color}    ██      ██ {x8} │                                           │                                                 │")
    print(f"{player.color}      ██████   {x8} │                                           │                                                 │")
    print(f"{player.color}        ██  ██ {x8} │                                           │                                                 │")
    print(f"{player.color}  ██    ██   ██{x8} │                                           │                                                 │")
    print(f"{player.color}    ██  ██  ██ {x8} │                                           │                                                 │")
    print(f"{player.color}      ██████   {x8} │                                           │                                                 │")
    print(f"{player.color}        ██     {x8} │                                           │                                                 │")
    print(f"{player.color}        ██     {x8} │                                           │                                                 │")
    print(f"{player.color}        ██     {x8} │                                           │                                                 │")
    print(f"{player.color}      ██  ██   {x8} │                                           │                                                 │")
    print(f"{player.color}    ██      ██ {x8} ├───────────────────────────────────────────┼─────────────────────────────────────────────────┤")
    print(f"{player.color}               {x8} │                                           │                                                 │")
    print(f"{player.color}               {x8} ╰───────────────────────────────────────────┴─────────────────────────────────────────────────╯\033[0m")

    print(f"{reset}\033[16;19H🔱 {bold}{xlorange}{category_title} {xlyellow}{unbold}→ {xlorange}{bold}Empty {x7}(items: {xf}{bold}0{x7}{unbold}){reset}")
    print(f"\033[23;26H{x8}{x7}— {xlyellow}No items in this category. {x7}—{reset}")
    print(f"\033[31;19H{xlorange}Go back → {xlyellow}{bold}{bind.back.upper()} {reset}{xlorange}or {xlyellow}{bold}ESC{reset}")

    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            game.goto = inventory
            return

def startup():
    # check if <cd>/General/screensetup.txt exists
    if not os.path.exists("General/screensetup.txt"):
        game.goto = screensetup
        return
    # check if <cd>/General/setup.txt exists
    if not os.path.exists("General/setup.txt"):
        game.goto = first_time_setup
        return
    sound(random.choice(["music_default"]))
    game.goto = (
        mainmenu
        if setting.effective_setting("disable_startup_animation")
        else startup_animation
    )
    return


INVENTORY_RARITY_STYLES = {
    "08": (xf, (255, 255, 255)),
    "02": (xa, (70, 198, 107)),
    "03": (xb, (122, 195, 230)),
    "0d": (xd, (214, 138, 230)),
    "0e": (xe, (240, 232, 158)),
}


def inv_category_title(category):
    return {
        "Weapons": "Weapons",
        "Bodywear": " Armor ",
        "Helmets": "Helmets",
        "Fragments": "Fragments",
    }.get(category, str(category))


def inv_item_label(category):
    return {
        "Weapons": "weapon",
        "Bodywear": "armour",
        "Helmets": "helmet",
        "Fragments": "fragment",
    }.get(category, "item")


def inv_active_path(category, item_obj=None):
    if category == "Fragments":
        return fragment_slot_path(getattr(item_obj, "slot", None))
    return {
        "Weapons": "Items/active_weapon",
        "Bodywear": "Items/active_body",
        "Helmets": "Items/active_head",
    }.get(category)


def inv_active_paths(category):
    if category == "Fragments":
        return [fragment_slot_path(slot) for slot in FRAGMENT_SLOTS]
    path = inv_active_path(category)
    return [path] if path else []


def inv_item_number_marker(category, item_id, item_obj):
    # show a checkmark for equipped fragments
    if category == "Fragments":
        equipped_path = inv_active_path(category, item_obj)
        equipped_id = read(equipped_path, default="none") if equipped_path else "none"
        if str(item_id) == str(equipped_id).strip():
            return "✓"
    return "›"


def inv_type_icon(item_obj):
    type_raw = getattr(item_obj, "type_raw", None)
    fragment_icons = {
        "bracelet": "📿",
        "necklace": "🔗",
        "ring": "💍",
    }
    if type_raw in fragment_icons:
        return fragment_icons[type_raw]
    type_map = {
        None: "❌",
        "None": "❌",
        "bow": "🏹",
        "sword": "⚔️",
        "knife": "🔪",
        "dagger": "🗡️",
        "helmet": "⛑️",
        "bodywear": "👗",
        "book": "📖",
        "wand": "🪄",
        "axe": "🪓",
        "hammer": "⚒️",
        "pistol": "🔫",
        "flower": "🌹",
    }
    if type_raw in (None, "", "None"):
        return "❌"
    return type_map.get(type_raw, type_raw)


INVENTORY_COMPARISON_CATEGORIES = {"Weapons", "Bodywear", "Helmets"}


def inv_category_supports_comparison(category):
    return category in INVENTORY_COMPARISON_CATEGORIES


def inv_compare_value(item_obj, category):
    if not inv_category_supports_comparison(category):
        raise ValueError(f"{category} items do not support comparison.")
    if category == "Weapons":
        final_atk = get_actual_atk(item_obj)
        fragment_bonuses = get_fragment_bonuses()
        crit_bonus = (float(getattr(item_obj, "atkcrit", 0)) + fragment_bonuses["crit_damage"]) / 100
        crit_rate = 15 + (int(player.level) // 10)
        if getattr(item_obj, "substat", None) == "Crit Rate":
            crit_rate += item_obj.substat_value
        crit_rate += fragment_bonuses["crit_rate"]
        crit_rate = max(0, min(100, crit_rate)) / 100
        metric = setting.weapon_comparison_metric
        if metric == "Normal damage":
            return float(final_atk)
        if metric == "Critical damage":
            return float(final_atk) * (1 + crit_bonus)
        return float(final_atk) * (1 + crit_rate * crit_bonus)
    return float(get_actual_defense(item_obj))


def equipped_item_comparison(item_id, category):
    if not setting.compare_equipped_item or not inv_category_supports_comparison(category):
        return ""
    selected = load_item(item_id, category)
    if selected is None:
        return ""
    selected = copy(selected)
    path = inv_active_path(category, selected)
    equipped_id = str(read(path, default="none")).strip() if path else "none"
    if equipped_id == str(item_id):
        return "Currently equipped"
    if not equipped_id.isdigit() or int(equipped_id) <= 0:
        return "No equipped item to compare"
    try:
        selected_value = inv_compare_value(selected, category)
        try:
            equipped = load_item(int(equipped_id), category)
        except (FileNotFoundError, UnicodeError, ValueError, IndexError):
            return "No equipped item to compare"
        if equipped is None:
            return "No equipped item to compare"
        difference = selected_value - inv_compare_value(equipped, category)
        metric = setting.weapon_comparison_metric if category == "Weapons" else "Defense"
        unit = " percentage points" if category != "Weapons" else ""
        sign = "+" if difference > 0 else ""
        return f"{metric}: {sign}{format_number(difference)}{unit} vs equipped"
    finally:
        load_item(item_id, category)


def item_level_display(item_obj, category):
    level = clamp_item_level(getattr(item_obj, "level", 0), category)
    max_level = get_item_max_level(category)
    if max_level is None:
        return str(level)
    return f"{level}/{max_level}"


ITEM_RARITY_VALUES = {
    "08": (100, 50, 1),
    "02": (150, 200, 3),
    "03": (250, 350, 5),
    "0d": (350, 450, 12),
    "0e": (750, 500, 24),
}

ITEM_UPGRADE_BASE_COSTS = {
    "08": 25,
    "02": 40,
    "03": 60,
    "0d": 85,
    "0e": 120,
}


def round_upgrade_price(price):
    price = max(0, round(price))
    if price > 5000:
        return round(price, -2)
    if price > 100:
        return round(price, -1)
    return price


def item_upgrade_cost_for_level(item_obj, target_level, category=None):
    # price for upgrading to this level
    if category == "Fragments" or hasattr(item_obj, "slot"):
        level = max(1, int(target_level))
        return max(1, round(8 * (1.22 ** (level - 1))))
    base_cost = ITEM_UPGRADE_BASE_COSTS.get(
        getattr(item_obj, "rarity", None), 25
    )
    level = max(1, int(target_level))
    return max(1, round_upgrade_price(base_cost * (1.14 ** (level - 1))))


def item_upgrade_cost(item_obj, category, levels):
    current_level = clamp_item_level(getattr(item_obj, "level", 0), category)
    max_level = get_item_max_level(category)
    if max_level is None:
        return 0

    target_level = min(max_level, current_level + max(0, int(levels)))
    # add the price for each level
    total_cost = 0
    for level in range(current_level + 1, target_level + 1):
        total_cost += item_upgrade_cost_for_level(item_obj, level, category)
    return round_upgrade_price(total_cost)


def max_item_level_for_player(category, player_level):
    max_level = get_item_max_level(category)
    if max_level is None:
        return 0

    usable_level = 1
    for level in range(2, max_level + 1):
        if required_player_level_for_item(level, category) > int(player_level):
            break
        usable_level = level
    return usable_level


def max_affordable_upgrade_levels(item_obj, category, max_levels, gold):
    affordable_levels = 0
    for levels in range(1, max(0, int(max_levels)) + 1):
        if item_upgrade_cost(item_obj, category, levels) > gold:
            break
        affordable_levels = levels
    return affordable_levels


def apply_item_upgrade(item_obj, category, levels):
    # check the upgrade first, then spend the currency
    current_level = clamp_item_level(getattr(item_obj, "level", 0), category)
    max_level = get_item_max_level(category)
    if max_level is None:
        return False, 0

    requested_levels = max(0, int(levels))
    usable_level = min(
        max_level,
        max_item_level_for_player(category, player.level),
    )
    target_level = min(max_level, current_level + requested_levels)
    total_cost = item_upgrade_cost(item_obj, category, requested_levels)
    # fragments use dust, other equipment uses gold
    if category == "Fragments":
        currency_attr = "dust"
    else:
        currency_attr = "money"
    currency = getattr(player, currency_attr, 0)
    if (
        requested_levels <= 0
        or target_level > usable_level
        or target_level - current_level != requested_levels
        or currency < total_cost
    ):
        return False, total_cost

    if category == "Fragments":
        # roll new substats only after the upgrade checks passed
        apply_fragment_substats(item_obj, target_level)
    setattr(player, currency_attr, currency - total_cost)
    item_obj.level = target_level
    return True, total_cost


def weapon_refinement_cost(item_obj, target_stage):
    # gold needed for this refinement stage (starts at 1)
    target_stage = max(1, min(WEAPON_REFINEMENT_MAX, int(target_stage)))
    level_25_cost = item_upgrade_cost_for_level(
        item_obj,
        WEAPON_MAX_LEVEL,
        "Weapons",
    )
    return round_upgrade_price(level_25_cost * (1.5 + target_stage * 0.75))


def weapon_refinement_preview(item_obj):
    # calculate the next refinement without changing the weapon yet
    current_stage = max(0, int(getattr(item_obj, "refine", 0)))
    target_stage = min(WEAPON_REFINEMENT_MAX, current_stage + 1)
    at_max = current_stage >= WEAPON_REFINEMENT_MAX
    target_base_atk = int(getattr(item_obj, "atk", 0))
    if not at_max:
        target_base_atk = max(
            target_base_atk + 1,
            round(target_base_atk * (1 + WEAPON_REFINEMENT_ATK_RATE)),
        )
    # apply the weapon's level scaling to the new base atk
    level_power = float(getattr(item_obj, "level_power", 0))
    weapon_level = int(getattr(item_obj, "level", WEAPON_MAX_LEVEL))
    target_actual_atk = round(target_base_atk * ((1 + level_power) ** weapon_level))

    target_crit_damage = float(getattr(item_obj, "atkcrit", 0))
    if not at_max:
        target_crit_damage += WEAPON_REFINEMENT_CRIT_DAMAGE
    # max refinement has no next upgrade cost
    if at_max:
        gold_cost = 0
        dust_cost = 0
    else:
        gold_cost = weapon_refinement_cost(item_obj, target_stage)
        dust_cost = WEAPON_REFINEMENT_DUST_BASE_COST * target_stage

    return {
        "current_stage": current_stage,
        "target_stage": target_stage,
        "target_base_atk": target_base_atk,
        "target_actual_atk": target_actual_atk,
        "target_crit_damage": target_crit_damage,
        "gold_cost": gold_cost,
        "dust_cost": dust_cost,
    }


def apply_weapon_refinement(item_obj):
    # check gold and dust before upgrading
    no_cost = {"gold": 0, "dust": 0}
    current_stage = max(0, int(getattr(item_obj, "refine", 0)))
    if (
        int(getattr(item_obj, "level", 0)) < WEAPON_MAX_LEVEL
        or current_stage >= WEAPON_REFINEMENT_MAX
    ):
        return False, no_cost

    preview = weapon_refinement_preview(item_obj)
    costs = {
        "gold": preview["gold_cost"],
        "dust": preview["dust_cost"],
    }
    if (
        getattr(player, "money", 0) < costs["gold"]
        or getattr(player, "dust", 0) < costs["dust"]
    ):
        return False, costs

    player.money -= costs["gold"]
    player.dust -= costs["dust"]
    item_obj.atk = preview["target_base_atk"]
    item_obj.atkcrit = preview["target_crit_damage"]
    item_obj.refine = preview["target_stage"]
    return True, costs


def item_stat_preview(item_obj, category, level):
    if category == "Weapons":
        return get_actual_atk(item_obj, level=level)
    if category == "Fragments":
        return scale_fragment_stat(
            item_obj.main_stat,
            get_fragment_main_stat_value(item_obj, level=level),
        )
    return get_actual_defense(item_obj, level=level)


def item_salvage_rewards(item_obj, category):
    if category == "Fragments":
        level = clamp_item_level(getattr(item_obj, "level", 1), category)
        return 0, max(2, round(level * 1.5))

    gold_multiplier, gold_bonus, dust_bonus = ITEM_RARITY_VALUES.get(
        getattr(item_obj, "rarity", None), (1, 100, 10)
    )
    level = clamp_item_level(getattr(item_obj, "level", 0), category)
    gold = round((gold_multiplier * level ** 2) / 98 + gold_bonus)

    dust_multiplier = gold_multiplier
    if category == "Weapons":
        level_power = max(0.0, float(getattr(item_obj, "level_power", 0)))
        dust = round((dust_multiplier * level * level_power) / 150 + dust_bonus)
    else:
        dust = round((dust_multiplier * level) / 150 + dust_bonus)
    if dust >= 1000:
        dust = round(dust, -1)
    return gold, dust


def draw_confirmation_progress(filled, action):
    filled = max(0, min(43, int(filled)))
    d.hold_item = filled
    if action == "upgrade":
        filled_colour = xba
        empty_colour = rgback(17, 45, 69)
    else:
        filled_colour = xbc
        empty_colour = rgback(48, 18, 18)
    xpbar = (
        f"{filled_colour}{' ' * filled}"
        f"{empty_colour}{' ' * (43 - filled)}"
    )
    print(f"\033[20;63H{xb0}  {xpbar}{xb0}  {reset}")
    print(f"\033[21;63H{xb0}  {xpbar}{xb0}  {reset}", end="", flush=True)


def hold_for_confirmation(action, duration=None, initial_confirm=False):
    # wait for holding the key or tapping it twice, depending on settings
    if duration is None:
        duration = setting.confirmation_hold_duration
    if getattr(d, "inventory_action_mode", None) != action:
        return False

    if getattr(setting, "double_tap_confirmation", False):
        taps = 1 if initial_confirm else 0
        last_filled = -1
        if taps:
            last_filled = round(43 / 2)
            draw_confirmation_progress(last_filled, action)

        while True:
            k = getx(0, 0, expect="key", timeout=0.05)
            lowered = k.lower() if isinstance(k, str) else ""

            if lowered in ("esc", bind.back.lower()):
                draw_confirmation_progress(0, action)
                return False

            if lowered in ("enter", bind.confirm.lower()):
                taps += 1
                filled = 43 if taps >= 2 else round(43 / 2)
                if filled != last_filled:
                    draw_confirmation_progress(filled, action)
                    last_filled = filled
                if taps >= 2:
                    return True
                continue

            if k == "TIMEOUT":
                continue

            taps = 0
            if last_filled != 0:
                draw_confirmation_progress(0, action)
                last_filled = 0

    started = time.monotonic() if initial_confirm else None
    last_confirm = started
    repeating = False
    last_filled = -1

    while True:
        k = getx(0, 0, expect="key", timeout=0.05)
        now = time.monotonic()
        lowered = k.lower() if isinstance(k, str) else ""

        if lowered in ("esc", bind.back.lower()):
            draw_confirmation_progress(0, action)
            return False

        if lowered in ("enter", bind.confirm.lower()):
            allowed_gap = 0.15 if repeating else 0.7
            if last_confirm is None or now - last_confirm > allowed_gap:
                started = now
                repeating = False
            elif last_confirm is not None:
                repeating = True
            last_confirm = now
            elapsed = now - started
            filled = round(43 * min(1.0, elapsed / duration))
            if filled != last_filled:
                draw_confirmation_progress(filled, action)
                last_filled = filled
            if elapsed >= duration:
                draw_confirmation_progress(43, action)
                return True
            continue

        if k == "TIMEOUT":
            allowed_gap = 0.15 if repeating else 0.7
            if last_confirm is None or now - last_confirm <= allowed_gap:
                continue

        started = None
        last_confirm = None
        repeating = False
        if last_filled != 0:
            draw_confirmation_progress(0, action)
            last_filled = 0


def draw_upgrade_menu(
    item_obj,
    category,
    levels,
    message="",
    draw_title=False,
):
    current_level = clamp_item_level(getattr(item_obj, "level", 0), category)
    max_level = get_item_max_level(category)
    target_level = min(max_level, current_level + levels)
    total_cost = item_upgrade_cost(item_obj, category, levels)
    current_stat = item_stat_preview(item_obj, category, current_level)
    target_stat = item_stat_preview(item_obj, category, target_level)
    if category == "Weapons":
        stat_name = "ATK"
    elif category == "Fragments":
        stat_name = normalize_fragment_stat(item_obj.main_stat)
    else:
        stat_name = "DEF"

    blank(18, 63, 29, 110)
    blank(31, 63, 31, 110)
    if draw_title:
        blank(16, 63, 16, 110)
        print(f"\033[16;63H{bold}↑ {xlyellow}Upgrade {item_obj.name}{reset}")

    filled = round((target_level * 43) / max_level)
    xpbar = f"{xbb}{' ' * filled}{rgback(17,45,69)}{' ' * (43 - filled)}"
    print(f"\033[19;63H{xb0}{' ' * 47}{reset}")
    print(f"\033[20;63H{xb0}  {xpbar}{xb0}  {reset}")
    print(f"\033[21;63H{xb0}  {xpbar}{xb0}  {reset}")
    print(f"\033[22;63H{xb0}{' ' * 47}{reset}")

    print(f"\033[24;63H{xf}{simple_text('Target level', 'New level')}: {x7}{current_level} {xf}→ {xlyellow}{bold}{target_level}/{max_level}{reset}")
    print(f"\033[25;63H{xf}Levels: {xlyellow}{bold}+{levels}{reset}{x7}  (+ increase / - decrease){reset}")
    if category == "Fragments":
        current_display = format_fragment_stat(stat_name, current_stat)
        target_display = format_fragment_stat(stat_name, target_stat)
        print(f"\033[27;63H{xf}Main stat: {x7}{current_display} {xf}→ {xa}{bold}{target_display}{reset}")
    else:
        print(f"\033[27;63H{xf}{stat_name}: {x7}{format_number(current_stat)} {xf}→ {xa}{bold}{format_number(target_stat)}{reset}")
    currency = player.dust if category == "Fragments" else player.money
    currency_name = "magic dust" if category == "Fragments" else "gold"
    cost_colour = xlyellow if currency >= total_cost else xlred
    print(f"\033[28;63H{xf}Cost: {cost_colour}{bold}{format_number(total_cost)} {currency_name}{reset}{x7}  (you have {format_number(currency)}){reset}")
    if category == "Fragments":
        existing_count = len(get_fragment_substats(item_obj))
        target_count = min(3, target_level // 5)
        new_substat_count = max(0, target_count - existing_count)
        if new_substat_count:
            plural = "substats" if new_substat_count != 1 else "substat"
            print(
                f"\033[29;63H{xf}{simple_text('After confirmation', 'New bonuses')}: "
                f"{xa}{bold}{new_substat_count} random {plural}{reset}"
            )
    if message:
        print(f"\033[31;63H{message}{reset}")
    else:
        confirm_action = "Confirm"
        print(f"\033[31;63H{xlorange}{confirm_action} → {xlyellow}{bold}Enter/{bind.confirm.title()} {reset}{xlorange}| Back → {xlyellow}{bold}{bind.back.title()}/Esc{reset}")


def draw_refinement_menu(item_obj, message="", draw_title=False):
    preview = weapon_refinement_preview(item_obj)
    current_stage = preview["current_stage"]
    target_stage = preview["target_stage"]
    current_atk = get_actual_atk(item_obj)
    current_crit = compact_number(getattr(item_obj, "atkcrit", 0))
    target_crit = compact_number(preview["target_crit_damage"])

    # clear above and below row 30, keep the inventory border
    blank(18, 63, 29, 110)
    blank(31, 63, 31, 110)
    if draw_title:
        blank(16, 63, 16, 110)
        print(f"\033[16;63H{bold}✦ {xd}Refine {item_obj.name}{reset}")

    filled = round((target_stage * 43) / WEAPON_REFINEMENT_MAX)
    refine_bar = (
        f"{xbd}{' ' * filled}"
        f"{rgback(54,18,49)}{' ' * (43 - filled)}"
    )
    print(f"\033[19;63H{xb0}{' ' * 47}{reset}")
    print(f"\033[20;63H{xb0}  {refine_bar}{xb0}  {reset}")
    print(f"\033[21;63H{xb0}  {refine_bar}{xb0}  {reset}")
    print(f"\033[22;63H{xb0}{' ' * 47}{reset}")

    print(
        f"\033[24;63H{xf}{simple_text('Refinement', 'Weapon boost')}: {x7}R{current_stage} {xf}→ "
        f"{xd}{bold}R{target_stage}/{WEAPON_REFINEMENT_MAX}{reset}"
    )
    print(
        f"\033[26;63H{xf}ATK: {x7}{current_atk} {xf}→ "
        f"{xd}{bold}{preview['target_actual_atk']}{reset}"
    )
    print(
        f"\033[27;63H{xf}Crit DMG: {x7}{current_crit}% {xf}→ "
        f"{xd}{bold}{target_crit}%{reset}"
    )
    gold_colour = xd if player.money >= preview["gold_cost"] else xlred
    dust_colour = xd if player.dust >= preview["dust_cost"] else xlred
    print(
        f"\033[28;63H{xf}Gold: {gold_colour}{bold}{preview['gold_cost']}"
        f"{reset}{x7}  (you have {format_number(player.money)}){reset}"
    )
    print(
        f"\033[29;63H{xf}Magic dust: {dust_colour}{bold}"
        f"{preview['dust_cost']}"
        f"{reset}{x7}  (you have {format_number(player.dust)}){reset}"
    )

    if message:
        print(f"\033[31;63H{message}{reset}")
    elif current_stage >= WEAPON_REFINEMENT_MAX:
        print(f"\033[31;63H{xd}{bold}Maximum refinement reached.{reset}")
    else:
        print(
            f"\033[31;63H{xd}Refine → {bold}Enter/{bind.confirm.title()} "
            f"{reset}{xlorange}| Back → {xlyellow}{bold}"
            f"{bind.back.title()}/Esc{reset}"
        )


def upgrade_selected_item():
    if getattr(d, "inventory_action_mode", "inventory") != "inventory":
        return False
    d.inventory_action_mode = "upgrade"
    try:
        return _upgrade_selected_item_flow()
    finally:
        d.inventory_action_mode = "inventory"


def _upgrade_selected_item_flow():
    item_obj = load_item(d.currsel, game.sel)
    max_level = get_item_max_level(game.sel)
    if not item_obj or max_level is None:
        return False

    levels = 1
    message = ""
    draw_title = True
    screen_mode = None

    while True:
        item_obj = load_item(d.currsel, game.sel)
        current_level = clamp_item_level(
            getattr(item_obj, "level", 0),
            game.sel,
        )

        if game.sel == "Weapons" and current_level >= WEAPON_MAX_LEVEL:
            if screen_mode != "refinement":
                screen_mode = "refinement"
                draw_title = True
                message = ""

            draw_refinement_menu(
                item_obj,
                message,
                draw_title=draw_title,
            )
            draw_title = False
            k = getx(0, 0, expect="key")
            lowered = k.lower() if isinstance(k, str) else ""

            if lowered in ("esc", bind.back.lower()):
                sound("map_left")
                game.preserve_offset = True
                displaynewsel()
                return False
            if lowered not in ("enter", bind.confirm.lower()):
                continue

            preview = weapon_refinement_preview(item_obj)
            if preview["current_stage"] >= WEAPON_REFINEMENT_MAX:
                message = f"{xd}Maximum refinement reached.{reset}"
                sound("error2")
                continue
            missing_costs = []
            if player.money < preview["gold_cost"]:
                missing_costs.append(
                    f"{preview['gold_cost'] - player.money} more gold"
                )
            if player.dust < preview["dust_cost"]:
                missing_costs.append(
                    f"{preview['dust_cost'] - player.dust} more magic dust"
                )
            if missing_costs:
                message = (
                    f"{xlred}🚫 You need {' and '.join(missing_costs)}.{reset}"
                )
                sound("error2")
                continue

            refined, _ = apply_weapon_refinement(item_obj)
            if not refined:
                message = f"{xlred}🚫 This refinement is no longer available.{reset}"
                sound("error2")
                continue

            with backup_transaction(PROJECT_ROOT):
                save_item(d.currsel, "Weapons")
                player.save()
            refresh_player_core_stats()
            sound("positive7")
            message = (
                f"{xd}✦ Refined to R{preview['target_stage']}! "
                f"Stats updated.{reset}"
            )
            continue

        if screen_mode != "upgrade":
            screen_mode = "upgrade"
            draw_title = True
            message = ""

        usable_level = min(
            max_level,
            max_item_level_for_player(game.sel, player.level),
        )
        available_levels = max(0, usable_level - current_level)
        currency = player.dust if game.sel == "Fragments" else player.money

        if available_levels <= 0:
            levels = 0
            if not message:
                if current_level >= max_level:
                    message = (
                        f"{xlyellow}This item is already at its maximum level."
                        f"{reset}"
                    )
                else:
                    next_level = min(max_level, current_level + 1)
                    required_level = required_player_level_for_item(
                        next_level,
                        game.sel,
                    )
                    message = (
                        f"{xlred}🚫 Reach player level {required_level} "
                        f"to upgrade this item again.{reset}"
                    )
        else:
            levels = max(1, min(levels, available_levels))
            if getattr(setting, "item_level_up_mode", "One at a time") == "All":
                affordable_levels = max_affordable_upgrade_levels(
                    item_obj,
                    game.sel,
                    available_levels,
                    currency,
                )
                levels = max(1, affordable_levels)

        draw_upgrade_menu(
            item_obj,
            game.sel,
            levels,
            message,
            draw_title=draw_title,
        )
        draw_title = False
        k = getx(0, 0, expect="key")
        lowered = k.lower() if isinstance(k, str) else ""

        if lowered == "+":
            if levels < available_levels:
                levels += 1
                message = ""
                sound("map_switch2")
            else:
                sound("map_switch2_end")
        elif lowered == "-":
            if levels > 1:
                levels -= 1
                message = ""
                sound("map_switch3")
            else:
                sound("map_switch1_end")
        elif lowered in ("esc", bind.back.lower()):
            sound("map_left")
            game.preserve_offset = True
            displaynewsel()
            return False
        elif lowered in ("enter", bind.confirm.lower()):
            if available_levels <= 0 or levels <= 0:
                sound("error2")
                continue

            total_cost = item_upgrade_cost(item_obj, game.sel, levels)
            currency = player.dust if game.sel == "Fragments" else player.money
            currency_name = "magic dust" if game.sel == "Fragments" else "gold"
            if currency < total_cost:
                message = f"{xlred}🚫 You need {total_cost - currency} more {currency_name}.{reset}"
                sound("error2")
                continue

            target_level = min(max_level, current_level + levels)
            if target_level <= current_level:
                sound("error2")
                continue

            upgraded, _ = apply_item_upgrade(
                item_obj,
                game.sel,
                levels,
            )
            if not upgraded:
                message = f"{xlred}🚫 This upgrade is no longer available.{reset}"
                sound("error2")
                continue
            with backup_transaction(PROJECT_ROOT):
                save_item(d.currsel, game.sel)
                player.save()
            refresh_player_core_stats()
            sound("positive7")
            new_level = current_level + levels
            message = (
                f"{xa}✓ Upgraded to level {new_level}. Stats updated.{reset}"
            )
            levels = 1


@save_operation
def remove_inventory_item(item_id, category, length):
    # delete the item and update the remaining item numbers
    # remember equipped items before moving files
    equipped_ids = {}
    for equipped_path in inv_active_paths(category):
        try:
            equipped_ids[equipped_path] = int(read(equipped_path, default="none"))
        except (TypeError, ValueError):
            equipped_ids[equipped_path] = None

    target = os.path.join("Items", category, f"item{item_id}.txt")
    if not os.path.exists(target):
        return False
    backup_before_write(PROJECT_ROOT, target, "", setting.backup_count)
    os.remove(target)

    # move the remaining files down
    for i in range(item_id + 1, length + 1):
        src = os.path.join("Items", category, f"item{i}.txt")
        dst = os.path.join("Items", category, f"item{i - 1}.txt")
        if os.path.exists(src):
            shutil.move(src, dst)

    # update equipped item numbers
    for equipped_path, equipped_id in equipped_ids.items():
        if equipped_id == item_id:
            update(equipped_path, "none")
        elif equipped_id is not None and equipped_id > item_id:
            update(equipped_path, equipped_id - 1)

    refresh_player_core_stats()
    return True


@save_operation
def duplicate_inventory_item(item_id, category, length):
    # add a copy after this item, update equipped item numbers too
    source = os.path.join("Items", category, f"item{item_id}.txt")
    if not os.path.exists(source):
        return False

    backup_before_write(PROJECT_ROOT, source, "", setting.backup_count)

    # remember equipped items before moving files
    equipped_ids = {}
    for equipped_path in inv_active_paths(category):
        try:
            equipped_ids[equipped_path] = int(read(equipped_path, default="none"))
        except (TypeError, ValueError):
            equipped_ids[equipped_path] = None

    # move files up, start at the end so nothing gets overwritten
    for i in range(length, item_id, -1):
        src = os.path.join("Items", category, f"item{i}.txt")
        dst = os.path.join("Items", category, f"item{i + 1}.txt")
        if os.path.exists(src):
            shutil.move(src, dst)
    shutil.copy(source, os.path.join("Items", category, f"item{item_id + 1}.txt"))

    # update equipped item numbers
    for equipped_path, equipped_id in equipped_ids.items():
        if equipped_id is not None and equipped_id > item_id:
            update(equipped_path, equipped_id + 1)
    refresh_player_core_stats()
    return True


def draw_delete_menu(item_obj, category):
    blank(16, 63, 16, 110)
    blank(18, 63, 29, 110)
    blank(31, 63, 31, 110)
    print(f"\033[16;63H{bold}🗑️ {xlred}Delete {item_obj.name}?{reset}")
    print(f"\033[19;63H{x0}███████████████████████████████████████████████")
    draw_confirmation_progress(0, "delete")
    print(f"\033[22;63H{x0}███████████████████████████████████████████████{reset}")

    item_label = inv_item_label(category)
    confirm_label = bind.confirm.upper()
    if getattr(setting, "double_tap_confirmation", False):
        confirmation_prompt = (
            f"Press {bold}{xlred}Enter / {confirm_label}{reset}{xc} twice"
        )
    else:
        confirmation_prompt = (
            f"Hold {bold}{xlred}Enter / {confirm_label}{reset}{xc}"
        )
    print(f"\033[24;63H{reset}{xf}→ {xc}📛 {confirmation_prompt} to delete {item_label}.{reset}")
    print(f"\033[25;63H{reset}{xf}→ {xb}💤 Press {bold}{x3}{bind.back.upper()} / ESC{reset}{xb} to cancel deletion.{reset}")

    gold, dust = item_salvage_rewards(item_obj, category)
    print(f"\033[27;63H{reset}{xf}{rgb(255, 206, 124)}📦 Deleting this {item_label} will give you:{reset}")
    if category == "Fragments":
        print(f"\033[28;66H{reset}{x7}╰─ ✨ {xlyellow}{bold}{format_number(dust)} {reset}{xlyellow}magic dust")
    else:
        print(f"\033[28;66H{reset}{x7}├─ 🪙 {xlyellow}{bold}{format_number(gold)} {reset}{xlyellow}gold")
        print(f"\033[29;66H{reset}{x7}╰─ ✨ {xlyellow}{bold}{format_number(dust)} {reset}{xlyellow}magic dust")
    print(f"\033[31;63H{xlorange}⚠️ You will lose this {item_label} permanently!{reset}")


def delete_selected_item():
    if getattr(d, "inventory_action_mode", "inventory") != "inventory":
        return False
    d.inventory_action_mode = "delete"
    try:
        return _delete_selected_item_flow()
    finally:
        d.inventory_action_mode = "inventory"


@save_operation
def _delete_selected_item_flow():
    item_obj = load_item(d.currsel, game.sel)
    if not item_obj:
        return False
    if int(getattr(item_obj, "locked", 0)) == 1:
        blank(31, 63, 31, 110)
        print(f"\033[31;63H{xlred}🔒 Unlock this item before deleting it.{reset}")
        sound("error2")
        return False

    draw_delete_menu(item_obj, game.sel)
    if not hold_for_confirmation("delete"):
        sound("map_left")
        game.preserve_offset = True
        displaynewsel()
        return False

    gold, dust = item_salvage_rewards(item_obj, game.sel)
    if not remove_inventory_item(d.currsel, game.sel, d.length):
        sound("error2")
        game.preserve_offset = True
        displaynewsel()
        return False

    player.money += gold
    player.dust += dust
    player.save()
    d.length -= 1
    game.comparing.clear()
    game.is_comparing = False
    d.inventory_equip_blocked_until = time.monotonic() + 1.0
    sound("pop_1")

    if d.length <= 0:
        game.goto = noitems
        return True

    d.preserved_item_id = max(1, min(d.currsel, d.length))
    game.goto = reload_items
    return True

def inventory_prep():
    d.massdelete = 0
    d.current = 0
    d.hold_item = 0
    d.inventory_action_mode = "inventory"
    d.length = len(list(Path(f"Items/{game.sel}").glob("item*.txt")))

    if d.length == 0:
        game.goto = noitems
        return

    cls()
    cursor(False)
    print()

    category_title = inv_category_title(game.sel)

    # top symbols for stuff
    if game.sel in ("Bodywear", "Helmets"):
        print("                                                      \033[38;5;4m██████████████        ")
        print("                                                      \033[38;5;4m██\033[38;5;6m██████████\033[38;5;4m██")
        print("                                                      \033[38;5;4m██\033[38;5;6m██████████\033[38;5;4m██")
        print("                                                      \033[38;5;4m ██\033[38;5;6m████████\033[38;5;4m██ ")
        print("                                                       \033[38;5;4m ██\033[38;5;6m██████\033[38;5;4m██  ")
        print("                                                         \033[38;5;4m ██\033[38;5;6m██\033[38;5;4m██    ")
        print("                                                            \033[38;5;4m██              ")
    elif game.sel == "Weapons":
        atksymbol1=f"{x6}██████{xlyellow}"
        atksymbol2=f"{x6}██{xlyellow}██{xe}██{xlyellow}██{x6}██{xlyellow}"
        atksymbol3=f"{x6}██{xlyellow}██████{xe}██{xlyellow}██{x6}██{xlyellow}"
        atksymbol4=f"{x6}██{xlyellow}{xe}██████████{xlyellow}{x6}██{xlyellow}"
        atksymbol5=f"{x6}██{xlyellow}██████{xe}██{xlyellow}██{x6}██{xlyellow}"
        atksymbol6=f"{x6}██{xlyellow}██{xe}██{xlyellow}██{x6}██{xlyellow}"
        atksymbol7=f"{x6}██████{xlyellow}"
        print(f"                                                          \033[38;2;2;74;48m{atksymbol1}")
        print(f"                                                        \033[38;2;2;74;48m{atksymbol2}")
        print(f"                                                      \033[38;2;2;74;48m{atksymbol3}")
        print(f"                                                      \033[38;2;2;74;48m{atksymbol4}")
        print(f"                                                      \033[38;2;2;74;48m{atksymbol5}")
        print(f"                                                        \033[38;2;2;74;48m{atksymbol6}")
        print(f"                                                          \033[38;2;2;74;48m{atksymbol7}")
    elif game.sel == "Fragments":
        fragment_colour = RGB + "186;243;219m"
        print(f"                                                            {fragment_colour}╭──╮")
        print(f"                                                          {fragment_colour}╭─╯  ╰─╮")
        print(f"                                                        {fragment_colour}╭─╯  🧩  ╰─╮")
        print(f"                                                        {fragment_colour}│          │")
        print(f"                                                        {fragment_colour}╰─╮      ╭─╯")
        print(f"                                                          {fragment_colour}╰─╮  ╭─╯")
        print(f"                                                            {fragment_colour}╰──╯")
    
    # title
    title_inner_width = 23
    title_padding = max(0, title_inner_width - visible_len(category_title))
    title_left = " " * (title_padding // 2)
    title_right = " " * (title_padding - len(title_left))
    print(f"\033#3{reset}                  {xlorange}╭───────────────────────{xlorange}╮")
    print(f"\033#4                  {xlorange}╭───────────────────────{xlorange}╮")
    print(f"\033#3                  {xlorange}│{title_left}{bold}{xlyellow}{category_title}{title_right}{xlorange}│")
    print(f"\033#4                  {xlorange}│{title_left}{bold}{xlyellow}{category_title}{title_right}{xlorange}│")
    print(f"\033#3                  {xlorange}╰───────────────────────{xlorange}╯")
    print(f"\033#4                  {xlorange}╰───────────────────────{xlorange}╯")

    d.moving_progress = 0
    remembered = 1
    if getattr(setting, "remember_last_inventory_selection", False):
        remembered = getattr(setting, "inventory_last_selections", {}).get(
            game.sel,
            1,
        )
    d.currsel = max(1, min(int(remembered), d.length))
    d.page = (d.currsel - 1) // 10
    d.begin = d.page * 10 + 1
    d.end = d.begin + 9
    d.current = d.begin - 1

    # border & character
    print(f"{x8}",end="")
    print(f"{player.color}               {x8} ╭───────────────────────────────────────────┬─────────────────────────────────────────────────╮")
    print(f"{player.color}               {x8} │                                           │                                                 │")
    print(f"{player.color}      ██████   {x8} ├───────────────────────────────────────────┼─────────────────────────────────────────────────┤")
    print(f"{player.color}    ██      ██ {x8} │                                           │                                                 │")
    print(f"{player.color}    ██ •  • ██ {x8} │                                           │                                                 │")
    print(f"{player.color}    ██      ██ {x8} │                                           │                                                 │")
    print(f"{player.color}      ██████   {x8} │                                           │                                                 │")
    print(f"{player.color}        ██  ██ {x8} │                                           │                                                 │")
    print(f"{player.color}  ██    ██   ██{x8} │                                           │                                                 │")
    print(f"{player.color}    ██  ██  ██ {x8} │                                           │                                                 │")
    print(f"{player.color}      ██████   {x8} │                                           │                                                 │")
    print(f"{player.color}        ██     {x8} │                                           │                                                 │")
    print(f"{player.color}        ██     {x8} │                                           │                                                 │")
    print(f"{player.color}        ██     {x8} │                                           │                                                 │")
    print(f"{player.color}      ██  ██   {x8} │                                           │                                                 │")
    print(f"{player.color}    ██      ██ {x8} ├───────────────────────────────────────────┼─────────────────────────────────────────────────┤")
    print(f"{player.color}               {x8} │                                           │                                                 │")
    print(f"{player.color}               {x8} ╰───────────────────────────────────────────┴─────────────────────────────────────────────────╯\033[0m")

    #print(f"\n                         {italic}{xlorange}Equip an item with {xlyellow}Enter{xlorange}, delete it with {xlyellow}Backspace{xlorange} or level it up with {xlyellow}Space{xlorange}.")

    print(f"{reset}\033[16;19H🔱 {bold}{xlorange}{category_title} {xlyellow}{unbold}→ {xlorange}{bold}Page {bold}{d.page + 1} {unbold}{x7}(items: {xf}{bold}{d.length}{x7}{unbold}){reset}")
    print(f"\033[31;19H{xlorange}Move {xlyellow}{bold}{setting.menu_up.upper()}/{setting.menu_down.upper()} {setting.menu_left.upper()}/{setting.menu_right.upper()} {reset}{xlorange}| Upgrade {xlyellow}{bold}U {reset}{xlorange}| Delete {xlyellow}{bold}⌫{reset}")

    game.preserve_offset = False
    
    # make comparison array empty
    game.comparing = []
    # comparing is false
    game.is_comparing = False
    
    item_pager()




# item ability specials (line two)
def get_specials(name):
    # weapons:
    # if d.ability_line1, d.ability_line2, d.notice, or d.notice_text are defined, delete them
    d.ability_line1 = None
    d.ability_line2 = None
    d.notice = None
    d.notice_text = None
    blank(1,80,8,126)
    if name == "Befriend a Shark in 30 Days":
        d.ability_line1 = f"A cute shark will attack after you do!"
        d.ability_line2 = f"He's considered a {rainbow(text='phantom', bold=True, offset=d.offset)} during a battle."
        d.notice = "Phantom"
        d.notice_text = f"Phantom beings can't be killed. They appear {shine(text='invisible', bold=True, offset=d.offset+0.2)} to all enemies."
    elif name == "Krita User Manual":
        d.ability_line1 = f"Hitting an enemy makes it panic about"
        d.ability_line2 = f"color theory → it gets {xlbrown}dizzy{reset} permanently."
        d.notice = "Dizzy"
        d.notice_text = f"Every stack makes the target move 1% slower and take 1% more damage from attacks."
    elif name == "Wand of Galanb III.":
        d.ability_line1 = f"3 pigeons will aid you in battle! Each one"
        d.ability_line2 = f"inflicts 2 turns of {xc}{bold}bleeding{reset} every turn."
        d.notice = "Bleeding"
        d.notice_text = f"Every stack chops away {xlred}{bold}0-1% {x7}(randomized) {reset}of the enemy's remaining HP every turn."
    
    
    # if d.ability_line1 is defined:
    if d.ability_line1:
        print(f"\033[27;64H› {xf}{d.ability_line1}")
    if d.ability_line2:
        print(f"\033[28;64H  {xf}{d.ability_line2}")
    if d.notice:
        draw_box_border(2,90,8,126,text=f"{d.notice}",text_color=xlyellow,border_color=xlorange,bold=True,align="right")
    if d.notice_text:
        draw_box_text(text=d.notice_text,y1=4,x1=93,y2=6,x2=123)

def inventory_waitkey():
    # only reset offset if preservation was off
    if not game.preserve_offset:
        d.offset = 0
    else:
        game.preserve_offset = False
    animate_inventory_effects = animations_enabled()
    while True:
        item = load_item(d.currsel, game.sel)
        ityped = inv_type_icon(item)
        number_marker = inv_item_number_marker(game.sel, d.currsel, item)
        itemcolour, itemcolour_rgb = INVENTORY_RARITY_STYLES.get(
            getattr(item, "rarity", None),
            (xf, (255, 255, 255)),
        )
        if animate_inventory_effects:
            d.offset += 0.0035
        print(f"\033[{d.currselrow};20H{bold}{itemcolour}{d.currsel} {unbold}{number_marker} {ityped} {shine(text=item.name,bold=True,offset=d.offset,color=itemcolour_rgb)}",end="",flush=True)
        k = getx(
            0,
            0,
            expect="key",
            timeout=0 if animate_inventory_effects else None
        )
        k = menu_navigation_key(k)
        if k == "up":
            move_item_selection(-1)
        elif k == "down":
            move_item_selection(1)
        elif k == "left":
            change_inventory_page(-1)
        elif k == "right":
            change_inventory_page(1)
        elif k in (bind.back, "esc"):
            if getattr(setting, "remember_last_inventory_selection", False):
                selections = dict(
                    getattr(setting, "inventory_last_selections", {})
                )
                selections[game.sel] = d.currsel
                setting.inventory_last_selections = selections
            game.goto = inventory
            return
        elif k in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]:
            # switch cursor to select that item on the page, if it exists
            target = (d.page * 10) + int(k)
            if target <= d.length and target >= d.begin:
                unselect_current()
                d.currsel = target
                d.currselrow = 19 + (d.currsel - d.begin)
                displaynewsel()
            # if pressed 0, treat as 10
            if k == "0":
                target = (d.page * 10) + 10
                if target <= d.length and target >= d.begin:
                    unselect_current()
                    d.currsel = target
                    d.currselrow = 19 + (d.currsel - d.begin)
                    displaynewsel()
        # E opens the item file in a text editor
        elif setting.debug_shortcuts and k.lower() == "e":
            item_path = f"Items/{game.sel}/item{d.currsel}.txt"
            sound("positive7")
            if os.path.exists(item_path):
                open_text_file(item_path)
        # equip directly, no hold confirmation needed
        elif k.lower() == "enter":
            if time.monotonic() < getattr(d, "inventory_equip_blocked_until", 0):
                continue
            item = load_item(d.currsel, game.sel)
            equipped_path = inv_active_path(game.sel, item)
            if not equipped_path:
                continue
            req_level = required_player_level_for_item(item.level, game.sel)
            if req_level <= player.level:
                current_equipped = str(read(equipped_path, default="none")).strip()
                if current_equipped == str(d.currsel):
                    sound("pop_1")
                    update(equipped_path, "none")
                else:
                    sound(f"equip_{random.choice(['1','2','3'])}")
                    update(equipped_path, d.currsel)
                refresh_player_core_stats()
                # preserve current offset for shine effect
                game.preserve_offset = True
                displaynewsel()
            else:
                blank(31,62, 31,62+48)
                item_label = inv_item_label(game.sel)
                print(f"\033[31;63H🚫 {xlred}This {item_label} requires level {bold}{req_level}{reset}{xlorange} (+{req_level-player.level} more){reset}{xlred}!")
                sound("error2")
        # when you press L, lock the item (item.locked = 1)
        elif k.lower() == "l":
            item = load_item(d.currsel, game.sel)
            if getattr(item, "locked", None) is None:
                continue
            if int(getattr(item, "locked", 0)) == 1:
                item.locked = 0
                sound("lock 1")
            else:
                item.locked = 1
                sound("lock 1")
            # save the locked status into the item file
            save_item(item_id=d.currsel, category=game.sel)
            game.preserve_offset = True
            displaynewsel()
        elif k.lower() == "u":
            if upgrade_selected_item():
                return
        # Ctrl+D duplicates selected item (developer function). The dupe will be saved as the next item (duping item 5 will create item 6, shifting all subsequent items up by one if they exist)
        elif setting.debug_shortcuts and k == "ctrl/d":
            if not duplicate_inventory_item(d.currsel, game.sel, d.length):
                sound("error2")
                continue
            d.length += 1
            sound("pop_2")
            game.preserve_offset = True
            game.goto = reload_items
            d.preserved_item_id = d.currsel
            return
            
        # Ctrl+X deletes selected item (developer function). Shifts subsequent items down.
        elif setting.debug_shortcuts and k == "ctrl/x":
            if remove_inventory_item(d.currsel, game.sel, d.length):
                d.length -= 1
                sound("pop_1")
                if d.length <= 0:
                    game.goto = noitems
                else:
                    game.goto = reload_items
                    d.preserved_item_id = max(1, min(d.currsel, d.length))
                return
            sound("error2")
        
        # Backspace: production version to delete with confirmation
        elif k == "backspace":
            if delete_selected_item():
                return
        
        # Pressing space adds comparable equipment to comparison.
        elif k == "space" and inv_category_supports_comparison(game.sel):
            # append current selection to comparison array if it's not already in there
            # if 2 items are in the comparison array already, delete the array and start over with the new selection
            
            if len(game.comparing) >= 2:
                game.comparing.clear()
                game.is_comparing = False
                
            if d.currsel not in game.comparing:
                game.comparing.append(d.currsel)
                blank(31,63, 31,110)
                print(f"\033[31;63H{reset}{xa}✅ Item {bold}added{unbold} to comparison! {x7}({len(game.comparing)}/2){reset}")
                sound("pop_2")
                #game.preserve_offset = True
                #displaynewsel()
            else:
                game.comparing.remove(d.currsel)
                blank(31,63, 31,110)
                print(f"\033[31;63H{reset}{xlred}❌ Item {bold}removed{unbold} from comparison! {x7}({len(game.comparing)}/2){reset}")
                sound("pop_1")
                #game.preserve_offset = True
                #displaynewsel()
                
            if len(game.comparing) == 2:
                game.is_comparing = True
                sound("pop_3")
                # preserve offset for shine effect
                game.preserve_offset = True
                # delete all past comparison variables, if applicable
                try:
                    del item1
                    del item2
                    del item1_value
                    del item2_value
                    del comparison_winner
                    del stat_diff_percentage
                except NameError:
                    pass
                # load first item for comparison
                item1 = copy(load_item(game.comparing[0], game.sel))
                item1_value = inv_compare_value(item1, game.sel)
                item2 = copy(load_item(game.comparing[1], game.sel))
                item2_value = inv_compare_value(item2, game.sel)
                stat_label = "DMG" if game.sel == "Weapons" else "DEF"
                
                
                # determine if item2 is an upgrade or downgrade
                if item2_value > item1_value:
                    comparison_winner = 2
                elif item2_value < item1_value:
                    comparison_winner = 1
                else:
                    comparison_winner = 0
                # if item 2 wins, calculate its win percentage
                if comparison_winner == 2:
                    stat_diff_percentage = round(((item2_value - item1_value) / item1_value) * 100) if item1_value else 0
                elif comparison_winner == 1:
                    stat_diff_percentage = round(((item1_value - item2_value) / item2_value) * 100) if item2_value else 0
                else:
                    stat_diff_percentage = 0
                blank(16,63, 16,110)
                blank(18,63, 29,110)
                blank(31,63, 31,110)
                item_label_title = inv_item_label(game.sel).title()
                print(f"\033[16;63H{bold}⚖ {xlyellow}{bold} {item_label_title} comparison complete!{reset}")
                
                # line 18: display only item 1 type, name in bold and level
                # determine item1 color based on whether it's an upgrade or downgrade compared to item2
                item1_tag = ""
                item2_tag = ""
                if comparison_winner == 1:
                    item1_color = xlyellow
                    item2_color = xlorange
                    item1_tag = f"{xf}← {bold}Winner{reset}"
                    winner_name = item1.name
                elif comparison_winner == 2:
                    item1_color = xlorange
                    item2_color = xlyellow
                    item2_tag = f"{xf}← {bold}Winner{reset}"
                    winner_name = item2.name
                else:
                    item1_color = xlorange
                    item2_color = xlorange
                    item1_tag = f"{xf}← {bold}Tie{reset}"
                    item2_tag = f"{xf}← {bold}Tie{reset}"
                item1 = copy(load_item(game.comparing[0], game.sel))
                item1_icon = inv_type_icon(item1)
                print(f"\033[19;63H{reset}{item1_icon} {x7}↑{item1.level} {item1_color}{bold}{item1.name}{unbold} {item1_tag}{reset}")
                
                item2 = copy(load_item(game.comparing[1], game.sel))
                item2_icon = inv_type_icon(item2)
                print(f"\033[21;63H{reset}{item2_icon} {x7}↑{item2.level} {item2_color}{bold}{item2.name}{unbold} {item2_tag}{reset}")
                print(f"\033[23;61H{reset}{x8}├─────────────────────────────────────────────────┤{reset}")
                item_label = inv_item_label(game.sel)
                stat_caption = setting.weapon_comparison_metric.lower() if game.sel == "Weapons" else "defense"
                if not comparison_winner == 0:
                    print(f"\033[25;63H{reset}{xlorange}⇝ {xf}Using {item_label} {bold}{xlorange}#{comparison_winner}{reset} will give you {bold}{xlorange}{format_number(stat_diff_percentage)}% more {stat_label}{reset}")
                    print(f"\033[26;63H{reset}{xf}  compared to the other selected {item_label} ({bold}#{3 - comparison_winner}{unbold}).{reset}")
                    if comparison_winner == 1:
                        print(f"\033[28;63H{reset}{xlorange}• {xlyellow}{bold}{round(item1_value)} {reset}vs {bold}{xlorange}{round(item2_value)} {reset}{stat_caption}{reset}")
                    if comparison_winner == 2:
                        print(f"\033[28;63H{reset}{xlorange}• {xlorange}{bold}{round(item1_value)} {reset}vs {bold}{xlyellow}{round(item2_value)} {reset}{stat_caption}{reset}")
                else:
                    print(f"\033[25;63H{reset}{xlorange}⇝ {xf}Both items have the {bold}{xlorange}exact same{reset} {stat_label}!{reset}")
                    print(f"\033[26;63H{reset}{xf}  Check other stats to determine your choice.{reset}")
                    print(f"\033[28;63H{reset}{xlorange}• {bold}{round(item1_value)} {reset}{stat_caption} for both items{reset}")
                # finally, in row 31, print instructions for the user
                print(f"\033[31;63H{reset}{xf}📜 Navigate any way to exit comparison.{reset}")
        if animate_inventory_effects:
            time.sleep(0.01)

def unselect_current():
    item = load_item(d.currsel, game.sel)
    if not item: return
    ityped = inv_type_icon(item)
    number_marker = inv_item_number_marker(game.sel, d.currsel, item)

    req_level = required_player_level_for_item(item.level, game.sel)
    colour = x7 if req_level <= int(player.level) else xlred
    print(f"\033[{d.currselrow};20H\033[38;5;8m{d.currsel} {number_marker} {ityped} \033[0m{x7}{item.name} \033[{d.currselrow};56H{colour}↑{item.level}")

def move_item_selection(direction):
    unselect_current()
    d.currsel += direction
    if direction > 0:
        if d.currsel > d.length:
            d.currsel = d.length
        elif d.currsel > d.current:
            d.currsel = d.current
        else:
            d.currselrow += 1
    else:
        if d.currsel < d.begin:
            d.currsel = (d.page * 10) + 1
        elif d.currsel == 0:
            d.currsel = 1
        else:
            d.currselrow -= 1
    displaynewsel()

def reload_items():
    if d.moving_progress not in (1, 2):
        if getattr(d, 'preserved_item_id', None) is not None:
            d.currsel = d.preserved_item_id
            d.page = (d.currsel - 1) // 10
            d.begin = (d.page * 10) + 1
            d.end = d.begin + 9
            d.preserved_item_id = None
        else:
            d.currsel = (d.page * 10) + 1
    d.current = d.begin - 1

    if d.moving_progress not in (1, 2):
        for r in range(19, 29):
            print(f"\033[{r};20H                                        ")
    item_pager()

def change_inventory_page(direction):
    if direction > 0:
        if d.length <= 10 + (d.page * 10):
            return
    elif d.page < 1:
        return

    d.page += direction
    d.begin += 10 * direction
    d.end += 10 * direction
    d.currsel = (d.page * 10) + 1
    d.current = d.begin - 1
    reload_items()

def item_pager():
    d.rowdisplay = 18
    d.currselrow = 19 + (d.currsel - d.begin)

    for a in range(d.begin, d.end + 1):
        render_items()
    displaynewsel()
    game.goto = inventory_waitkey

def render_items():
    while True:
        if d.length == d.current:
            break
        
        d.current += 1
        d.rowdisplay += 1
        
        item = load_item(d.current, game.sel)
        if not item: 
            break

        ityped = inv_type_icon(item)
        number_marker = inv_item_number_marker(game.sel, d.current, item)

        print(f"\033[{d.rowdisplay};20H{x8}{' '*40}{xf}",end="")
        
        indicator = "↑"
        req_level = required_player_level_for_item(item.level, game.sel)
        colour = x7 if req_level <= int(player.level) else xlred
        print(f"\033[{d.rowdisplay};20H\033[38;5;8m{bold}{d.current} {unbold}{x7}{number_marker} {ityped} {x7}{item.name} {reset}\033[{d.rowdisplay};56H{colour}{indicator}{item.level}")
        
        if d.current >= d.end:
            break
        #print(f"\033[1;1H{x8}page: {d.page} | current: {d.current} | begin: {d.begin} | end: {d.end}        ")
        if d.current >= (d.page) * 10:
            break

def displaynewsel():
    # clear the line the comparison made, if any
    print(f"\033[23;61H{reset}{x8}│                                                 │{reset}")
    # if compared, set compared to false and clear variable
    if game.is_comparing:
        game.is_comparing = False
        game.comparing.clear()
    category_title = inv_category_title(game.sel)
    print(f"{reset}\033[16;19H🔱 {bold}{xlorange}{category_title} {xlyellow}{unbold}→ {xlorange}{bold}Page {bold}{d.page + 1} {unbold}{x7}(items: {xf}{bold}{d.length}{x7}{unbold}){reset}")
    # Always re-calculate current row to prevent cursor drift
    d.currselrow = 8 + d.currsel - ((d.page - 1) * 10)
    
    for r in range(18, 30):
        if r != 30:
            print(f"\033[{r};62H                                                ")
    print(f"\033[31;62H                                                ")

    item = load_item(d.currsel, game.sel)
    if not item: return

    ityped = inv_type_icon(item)
    type_raw = getattr(item, "type_raw", None)
    type_label = (
        "None"
        if not type_raw or type_raw == "None"
        else str(type_raw).title()
    )
    number_marker = inv_item_number_marker(game.sel, d.currsel, item)

    # Write selection in list
    indicator = "↑"
    req_level = required_player_level_for_item(item.level, game.sel)
    colour = x7 if req_level <= int(player.level) else xlred
    itemcolour, itemcolour_rgb = INVENTORY_RARITY_STYLES.get(
        getattr(item, "rarity", None),
        (xf, (255, 255, 255)),
    )
    req_level = required_player_level_for_item(item.level, game.sel)
    colour = x7 if req_level <= int(player.level) else xlred
    if not game.preserve_offset:
        d.offset = 0
    else:
        game.preserve_offset = False
    print(f"\033[{d.currselrow};20H{bold}{itemcolour}{d.currsel} {unbold}{number_marker} {ityped} {shine(text=item.name, color=itemcolour_rgb,bold=True,offset=d.offset)} {reset}\033[{d.currselrow};56H{colour}{indicator}{item.level}")
    #print(f"\033[{d.currselrow};20H{d.current} {unbold}{xa}› {ityped}{itemcolour}{bold} \033[0m{item.name} {reset}\033[{d.rowdisplay};56H{colour}{indicator}{item.level}")
    # Write Description UI
    blank(16,63, 16,110)
    blank(18,63, 29,110)
    
    # Create XP bar
    xpbar = ""
    max_lvl = get_item_max_level(game.sel) or 1
    filled = round((item.level*43)/max_lvl)
    empty = 43-filled
    
    for i in range(filled):
        xpbar += f"{xbb} "
    for i in range(empty):
        xpbar += f"{rgback(17,45,69)} "
    
    print(f"[19;63H{xb0}{' ' * 47}{reset}")
    print(f"[20;63H{xb0}  {xpbar}{xb0}  {reset}")
    print(f"[21;63H{xb0}  {xpbar}{xb0}  {reset}")
    print(f"[22;63H{xb0}{' ' * 47}{reset}")
    indicators = ""
    # If equipped, show equipped indicator
    equipped_path = inv_active_path(game.sel, item)
    if equipped_path and str(d.currsel) == str(read(equipped_path)):
        indicators += "✅"
    # If locked (item.locked = 1), show locked indicator
    if str(getattr(item, "locked", 0)) == "1":
        indicators += "🔒"
    # If the player's level is below this item's requirement, show lock indicator.
    req_level = required_player_level_for_item(item.level, game.sel)
    if req_level > int(player.level):
        indicators += f"🚫"
    # If item is currently in comparison, show comparison indicator
    if d.currsel in game.comparing:
        indicators += f"⚔️"
    if not indicators == "":
        print(f"\033[16;63H{ityped} {bold}{underline}{itemcolour}{item.name}{reset}{x7} ({type_label} → {reset}{indicators}{reset}{x7}){reset}")
    # if no indicators, don't show any, neither the arrow
    if indicators == "":
        print(f"\033[16;63H{ityped} {bold}{underline}{itemcolour}{item.name}{reset}{x7} ({type_label}){reset}")
    if game.sel == "Weapons":
        item.actual_atk = get_actual_atk()
        print(f"\033[24;66H❇️ {xa}{bold}{format_number(item.actual_atk)}{unbold} ATK")
        # if item.atkcrit can also be an int (0 after decimal point), convert to int
        try:
            atkcrit = int(float(item.atkcrit))
        except ValueError:
            atkcrit = item.atkcrit
        print(f"\033[24;80H✴️ {xlyellow}{bold}{atkcrit}{unbold}% Crit")
        
        if item.level >= WEAPON_MAX_LEVEL:
            print(
                f"\033[24;94H{xd}✦ Ref. {bold}"
                f"{int(getattr(item, 'refine', 0))}"
                f"/{WEAPON_REFINEMENT_MAX}{reset}"
            )
        else:
            print(
                f"\033[24;94H📶 {xf}Lv {bold}"
                f"{item_level_display(item, game.sel)}{unbold}{x7}"
            )
        
        ability = item.ability if item.ability and item.ability.strip() else "None"
        print(f"\033[26;63H🍹 {bold}{xf}Combat ability:{reset}")
        print(f"\033[27;64H› {xf}{ability}")
        print(f"\033[31;63H📜{xlorange} {item.description}\033[0m")
    elif game.sel == "Fragments":
        main_value = scale_fragment_stat(
            item.main_stat,
            get_fragment_main_stat_value(item),
        )
        main_display = format_fragment_stat(item.main_stat, main_value, signed=True)
        main_icon = fragment_stat_icon(item.main_stat)
        print(
            f"\033[24;63H{main_icon} {xa}{bold}{main_display}{unbold}"
            f"{reset}{x7}  ↑ Lv {xf}{item_level_display(item, game.sel)}"
            f"{reset}{x7}  ◈ {xlyellow}{item.set_name}{reset}"
        )
        substats = get_fragment_substats(item)
        print(f"\033[26;63H✦ {bold}{xf}Substats:{reset}")
        for index, unlock_level in enumerate((5, 10, 15)):
            row = 27 + index
            if index < len(substats):
                stat_name, value = substats[index]
                effective_value = scale_fragment_stat(stat_name, value)
                stat_display = format_fragment_stat(
                    stat_name,
                    effective_value,
                    signed=True,
                )
                stat_icon = fragment_stat_icon(stat_name)
                print(f"\033[{row};64H{stat_icon} {xf}{stat_display}{reset}")
            else:
                print(
                    f"\033[{row};64H◇ {x7}Unlocks at Lv {unlock_level}{reset}"
                )
        print(f"\033[31;63H📜{xlorange} {item.description}\033[0m")
    else:
        item.actual_defense = get_actual_defense(item)
        print(f"\033[24;66H🛡️ {xb}{bold}{format_number(item.actual_defense)}{unbold}% DEF")
        print(f"\033[24;94H📶 {xf}Lv {bold}{item_level_display(item, game.sel)}{unbold}{x7}")
        ability = item.ability if item.ability and item.ability.strip() else "None"
        description = item.description if item.description and item.description.strip() else "None"
        print(f"\033[26;63H🍹 {bold}{xf}Combat ability:{reset}")
        print(f"\033[27;64H› {xf}{ability}")
        print(f"\033[31;63H📜{xlorange} {description}\033[0m")
    # finally, call function to display item ability specials, if applicable
    get_specials(item.name)
    comparison = equipped_item_comparison(d.currsel, game.sel)
    if comparison:
        move(29, 63)
        print(f"{xf}{comparison[:47]:<47}{reset}", end="")


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
PROGRAM PART
Yep. This is everything that actually makes the thing work.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
if __name__ == "__main__":
    cls()
    cursor(False)

    game.goto = startup # adjust to change your landing!

    try:
        while True:
            game.goto()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        cursor(True)
        print(reset, end="", flush=True)
