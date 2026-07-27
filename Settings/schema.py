"""Declarative settings schema shared by persistence and the settings screen."""

from Settings.accessibility import SETTINGS as ACCESSIBILITY_SETTINGS
from Settings.appearance import SETTINGS as APPEARANCE_SETTINGS
from Settings.battles import SETTINGS as BATTLE_SETTINGS
from Settings.developer import SETTINGS as DEVELOPER_SETTINGS
from Settings.keybinds import SETTINGS as KEYBIND_SETTINGS
from Settings.sound import SETTINGS as SOUND_SETTINGS


SETTINGS_PAGES = [
    BATTLE_SETTINGS,
    APPEARANCE_SETTINGS,
    SOUND_SETTINGS,
    KEYBIND_SETTINGS,
    ACCESSIBILITY_SETTINGS,
    DEVELOPER_SETTINGS,
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
}

KEYBIND_DEFAULTS = {
    item["attr"]: item["default"]
    for item in KEYBIND_SETTINGS
}
