"""Inventory file sorting shared by the game and the command-line helper."""

import argparse
import re
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parent
ITEM_CATEGORIES = ("Weapons", "Bodywear", "Helmets", "Fragments")
RARITY_TIERS = ("08", "02", "03", "0d", "0e")
ACTIVE_ITEM_FILES = {
    "Weapons": ("active_weapon.txt",),
    "Bodywear": ("active_body.txt",),
    "Helmets": ("active_head.txt",),
    "Fragments": (
        "active_fragment_bracelet.txt",
        "active_fragment_necklace.txt",
        "active_fragment_ring.txt",
    ),
}
ITEM_FILE_PATTERN = re.compile(r"item(\d+)\.txt$")


def _item_metadata(path, category):
    """Return name, level and rarity from either equipment file format."""
    parts = path.read_text(encoding="utf-8").splitlines()[0].split(";;")
    if category == "Fragments":
        name = parts[1] if len(parts) > 1 else ""
        level_text = parts[2] if len(parts) > 2 else ""
        rarity = ""
    else:
        rarity = parts[1] if len(parts) > 1 else ""
        name = parts[2] if len(parts) > 2 else ""
        level_text = parts[3] if len(parts) > 3 else ""
    try:
        level = float(level_text)
    except (TypeError, ValueError):
        level = float("inf")
    rarity_tier = (
        RARITY_TIERS.index(rarity)
        if rarity in RARITY_TIERS
        else -1
    )
    return {
        "name": name.casefold(),
        "level": level,
        "rarity": rarity_tier,
    }


def _numbered_item_files(folder):
    files = []
    if not folder.is_dir():
        return files
    for path in folder.iterdir():
        match = ITEM_FILE_PATTERN.fullmatch(path.name)
        if match:
            files.append((int(match.group(1)), path))
    return sorted(files)


def _update_active_item_ids(items_root, category, id_map):
    for filename in ACTIVE_ITEM_FILES.get(category, ()):
        path = items_root / filename
        if not path.exists():
            continue
        value = path.read_text(encoding="utf-8").strip()
        try:
            old_id = int(value)
        except ValueError:
            continue
        if old_id in id_map:
            path.write_text(str(id_map[old_id]), encoding="utf-8")


def sort_item_category(items_root, category, sorting, order):
    """Sort and sequentially rename one item category; return old-to-new IDs."""
    if sorting == "Off":
        return {}
    if category not in ITEM_CATEGORIES:
        raise ValueError(f"Unknown item category: {category}")
    key_name = sorting.casefold()
    if key_name not in {"name", "level", "rarity"}:
        raise ValueError(f"Unknown inventory sorting method: {sorting}")

    items_root = Path(items_root)
    folder = items_root / category
    records = []
    for old_id, path in _numbered_item_files(folder):
        try:
            metadata = _item_metadata(path, category)
        except (OSError, IndexError, UnicodeError):
            metadata = {"name": "", "level": float("inf"), "rarity": -1}
        records.append((old_id, path, metadata))

    records.sort(
        key=lambda record: record[2][key_name],
        reverse=order == "Descending",
    )
    id_map = {
        old_id: new_id
        for new_id, (old_id, _, _) in enumerate(records, start=1)
    }
    if all(old_id == new_id for old_id, new_id in id_map.items()):
        return id_map

    temporary_paths = []
    token = uuid4().hex
    for old_id, path, _ in records:
        temporary = folder / f".{path.name}.{token}.sorting"
        path.replace(temporary)
        temporary_paths.append((old_id, temporary))
    for old_id, temporary in temporary_paths:
        temporary.replace(folder / f"item{id_map[old_id]}.txt")

    _update_active_item_ids(items_root, category, id_map)
    return id_map


def sort_inventory(items_root, sorting, order):
    """Apply the configured ordering to every inventory category."""
    if sorting == "Off":
        return {}
    return {
        category: sort_item_category(items_root, category, sorting, order)
        for category in ITEM_CATEGORIES
    }


def main():
    parser = argparse.ArgumentParser(description="Sort inventory item files.")
    parser.add_argument("sorting", choices=("Name", "Level", "Rarity"))
    parser.add_argument("order", choices=("Ascending", "Descending"))
    args = parser.parse_args()
    sort_inventory(PROJECT_ROOT / "Items", args.sorting, args.order)


if __name__ == "__main__":
    main()
