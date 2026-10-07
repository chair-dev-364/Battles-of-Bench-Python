"""Declarative settings schema shared by persistence and the settings screen."""

from Scripts.Settings.accessibility import SETTINGS as ACCESSIBILITY_SETTINGS
from Scripts.Settings.appearance import SETTINGS as APPEARANCE_SETTINGS
from Scripts.Settings.battles import SETTINGS as BATTLE_SETTINGS
from Scripts.Settings.inventory import SETTINGS as INVENTORY_SETTINGS
from Scripts.Settings.keybinds import SETTINGS as KEYBIND_SETTINGS
from Scripts.Settings.sound import SETTINGS as SOUND_SETTINGS
from Scripts.Settings.controls import SETTINGS as CONTROL_SETTINGS
from Scripts.Settings.save_data import SETTINGS as SAVE_SETTINGS
from Scripts.Settings.developer import SETTINGS as DEVELOPER_SETTINGS


SETTINGS_PAGES = [
    BATTLE_SETTINGS,
    APPEARANCE_SETTINGS,
    SOUND_SETTINGS,
    KEYBIND_SETTINGS,
    ACCESSIBILITY_SETTINGS,
    INVENTORY_SETTINGS,
    CONTROL_SETTINGS,
    SAVE_SETTINGS,
    DEVELOPER_SETTINGS,
]

CATEGORY_NAMES = ["Battles", "Look & feel", "Sound & music", "Key binds",
                  "Accessibility", "Inventory", "Controls", "Save & data", "Developer"]
CATEGORY_ICONS = ["◆", "◐", "◇", "⬙", "∴", "▦", "⌘", "▣", "⚒"]

CATEGORY_DESCRIPTIONS = [
    "Change how battles play out, and what information is shown.",
    "Change animations, text effects, and number formatting.",
    "Change how sound and music are played, and their volume.",
    "Change what keys do what both in menus and battles.",
    "Make the game easier to read and use.",
    "Edit your preferred item sorting, upgrade, and comparison preferences.",
    "Choose how you navigate menus.",
    "Keep previous saves for recovery.",
    "Enable optional cheats and developer shortcuts.",
]

SETTINGS_BY_ATTR = {
    item["attr"]: item
    for page in SETTINGS_PAGES
    for item in page
}

if sum(map(len, SETTINGS_PAGES)) != len(SETTINGS_BY_ATTR):
    raise ValueError("Every setting must have a unique 'attr' value.")

for attr, item in SETTINGS_BY_ATTR.items():
    if "default" not in item:
        raise ValueError(f"Setting {attr!r} is missing a default value.")

PERSISTENT_DEFAULTS = {
    attr: item["default"]
    for attr, item in SETTINGS_BY_ATTR.items()
    if item.get("persistent", True)
}

KEYBIND_DEFAULTS = {
    item["attr"]: item["default"]
    for item in SETTINGS_BY_ATTR.values()
    if item["type"] == "keybind"
}
