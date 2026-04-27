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

import msvcrt, os, time, sys, ctypes, ast, operator as op, subprocess, json, re, random  # noqa: E401, E402
from pathlib import Path  # noqa: E402
from typing import Literal  # noqa: E402

version=1
subversion=0

RGB="[38;2;"
TITLE = f"Battles of Bench - a{version}.{subversion}"

os.system(f"title {TITLE}")
sys.stdout.reconfigure(encoding="utf-8") # actually make it display shit

sound_process = subprocess.Popen(
    [sys.executable, "sound_player.py"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

current_pid = os.getpid()
current_script = os.path.abspath(__file__)

kernel32 = ctypes.windll.kernel32

# Create a Job Object
job = kernel32.CreateJobObjectW(None, None)

# Set the job to kill all child processes when this process dies
class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", ctypes.c_byte * 40),
        ("IoInfo", ctypes.c_byte * 48),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]

info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

ctypes.memset(ctypes.byref(info), 0, ctypes.sizeof(info))
info.BasicLimitInformation[16] = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE & 0xFF

kernel32.SetInformationJobObject(
    job,
    9,  # JobObjectExtendedLimitInformation
    ctypes.byref(info),
    ctypes.sizeof(info)
)

kernel32.AssignProcessToJobObject(job, kernel32.GetCurrentProcess())

kernel32 = ctypes.windll.kernel32
handle = kernel32.GetStdHandle(-11)
mode = ctypes.c_uint()
kernel32.GetConsoleMode(handle, ctypes.byref(mode))
kernel32.SetConsoleMode(handle, mode.value | 4)

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
    return _eval(parsed.body)

# Simple. "cursor(True)" to show, "cursor(False)" to hide.
def cursor(x):
    handle = ctypes.windll.kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    info = CONSOLE_CURSOR_INFO()
    ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(info))
    info.bVisible = bool(x)  # True = show, False = hide
    ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(info))

# Move cursor to (row, col). Yes, it's reversed because I got used to ANSI.
def move(row, col):
    print(f"[{row};{col}H", end="")

# Wrong answer in getx() later, obliterate it.
def clear_input(row, start_col, width):
    move(row, start_col)
    print(" " * width, end="")
    move(row, start_col)

# Flashes the prompt in red for a moment. Used in getx() when input is invalid.
def flash_prompt(row, col, prompt):
    cursor(False)
    move(row, col)
    print(f"{xlred}{bold}{prompt}{reset}", end="", flush=True)
    time.sleep(0.12)
    move(row, col)
    print(prompt, end="", flush=True)
    cursor(True)
    
ANSI_PATTERN = re.compile(r'\x1b\[[0-9;?]*[A-Za-z]') # what this does, I have no clue.

# Returns the length of the text without ANSI codes. Used to properly calculate cursor positions in getx().
def visible_len(text):
    return len(ANSI_PATTERN.sub('', text))

# FINALLY, getx(). Basically input(), but actually good.
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
    highlight_keywords=None # dictionary of keywords to highlight in the input. Format: {"keyword": (prefix, suffix), ...}. E.g. {"*": (x4, reset)} would make all asterisks red regardless of validity.
):
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
                            val = float(buffer) if "." in buffer else int(buffer)
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

                ch = msvcrt.getwch()

                if ch == "\r":
                    break

                if ch == "\x08":
                    buffer = buffer[:-1]
                    continue

                if not ch.isprintable():
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
                        value = float(buffer) if "." in buffer else int(buffer)

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
            "skills": 1,
            "xp": 0,
            "xpneeded": 25,
            "tryd": 0
        }

        self.load()

    # ───────────── LOAD ─────────────
    def load(self):
        if not os.path.exists(self._path):
            self._create_default_file()

        try:
            with open(self._path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}

        # Load persistent stats only
        for key, default in self._persistent_fields.items():
            setattr(self, key, data.get(key, default))

    # ───────────── SAVE ─────────────
    def save(self):
        data = {
            key: getattr(self, key)
            for key in self._persistent_fields.keys()
        }

        with open(self._path, "w") as f:
            json.dump(data, f, indent=4)

    # ───────────── RESET ─────────────
    def reset(self):
        for key, default in self._persistent_fields.items():
            setattr(self, key, default)
        self.save()

    # ───────────── CREATE DEFAULT FILE ─────────────
    def _create_default_file(self):
        with open(self._path, "w") as f:
            json.dump(self._persistent_fields, f, indent=4)

player = PlayerData()
class EnemyData:
    pass
enemy = EnemyData()


# Load settings.
class SettingsData:
    def __init__(self):
        # Path setup
        base_dir = os.path.dirname(os.path.abspath(__file__))
        settings_dir = os.path.join(base_dir, "Settings")
        os.makedirs(settings_dir, exist_ok=True)

        self._path = os.path.join(settings_dir, "settings.txt")

        # --- Allowed / persistent fields ---
        self._persistent = {
            "difficulty": 0,
            "datatype": 1,
            "sorting": 0,
            "levelup_mode": 0,
            "music": 5,
            "pronouns": "they/them/their",
            "sfx": 10,
            "skipboot": 0,
            "skiplevelanim": 0,
            "sound": 10,
            "spatial": 0
        }

        self.load()

    # ------------------------
    # LOAD
    # ------------------------
    def load(self):
        if not os.path.exists(self._path):
            self._create_default_file()

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}

        for key, default in self._persistent.items():
            setattr(self, key, data.get(key, default))

    # ------------------------
    # SAVE
    # ------------------------
    def save(self):
        data = {
            key: getattr(self, key)
            for key in self._persistent.keys()
        }

        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # ------------------------
    # RESET (optional)
    # ------------------------
    def reset(self):
        for key, default in self._persistent.items():
            setattr(self, key, default)
        self.save()

    # ------------------------
    # Create default file
    # ------------------------
    def _create_default_file(self):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._persistent, f, indent=4)


# Create global instance
setting = SettingsData()
class ItemData:
    pass
item = ItemData()
class FragmentData:
    pass
fragment = FragmentData()
class ArmorData:
    pass
armor = ArmorData()
class HeadwearData:
    pass
head = HeadwearData()
class SystemData:
    def __init__(self):
        self.updatable = False

game = SystemData()
class KeyBinds:
    def __init__(self, filename="keybinds.txt"):
        # ───────────── PATH SETUP ─────────────
        base_dir = os.path.dirname(os.path.abspath(__file__))
        settings_dir = os.path.join(base_dir, "Settings")
        os.makedirs(settings_dir, exist_ok=True)

        self._path = os.path.join(settings_dir, filename)

        # ───────────── PERSISTENT BINDS SCHEMA ─────────────
        self._persistent_fields = {
            "attack": "space",
            "heal": "+",
            "skill": "s",
            "ult": "w",
            "back": "b",
            "confirm": "enter",
            "deny": "esc",
            "forfeit": "x"
        }

        self.load()

    # ───────────── LOAD ─────────────
    def load(self):
        if not os.path.exists(self._path):
            self._create_default_file()

        try:
            with open(self._path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}

        for key, default in self._persistent_fields.items():
            setattr(self, key, data.get(key, default))

    # ───────────── SAVE ─────────────
    def save(self):
        data = {
            key: getattr(self, key)
            for key in self._persistent_fields.keys()
        }

        with open(self._path, "w") as f:
            json.dump(data, f, indent=4)

    # ───────────── RESET ─────────────
    def reset(self):
        for key, default in self._persistent_fields.items():
            setattr(self, key, default)
        self.save()

    # ───────────── CREATE DEFAULT FILE ─────────────
    def _create_default_file(self):
        with open(self._path, "w") as f:
            json.dump(self._persistent_fields, f, indent=4)
bind = KeyBinds()

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

class CONSOLE_CURSOR_INFO(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.c_int),
        ("bVisible", ctypes.c_bool)
    ] # yep, cursor hide core

# Clear screen. Simple as that. Sorry, Linux or Mac.
def cls():
    os.system("cls")

# Key. As simple as that. Press a key, and... that's the return. With some specials.
def key(timeout=None):
    start = time.time()
    while True:
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            # Arrow keys & special keys come as '\x00' or '\xe0'
            if ch in ('\x00', '\xe0'):
                special = msvcrt.getwch()
                specials = {
                    'H': "up",
                    'P': "down",
                    'K': "left",
                    'M': "right",
                }
                return specials.get(special, "special")
            if ch == '\r':
                return "enter"
            if ch == '\x1b':
                return "esc"
            if ch == '\x08':
                return "backspace"
            if ch == ' ':
                return "space"
            # CTRL+A to CTRL+Z
            if 1 <= ord(ch) <= 26:
                letter = chr(ord(ch) + 96)
                return f"ctrl/{letter}"
            return ch  # letters, numbers, symbols cleanly handled
        if timeout is not None and (time.time() - start) >= timeout:
            return "TIMEOUT"    

# INTERACTIVITY TIME! Sound() plays a sound effect. It does this by writing the command to a text file, which is then read by the sound player.
def sound(cmd):
    path = os.path.join(os.getcwd(), "general", "temp", "sound_cmd_queue.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(str(cmd) + "\n")


def stopsound(target=None):
    """Stop sounds via UDP.
    - stopsound() -> stops all sounds and music.
    - stopsound("music") -> stops only streaming music.
    - stopsound("specific sound") -> stops that specific sound.
    """
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            if target is None:
                msg = b"STOP"
            elif target.lower() == "music":
                msg = b"STOP MUSIC"
            else:
                msg = f"STOP {target}".encode('utf-8')
            s.sendto(msg, ("127.0.0.1", 65432))
    except Exception:
        pass


def update(path, value):
    """
    Overwrites a .txt file relative to current directory.
    update("settings/music", 3)
    → writes to ./settings/music.txt
    """
    # Normalize path
    full_path = os.path.join(os.getcwd(), path + ".txt")
    # Ensure directory exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    # Overwrite file
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(str(value))
        
def read(path, default=None):
    """
    Reads ./path.txt and auto-detects type.
    Returns int, float, or string.
    """
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

# Loads an item by ID and category. If ID is 0, loads equipped items from the "active_*.txt" files. Otherwise, loads from the corresponding item file.
def load_item(item_id, category="Weapons"):
    base_dir = os.getcwd()
    items_dir = os.path.join(base_dir, "Items")

    # ─────────────────────────────────────────────
    # UNIVERSAL EQUIPPED LOADER (ID = 0)
    # ─────────────────────────────────────────────
    if str(item_id) == "0":
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
                    "level_power": 0,
                    "ability": None,
                    "locked": 0,
                    "refine": 0,
                    "special": None,
                    "specialvalue": 0,
                },
            ),
            "active_body.txt": ("Bodywear", armor, {"type_raw": None, "rarity": None, "name": None, "level": 0, "defense": 0}),
            "active_head.txt": ("Helmets", head, {"type_raw": None, "rarity": None, "name": None, "level": 0, "defense": 0}),
            "active_fragment.txt": ("Fragments", fragment, {"name": None, "level": 0}),
        }

        for filename, (cat, obj, defaults) in slot_map.items():
            path = os.path.join(items_dir, filename)

            _reset_object(obj, defaults)

            if not os.path.exists(path):
                continue

            with open(path, "r", encoding="utf-8") as f:
                content = f.readline().strip()

            if content.lower() == "none" or content == "":
                continue

            # Load actual item file via recursion
            load_item(content, cat)

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
        item.level = int(item.level)
        item.atk = int(item.atk)
        item.atkcrit = float(item.atkcrit)
        item.substat_value = int(item.substat_value)
        item.level_power = int(item.level_power)
        item.locked = int(item.locked)
        item.refine = int(item.refine)

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

        head.type_raw = parts[0]
        head.rarity = parts[1]
        head.name = parts[2]
        head.level = int(parts[3])
        head.defense = int(parts[4])
        return head

    # ───────────── BODYWEAR ─────────────
    elif category == "Bodywear":
        _clear_object(armor)

        armor.type_raw = parts[0]
        armor.rarity = parts[1]
        armor.name = parts[2]
        armor.level = int(parts[3])
        armor.defense = int(parts[4])
        return armor

    # ───────────── FRAGMENTS ─────────────
    elif category == "Fragments":
        _clear_object(fragment)

        fragment.name = parts[0]
        fragment.level = int(parts[1])

        stats = parts[2:]
        # process fragments details
        return fragment

        for i in range(0, len(stats), 2):
            stat_name = stats[i]
            stat_value = stats[i + 1] if i + 1 < len(stats) else None

            if stat_value is not None:
                try:
                    stat_value = float(stat_value)
                except ValueError:
                    pass

            setattr(fragment, f"stat{i//2 + 1}", stat_name)
            setattr(fragment, f"stat{i//2 + 1}_value", stat_value)

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
            str(getattr(item, "level_power", 0)),
            str(getattr(item, "ability", "") or ""),
            str(getattr(item, "locked", 0)),
            str(getattr(item, "refine", 0))
        ]

    # ───────────── HELMETS ─────────────
    elif category == "Helmets":
        parts = [
            head.type_raw,
            head.rarity,
            head.name,
            str(head.level),
            str(head.defense)
        ]

    # ───────────── BODYWEAR ─────────────
    elif category == "Bodywear":
        parts = [
            armor.type_raw,
            armor.rarity,
            armor.name,
            str(armor.level),
            str(armor.defense)
        ]

    # ───────────── FRAGMENTS ─────────────
    elif category == "Fragments":
        parts = [
            fragment.name,
            str(fragment.level)
        ]

        # Dynamically append stat pairs
        i = 1
        while hasattr(fragment, f"stat{i}"):
            stat_name = getattr(fragment, f"stat{i}")
            stat_value = getattr(fragment, f"stat{i}_value", None)

            parts.append(str(stat_name))
            parts.append(str(stat_value))

            i += 1

    else:
        raise ValueError(f"Unknown category: {category}")

    line = ";;".join(parts)

    with open(path, "w", encoding="utf-8") as f:
        f.write(line)




BASE = Path("Settings/Keybinds")
# Loads a bind by name. E.g. load_bind("attack") would read the "attack.txt" file in the Keybinds folder and return the value.
def load_bind(name):
    value = read(BASE / f"{name}.txt").strip()
    return value
    
def setbinds():
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
setbinds()

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
        
def draw_box(
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

def center(text, row):
    cols = os.get_terminal_size().columns
    text_len = visible_len(text)
    col = max(1, (cols - text_len) // 2 + 1)
    draw_text(col, row, text)

# why? Don't ask. Just... rainbow text. That's all.
def rainbow(text, offset=0, bold=False, italic=False):
    colors = [
        (255, 100, 100),
        (255, 180, 100),
        (255, 255, 120),
        (120, 255, 120),
        (120, 180, 255),
        (180, 120, 255),
        (255, 100, 100),
    ]

    result = ""
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
def shine(text, offset=0, color=(255, 255, 0), bold=False):
    result = ""
    length = max(len(text), 1)

    # 🔁 cycle
    cycle = offset % 1.0

    # ⚙️ tuning
    active_window = 0.75   # how long shine is active
    width = 0.6           # how wide the shine is
    intensity = 3         # intensity falloff (higher = sharper shine, lower = more spread out)

    for i, char in enumerate(text):
        t = i / (length - 1) if length > 1 else 0

        if cycle > active_window:
            # 💤 fully idle (no shine at all)
            r, g, b = 255, 255, 255

        else:
            # normalize 0 → 1 within active window
            t_cycle = cycle / active_window

            # 👇 IMPORTANT: extend travel range
            center = -width + t_cycle * (1 + 2 * width)

            dist = abs(t - center)

            # smooth falloff
            strength = max(0, 1 - dist * intensity)

            r = int(255 * (1 - strength) + color[0] * strength)
            g = int(255 * (1 - strength) + color[1] * strength)
            b = int(255 * (1 - strength) + color[2] * strength)
        style = "\033[1m" if bold else ""
        result += f"\033[38;2;{r};{g};{b}m{style}{char}"
    return result + "\033[0m"

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
INTERFACE
Here's where... you really don't want to look. This is the absolute mess of hardcoded coordinates, colors, and styles that
creates the actual game interface. It's a nightmare to maintain, but it works, so good luck.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def startup_animation():
    cls()
    fade_duration = 1
    steps = 25
    step_delay = fade_duration / steps
    
    art = f"""
    [1;4H{x7}⁺    ⁺     ⋆⁺₊⋆⁺₊⋆₊    ⋆⁺ ₊⋆  ⁺₊⋆     ⁺    ⋆⁺    ⋆⁺₊⋆⁺₊⋆   ⁺ ⋆⁺₊⋆₊⋆⁺ ⁺₊⋆     ⁺     ⋆⁺₊⋆⁺₊     ⋆⁺₊⋆  ⁺₊⋆ ⁺        ⋆⁺₊ ⋆⁺₊  {reset}
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
        time.sleep(step_delay)

    game.skip_mainmenu_cls = True
    game.goto = mainmenu
    return


def mainmenu():
    if not getattr(game, "skip_mainmenu_cls", False):
        cls()
        print(f"""
        [1;4H{x7}⁺    ⁺     ⋆⁺₊⋆⁺₊⋆₊    ⋆⁺ ₊⋆  ⁺₊⋆     ⁺    ⋆⁺    ⋆⁺₊⋆⁺₊⋆   ⁺ ⋆⁺₊⋆₊⋆⁺ ⁺₊⋆     ⁺     ⋆⁺₊⋆⁺₊     ⋆⁺₊⋆  ⁺₊⋆ ⁺        ⋆⁺₊ ⋆⁺₊  {reset}
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
        if not game.updatable:
            center(f"{xf}{italic}{random.choice(tips)}{reset}", 8)
        else:
            time.sleep(0.2)
            center(f"{xf}{italic}{random.choice(tips)}{reset}    {xb}{bold}✨ New Battles of Bench update available!{reset} {xf}Press {bold}[Ctrl+U]{reset} to update the game.{reset}", 8)    
    else:
        game.skip_mainmenu_cls = False
    # display announcement if new version is available:
    if game.updatable:
            sound("announcement")
            game.updatable = False  # prevent repeated announcements
    offset = 0
    while True:
        offset += 0.005
        print(f"[33;1H{x8}______│_____│_______│_____│_______│__[ == ==]/{x7}.::::::;;; {xlred}{bold}{shine("[B] to battle",offset=offset, color=(255, 71, 76), bold=True)}{reset}{x7} ;;;:::::::.{x8}\\[=  == ]___│_______│_______│_______│___│__{reset}")
        print(f"[34;1H{reset}{shine('[Ctrl+T] to modify data', offset=offset, bold=True, color=(132, 224, 133))}",end="",flush=True)
        k = key(timeout=0)
        if k.lower() == "b":
            sound("woosh")
            subprocess.run(["py", "wipe.py", "normal", "10"])
            game.goto = battle
            return
        if k.lower() == "1":
            sound("door2")
            game.goto = house
            return
        # cheats interface (terminal) => Ctrl+T
        if k.lower() == "ctrl/t":
            game.goto = modify
            return
        time.sleep(0.01)
        # play sound: ctrl+R
        if k.lower() == "ctrl/r":
            game.goto = sounds_test
            return
        # update gane: ctrl+U
        if k.lower() == "ctrl/u" and game.updatable:
            game.goto = updater
            return

def sounds_test():
    while True:
        # enter sound
        cls()
        # ask for sound and pitch with input
        print("Enter sound name:")
        name = input().strip()
        # if name is back, go back to main menu
        if name.lower() == "back":
            game.goto = mainmenu
            return
        print("Enter pitch:")
        try:
            pitch = float(input().strip())
        except ValueError:
            pitch = 1.0
        sound(f"{name} {pitch}")


def modify():
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
            k = key()
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
    setbinds()
    load_item(0)

    targets = {
        "p": ("player", player),
        "w": ("weapon", item),
        "h": ("head", head),
        "a": ("armor", armor),
        "f": ("fragment", fragment),
        "g": ("general", d),
        "y": ("system", game),
        "s": ("settings", setting),
    }

    slot_paths = {
        "w": ("Weapon", "Items/active_weapon"),
        "h": ("Head", "Items/active_head"),
        "a": ("Armor", "Items/active_body"),
        "f": ("Fragment", "Items/active_fragment"),
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
{x4}[+]{xf} 💥 Clear or reset...
{xf}--------------------------------------------
{xc}[B]{xf} Back to main menu
{reset}
""")

            choice = read_key_choice({"p", "n", "w", "h", "a", "f", "g", "y", "s", "e", "k", "+", "b"})

            if choice == "b":
                game.goto = mainmenu
                return

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
                            input(f"{x8}Cancelled.{xf} Press Enter to continue...")
                            continue
                        if os.path.exists(delete_screen_path):
                            os.remove(delete_screen_path)
                            input(f"{xa}Deleted.{xf} Press Enter to continue...")
                        else:
                            input(f"{x8}File not found, nothing to delete.{xf} Press Enter to continue...")
                        continue

                    if adv_choice == "u":
                        if not confirm_destructive("Delete General/setup.txt?"):
                            input(f"{x8}Cancelled.{xf} Press Enter to continue...")
                            continue
                        if os.path.exists(delete_setup_path):
                            os.remove(delete_setup_path)
                            input(f"{xa}Deleted.{xf} Press Enter to continue...")
                        else:
                            input(f"{x8}File not found, nothing to delete.{xf} Press Enter to continue...")
                        continue

                    target_idx = int(adv_choice) - 1
                    target_label, target_obj = reset_targets[target_idx]
                    if not confirm_destructive(f"Reset {target_label}?"):
                        input(f"{x8}Cancelled.{xf} Press Enter to continue...")
                        continue

                    try:
                        target_obj.reset()
                        if target_obj is bind:
                            setbinds()
                        if target_obj is setting:
                            setting.load()
                        if target_obj is player:
                            player.load()
                        input(f"{xa}Reset complete:{xf} {target_label}. Press Enter to continue...")
                    except Exception as exc:
                        input(f"{xlred}Reset failed:{xf} {exc}. Press Enter to continue...")
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
                new_name = input(f"{x3}New name{xf}: ").strip()
                if new_name.lower() == "b":
                    continue
                if len(new_name) < 2 or len(new_name) > 15:
                    input(f"{xlred}Name must be between 2 and 15 characters.{xf} Press Enter to continue...")
                    continue

                update("General/playername", new_name)
                player.name = new_name
                input(f"{xa}Saved{xf} player name as {new_name!r}. Press Enter to continue...")
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
    {xa}Fragment{xf}: {read('Items/active_fragment', default='none')}

{xf}Choose slot:
    {xa}[W]{xf} Weapon
    {xa}[H]{xf} Head
    {xa}[A]{xf} Armor
    {xa}[F]{xf} Fragment

{xc}[B]{xf} Back
{reset}
""")

                    slot_choice = read_key_choice({"w", "h", "a", "f", "b"})
                    if slot_choice == "b":
                        break

                    slot_name, slot_path = slot_paths[slot_choice]
                    raw_id = input(f"{x3}New item ID for {slot_name}{xf} ({xc}B{xf}=back, Enter=none): ").strip()
                    if raw_id.lower() == "b":
                        continue

                    if raw_id == "" or raw_id.lower() == "none":
                        update(slot_path, "none")
                        try:
                            load_item(0)
                            msg = f"{x2}Updated{xf} {slot_name} slot to {xa}'none'{xf}."
                        except Exception as exc:
                            msg = f"{xlorange}Updated file to 'none', but loading failed:{xf} {exc}"
                        input(msg + " Press Enter to continue...")
                        continue

                    try:
                        new_id = int(raw_id)
                        if new_id < 0:
                            raise ValueError()
                    except ValueError:
                        input(f"{xlred}Please enter a valid non-negative number.{xf} Press Enter to continue...")
                        continue

                    update(slot_path, new_id)
                    try:
                        load_item(0)
                        msg = f"{x2}Updated{xf} {slot_name} slot to item ID {new_id}."
                    except Exception as exc:
                        msg = f"{xlorange}Updated file, but loading failed:{xf} {exc}"
                    input(msg + " Press Enter to continue...")
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

                    field = input(f"{x3}Keybind{xf}: ").strip().lower()
                    if field == "b":
                        break
                    if field not in bind._persistent_fields:
                        input(f"{xlred}Unknown keybind.{xf} Press Enter to continue...")
                        continue

                    raw_value = input(f"{x3}New value for {field}{xf} (current={getattr(bind, field)!r}) [{xc}B{xf}=back]: ").strip()
                    if raw_value.lower() == "b":
                        continue
                    if raw_value == "":
                        input(f"{xlred}Keybind cannot be empty.{xf} Press Enter to continue...")
                        continue

                    setattr(bind, field, raw_value.lower())
                    bind.save()
                    setbinds()
                    input(f"{x2}Saved{xf} keybind {field} = {raw_value.lower()!r}. Press Enter to continue...")
                continue

            if choice not in targets:
                input(f"{xlred}Invalid option.{xf} Press Enter to continue...")
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

                field = input(f"{x3}Attribute{xf}: ").strip()

                if field.lower() == "b":
                    break

                current_value = getattr(target_obj, field, "<missing>")
                raw_value = input(f"{x3}New value for {field}{xf} (current={current_value!r}) [{xc}B{xf}=back]: ").strip()

                if raw_value.lower() == "b":
                    continue

                new_value = parse_override_value(raw_value)
                setattr(target_obj, field, new_value)

                # Persist canonical player/settings fields automatically.
                if target_obj is player and field in getattr(player, "_persistent_fields", {}):
                    player.save()
                    save_note = " (saved to Player/data.txt)"
                elif target_obj is setting and field in getattr(setting, "_persistent", {}):
                    setting.save()
                    save_note = " (saved to Settings/settings.txt)"
                elif target_obj in (item, head, armor, fragment):
                    category_map = {
                        item: ("Items/active_weapon", "Weapons"),
                        head: ("Items/active_head", "Helmets"),
                        armor: ("Items/active_body", "Bodywear"),
                        fragment: ("Items/active_fragment", "Fragments"),
                    }
                    active_path, category_name = category_map[target_obj]
                    active_id = read(active_path, default=0)
                    try:
                        active_id = int(active_id)
                    except Exception:
                        active_id = 0

                    if active_id > 0:
                        save_item(active_id, category_name)
                        save_note = f" (saved to Items/{category_name}/item{active_id}.txt)"
                    else:
                        save_note = " (runtime only: no active item id to save)"
                else:
                    save_note = ""

                print(f"{xa}Set{xf} {target_name}.{field} = {new_value!r}{save_note}")
                input("Press Enter to continue...")
    finally:
        cursor(False)

def battle():
    cls()
    print("battle")
    while True:
        k = key()
        if k.lower() == "b":
            game.goto = mainmenu
            return
    

def house():
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
{player.color}       ██████       {x8}│{player.color}{bold}  This is your house, welcome in!  {reset}{x8}  │  {xlyellow}{bold}[C]{reset}{xe} 🚶 Manage character          {x8}  │ 
{player.color}         ██         {x8}│{x9}                                    {x8} │   ╰─ {x2}{bold}[I]{reset}{xa} 💼 Enter inventory       {x8}  │           
{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x3}{bold}[E]{reset}{xb} 💎 Convert excess XP     {x8}  │ 
{player.color}         ██  ██     {x8}│{xlyellow}  character or personalization will {x8} │{x1}                                   {x8}  │ 
{player.color}      ███████       {x8}│{xlyellow}  be displayed here on the right!   {x8} │  {x7}{bold}[S]{reset}{xf} ⚙️ Settings & info           {x8}  │ 
{player.color}    ██   ██         {x8}│{x9}                                    {x8} │{x1}                                   {x8}  │  
{player.color}         ██         {x8}│{xlorange}  To access any option on the right,{x8} │  {x5}{bold}[R]{reset}{xd} 🎧 Refresh game music       {x8}   │ 
{player.color}         ██         {x8}│{xlorange}  simply press the keys that are{x8}     │                                   {x8}  │    
{player.color}       ██  ██       {x8}│{xlorange}  shown next to them!            {x8}    │  {xc}{bold}[{bind.back_display}] {reset}🏡 {xlred}{italic}<- Return to the main menu{x8}{x8}  │ 
{player.color}     ██      ██     {x8}│{x9}                                    {x8} │                                     │              
{player.color}                    {x8}╰{x8}────────────────────────────────────{x8}─┴─────────────────────────────────────╯         
    """)
    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            game.goto = mainmenu
            return
        if k.lower() == "s":
            game.goto = settings
            return
        if k.lower() == "i":
            game.goto = inventory
            return
        if k.lower() == "c":
            sound("map_right")
            game.goto = character
            return
        # this is the pitch testing code!
        if k.lower() == "o":
            draw_box(32,20,34,60,text="Enter an int 1 to 50:",bold=True,text_color=xlyellow)
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

# (i'm sorry)
def character():
    player.load()
    setbinds()
    load_item(0)
    cls()
    thresholds = [
        (0, x8), (5, x7), (10, xf),(15, x3),(20, x9),(25, xb),(30, x2),(35, xa),(40, xlorange),(45, xlyellow),(50, xe),(55, x5),(60, xd),(65, xlred),(70, xc),(75, x4),(80, rgb(184, 172, 246)),(85, rgb(254, 163, 98)),(90, rgb(186, 243, 219)),(95, rgb(255, 131, 101)),(100, rgb(227, 62, 57)),
    ]
    player.color = None
    for req_level, color in thresholds:
        if player.level >= req_level:
            player.color = color
    scales = [None]
    
    scales.extend([
        {"mdmg": 80,  "sdmg": 175, "ulthp": 5,  "erch": 100},
        {"mdmg": 84,  "sdmg": 185, "ulthp": 6,  "erch": 100},
        {"mdmg": 88,  "sdmg": 195, "ulthp": 7,  "erch": 100},
        {"mdmg": 95,  "sdmg": 210, "ulthp": 8,  "erch": 100},
        {"mdmg": 100, "sdmg": 225, "ulthp": 10, "erch": 100},
        {"mdmg": 104, "sdmg": 235, "ulthp": 11, "erch": 102},
        {"mdmg": 108, "sdmg": 240, "ulthp": 12, "erch": 104},
        {"mdmg": 112, "sdmg": 250, "ulthp": 13, "erch": 106},
        {"mdmg": 116, "sdmg": 260, "ulthp": 14, "erch": 110},
        {"mdmg": 125, "sdmg": 275, "ulthp": 15, "erch": 115},
        {"mdmg": 130, "sdmg": 290, "ulthp": 17, "erch": 120},
        {"mdmg": 136, "sdmg": 305, "ulthp": 18, "erch": 124},
        {"mdmg": 140, "sdmg": 320, "ulthp": 20, "erch": 126},
        {"mdmg": 144, "sdmg": 335, "ulthp": 22, "erch": 130},
        {"mdmg": 180, "sdmg": 390, "ulthp": 33, "erch": 145},
    ])
    ref = scales[player.skills]
    player.dmg_main = ref["mdmg"]
    player.dmg_skill = ref["sdmg"]
    player.dmg_ulthp = ref["mdmg"]
    player.energyrecharge = ref["sdmg"]
    boxwidth = 25
    playername=read("General/playername")
    playernamd = f"{playername} › Attributes"
    length = visible_len(playernamd)
    pad = (boxwidth - length) // 2 + 1
    spaces = " " * max(pad, 0)
    centered = spaces + playernamd
    x=player.level
    basehp=50 + (x-1)*20 + ((x-1)*(x+2))/4
    baseatk=player.level*10
    basedef=round(player.level*0.3,1)

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
    # let's make crit rate
    # base crit rate is 15%
    base_crit_rate = 15
    # if weapon substat is crit rate, add the same
    weapon_crit_rate = 0
    if getattr(item, "substat", None) == "Crit Rate":
        weapon_crit_rate = item.substat_value
    # any bonuses:
    bonus_crit_rate = 0
    # for every 10 levels of player, +1% crit rate
    level_crit_rate = (player.level // 10) * 1
    player.crit_rate = base_crit_rate + weapon_crit_rate + level_crit_rate + bonus_crit_rate
    del base_crit_rate, weapon_crit_rate, level_crit_rate, bonus_crit_rate
    
    abilityatk=0
    abilitydef=0
    abilityhp=0
    totaldmg=round(baseatk*185/100 + abilityatk*4 + item.atk/5)
    totalcritdmg=round(totaldmg*(1+item.atkcrit/100))
    item.atkcrit = round(item.atkcrit)
    basehp = round(basehp)
    basedef = round(basedef,1)
    critrate = round(player.crit_rate)
    expected = round(totaldmg * (1 + (critrate / 100) * (item.atkcrit / 100)))
    number = 1
    # --- Defence ---
    totaldef = basedef

    if getattr(item, "substat", None) == "Defence":
        totaldef += item.substat_value

    if getattr(armor, "name", None):
        totaldef += armor.defense

    if getattr(head, "name", None):
        totaldef += head.defense


    # --- Health ---
    totalhp = basehp

    if getattr(item, "substat", None) == "Health":
        totalhp += item.substat_value
    # ===== INPUTS =====
    EXP = player.xp
    EXP_NEEDED = player.xpneeded

    # ===== CONFIG =====
    BAR_LENGTH = 30
    FILLED_SEG = f"{xa}█"
    EMPTY_SEG = f"{x0}█"

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
    # base dodge rate is 5
    base_dodge = 5
    # for every 10 levels in armor, +0.1% dodge rate
    armor_dodge = (getattr(armor, "level", 0) // 10) * 0.1
    # weapon if substat if dodge, add the same
    weapon_dodge = 0
    if getattr(item, "substat", None) == "Dodge":
        weapon_dodge = item.substat_value
    # headwear dodge functions exactly like armor
    head_dodge = (getattr(head, "level", 0) // 10) * 0.1
    player.dodge = base_dodge + armor_dodge + weapon_dodge + head_dodge
    del base_dodge, armor_dodge, weapon_dodge, head_dodge  
    
    # now, let's do effect res
    # for example, either reduce duration of negative effects by x%, or reduce their potency by x%
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
    base_life_steal = 0.1
    # for every 10 levels in weapon, +0.05% life steal
    weapon_life_steal = (getattr(item, "level", 0) // 10) * 0.05
    # if weapon substat, add the same
    if getattr(item, "substat", None) == "Life Steal":
        weapon_life_steal += item.substat_value    
    # if any bonuses:
    bonus_life_steal = 0
    player.life_steal = base_life_steal + weapon_life_steal + bonus_life_steal
    
    # regeneration (get more hp from potions)
    # base potion gives 20% back
    base_regen = 0.2
    # if weapon substat is regen, add the same
    weapon_regen = 0
    if getattr(item, "substat", None) == "Regeneration":
        weapon_regen = item.substat_value
    # any bonuses:
    bonus_regen = 0
    player.regen = base_regen + weapon_regen + bonus_regen
    del base_regen, weapon_regen, bonus_regen
    
    # let's make speed work
    # base speed is 100
    base_speed = 100
    # if weapon substat is speed, add the same
    weapon_speed = 0
    if getattr(item, "substat", None) == "Speed":
        weapon_speed = item.substat_value
    # for every 10 levels of player, +5 speed
    level_speed = (player.level // 10) * 5
    # any bonuses:
    bonus_speed = 0
    player.speed = base_speed + weapon_speed + level_speed + bonus_speed
    del base_speed, weapon_speed, level_speed, bonus_speed
    
    
    
    # now, make total ATK, DEF and Hp actually global
    player.total_dmg = totaldmg
    player.total_def = totaldef
    player.total_hp = totalhp
    
    print(f"""
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
[26;3H{x6}{bold}╭────────────────────────────────────╮
[27;3H{x6}{bold}│                                    │
[28;3H{x6}{bold}│ {reset}{xf}{bold}→      {xlyellow}Viewing {reset}{xf}-{xe} Attributes      {xf}{bold}←{x6}{bold} │
[29;3H{x6}{bold}│                                    │
[30;3H{x6}{bold}╰────────────────────────────────────╯{reset}
[31;3H{x7}╭────────────────────────────────────╮
[32;3H{x7}│ {xf}↓ Press {xlyellow}{bold}[S] once{reset}{xe} {xf}-{xe} Equipment       {x7}│
[33;3H{x7}╰────────────────────────────────────╯
[34;3H{x7}╭────────────────────────────────────╮

[35;3H{x7}│ {xf}⇓ Press {xlyellow}{bold}[S] twice {reset}{xe}{xf}-{xe} Skill tree{reset}{x7}     │
[15;20H{item.type} {xlyellow}Attack{reset}{x8}.....{bold}{xe}{round(totaldmg)}{reset}
[16;20H🛡️ {x3}Defence{reset}{x8}....{bold}{xb}{round(totaldef,1)}%{reset}
[17;20H❤️ {xc}Health{reset}{x8}.....{bold}{xlred}{round(totalhp)} {reset}
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
[11;62H{RGB}255;219;187mBase ATK{x8}------{xlyellow}{bold}{baseatk}{reset}
[12;60H{reset}† 
[12;62H{RGB}255;219;187mWeapon{x8}--------{xlyellow}{bold}{item.atk}{reset}
[13;60H{reset}✸ 
[13;62H{RGB}255;219;187mCrit Rate{x8}-----{xlyellow}{bold}{player.crit_rate}%{reset}
[14;60H{reset}※ 
[14;62H{RGB}255;219;187mCrit DMG{x8}------{xlyellow}{bold}{item.atkcrit}%{reset}
[15;60H{reset}⟐ 
[15;62H{RGB}255;219;187mSpeed{x8}---------{xlyellow}{bold}{player.speed}{reset}
[18;44H{reset}{RGB}255;219;187m⇝{xf} 
[13;101H{reset}⌬ 
[13;103H{RGB}186;243;219mSkill Lv.{x8}-----{xa}{bold}{player.skills}{reset}{RGB}186;243;219m/15{reset}
[14;101H{reset}⇋ 
[14;103H{RGB}186;243;219mWeapon Lv.{x8}----{xa}{bold}{getattr(item, "level", 0)}{reset}{RGB}186;243;219m/{player.level}{reset}
[21;86H{reset}{RGB}186;243;219m⇝{xf} 
[21;88HHigher levels provide upgrades to {reset}
[22;86H{reset}{RGB}255;219;187m {xf} 
[22;88Hhealth, defence and power. Moreover{reset}
[23;86H{reset}{RGB}255;219;187m {xf} 
[23;88Hthey also unlock skill tree items.{reset}
[21;44H{reset}{RGB}255;219;187m•{xf} 
[21;46HDamage every normal hit: {RGB}255;219;187m{bold}{totaldmg}{reset}

[29;60H{reset}◇ 
[29;62H{RGB}173;216;225mBase DEF{x8}------{xb}{bold}{basedef}%{reset}
[30;60H{reset}∆ 
[30;62H{RGB}173;216;225mArmour DEF{x8}----{xb}{bold}{getattr(armor, "defense", 0)}%{reset}
[31;60H{reset}⦿ 
[31;62H{RGB}173;216;225mHelmet DEF{x8}----{xb}{bold}{getattr(head, "defense", 0)}%{reset}
[32;60H{reset}★ 
[32;62H{RGB}173;216;225mBonus DEF{x8}-----{xb}{bold}{abilitydef}%{reset}
[33;60H{reset}⊗ 
[33;62H{RGB}173;216;225mDodge Rate{x8}----{xb}{bold}{player.dodge}%{reset}
[29;101H{reset}♥ 
[29;103H{RGB}255;203;204mBase HP{x8}---------{xlred}{bold}{basehp}{reset}
[30;101H{reset}♡ 
[30;103H{RGB}255;203;204mBonus HP{x8}--------{xlred}{bold}{abilityhp}{reset}
[31;101H{reset}⬣ 
[31;103H{RGB}255;203;204mEffect RES{x8}------{xlred}{bold}{round(player.effect_res)}%{reset}
[32;101H{reset}↺ 
[32;103H{RGB}255;203;204mRegeneration{x8}----{xlred}{bold}{round(player.regen,1)}%{reset}
[33;101H{reset}⸕ 
[33;103H{RGB}255;203;204mLife Steal{x8}------{xlred}{bold}{round(player.life_steal,1)}%{reset}
[36;42H{RGB}173;216;225m╰───────────────────────────────────────╯ {RGB}255;203;204m╰─────────────────────────────────────────╯
[36;3H{x7}╰────────────────────────────────────╯{reset}
""".strip().replace("\n", ""),end="",flush=True)
    if item.type_raw is not None: print(f"""
[18;46HYour {item.type_raw} {bold}crits {RGB}255;219;187m{player.crit_rate}%{reset} of the time,{reset}
[19;46H{reset}in which case you deal {RGB}255;219;187m{bold}+{item.atkcrit}%{reset} DMG:
[22;44H{reset}{RGB}255;219;187m•{xf} 
[22;46HDamage every critical hit: {RGB}255;219;187m{bold}{totalcritdmg}{reset}
[23;44H{reset}{RGB}255;219;187m•{xf} 
[23;46HExpected average damage: {RGB}255;219;187m{bold}{expected}{reset}
""".strip().replace("\n",""),end="",flush=True)  # noqa: E701
    if item.type_raw is None or item.type_raw == "None": print(f"""
[18;46HYour fists are {xlred}too weak{reset} to crit,{reset}
[19;46H{reset}so all your hits perform the same:
""".strip().replace("\n",""),end="",flush=True)  # noqa: E701
        # ===== RESULT =====
    print(f"[12;101H{reset}✧ [12;103H{RGB}186;243;219mLevel{x8}---------{xa}{bold}{player.level}{reset}{RGB}186;243;219m/100{reset}")
    EXP = 0
    fragments=50
    for i in range(fragments):
        EXP += round(player.xp/fragments)
        
        EXP_NEEDED = player.xpneeded

        # ===== CONFIG =====
        BAR_LENGTH = 30
        FILLED_SEG = f"{xa}█"
        EMPTY_SEG = f"{x0}█"

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
        print(f"\033[18;86H{reset}{rgb(255,219,187)}{rgb(186,243,219)}✚{xf}\033[18;88H{bold}EXP: {EXP_BAR}{reset}", end="")
        if round(player.xp/player.xpneeded*100) < 10:
            print(f"{xf}{bold}{rgback(0,0,1)}\033[18;94H{round(EXP/player.xpneeded*100)}%")
        else:
            print(f"{xba}{xf}{bold}\033[18;94H{round(EXP/player.xpneeded*100)}%")
        print(f"\033[19;93H{reset}{x7}{rgb(186,243,219)}↑ {bold}{EXP}/{EXP_NEEDED} {reset}XP to get level {player.level+1}{reset}")
    EXP = player.xp
    # ===== CONFIG =====
    BAR_LENGTH = 30
    FILLED_SEG = f"{xa}█"
    EMPTY_SEG = f"{x0}█"

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
    print(f"\033[18;86H{reset}{rgb(255,219,187)}{rgb(186,243,219)}✚{xf}\033[18;88H{bold}EXP: {EXP_BAR}{reset}", end="")
    if round(player.xp/player.xpneeded*100) < 10:
            print(f"{xf}{bold}{rgback(0,0,1)}\033[18;94H{round(player.xp/player.xpneeded*100)}%")
    else:
            print(f"{xba}{xf}{bold}\033[18;94H{round(player.xp/player.xpneeded*100)}%")
    print(f"\033[19;93H{reset}{x7}{rgb(186,243,219)}↑ {bold}{player.xp}/{player.xpneeded} {reset}XP to get level {player.level+1}{reset}")
    print(f"""
[15;20H{item.type} {xlyellow}Attack{reset}{x8}.....{bold}{xe}{round(totaldmg)}{reset}
[16;20H🛡️ {x3}Defence{reset}{x8}....{bold}{xb}{round(totaldef,1)}%{reset}
[17;20H❤️ {xc}Health{reset}{x8}.....{bold}{xlred}{round(totalhp)} {reset}
""".strip().replace("\n",""),end="",flush=True)
    del hpsymbol1,hpsymbol2,hpsymbol3,hpsymbol4,hpsymbol5,hpsymbol6,hpsymbol7, atksymbol1,atksymbol2,atksymbol3,atksymbol4,atksymbol5,atksymbol6,atksymbol7,defsymbol1,defsymbol2,defsymbol3,defsymbol4,defsymbol5,defsymbol6,defsymbol7,lvsymbol1,lvsymbol2,lvsymbol3,lvsymbol4,lvsymbol5,lvsymbol6,lvsymbol7
    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            game.goto = house
            return

def settings():
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
{player.color}                    {x8}│{xf}  {xlorange}🔎 {bold}Press space to search...    {reset}{x8}    │  {xc}{bold}[{bind.back_display}] {reset}🏡 {xlred}{italic}<- Return to your house{x8}{x8}     │ 
{player.color}  {x8}{italic}                  {reset}{x8}│{x9}                                    {x8} │                                     │              
{player.color} {x8}{italic}     {reset}        {x8}{italic}      {reset}{x8}╰{x8}────────────────────────────────────{x8}─┴─────────────────────────────────────╯   
    """,end="")
    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            game.goto = house
            return
            
def inventory():
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
{player.color}         ██         {x8}│{xe}  Your inventory has an unlimited   {x8} │  {xlyellow}{bold}[E]{reset}{xe} 🧰 View everything else      {x8}  │ 
{player.color}         ██         {x8}│{xe}  capacity - store as many things as {x8}│                                   {x8}  │    
{player.color}       ██  ██       {x8}│{xe}  you need! Now, select an option:  {x8} │  {xc}{bold}[{bind.back_display}] {reset}🏡 {xlred}{italic}<- Return to your house{x8}{x8}     │ 
{player.color}     ██      ██     {x8}│{x9}                                    {x8} │                                     │              
{player.color}                    {x8}╰{x8}────────────────────────────────────{x8}─┴─────────────────────────────────────╯   
    """)
    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            game.goto = house
            return
        if k.lower() == "1":
            game.sel = "Weapons"
            game.goto = maininv
            return

def screensetup():
    cls()
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
            with open("general/screensetup.txt", "w") as f:
                f.write("okay")
            game.goto = startup
            return
        else:
            game.goto = screensetup
            return

def setup():
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
    center(f"{xlorange}🔸 press A on your keyboard to start setup 🔸",row=29)
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

                  {xlorange}Change the course of history! Enter what you'd want to be called, then hit {bold}Enter {reset}{xlorange}to confirm.
                 {xlorange}⚠️ Your new name must be between {bold}{xlred}2 and 15 {reset}{xlorange}characters. Try not to become the next Picasso here!

                                {x7}╭┤ {xb}Enter your new name here...{x7} ├─────────────────────╮
                                {x7}│ {xb}{bold}› {x7}                                                 │
                                {x7}╰────────────────────────────────────────────────────╯{reset}
""".strip(),end="",flush=True)
    player.name = getx(23,35,f"{xb}{bold}› {xf}{bold}",max_len=15)
    # save player name into settings (general/playername.txt)
    with open("general/playername.txt", "w") as f:
        f.write(player.name)
    # setup confirmed! write into setup
    with open("general/setup.txt", "w") as f:
        f.write("okay")
    sound("level_ascend")
    # wipe screen with animation (using wipe.py)
    subprocess.run(["py", "wipe.py", "normal", "15"])
    game.goto = startup
    return


def check_update():
    import urllib.request
    try:
        req = urllib.request.Request(
            'https://api.github.com/repos/chair-dev-364/Battles-of-Bench-Python/commits/main',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            remote_sha = data.get('sha')
        
        local_sha = None
        version_file = os.path.join(os.getcwd(), "General", "version.txt")
        if os.path.exists(version_file):
            with open(version_file, "r") as f:
                local_sha = f.read().strip()
        else:
            try:
                local_sha = subprocess.check_output(['git', 'log', '-1', '--format=%H'], stderr=subprocess.DEVNULL).decode().strip()
            except Exception:
                pass
                
        if remote_sha and local_sha != remote_sha:
            game.updatable = True
            game.remote_sha = remote_sha
        else:
            game.updatable = False
    except Exception:
        game.updatable = False

def updater():
    import shutil
    import tempfile
    import stat

    cursor(True)
    cls()

    base_dir = os.getcwd()
    backup_dir = os.path.join(base_dir, "Backup")
    os.makedirs(backup_dir, exist_ok=True)

    n = 1
    while os.path.exists(os.path.join(backup_dir, f"Backup{n}")):
        n += 1
    target_backup = os.path.join(backup_dir, f"Backup{n}")

    def ignore_sounds(src_dir, contents):
        ignored = []
        if os.path.basename(src_dir) == "Sounds":
            return contents
        if "Sounds" in contents:
            ignored.append("Sounds")
        if "Backup" in contents and src_dir == base_dir:
            ignored.append("Backup")
        if ".git" in contents and src_dir == base_dir:
            ignored.append(".git")
        return ignored

    print(f"{x7}\n[1] Backup creation in progress...{reset}", flush=True)
    shutil.copytree(base_dir, target_backup, ignore=ignore_sounds)
    print(f"{xa}Backup created!{reset} {target_backup}", flush=True)

    updater_script = f'''import os
import shutil
import sys
import urllib.request
import zipfile
import stat

base_dir = r"{base_dir}"
backup_dir = r"{backup_dir}"
remote_sha = {getattr(game, "remote_sha", None)!r}
zip_url = "https://github.com/chair-dev-364/Battles-of-Bench-Python/archive/refs/heads/main.zip"
zip_path = os.path.join(backup_dir, "update.zip")
extract_dir = os.path.join(backup_dir, "Battles-of-Bench-Python-main")

def log(message):
    print(message, flush=True)

log("Downloading the latest version...")
req = urllib.request.Request(zip_url, headers={{'User-Agent': 'Mozilla/5.0'}})
with urllib.request.urlopen(req) as response, open(zip_path, "wb") as out_file:
    while True:
        chunk = response.read(1024 * 64)
        if not chunk:
            break
        out_file.write(chunk)

log("Download completed!")
log("Extracting files...")
with zipfile.ZipFile(zip_path, "r") as zip_ref:
    zip_ref.extractall(backup_dir)

log("Copying updated files into place...")
def make_writable(path):
    try:
        os.chmod(path, stat.S_IWRITE)
    except OSError:
        pass

def replace_path(source, destination):
    if os.path.isdir(source):
        if os.path.isfile(destination) or os.path.islink(destination):
            make_writable(destination)
            try:
                os.remove(destination)
            except OSError:
                pass
        os.makedirs(destination, exist_ok=True)
        for name in os.listdir(source):
            replace_path(os.path.join(source, name), os.path.join(destination, name))
        return

    if os.path.isdir(destination):
        shutil.rmtree(destination, ignore_errors=True)
    elif os.path.exists(destination):
        make_writable(destination)
        try:
            os.remove(destination)
        except OSError:
            pass

    os.makedirs(os.path.dirname(destination), exist_ok=True)
    shutil.copy2(source, destination)

for item in os.listdir(extract_dir):
    source = os.path.join(extract_dir, item)
    destination = os.path.join(base_dir, item)
    replace_path(source, destination)

if remote_sha:
    version_file = os.path.join(base_dir, "General", "version.txt")
    with open(version_file, "w", encoding="utf-8") as f:
        f.write(remote_sha)

try:
    os.remove(zip_path)
except OSError:
    pass

try:
    shutil.rmtree(extract_dir)
except OSError:
    pass

log(f"\n{x7}---------------------------------------------\n{xa}Update applied. Please restart the game manually!{reset}")
'''

    fd, script_path = tempfile.mkstemp(prefix="bob_updater_", suffix=".py")
    with os.fdopen(fd, "w", encoding="utf-8") as script_file:
        script_file.write(updater_script)

    print(f"{x2}Running update command live...{reset}", flush=True)
    subprocess.run([sys.executable, "-u", script_path], cwd=base_dir)

    try:
        os.remove(script_path)
    except OSError:
        pass

    sys.exit(0)

def startup():
    check_update()
    waiting_file = os.path.join(os.getcwd(), "General", "waiting.txt")
    # Race guard: sound server may create waiting.txt shortly after startup() begins.
    saw_waiting_marker = os.path.exists(waiting_file)
    marker_wait_deadline = time.time() + 3.0
    while not saw_waiting_marker and time.time() < marker_wait_deadline:
        if sound_process.poll() is not None:
            break
        saw_waiting_marker = os.path.exists(waiting_file)
        if not saw_waiting_marker:
            time.sleep(0.05)

    if saw_waiting_marker:
        while os.path.exists(waiting_file):
            if sound_process.poll() is not None:
                break
            time.sleep(0.1)
    # check if <cd>/general/screensetup.txt exists
    if not os.path.exists("general/screensetup.txt"):
        game.goto = screensetup
        return
    # check if <cd>/general/setup.txt exists
    if not os.path.exists("general/setup.txt"):
        game.goto = setup
        return
    sound("music_alt1")
    game.goto = startup_animation
    return




def maininv_md():
    for r in range(19, 29):
        print(f"\033[{r};20H                                        ")

    d.length = len(list(Path(f"Items/{game.sel}").glob("item*.txt")))
    d.currsel = (d.page * 10) + 1
    d.current = d.begin - 1

    if d.length == d.page * 10:
        itemsel_page_prev()
        return
    gdi_pager()

def maininv():
    d.massdelete = 0
    d.current = 0
    d.hold_item = 0
    d.length = len(list(Path(f"Items/{game.sel}").glob("item*.txt")))

    if d.length == 0:
        # noitems_new() -> just placeholder for now
        return

    cls()
    cursor(False)

    # Simplified display logic, utilizing python printing
    if game.sel == "Bodywear":
        print("                                                       \033[38;5;8m██████████████        ")
        print("                                                       \033[38;5;4m██\033[38;5;6m██████████\033[38;5;8m██")
        print("                                                       \033[38;5;4m██\033[38;5;6m██████████\033[38;5;8m██")
        print("                                                       \033[38;5;4m ██\033[38;5;6m████████\033[38;5;8m██ ")
        print("                                                        \033[38;5;4m ██\033[38;5;6m██████\033[38;5;8m██  ")
        print("                                                          \033[38;5;4m ██\033[38;5;6m██\033[38;5;8m██    ")
        print("                                                             \033[38;5;4m██              ")
        print()
    elif game.sel == "Weapons":
        print("\n                                                          \033[38;2;2;74;48m██████                             ")
        print("                                                        \033[38;2;2;74;48m██\033[38;5;2m██\033[38;5;10m██\033[38;5;2m██\033[38;2;2;74;48m██  ")
        print("                                                      \033[38;2;2;74;48m██\033[38;5;2m██████\033[38;5;10m██\033[38;5;2m██\033[38;2;2;74;48m██")
        print("                                                      \033[38;2;2;74;48m██\033[38;5;2m\033[38;5;10m██████████\033[38;5;2m\033[38;2;2;74;48m██")
        print("                                                      \033[38;2;2;74;48m██\033[38;5;2m██████\033[38;5;10m██\033[38;5;2m██\033[38;2;2;74;48m██")
        print("                                                        \033[38;2;2;74;48m██\033[38;5;2m██\033[38;5;10m██\033[38;5;2m██\033[38;2;2;74;48m██  ")
        print("                                                          \033[38;2;2;74;48m██████                             ")
    
    # Rest of the static UI drawing
    print(f"\033#3{reset}                  {x2}╭───────────────────────{x2}╮")
    print(f"\033#4                  {x2}╭───────────────────────{x2}╮")
    print(f"\033#3                  {x2}│        {bold}{xa}Weapons        {x2}│")
    print(f"\033#4                  {x2}│        {bold}{xa}Weapons        {x2}│")
    print(f"\033#3                  {x2}╰───────────────────────{x2}╯")
    print(f"\033#4                  {x2}╰───────────────────────{x2}╯")

    d.moving_progress = 0
    d.page = 0
    d.begin = 1
    d.end = 10

    # Drawing the borders
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

    print(f"\n                         {italic}{xlorange}Equip an item with {xlyellow}Enter{xlorange}, delete it with {xlyellow}Backspace{xlorange} or level it up with {xlyellow}Space{xlorange}.")

    print(f"{reset}\033[16;19H🔱 {bold}{xlorange}Weapons {xlyellow}{unbold}→ {xlorange}{bold}Page {bold}{d.page + 1} {unbold}{x7}(items: {xf}{bold}{d.length}{x7}{unbold}){reset}")
    print(f"\033[31;19H{xlorange}Switch pages → {xlyellow}{bold}A/D {reset}{xlorange}| Select an item → {xlyellow}{bold}W/S{reset}")

    d.currsel = 1
    gdi_pager()

def itemsel_waitkey():
    d.offset = 0
    load_item(d.currsel, game.sel)
    ityped = "🗡️"
    if item.type == "bow": ityped="🏹"
    elif item.type == "sword": ityped="⚔️"
    elif item.type == "knife": ityped="🔪"
    elif item.type == "axe": ityped="🪓"
    elif item.type == "hammer": ityped="⚒️"
    elif item.type == "pistol": ityped="🔫"
    elif item.type == "wand": ityped="🪄"
    elif item.type == "book": ityped="📖"
    ityped = item.type
    if item.rarity == "08":
        itemcolour = xf
        itemcolour_rgb = (255, 255, 255)
    elif item.rarity == "02":
        itemcolour = xa
        itemcolour_rgb = (70, 198, 107)
    elif item.rarity == "03":
        itemcolour = xb
        itemcolour_rgb = (122, 195, 230)
    elif item.rarity == "0d":
        itemcolour = xd
        itemcolour_rgb = (214, 138, 230)
    elif item.rarity == "0e":
        itemcolour = xe
        itemcolour_rgb = (240, 232, 158)
    counter = 0
    while True:
        load_item(d.currsel, game.sel)
        ityped = "🗡️"
        if item.type == "bow": ityped="🏹"
        elif item.type == "sword": ityped="⚔️"
        elif item.type == "knife": ityped="🔪"
        elif item.type == "axe": ityped="🪓"
        elif item.type == "hammer": ityped="⚒️"
        elif item.type == "pistol": ityped="🔫"
        elif item.type == "wand": ityped="🪄"
        elif item.type == "book": ityped="📖"
        ityped = item.type
        if item.rarity == "08":
            itemcolour = xf
            itemcolour_rgb = (255, 255, 255)
        elif item.rarity == "02":
            itemcolour = xa
            itemcolour_rgb = (70, 198, 107)
        elif item.rarity == "03":
            itemcolour = xb
            itemcolour_rgb = (122, 195, 230)
        elif item.rarity == "0d":
            itemcolour = xd
            itemcolour_rgb = (214, 138, 230)
        elif item.rarity == "0e":
            itemcolour = xe
            itemcolour_rgb = (240, 232, 158)
        d.offset += 0.0035
        counter += 1
        print(f"\033[1;1H{counter} / {d.offset} / currsel: {d.currsel} / current: {d.current} / begin: {d.begin} / end: {d.end} / page: {d.page}")
        print(f"\033[{d.currselrow};20H{bold}{itemcolour}{d.currsel} {unbold}› {ityped} {shine(text=item.name,bold=True,offset=d.offset,color=itemcolour_rgb)}",end="",flush=True)
        k = key(timeout=0)  # Use your key fetching function appropriately
        if k == "w":
            itemsel_rem()
        elif k == "s":
            itemsel_add()
        elif k == "a":
            itemsel_page_prev()
        elif k == "d":
            itemsel_page_next()
        elif k == bind.back:
            game.goto = inventory
            return
        time.sleep(0.01)

def unselect_current():
    item = load_item(d.currsel, game.sel)
    if not item: return
    ityped = "🗡️"
    if item.type == "bow": ityped="🏹"
    elif item.type == "sword": ityped="⚔️"
    elif item.type == "knife": ityped="🔪"
    elif item.type == "axe": ityped="🪓"
    elif item.type == "hammer": ityped="⚒️"
    elif item.type == "pistol": ityped="🔫"
    elif item.type == "wand": ityped="🪄"
    elif item.type == "book": ityped="📖"
    
    ityped = item.type

    colour = x7 if int(item.level) <= int(player.level) else xlred
    print(f"\033[{d.currselrow};20H\033[38;5;8m{d.currsel} › {ityped} \033[0m{x7}{item.name} \033[{d.currselrow};56H{colour}↑{item.level}")

def itemsel_add():
    unselect_current()
    d.currsel += 1
    if d.currsel > d.length:
        d.currsel = d.length
    elif d.currsel > d.current:
        d.currsel = d.current
    else:
        d.currselrow += 1
    displaynewsel()

def itemsel_rem():
    unselect_current()
    d.currsel -= 1
    if d.currsel < d.begin:
        d.currsel = (d.page * 10) + 1
    elif d.currsel == 0:
        d.currsel = 1
    else:
        d.currselrow -= 1
    displaynewsel()

def gdi_refresh():
    if d.moving_progress not in (1, 2):
        d.currsel = (d.page * 10) + 1
    d.current = d.begin - 1

    if d.moving_progress not in (1, 2):
        for r in range(19, 29):
            print(f"\033[{r};20H                                        ")
    gdi_pager()

def itemsel_page_next():
    if d.length > 10 + (d.page * 10):
        d.page += 1
        d.begin += 10
        d.end += 10
        d.currsel = (d.page * 10) + 1
        d.current = d.begin - 1
        gdi_refresh()

def itemsel_page_prev():
    if d.page >= 1:
        d.page -= 1
        d.begin -= 10
        d.end -= 10
        d.currsel = (d.page * 10) + 1
        d.current = d.begin - 1
        gdi_refresh()

def gdi_pager():
    d.rowdisplay = 18
    d.currselrow = 19

    for a in range(d.begin, d.end + 1):
        gdi()
    displaynewsel()
    game.goto = itemsel_waitkey

def gdi():
    while True:
        if d.length == d.current:
            break
        
        d.current += 1
        d.rowdisplay += 1
        
        item = load_item(d.current, game.sel)
        if not item: 
            break

        ityped = "🗡️" # Default
        if item.type == "bow": ityped="🏹"
        elif item.type == "sword": ityped="⚔️"
        elif item.type == "knife": ityped="🔪"
        elif item.type == "axe": ityped="🪓"
        elif item.type == "hammer": ityped="⚒️"
        elif item.type == "pistol": ityped="🔫"
        elif item.type == "wand": ityped="🪄"
        elif item.type == "book": ityped="📖"
        
        ityped = item.type

        print(f"\033[{d.rowdisplay};20H{x8}{" "*40}{xf}",end="")
        
        indicator = "↑"
        colour = x7 if int(item.level) <= int(player.level) else xlred
        if item.rarity == "08":
            itemcolour = xf
        elif item.rarity == "02":
            itemcolour = xa
        elif item.rarity == "03":
            itemcolour = xb
        elif item.rarity == "0d":
            itemcolour = xd
        elif item.rarity == "0e":
            itemcolour = xe
        print(f"\033[{d.rowdisplay};20H\033[38;5;8m{bold}{d.current} {unbold}{x7}› {ityped} {x7}{item.name} {reset}\033[{d.rowdisplay};56H{colour}{indicator}{item.level}")
        
        if d.current >= d.end:
            break
        print(f"\033[1;1H{x8}page: {d.page} | current: {d.current} | begin: {d.begin} | end: {d.end}        ")
        if d.current >= (d.page) * 10:
            break

def displaynewsel():
    # Always re-calculate current row to prevent cursor drift
    d.currselrow = 8 + d.currsel - ((d.page - 1) * 10)
    
    for r in range(18, 30):
        if r != 30:
            print(f"\033[{r};62H                                                ")
    print(f"\033[31;62H                                                ")

    item = load_item(d.currsel, game.sel)
    if not item: return

    ityped = "🗡️" # Default or lookup based on item.type
    if item.type == "bow": ityped="🏹"
    elif item.type == "sword": ityped="⚔️"
    elif item.type == "knife": ityped="🔪"
    elif item.type == "axe": ityped="🪓"
    elif item.type == "hammer": ityped="⚒️"
    elif item.type == "pistol": ityped="🔫"
    elif item.type == "wand": ityped="🪄"
    elif item.type == "book": ityped="📖"
    
    ityped = item.type

    # Write selection in list
    indicator = "↑"
    colour = x7 if int(item.level) <= int(player.level) else xlred
    if item.rarity == "08":
        itemcolour = xf
        itemcolour_rgb = (255, 255, 255)
    elif item.rarity == "02":
        itemcolour = xa
        itemcolour_rgb = (70, 198, 107)
    elif item.rarity == "03":
        itemcolour = xb
        itemcolour_rgb = (122, 195, 230)
    elif item.rarity == "0d":
        itemcolour = xd
        itemcolour_rgb = (214, 138, 230)
    elif item.rarity == "0e":
        itemcolour = xe
        itemcolour_rgb = (240, 232, 158)
    colour = x7 if int(item.level) <= int(player.level) else xlred
    d.offset = 0
    print(f"\033[{d.currselrow};20H{bold}{itemcolour}{d.currsel} {unbold}› {ityped} {shine(text=item.name, color=itemcolour_rgb,bold=True,offset=d.offset)} {reset}\033[{d.currselrow};56H{colour}{indicator}{item.level}")
    #print(f"\033[{d.currselrow};20H{d.current} {unbold}{xa}› {ityped}{itemcolour}{bold} \033[0m{item.name} {reset}\033[{d.rowdisplay};56H{colour}{indicator}{item.level}")
    # Write Description UI
    print(f"\033[16;63H{item.type}{bold}{itemcolour} {item.name} {reset}")
    print(f"\033[24;66H❇️ {xa}{bold}{item.atk}{unbold} ATK")
    # if item.atkcrit can also be an int (0 after decimal point), convert to int
    try:
        atkcrit = int(float(item.atkcrit))
    except ValueError:
        atkcrit = item.atkcrit
    print(f"\033[24;80H✴️ {xlyellow}{bold}{atkcrit}{unbold}% Crit")
    
    ability = item.ability if item.ability and item.ability.strip() else "None"
    print(f"\033[26;63H🍹 {bold}{itemcolour}Combat ability:{reset}")
    print(f"\033[27;64H› {xf}{ability}")
    print(f"\033[31;64H📜{xlorange}{italic} {item.description}\033[0m")














































































"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
PROGRAM PART
Yep. This is everything that actually makes the thing work.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
cls()
cursor(False)

game.goto = startup # adjust to change your landing!

while True:
    game.goto()