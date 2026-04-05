import os
import sys
import time

# Folder containing your items
ITEM_FOLDER = os.path.join(os.getcwd(), "Items", "Weapons")

# ANSI escape codes
WHITE = "\033[97m"
RESET = "\033[0m"
CURSOR_HOME = "\033[1;1H"

# Get all item[n].txt files
item_files = [f for f in os.listdir(ITEM_FOLDER) if f.lower().startswith("item") and f.endswith(".txt")]
item_numbers = sorted([int(f[4:-4]) for f in item_files if f[4:-4].isdigit()])

# Find first missing slot
deleted_from = None
for i in range(1, max(item_numbers) + 2):  # +2 just in case last is missing
    expected_file = os.path.join(ITEM_FOLDER, f"item{i}.txt")
    if not os.path.exists(expected_file):
        deleted_from = i
        break

if deleted_from is None:
    sys.exit(0)

# Prepare total shift count
last_item = max(item_numbers)
total_to_shift = last_item - deleted_from + 1
start_time = time.time()

def print_progress(current, total):
    percent = (current / total) * 100
    filled = int((current / total) * 20)  # 20 blocks wide
    bar = "█" * filled + "▒" * (20 - filled)

    # Time estimate
    elapsed = time.time() - start_time
    est_total = (elapsed / current) * total if current > 0 else 0
    remaining = max(0, est_total - elapsed)
    time_str = f"{remaining:.1f}s left"

    # Cursor to top-left, white text, no newline
    print(f"{CURSOR_HOME}{WHITE}🗑️ {percent:5.1f}% complete {bar} ({str(current).zfill(3)}/{total} - {time_str}){RESET}", end="", flush=True)

# Begin shifting
i = deleted_from
shifted = 0

while True:
    current_file = os.path.join(ITEM_FOLDER, f"item{i}.txt")
    next_file = os.path.join(ITEM_FOLDER, f"item{i+1}.txt")

    if os.path.exists(next_file):
        os.rename(next_file, current_file)
        shifted += 1
        print_progress(shifted, total_to_shift)
        i += 1
    else:
        break

# Finish cleanly