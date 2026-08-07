import sys
import os
import time
import math
import random
import shutil
import argparse

def enable_virtual_terminal_output():
    """Enable ANSI output when running in a Windows console."""
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except (AttributeError, OSError):
        pass


enable_virtual_terminal_output()

def move_cursor(x, y):
    """Move the cursor to column x, row y (0-indexed)."""
    sys.stdout.write(f"\033[{y + 1};{x + 1}H")

def write_text(text):
    """Write text immediately using the active terminal encoding."""
    sys.stdout.write(text)
    sys.stdout.flush()

def sleep_ms(ms):
    time.sleep(ms / 1000.0)

def accelerate(delay, accel):
    """If acceleration is on, reduce delay by 10% each step."""
    return max(1, delay * 0.9) if accel else delay

def get_terminal_size():
    size = shutil.get_terminal_size()
    return size.columns, size.lines

# ===== color stuff =====
# simple color map
COLORS = {
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "MAGENTA": "\033[35m",
    "CYAN": "\033[36m",
    "WHITE": "\033[37m",
}
RESET_COLOR = "\033[0m"

def apply_color(text, color_enabled):
    """Wrap the text with a random color if enabled."""
    if color_enabled:
        # pick a random color
        color = random.choice(list(COLORS.values()))
        return color + text + RESET_COLOR
    return text

# ===== clear a line =====
def clear_line_at(row, filler=" ", color_enabled=False):
    """Clear a given row (1-indexed) by writing filler characters across the full width."""
    cols, _ = get_terminal_size()
    move_cursor(0, row - 1)
    line = apply_color(filler * cols, color_enabled)
    write_text(line)

# ===== Wipe Effects =====

def wipe_classic(delay, filler, accel, color_enabled):
    """Classic wipe: from top to bottom."""
    _, rows = get_terminal_size()
    d = delay
    for row in range(1, rows + 1):
        clear_line_at(row, filler, color_enabled)
        sleep_ms(d)
        d = accelerate(d, accel)

def wipe_reverse_classic(delay, filler, accel, color_enabled):
    """Reverse classic wipe: bottom to top."""
    _, rows = get_terminal_size()
    d = delay
    for row in range(rows, 0, -1):
        clear_line_at(row, filler, color_enabled)
        sleep_ms(d)
        d = accelerate(d, accel)

def wipe_center(delay, filler, accel, color_enabled):
    """Inside-out wipe: clear from the center toward the edges."""
    _, rows = get_terminal_size()
    d = delay
    # center row logic
    center = rows // 2
    top = center if rows % 2 == 1 else center
    bottom = center + 1
    while top >= 1 or bottom <= rows:
        if top >= 1:
            clear_line_at(top, filler, color_enabled)
            top -= 1
        if bottom <= rows:
            clear_line_at(bottom, filler, color_enabled)
            bottom += 1
        sleep_ms(d)
        d = accelerate(d, accel)

def wipe_outside_in(delay, filler, accel, color_enabled):
    """Outside-in wipe: clear from the top and bottom inward toward the center."""
    _, rows = get_terminal_size()
    d = delay
    top = 1
    bottom = rows
    while top <= bottom:
        clear_line_at(top, filler, color_enabled)
        if top != bottom:
            clear_line_at(bottom, filler, color_enabled)
        sleep_ms(d)
        d = accelerate(d, accel)
        top += 1
        bottom -= 1

def wipe_wave(delay, filler, accel, color_enabled):
    """Wave wipe: create a ripple effect using a sine function for horizontal offsets."""
    cols, rows = get_terminal_size()
    d = delay
    for row in range(1, rows + 1):
        # make a little wave offset
        offset = int((math.sin((row / rows) * math.pi * 2) + 1) / 2 * (cols // 2))
        move_cursor(0, row - 1)
        # build the line
        line = (" " * offset) + (filler * (cols - offset))
        line = apply_color(line, color_enabled)
        write_text(line)
        sleep_ms(d)
        d = accelerate(d, accel)

def wipe_glitch(delay, filler, accel, color_enabled, noise):
    """Glitch wipe: randomly flicker rows; if noise is on, replace with random noise characters."""
    cols, rows = get_terminal_size()
    d = delay
    iterations = rows * 2
    for _ in range(iterations):
        row = random.randint(1, rows)
        if noise:
            # make some random noise
            noise_line = ''.join(random.choice([filler, "!", "@", "#", "$", "%", "&", "*", " "]) for _ in range(cols))
            line = apply_color(noise_line, color_enabled)
        else:
            line = apply_color(filler * cols, color_enabled)
        move_cursor(0, row - 1)
        write_text(line)
        sleep_ms(d)
        d = accelerate(d, accel)

def wipe_multi(delay, filler, accel, color_enabled, noise):
    """Multi wipe: run several effects in sequence."""
    effects = [wipe_center, wipe_diagonal, wipe_glitch, wipe_classic]
    for effect in effects:
        effect(delay, filler, accel, color_enabled)
        # short pause between effects
        sleep_ms(100)

def wipe_diagonal(delay, filler, accel, color_enabled):
    """Diagonal wipe: clear diagonally across the screen."""
    cols, rows = get_terminal_size()
    d = delay
    # go through diagonal steps
    for diag in range(rows + cols - 1):
        for row in range(1, rows + 1):
            col = diag - (row - 1)
            if 1 <= col <= cols:
                move_cursor(col - 1, row - 1)
                text = apply_color(filler, color_enabled)
                write_text(text)
        sleep_ms(d)
        d = accelerate(d, accel)

# ===== Mode Dictionary =====
MODES = {
    "top": wipe_classic,
    "bottom": wipe_reverse_classic,
    "center": wipe_center,
    "normal": wipe_outside_in,
    "wave": wipe_wave,
    "glitch": wipe_glitch,
    "diagonal": wipe_diagonal,
    "multi": wipe_multi,
}

# ===== optional sound =====
def play_sound_effect():
    # ASCII BEL is the portable terminal-notification equivalent.
    sys.stdout.write("\a")
    sys.stdout.flush()

# ===== Argument Parsing & Main Runner =====
def main():
    parser = argparse.ArgumentParser(
        description="Terminal wipe engine",
        usage="Scripts/wipe.py <mode> <delay_ms> [--reverse] [--color] [--noise] [--cycles N] [--sound]"
    )
    parser.add_argument("mode", help="Wipe mode. Options: " + ", ".join(MODES.keys()))
    parser.add_argument("delay_ms", type=int, nargs="?", default=50, help="Delay between steps in ms (default: 50)")
    parser.add_argument("--color", action="store_true", help="Enable random color effects")
    parser.add_argument("--noise", action="store_true", help="Enable noise (for glitch mode)")
    parser.add_argument("--cycles", type=int, default=1, help="Number of cycles to run the effect (default: 1)")
    parser.add_argument("--sound", action="store_true", help="Play a sound effect at the end of each cycle")
    # --reverse flips the wipe direction when it can
    parser.add_argument("--reverse", action="store_true", help="Invert the wipe direction")
    
    args = parser.parse_args()

    mode_name = args.mode.lower()
    delay = args.delay_ms
    color_enabled = args.color
    noise = args.noise
    cycles = args.cycles
    reverse_flag = args.reverse
    sound_flag = args.sound

    # pick the wipe effect
    if mode_name not in MODES:
        print("Unknown mode. Available modes:")
        for m in MODES:
            print(" - " + m)
        sys.exit(1)
    
    effect_func = MODES[mode_name]

    # run the chosen effect for the requested cycles
    for i in range(cycles):
        effect_func(delay, " ", False if reverse_flag else False or color_enabled, color_enabled)  # call normally
        # if reverse flag is on, use the reverse version if it exists
        if reverse_flag:
            # classic/center swap to their reverse versions
            if mode_name == "classic":
                wipe_reverse_classic(delay, " ", False, color_enabled)
            elif mode_name == "center":
                wipe_outside_in(delay, " ", False, color_enabled)
            # other modes just keep going as-is for now
        if sound_flag:
            play_sound_effect()

    # move cursor to bottom and finish
    cols, rows = get_terminal_size()
    move_cursor(0, rows - 1)
    print(RESET_COLOR)
    #print("Wipe complete. Enjoy!")

if __name__ == "__main__":
    main()
