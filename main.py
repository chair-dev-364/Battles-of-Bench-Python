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

import msvcrt, os, time, sys, ctypes, ast, math, operator as op, subprocess, json, re, random, shutil, socket, tempfile, stat, urllib.request  # noqa: E401, E402
from pathlib import Path  # noqa: E402
from typing import Literal  # noqa: E402
RGB="[38;2;"

version=1
subversion=2
subberversion=1

CHARACTER_MAX_LEVEL = 100
WEAPON_MAX_LEVEL = 25
ARMOR_MAX_LEVEL = 20
HEADWEAR_MAX_LEVEL = 20


if subberversion != 0:
    TITLE = f"Battles of Bench - a{version}.{subversion}.{subberversion}"
else:
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

# make job object
job = kernel32.CreateJobObjectW(None, None)

# kill child processes when this one dies
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

# well, just see the name. Obvious, right?
def get_item_max_level(category):
    return {
        "Weapons": WEAPON_MAX_LEVEL,
        "Bodywear": ARMOR_MAX_LEVEL,
        "Helmets": HEADWEAR_MAX_LEVEL,
    }.get(category)


def clamp_item_level(level, category):
    try:
        parsed = int(level)
    except Exception:
        parsed = 0

    max_level = get_item_max_level(category)
    if max_level is None:
        return max(0, parsed)
    return max(0, min(parsed, max_level))


def required_player_level_for_item(item_level, category):
    level = clamp_item_level(item_level, category)
    if level <= 1:
        return 0
    if category == "Weapons":
        return level * 4
    if category in ("Bodywear", "Helmets"):
        return level * 5
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
    return _eval(parsed.body)

# woosh, character screen rounding!! DEF is happy with this
def char_round(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)

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

# get visible length without ansi codes
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
    def __init__(self, **stats):
        for name, value in stats.items():
            setattr(self, name, value)

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
            "music": 3,
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
    pass

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
    # Normalize path
    full_path = os.path.join(os.getcwd(), path + ".txt")
    # Ensure directory exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    # Overwrite file
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(str(value))
        
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

# Loads an item by ID and category. If ID is 0, loads equipped items from the "active_*.txt" files.
# Otherwise, loads from the corresponding item file.
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
                    "description": None,
                    "ability": None,
                    "locked": 0,
                },
            ),
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
        item.level = clamp_item_level(item.level, "Weapons")
        item.atk = int(item.atk)
        item.atkcrit = float(item.atkcrit)
        item.substat_value = int(item.substat_value)
        item.level_power = float(item.level_power)
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

        head.type_raw = parts[0] if len(parts) > 0 else None
        head.rarity = parts[1] if len(parts) > 1 else None
        head.name = parts[2] if len(parts) > 2 else None
        raw_level = int(parts[3]) if len(parts) > 3 and parts[3] else 0
        head.level = clamp_item_level(raw_level, "Helmets")
        head.defense = int(parts[4]) if len(parts) > 4 and parts[4] else 0
        head.description = parts[5] if len(parts) > 5 else ""
        head.ability = parts[6] if len(parts) > 6 else ""
        head.locked = int(parts[7]) if len(parts) > 7 and parts[7] != "" else 0
        return head

    # ───────────── BODYWEAR ─────────────
    elif category == "Bodywear":
        _clear_object(armor)

        armor.type_raw = parts[0] if len(parts) > 0 else None
        armor.rarity = parts[1] if len(parts) > 1 else None
        armor.name = parts[2] if len(parts) > 2 else None
        raw_level = int(parts[3]) if len(parts) > 3 and parts[3] else 0
        armor.level = clamp_item_level(raw_level, "Bodywear")
        armor.defense = int(parts[4]) if len(parts) > 4 and parts[4] else 0
        armor.description = parts[5] if len(parts) > 5 else ""
        armor.ability = parts[6] if len(parts) > 6 else ""
        armor.locked = int(parts[7]) if len(parts) > 7 and parts[7] != "" else 0
        return armor

    # ───────────── FRAGMENTS ─────────────
    elif category == "Fragments":
        _clear_object(fragment)

        fragment.name = parts[0] if len(parts) > 0 else None
        fragment.level = int(parts[1]) if len(parts) > 1 and parts[1] else 0

        stats = parts[2:]

        for i in range(0, len(stats), 2):
            stat_name = stats[i] if stats[i] != "" else None
            stat_value = stats[i + 1] if i + 1 < len(stats) else None

            if stat_value is not None and stat_value != "":
                try:
                    if "." in stat_value:
                        val = float(stat_value)
                        if val.is_integer():
                            val = int(val)
                        stat_value = val
                    else:
                        stat_value = int(stat_value)
                except Exception:
                    pass

            idx = i // 2 + 1
            setattr(fragment, f"stat{idx}", stat_name)
            setattr(fragment, f"stat{idx}_value", stat_value)

        return fragment

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
        head.level = clamp_item_level(getattr(head, "level", 0), "Helmets")
        parts = [
            str(getattr(head, "type_raw", "") or ""),
            str(getattr(head, "rarity", "") or ""),
            str(getattr(head, "name", "") or ""),
            str(getattr(head, "level", 0)),
            str(getattr(head, "defense", 0)),
            str(getattr(head, "description", "") or ""),
            str(getattr(head, "ability", "") or ""),
            str(getattr(head, "locked", 0))
        ]

    # ───────────── BODYWEAR ─────────────
    elif category == "Bodywear":
        armor.level = clamp_item_level(getattr(armor, "level", 0), "Bodywear")
        parts = [
            str(getattr(armor, "type_raw", "") or ""),
            str(getattr(armor, "rarity", "") or ""),
            str(getattr(armor, "name", "") or ""),
            str(getattr(armor, "level", 0)),
            str(getattr(armor, "defense", 0)),
            str(getattr(armor, "description", "") or ""),
            str(getattr(armor, "ability", "") or ""),
            str(getattr(armor, "locked", 0))
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
    
def get_actual_atk(item_obj=None):

    target = item_obj if item_obj is not None else item
    base = float(getattr(target, "atk", 0))
    level = int(getattr(target, "level", 0))
    growth = float(getattr(target, "level_power", 0))

    return round(base * ((1 + growth) ** level))

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
            space_raw = tok
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
                    for c in chunks[1:]:
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
    visible_total = visible_len(ANSI_PATTERN.sub('', text))
    produced_vis = sum(visible_len(l) for l in lines)
    if produced_vis < visible_total or len(lines) > height:
        overflow = True

    # Truncate/pad to height
    if len(lines) > height:
        lines = lines[:height]
        overflow = True

    if overflow and height > 0:
        last_idx = height - 1
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
            lines[last_idx] = cur + ''

    # pad with empty lines if necessary
    while len(lines) < height:
        lines.append('')

    # print lines at given coordinates (do not start at column 1)
    for idx, raw_line in enumerate(lines):
        row = y1 + idx
        draw_text(x1, row, raw_line)

    return lines

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
            "    ██  ",
            "  ████  ",
            "██  ██  ",
            "    ██  ",
            "  ██████"
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

def bignumber(number_str, display=False):
    if not number_str.isdigit() or len(number_str) < 1 or len(number_str) > 3:
        return None

    digit_arts = [bignumber_db(digit) for digit in number_str]
    
    result_lines = []
    for line_idx in range(5):
        line_parts = [art[line_idx] for art in digit_arts]
        result_lines.append(" ".join(line_parts))

    if display:
        print("\n".join(result_lines))
    
    return result_lines

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
INTERFACE
Here's where... you really don't want to look. This is the absolute mess of hardcoded coordinates, colors, and styles that
creates the actual game interface. It's a nightmare to maintain, but it works, so good luck.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def levelup():
    # don't overflow :c
    max_level = 100
    if player.level >= max_level:
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
    subprocess.run(["py", "wipe.py", "center", "15"]) # clear screen
    cls()
    delay = 0.05
    print(f"[10;1H{xf}                                  | |   _ / /__\\\\[ \\ [  ]/ /__\\\\ | |  [  | | |[ '/'`\\ \\| | ")
    time.sleep(delay)
    print(f"[10;1H{xf}{player.color}                                  | |   _ / /__\\\\[ \\ [  ]/ /__\\\\ | |  [  | | |[ '/'`\\ \\| | ")
    print(f"[9;1H{xf}                                  | |      .---.  _   __  .---.  | |   __   _  _ .--.  | | ")
    print(f"[11;1H{xf}                                 _| |__/ || \\__., \\ \\/ / | \\__., | |   | \\_/ |,| \\__/ ||_| ")
    time.sleep(delay)
    print(f"[9;1H{xf}{player.color}                                  | |      .---.  _   __  .---.  | |   __   _  _ .--.  | | ")
    print(f"[11;1H{xf}{player.color}                                 _| |__/ || \\__., \\ \\/ / | \\__., | |   | \\_/ |,| \\__/ ||_| ")
    time.sleep(delay)
    print(f"[8;1H{xf}                                |_   _|                         [  |                   | | ")
    print(f"[12;1H{xf}                                |________| '.__.'  \\__/   '.__.'[___]  '.__.'_/| ;.__/ (_) ")
    time.sleep(delay)
    print(f"[8;1H{xf}{player.color}                                |_   _|                         [  |                   | | ")
    print(f"[12;1H{xf}{player.color}                                |________| '.__.'  \\__/   '.__.'[___]  '.__.'_/| ;.__/ (_) ")
    print(f"[7;1H{xf}{bold}                                 _____                           __                     _  ")
    print(f"[13;1H{xf}                                                                              [__|         {reset}")
    time.sleep(delay)
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
    
    graph = bignumber(str(level), display=False)

    print(f"""
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
""".strip(), end="")
    center(f"{xf}› press any key to confirm ‹", 31)
    pause = key()
    game.goto = mainmenu
    return
    
    






















def startup_animation():
    # Quick fade in.
    cls()
    fade_duration = 1.25
    steps = 15
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
        time.sleep(step_delay)

    game.skip_mainmenu_cls = True
    game.goto = mainmenu
    return


def mainmenu():
    if not getattr(game, "skip_mainmenu_cls", False):
        cls()
        # if it's nighttime (between 8pm and 6am), display stars in the background (but only if there is space and isn't already being occupied)
        current_hour = time.localtime().tm_hour
        if current_hour >= 20 or current_hour < 6:
            for _ in range(random.randint(30, 100)):
                x = random.randint(1, os.get_terminal_size().columns)
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
    
    # check if you can level up
    if player.xp >= player.xpneeded and player.level < 100:
        game.goto = levelup
        return
    
    while True:
        offset += 0.005
        print(f"[33;1H{x8}______│_____│_______│_____│_______│__[ == ==]/{x7}.::::::;;; {xlred}{bold}{shine("[B] to battle",offset=offset, color=(255, 71, 76), bold=True)}{reset}{x7} ;;;:::::::.{x8}\\[=  == ]___│_______│_______│_______│___│__{reset}")
        print(f"[35;53H{reset}{shine('[Ctrl+T] to modify data', offset=offset, bold=True,color=(132, 224, 133))}",end="",flush=True)
        k = key(timeout=0)
        if k.lower() == "b":
            sound("woosh")
            subprocess.run(["py", "wipe.py", "normal", "10"])
            game.goto = battle
            return
        if k.lower() == "1":
            game.goto = house
            return
        # cheats interface (terminal) => Ctrl+T
        if k.lower() == "ctrl/t":
            game.goto = internal_modify
            return
        time.sleep(0.01)
        # play sound: ctrl+R
        if k.lower() == "ctrl/r":
            game.goto = testsounds
            return
        # force levelup: ctrl+L
        if k.lower() == "ctrl/l":
            player.xp = player.xpneeded
            player.save()
            game.goto = mainmenu
            return

def testsounds():
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


def internal_modify():
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
    load_binds()
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
                            load_binds()
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
                    load_binds()
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
    d.frombattle = True
    d.first_turn = True
    d.latest_action = ""
    cls()
    game.goto = character # load stuff then immediately jump to battle2() from there
    return

def whose_turn():
    if player.av >= 100 and player.av >= enemy.av:
        return "player" # player
    if enemy.av >= 100 and enemy.av > player.av:
        return "enemy" # enemy
    return "none" # regen

def player_turn():
    d.latest_action += f"\n  {xf}→ Your turn, waiting for key..."
    battle_show_data()
    k = key()
    if k.lower() == bind.attack:
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
        game.goto = mainmenu
        return

def enemy_turn():
    d.latest_action += f"\n  {xf}→ Enemy's turn, attacking..."
    game.goto = enemy_attack
    return

def new_turn():
    d.latest_action += f"\n  {xf}→ New turn started!"
    if not d.first_turn:
         if player.regen > 0:
             heal_amount = round(player.total_hp * (player.regen / 100))
             player.hp = min(player.total_hp, player.hp + heal_amount)
             d.latest_action += f"\n  {xb}💧  Regenerated {heal_amount} HP{reset}"
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

def battle_win():
    cls()
    print(f"{xb}{bold}=== YOU WIN ==={reset}")
    print(f"{xf}You have defeated the {enemy.name}.")
    print(f"{x2}+{enemy.xp_reward} XP{reset}")
    print(f"{x2}+{enemy.gold_reward} Gold{reset}")
    player.xp += enemy.xp_reward
    player.money += enemy.gold_reward
    player.save()
    print(f"{x8}Press any key to return to the main menu.{reset}")
    key()
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
    time.sleep(0.5)
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
        EnemyData(name="Goblin", hp=7000, attack=1000, defense=10, xp_reward=20, gold_reward=10, speed=110),
        EnemyData(name="Orc", hp=5000, attack=2, defense=1, xp_reward=50, gold_reward=25, speed=80),
        EnemyData(name="Troll", hp=8000, attack=3, defense=2, xp_reward=100, gold_reward=50, speed=60),
        EnemyData(name="Dragon", hp=15000, attack=5, defense=3, xp_reward=200, gold_reward=100, speed=40),
        EnemyData(name="Dark Knight", hp=12000, attack=4, defense=4, xp_reward=150, gold_reward=75, speed=50),
        EnemyData(name="Necromancer", hp=10000, attack=3, defense=2, xp_reward=120, gold_reward=60, speed=70),
    ]    
    # give the player the option to choose an enemy to fight
    cls()
    print(f"{xb}{bold}=== CHOOSE AN ENEMY ==={reset}")
    for idx, enemy_data in enumerate(enemies_list, start=1):
        print(f"{xa}[{idx}]{xf} {enemy_data.name} (HP: {enemy_data.hp}, ATK: {enemy_data.attack}, DEF: {enemy_data.defense}, SPD: {enemy_data.speed})")
    print(f"{xc}[B]{xf} Back to main menu")
    while True:
        k = key()
        if k.lower() == "b":
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
    console_width = os.get_terminal_size().columns//2
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
    print(f"  {x7}HP{reset}  {hp_bar(enemy.hp, enemy_max_hp)}  {xf}{enemy.hp}/{enemy_max_hp}{reset}")
    print(f"  {x7}ATK{reset} {xf}{enemy.attack}{reset}  |  {x7}DEF{reset} {xf}{enemy.defense}{reset}  |  {x7}SPD{reset} {xf}{enemy.speed}{reset}")
    print(f"  {x7}Action Value{reset}  {xb}{enemy.av}{reset}  ({xf}{d.av_difference:+d}{reset})")
    print(f"  {x7}Reward:{reset} {xa}{enemy.xp_reward} XP{reset} and {xe}{enemy.gold_reward} gold coins{reset}")
    print()

    print(f"{bold}{xa}▸ {player.name}{reset}")
    print(f"  {x7}HP{reset}  {hp_bar(player.hp, player_max_hp)}  {xf}{player.hp}/{player_max_hp}{reset}")
    print(f"  {x7}Action Value{reset}  {xb}{player.av}{reset}")
    print(f"  {x7}ATK{reset} {xf}{player.total_dmg}{reset}  |  {x7}DEF{reset} {xf}{player.total_def}{reset}  |  {x7}SPD{reset} {xf}{player.speed}{reset}")
    print(f"  {x7}Regen{reset} {xf}{player.regen}%{reset}  |  {x7}Lifesteal{reset} {xf}{player.life_steal}%{reset}  |  {x7}Crit{reset} {xf}{player.crit_rate}%{reset}")
    print()

    print(f"{bold}{xb}⚙️ Keybinds you can use:{reset}")
    print(f"  {xf}{bind.attack.upper()}{reset} {x7}Attack{reset}  •  {xf}{bind.skill.upper()}{reset} {x7}Skill{reset}  •  {xf}{bind.ult.upper()}{reset} {x7}Ultimate{reset}  •  {xf}{bind.heal.upper()}{reset} {x7}Heal{reset}  •  {xf}{bind.forfeit.upper()}{reset} {x7}Forfeit{reset}")
    print()
    # if it's your turn or not,
    if player.av > enemy.av:
        turn_indicator = f"{xa} Your turn!{reset}"
    else:
        turn_indicator = f"{xlred} Enemy's turn!{reset}"
    print(f"{bold}{x7}● Last action:{reset}{turn_indicator}")
    if hasattr(d, "latest_action") and d.latest_action.strip():
        lines = [line.strip() for line in d.latest_action.splitlines() if line.strip()]
        for line in lines[:4]:
            print(f"  {line[:95]}")
    else:
        print(f"  {x7}Still nothing! Maybe try pressing some of the keys above, hmm?{reset}")

def enemy_attack():
    sound("shield")
    dmgdealt = max(0, round(enemy.attack * (100 - player.total_def) / 100))
    player.hp -= dmgdealt
    if dmgdealt > 0:
        d.latest_action += f"{xlred}⚔  {dmgdealt}{xa} DMG RCV{reset}"
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
    battle_show_data()
    game.goto = after_attack
    return

# functions for actions
def battle_attack():
    
    # add action value to enemy based on his speed
    player.av -= 100
    d.av_difference = player.av - enemy.av
    
    # normal hits (enemy.defense is a % reduction to damage, so 5 defense means 5% damage reduction):
    dmgdealt = round(max(0, int(player.total_dmg * (100 - enemy.defense) / 100)))
    
    # if critical (chance triggers: random int 0-100, if it's less than player's crit chance, it's a crit):
    is_crit = random.randint(0, 100) < player.crit_rate
    if is_crit:
        dmgdealt = round(dmgdealt * (1 + (getattr(item, "atkcrit", 0) / 100)))
        d.latest_action = f"{rgb(255, 215, 0)}✴  CRIT!{reset} {dmgdealt}{xa} DMG{reset}"
    else:
        d.latest_action = f"{xf}⚔  {dmgdealt}{xa} DMG{reset}"
    
    enemy.hp -= dmgdealt
    sound("sword2")
    
    # then, life steal (steal is float = % of damage dealt that is returned to you as HP):
    if player.life_steal > 0:
        steal_amount = round(dmgdealt * (player.life_steal / 100))
        player.hp = min(player.total_hp, player.hp + steal_amount)
        d.latest_action += f"\n{xlred}🩸 Life steal: {steal_amount} HP stolen!{reset}"
        
    # if player hp is above max, set it to max
    if player.hp >= player.total_hp:
        player.hp = player.total_hp
    
    # add separator to latest action
    d.latest_action += f"\n{x7}{chr(9472) * 60}{reset}\n"
    battle_show_data()
    game.goto = after_attack
    return

def battle_skill():
    game.goto = battle_loop
    return

def battle_ult():
    game.goto = battle_loop
    return

def battle_heal():
    game.goto = battle_loop
    return

def battle_forfeit():
    game.goto = battle_loop
    return

# battle loop incoming:
def battle_loop():
    game.goto = new_turn
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

{player.color}         ██  ██     {x8}│{xlyellow}  character or personalization will {x8} │{x1}                                   {x8}  │ 
{player.color}      ███████       {x8}│{xlyellow}  be displayed here on the right!   {x8} │  {x7}{bold}[S]{reset}{xf} ⚙️ Settings & info           {x8}  │ 
{player.color}    ██   ██         {x8}│{x9}                                    {x8} │{x1}                                   {x8}  │  
{player.color}         ██         {x8}│{xlorange}  To access any option on the right,{x8} │  {x5}{bold}[R]{reset}{xd} 🎧 Refresh game music       {x8}   │ 
{player.color}         ██         {x8}│{xlorange}  simply press the keys that are{x8}     │                                   {x8}  │    
{player.color}       ██  ██       {x8}│{xlorange}  shown next to them!            {x8}    │  {xc}{bold}[{bind.back_display}] {reset}🏡 {xlred}{italic}<- Return to the main menu{x8}{x8}  │ 
{player.color}     ██      ██     {x8}│{x9}                                    {x8} │                                     │              
{player.color}                    {x8}╰{x8}────────────────────────────────────{x8}─┴─────────────────────────────────────╯         
    """)
    if player.level >= 100:
        print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x3}{bold}[E]{reset}{xb} 💎 Convert excess XP     {x8}  │ ")
    else:
        print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x3}{bold}[G]{reset}{xb} 🦮 Level guide/Builder   {x8}  │ ")
    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            game.goto = mainmenu
            return
        if k.lower() == "s":
            sound("map_switch2")
            game.goto = settings
            return
        if k.lower() == "i":
            sound("map_switch2")
            game.goto = inventory
            return
        if k.lower() == "c":
            sound("map_switch2")
            game.goto = character
            return
        # xp time
        if k.lower() == "x":
            # move to 1;1 and ask how much xp you wanna earn
            move(1, 1)
            x = int(input("Enter XP to earn: "))
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
                time.sleep(0.025)
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
                
                counts = min(20, int(math.sqrt(excess_xp / 1000) * 4))
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
                        print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x6}{bold}[E]{reset}{xe} ⏳ Working{dotsdisplay} {xlyellow}({bold}+{round(gold/counts*(i+1))}{reset}🪙{xlyellow}) {reset}")
                    else:
                        # normalize to "k"
                        print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x6}{bold}[E]{reset}{xlred} 🔥 Working{dotsdisplay} {xlyellow}({bold}+{round(gold/counts*(i+1)/1000, 1)}k{reset}🪙{xlyellow}) {reset}")
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
                    time.sleep(delay)
                
                sound("map_right")
            
                sound(reward_sound)
                time.sleep(0.1)
                if gold < 100000:
                    print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x3}{bold}[E]{reset}{xb} 💎 Converted! {xlyellow}({bold}+{round(gold)}{reset}🪙{xlyellow})   {reset}")
                else:
                    # normalize to k
                    print(f"[23;1H{reset}{player.color}         ██    ██   {x8}│{xlyellow}  Everything related to you, your   {x8} │{x8}   ╰─ {x3}{bold}[E]{reset}{xb} 💎 Converted! {xlyellow}({bold}+{round(gold/1000, 1)}k{reset}🪙{xlyellow})  {reset}")
                
        # this is the pitch testing code!
        if k.lower() == "o":
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
        player.dmg_main = playerclass.main_damage[lvl_main - 1]
        player.dmg_skill = playerclass.skill_damage[lvl_skill - 1]
        player.dmg_ult = playerclass.ult_damage[lvl_ult - 1]

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
    item.actual_atk=get_actual_atk()
    totaldmg=baseatk + abilityatk + item.actual_atk
    totalcritdmg=round(totaldmg*(1+item.atkcrit/100))
    item.atkcrit = round(item.atkcrit)
    basehp = round(basehp)
    basedef = round(basedef,1)
    critrate = round(player.crit_rate)
    expected = round(totaldmg * (1 + (critrate / 100) * (item.atkcrit / 100)))
    number = 1
    # --- Defence ---
    raw_def = basedef

    if getattr(item, "substat", None) == "Defence":
        raw_def += item.substat_value

    if getattr(armor, "name", None):
        raw_def += armor.defense

    if getattr(head, "name", None):
        raw_def += head.defense

    totaldef = effective_def(raw_def)

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
    
    # let's make speed work
    # base speed is 100
    base_speed = 100
    # if weapon substat is speed, add the same
    weapon_speed = 0
    if getattr(item, "substat", None) == "Speed":
        weapon_speed = item.substat_value
    # for every 10 levels of player, +5 speed
    level_speed = (player.level // 10) * 5
    
    # at breakpoints of 20, 40, 60, 80, 100, +1 speed each (stacking)
    if player.level >= 20:
        level_speed += 1
    if player.level >= 40:
        level_speed += 1
    if player.level >= 60:
        level_speed += 1
    if player.level >= 80:
        level_speed += 1
    if player.level >= 100:
        level_speed += 1
    
    bonus_speed = 0
    # if fragment's stat is speed, add it
    if getattr(fragment, "stat1", None) == "Speed":
        bonus_speed += getattr(fragment, "stat1_value", 0)
    if getattr(fragment, "stat2", None) == "Speed":
        bonus_speed += getattr(fragment, "stat2_value", 0)
    if getattr(fragment, "stat3", None) == "Speed":
        bonus_speed += getattr(fragment, "stat3_value", 0)
    
    player.speed = base_speed + weapon_speed + level_speed + bonus_speed
    del base_speed, weapon_speed, level_speed, bonus_speed
    
    
    
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
        pass # skill tree
    
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
[17;20H❤️ {xc}Health{reset}{x8}.....{bold}{xlred}{char_round(round(totalhp))} {reset}
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
[14;62H{RGB}255;219;187mCrit DMG{x8}------{xlyellow}{bold}{char_round(item.atkcrit)}%{reset}
[15;60H{reset}⟐ 
[15;62H{RGB}255;219;187mSpeed{x8}---------{xlyellow}{bold}{char_round(player.speed)}{reset}
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
[30;62H{RGB}173;216;225mArmour DEF{x8}----{xb}{bold}{char_round(getattr(armor, "defense", 0))}%{reset}
[31;60H{reset}⦿ 
[31;62H{RGB}173;216;225mHelmet DEF{x8}----{xb}{bold}{char_round(getattr(head, "defense", 0))}%{reset}
[32;60H{reset}★ 
[32;62H{RGB}173;216;225mBonus DEF{x8}-----{xb}{bold}{char_round(abilitydef)}%{reset}
[33;60H{reset}⊗ 
[33;62H{RGB}173;216;225mDodge Rate{x8}----{xb}{bold}{char_round(player.dodge)}%{reset}
[29;101H{reset}♥ 
[29;103H{RGB}255;203;204mBase HP{x8}---------{xlred}{bold}{char_round(basehp)}{reset}
[30;101H{reset}♡ 
[30;103H{RGB}255;203;204mBonus HP{x8}--------{xlred}{bold}{char_round(abilityhp)}{reset}
[31;101H{reset}⬣ 
[31;103H{RGB}255;203;204mEffect RES{x8}------{xlred}{bold}{char_round(round(player.effect_res))}%{reset}
[32;101H{reset}↺ 
[32;103H{RGB}255;203;204mRegeneration{x8}----{xlred}{bold}{char_round(round(player.regen,1))}%{reset}
[33;101H{reset}⸕ 
[33;103H{RGB}255;203;204mLife Steal{x8}------{xlred}{bold}{char_round(round(player.life_steal,1))}%{reset}
[36;42H{RGB}173;216;225m╰───────────────────────────────────────╯ {RGB}255;203;204m╰─────────────────────────────────────────╯
[36;3H{x7}╰────────────────────────────────────╯{reset}
""".strip().replace("\n", ""),end="",flush=True)
    if item.type_raw is not None: print(f"""
[18;46HYour {item.type_raw} {bold}crits {RGB}255;219;187m{char_round(player.crit_rate)}%{reset} of the time,{reset}
[19;46H{reset}in which case you deal {RGB}255;219;187m{bold}+{char_round(item.atkcrit)}%{reset} DMG:
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
    FILLED_SEG = f"{xa}█"
    EMPTY_SEG = f"{x0}█"

    if EXP_NEEDED > 0:
        percent = min(100, max(0, round((EXP / EXP_NEEDED) * 100)))
        FILLED = min(BAR_LENGTH, max(0, (EXP * BAR_LENGTH) // EXP_NEEDED))
    else:
        percent = 0
        FILLED = 0

    EXP_BAR = (FILLED_SEG * FILLED) + (EMPTY_SEG * (BAR_LENGTH - FILLED))
    print(f"\033[18;86H{reset}{rgb(255,219,187)}{rgb(186,243,219)}✚{xf}\033[18;88H{bold}EXP: {EXP_BAR}{reset} ", end="")
    if percent < 10:
        print(f"{xf}{bold}{rgback(0,0,1)}\033[18;94H{percent}%")
    else:
        print(f"{xba}{xf}{bold}\033[18;94H{percent}%")
    print(f"\033[19;93H{reset}{x7}{rgb(186,243,219)}↑ {bold}{EXP}/{EXP_NEEDED} {reset}XP to get level {player.level+1}{reset} ")
    print(f"""
[15;20H{item.type} {xlyellow}Attack{reset}{x8}.....{bold}{xe}{char_round(round(totaldmg))}{reset}
[16;20H🛡️ {x3}Defence{reset}{x8}....{bold}{xb}{char_round(round(totaldef,1))}%{reset}
[17;20H❤️ {xc}Health{reset}{x8}.....{bold}{xlred}{char_round(round(totalhp))} {reset}
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
            sound("map_switch1")
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
            sound("map_switch1")
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

def character2():
    boxwidth = 25
    playername=read("General/playername")
    playernamd = f"{playername} › Equipment"
    length = visible_len(playernamd)
    pad = (boxwidth - length) // 2 + 1
    spaces = " " * max(pad, 0)
    centered = spaces + playernamd
    number = 1
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
[08;43H{RGB}255;219;187m{bold}┤ {item.name if item.name is not None else "Weapon"} ├
[08;85H{RGB}186;243;219m{bold}┤ {fragment.name if fragment.name is not None else "Fragments"} ├
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
[26;43H{RGB}173;216;225m{bold}┤ {head.name if head.name is not None else "Head"} ├
[26;85H{RGB}255;203;204m{bold}┤ {armor.name if armor.name is not None else "Armor"} ├
[36;42H{RGB}173;216;225m╰───────────────────────────────────────╯ {RGB}255;203;204m╰─────────────────────────────────────────╯
[36;3H{x7}╰────────────────────────────────────╯{reset}
""".strip().replace("\n",""),end="",flush=True)
    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            sound("map_switch1")
            game.goto = house
            return
        if k.lower() == bind.back or k.lower() == "1":
            d.character_view = 1
            sound("map_switch1")
            game.goto = character
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
    sound("payment_success")
    # wipe screen with animation (using wipe.py)
    subprocess.run(["py", "wipe.py", "normal", "20"])
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
    print(f"\033[31;19H{xlorange}Go back → {xlyellow}{bold}{bind.back_display.upper()} {reset}{xlorange}or {xlyellow}{bold}ESC{reset}")

    while True:
        k = key()
        if k.lower() == bind.back or k.lower() == "esc":
            game.goto = inventory
            return

def startup():
    # check if <cd>/general/screensetup.txt exists
    if not os.path.exists("general/screensetup.txt"):
        game.goto = screensetup
        return
    # check if <cd>/general/setup.txt exists
    if not os.path.exists("general/setup.txt"):
        game.goto = first_time_setup
        return
    sound(random.choice(["music_default"]))
    game.goto = startup_animation
    return


def inv_category_title(category):
    return {
        "Weapons": "Weapons",
        "Bodywear": " Armor ",
        "Helmets": "Helmets",
    }.get(category, str(category))


def inv_item_label(category):
    return {
        "Weapons": "weapon",
        "Bodywear": "armour",
        "Helmets": "helmet",
    }.get(category, "item")


def inv_active_path(category):
    return {
        "Weapons": "Items/active_weapon",
        "Bodywear": "Items/active_body",
        "Helmets": "Items/active_head",
    }.get(category)


def inv_type_icon(item_obj):
    type_raw = getattr(item_obj, "type_raw", None)
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


def inv_type_label(item_obj):
    type_raw = getattr(item_obj, "type_raw", None)
    if not type_raw or type_raw == "None":
        return "None"
    return str(type_raw).title()


def inv_compare_label(category):
    return "DMG" if category == "Weapons" else "DEF"


def inv_compare_value(item_obj, category):
    if category == "Weapons":
        final_atk = get_actual_atk(item_obj)
        crit_bonus = float(getattr(item_obj, "atkcrit", 0)) / 100
        return float(final_atk) * (1 + crit_bonus)
    return float(getattr(item_obj, "defense", 0))


def item_level_display(item_obj, category):
    level = clamp_item_level(getattr(item_obj, "level", 0), category)
    max_level = get_item_max_level(category)
    if max_level is None:
        return str(level)
    return f"{level}/{max_level}"


def maininv_md():
    for r in range(19, 29):
        print(f"\033[{r};20H                                        ")

    d.length = len(list(Path(f"Items/{game.sel}").glob("item*.txt")))
    d.currsel = (d.page * 10) + 1
    d.current = d.begin - 1

    if d.length == d.page * 10:
        inv_prevpage()
        return
    item_pager()

def inventory_prep():
    d.massdelete = 0
    d.current = 0
    d.hold_item = 0
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
    
    # title
    print(f"\033#3{reset}                  {xlorange}╭───────────────────────{xlorange}╮")
    print(f"\033#4                  {xlorange}╭───────────────────────{xlorange}╮")
    print(f"\033#3                  {xlorange}│        {bold}{xlyellow}{category_title}        {xlorange}│")
    print(f"\033#4                  {xlorange}│        {bold}{xlyellow}{category_title}        {xlorange}│")
    print(f"\033#3                  {xlorange}╰───────────────────────{xlorange}╯")
    print(f"\033#4                  {xlorange}╰───────────────────────{xlorange}╯")

    d.moving_progress = 0
    d.page = 0
    d.begin = 1
    d.end = 10

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
    print(f"\033[31;19H{xlorange}Switch pages → {xlyellow}{bold}A/D {reset}{xlorange}| Select an item → {xlyellow}{bold}W/S{reset}")

    d.currsel = 1
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
        d.ability_line2 = f"He's considered a {rainbow(text="phantom", bold=True, offset=d.offset)} during a battle."
        d.notice = "Phantom"
        d.notice_text = f"Phantom beings can't be killed. They appear {shine(text="invisible", bold=True, offset=d.offset)} to all enemies."
    elif name == "Krita User Manual":
        d.ability_line1 = f"Hitting an enemy makes it panic about"
        d.ability_line2 = f"color theory → it gets {xlbrown}dizzy{reset} permanently."
        d.notice = "Dizzy"
        d.notice_text = f"Every stack makes the target move 1% slower and take 1% more damage from attacks."
    
    
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
    item = load_item(d.currsel, game.sel)
    ityped = inv_type_icon(item)
    itemcolour = xf
    itemcolour_rgb = (255, 255, 255)
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
        item = load_item(d.currsel, game.sel)
        ityped = inv_type_icon(item)
        itemcolour = xf
        itemcolour_rgb = (255, 255, 255)
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
        #print(f"\033[1;1Hcounter: {counter} / offset: {round(d.offset,2)} / currsel: {d.currsel} / current: {d.current} / begin: {d.begin} / end: {d.end} / page: {d.page}                    ")
        print(f"\033[{d.currselrow};20H{bold}{itemcolour}{d.currsel} {unbold}› {ityped} {shine(text=item.name,bold=True,offset=d.offset,color=itemcolour_rgb)}",end="",flush=True)
        k = key(timeout=0)  # wait a very very short time for key input to allow shine effect to update at the same time
        if k == "w" or k == "up":
            itemsel_up()
        elif k == "s" or k == "down":
            itemsel_down()
        elif k == "a" or k == "left":
            inv_prevpage()
        elif k == "d" or k == "right":
            inv_nextpage()
        elif k == bind.back:
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
        # if E is pressed, open file in notepad
        elif k.lower() == "e":
            item_path = f"Items/{game.sel}/item{d.currsel}.txt"
            sound("positive7")
            if os.path.exists(item_path):
                subprocess.run(["notepad.exe", item_path])
        # equip item with enter
        elif k.lower() == "enter":
            item = load_item(d.currsel, game.sel)
            equipped_path = inv_active_path(game.sel)
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
                load_item(0)
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
        # Ctrl+D duplicates selected item (developer function). The dupe will be saved as the next item (duping item 5 will create item 6, shifting all subsequent items up by one if they exist)
        elif k == "ctrl/d":
            for i in range(d.length, d.currsel, -1):
                src = os.path.join("Items", game.sel, f"item{i}.txt")
                dst = os.path.join("Items", game.sel, f"item{i+1}.txt")
                if os.path.exists(src):
                    shutil.move(src, dst)
            
            src = os.path.join("Items", game.sel, f"item{d.currsel}.txt")
            dst = os.path.join("Items", game.sel, f"item{d.currsel+1}.txt")
            if os.path.exists(src):
                shutil.copy(src, dst)
                
            d.length += 1
            sound("pop_2")
            game.preserve_offset = True
            game.goto = reload_items
            d.preserved_item_id = d.currsel
            return
            
        # Ctrl+X deletes selected item (developer function). Shifts subsequent items down.
        elif k == "ctrl/x":
            target = os.path.join("Items", game.sel, f"item{d.currsel}.txt")
            if os.path.exists(target):
                os.remove(target)
            
            for i in range(d.currsel + 1, d.length + 1):
                src = os.path.join("Items", game.sel, f"item{i}.txt")
                dst = os.path.join("Items", game.sel, f"item{i-1}.txt")
                if os.path.exists(src):
                    shutil.move(src, dst)
                    
            if d.length > 0:
                d.length -= 1
            sound("pop_1")
            game.goto = reload_items
            d.preserved_item_id = max(1, min(d.currsel, d.length))
            return
        
        # Backspace: production version to delete with confirmation
        elif k == "backspace":
            blank(16,63, 16,110)
            blank(18,63, 29,110)
            blank(31,63, 31,110)
            print(f"\033[16;63H{bold}🗑️ {xlred}Delete {item.name}?{reset}")
            xpbar = ""
            filled = 0
            empty = 43-filled
            for i in range(filled):
                xpbar += f"{xc}█"
            for i in range(empty):
                xpbar += f"{rgb(48, 18, 18)}█"
            print(f"[19;63H{x0}███████████████████████████████████████████████")
            print(f"[20;63H██{xpbar}{x0}██")
            print(f"[21;63H██{xpbar}{x0}██")
            print(f"[22;63H{x0}███████████████████████████████████████████████")
            print(reset, end="")
            
            item_label = inv_item_label(game.sel)
            print(f"[24;63H{reset}{xf}→ {xc}📛 Hold {bold}{xlred}{bind.confirm.capitalize()}{reset}{xc} to delete {item_label}.{reset}")
            print(f"[25;63H{reset}{xf}→ {xb}💤 Press {bold}{x3}{bind.back.upper()} {reset}{xb}or {bold}{x3}{bind.deny.upper()}{reset} {xb}to cancel deletion.{reset}")
            
            print(f"[27;63H{reset}{xf}{rgb(255, 206, 124)}📦 Deleting this {item_label} will give you:{reset}")
            
            # gold multipliers and bases dictionary based on rarity:
            gold_bases = {
                "08": (100, 50),
                "02": (150, 200),
                "03": (250, 350),
                "0d": (350, 450),
                "0e": (750, 500)
            }
            goldmult, goldbonus = gold_bases.get(item.rarity, (1.0, 100))
            
            # dust multipliers and bases dictionary based on rarity:
            dust_bases = {
                "08": (100, 1),
                "02": (150, 3),
                "03": (250, 5),
                "0d": (350, 12),
                "0e": (750, 24)
            }
            dustmult, dustbonus = dust_bases.get(item.rarity, (1.0, 10))
            
            # calculate final payback
            goldpayback = round((goldmult * item.level**2) / 98 + goldbonus)
            if game.sel == "Weapons":
                dustpayback = round((dustmult * item.level) / (150 / item.level_power) + dustbonus)
            else:
                dustpayback = round((dustmult * item.level) / 150 + dustbonus)
            # at higher values:
            if dustpayback >= 1000:
                dustpayback = round(dustpayback, -1) # round to nearest 10
            
            print(f"[28;66H{reset}{x7}╰─ ✨ {xlyellow}{bold}{dustpayback} {reset}{xlyellow}magic dust")
            
            print(f"\033[31;63H{xlorange}⚠️ You will lose this {item_label} permanently!{reset}")
        
        # Pressing space adds item to comparison
        elif k == "space":
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
                item1 = load_item(game.comparing[0], game.sel)
                item1_value = inv_compare_value(item1, game.sel)
                item2 = load_item(game.comparing[1], game.sel)
                item2_value = inv_compare_value(item2, game.sel)
                stat_label = inv_compare_label(game.sel)
                
                
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
                item1 = load_item(game.comparing[0], game.sel)
                item1_icon = inv_type_icon(item1)
                print(f"\033[19;63H{reset}{item1_icon} {x7}↑{item1.level} {item1_color}{bold}{item1.name}{unbold} {item1_tag}{reset}")
                
                item2 = load_item(game.comparing[1], game.sel)
                item2_icon = inv_type_icon(item2)
                print(f"\033[21;63H{reset}{item2_icon} {x7}↑{item2.level} {item2_color}{bold}{item2.name}{unbold} {item2_tag}{reset}")
                print(f"\033[23;61H{reset}{x8}├─────────────────────────────────────────────────┤{reset}")
                item_label = inv_item_label(game.sel)
                stat_caption = "average damage" if game.sel == "Weapons" else "defense"
                if not comparison_winner == 0:
                    print(f"\033[25;63H{reset}{xlorange}⇝ {xf}Using {item_label} {bold}{xlorange}#{comparison_winner}{reset} will give you {bold}{xlorange}{stat_diff_percentage}% more {stat_label}{reset}")
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
        time.sleep(0.01)

def unselect_current():
    item = load_item(d.currsel, game.sel)
    if not item: return
    ityped = inv_type_icon(item)

    req_level = required_player_level_for_item(item.level, game.sel)
    colour = x7 if req_level <= int(player.level) else xlred
    print(f"\033[{d.currselrow};20H\033[38;5;8m{d.currsel} › {ityped} \033[0m{x7}{item.name} \033[{d.currselrow};56H{colour}↑{item.level}")

def itemsel_down():
    unselect_current()
    d.currsel += 1
    if d.currsel > d.length:
        d.currsel = d.length
    elif d.currsel > d.current:
        d.currsel = d.current
    else:
        d.currselrow += 1
    displaynewsel()

def itemsel_up():
    unselect_current()
    d.currsel -= 1
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

def inv_nextpage():
    if d.length > 10 + (d.page * 10):
        d.page += 1
        d.begin += 10
        d.end += 10
        d.currsel = (d.page * 10) + 1
        d.current = d.begin - 1
        reload_items()

def inv_prevpage():
    if d.page >= 1:
        d.page -= 1
        d.begin -= 10
        d.end -= 10
        d.currsel = (d.page * 10) + 1
        d.current = d.begin - 1
        reload_items()

def item_pager():
    d.rowdisplay = 18
    d.currselrow = 19

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

        print(f"\033[{d.rowdisplay};20H{x8}{" "*40}{xf}",end="")
        
        indicator = "↑"
        req_level = required_player_level_for_item(item.level, game.sel)
        colour = x7 if req_level <= int(player.level) else xlred
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
    type_label = inv_type_label(item)

    # Write selection in list
    indicator = "↑"
    req_level = required_player_level_for_item(item.level, game.sel)
    colour = x7 if req_level <= int(player.level) else xlred
    itemcolour = xf
    itemcolour_rgb = (255, 255, 255)
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
    req_level = required_player_level_for_item(item.level, game.sel)
    colour = x7 if req_level <= int(player.level) else xlred
    if not game.preserve_offset:
        d.offset = 0
    else:
        game.preserve_offset = False
    print(f"\033[{d.currselrow};20H{bold}{itemcolour}{d.currsel} {unbold}› {ityped} {shine(text=item.name, color=itemcolour_rgb,bold=True,offset=d.offset)} {reset}\033[{d.currselrow};56H{colour}{indicator}{item.level}")
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
        xpbar += f"{xb}█"
    for i in range(empty):
        xpbar += f"{rgb(17,45,69)}█"
    
    print(f"[19;63H{x0}███████████████████████████████████████████████")
    print(f"[20;63H██{xpbar}{x0}██")
    print(f"[21;63H██{xpbar}{x0}██")
    print(f"[22;63H{x0}███████████████████████████████████████████████")
    print(reset, end="")
    indicators = ""
    # If equipped, show equipped indicator
    equipped_path = inv_active_path(game.sel)
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
        print(f"\033[24;66H❇️ {xa}{bold}{item.actual_atk}{unbold} ATK")
        # if item.atkcrit can also be an int (0 after decimal point), convert to int
        try:
            atkcrit = int(float(item.atkcrit))
        except ValueError:
            atkcrit = item.atkcrit
        print(f"\033[24;80H✴️ {xlyellow}{bold}{atkcrit}{unbold}% Crit")
        
        print(f"\033[24;94H📶 {xf}Lv {bold}{item_level_display(item, game.sel)}{unbold}{x7}")
        
        ability = item.ability if item.ability and item.ability.strip() else "None"
        print(f"\033[26;63H🍹 {bold}{xf}Combat ability:{reset}")
        print(f"\033[27;64H› {xf}{ability}")
        print(f"\033[31;63H📜{xlorange} {item.description}\033[0m")
    else:
        print(f"\033[24;66H🛡️ {xb}{bold}{getattr(item, 'defense', 0)}{unbold}% DEF")
        print(f"\033[24;94H📶 {xf}Lv {bold}{item_level_display(item, game.sel)}{unbold}{x7}")
        ability = item.ability if item.ability and item.ability.strip() else "None"
        description = item.description if item.description and item.description.strip() else "None"
        print(f"\033[26;63H🍹 {bold}{xf}Combat ability:{reset}")
        print(f"\033[27;64H› {xf}{ability}")
        print(f"\033[31;63H📜{xlorange} {description}\033[0m")
    # finally, call function to display item ability specials, if applicable
    get_specials(item.name)














































































"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
PROGRAM PART
Yep. This is everything that actually makes the thing work.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
cls()
cursor(False)

game.goto = startup # adjust to change your landing!

while True:
    game.goto()