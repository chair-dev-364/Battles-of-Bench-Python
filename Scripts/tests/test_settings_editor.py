import unittest

from Scripts.Settings.editor import SettingEditor
from Scripts.Settings.keybinds import SETTINGS


KEYBINDS_BY_ATTR = {item["attr"]: item for item in SETTINGS}


class FakeSettings:
    _keybind_fields = tuple(KEYBINDS_BY_ATTR)

    def __init__(self):
        for attr, item in KEYBINDS_BY_ATTR.items():
            setattr(self, attr, item["default"])
        self.saved = False

    def save(self):
        self.saved = True


class KeybindConflictTests(unittest.TestCase):
    def setUp(self):
        self.owner = FakeSettings()
        self.editor = SettingEditor()

    def test_menu_bind_can_share_key_with_battle_bind(self):
        self.editor.begin(KEYBINDS_BY_ATTR["confirm"], self.owner)

        result = self.editor.handle_key("space")

        self.assertEqual(result, "saved")
        self.assertEqual(self.owner.confirm, "space")
        self.assertTrue(self.owner.saved)

    def test_menu_binds_still_conflict_with_each_other(self):
        self.owner.deny = "space"
        self.editor.begin(KEYBINDS_BY_ATTR["confirm"], self.owner)

        result = self.editor.handle_key("space")

        self.assertEqual(result, "error")
        self.assertEqual(self.owner.confirm, "y")
        self.assertIn("deny", self.editor.message)

    def test_battle_binds_still_conflict_with_each_other(self):
        self.editor.begin(KEYBINDS_BY_ATTR["skill"], self.owner)

        result = self.editor.handle_key("space")

        self.assertEqual(result, "error")
        self.assertEqual(self.owner.skill, "s")
        self.assertIn("attack", self.editor.message)

if __name__ == "__main__":
    unittest.main()
