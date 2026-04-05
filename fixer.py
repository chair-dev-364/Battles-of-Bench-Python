import os
import shutil
import re

global fixes
fixes = 0
ITEMS_FOLDER = os.path.join(os.getcwd(), "Items", "Weapons")
BACKUP_FOLDER = os.path.join(os.getcwd(), "Items", "WeaponsBackup")

def make_backup():
    global fixes
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    existing = [f for f in os.listdir(BACKUP_FOLDER) if os.path.isdir(os.path.join(BACKUP_FOLDER, f))]
    backup_number = 1

    while f"Backup{backup_number}" in existing:
        backup_number += 1

    backup_path = os.path.join(BACKUP_FOLDER, f"Backup{backup_number}")
    os.makedirs(backup_path)

    for file in os.listdir(ITEMS_FOLDER):
        if file.endswith(".txt"):
            shutil.copy(os.path.join(ITEMS_FOLDER, file), os.path.join(backup_path, file))

def fix_inventory():
    global fixes
    files = os.listdir(ITEMS_FOLDER)
    item_files = []
    extra_files = []

    # Regex to match valid item[n].txt
    pattern = re.compile(r"item(\d+)\.txt")

    for f in files:
        match = pattern.fullmatch(f)
        if match:
            index = int(match.group(1))
            item_files.append((index, f))
        elif f.endswith(".txt"):
            extra_files.append(f)

    # Sort existing item files by index
    item_files.sort()

    # 1. Check for item0.txt
    if item_files and item_files[0][0] == 0:
        #print("[1;1H[!] item0.txt found. Shifting everything up...")
        fixes += 1
        for index, filename in reversed(item_files):
            fixes += 1
            new_index = index + 1
            os.rename(
                os.path.join(ITEMS_FOLDER, filename),
                os.path.join(ITEMS_FOLDER, f"item{new_index}.txt")
            )
        item_files = [(i+1, f"item{i+1}.txt") for i, _ in item_files]

    # 2. Move extra .txt files to the end
    if extra_files:
        last_index = max([i for i, _ in item_files], default=0)
        #print(f"[1;1H[!] Found {len(extra_files)} nonstandard .txt files. Moving to end...")
        for f in extra_files:
            fixes += 1
            last_index += 1
            os.rename(
                os.path.join(ITEMS_FOLDER, f),
                os.path.join(ITEMS_FOLDER, f"item{last_index}.txt")
            )
            item_files.append((last_index, f"item{last_index}.txt"))

    # 3. Fix gaps
    item_files.sort()
    expected = 1
    corrected = []

    for actual_index, filename in item_files:
        if actual_index != expected:
            fixes += 1
            #print(f"[1;1H[!] Gap detected: {filename} should be item{expected}.txt")
            os.rename(
                os.path.join(ITEMS_FOLDER, filename),
                os.path.join(ITEMS_FOLDER, f"item{expected}.txt")
            )
            corrected.append(f"item{actual_index}.txt → item{expected}.txt")
        expected += 1

    # 4. Check total consistency
    total_files = len([f for f in os.listdir(ITEMS_FOLDER) if f.endswith(".txt")])
    if total_files != expected - 1:
        fixes += 1
        #print("[1;1H[!!!] Emergency repair mode activated.")
        all_txts = [f for f in os.listdir(ITEMS_FOLDER) if f.endswith(".txt")]
        all_txts.sort()  # for consistent output, not important
        for i, f in enumerate(all_txts, start=1):
            fixes += 1
            newname = f"item{i}.txt"
            os.rename(
                os.path.join(ITEMS_FOLDER, f),
                os.path.join(ITEMS_FOLDER, newname)
            )
        #print("[1;1H[✓] Files forcibly reordered.")

    if corrected:
        for line in corrected:
            print("[1;1H" + line)
        print(f"[1;1H⚠  Inventory unstable -> We applied {fixes} fixes to your weapons. They should be back to normal now!           ")

if __name__ == "__main__":
    make_backup()
    fix_inventory()
