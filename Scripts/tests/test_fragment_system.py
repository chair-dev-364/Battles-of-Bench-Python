import ast
import os
import random
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


CONSTANTS = {
    "CHARACTER_MAX_LEVEL",
    "WEAPON_MAX_LEVEL",
    "ARMOR_MAX_LEVEL",
    "HEADWEAR_MAX_LEVEL",
    "FRAGMENT_MAX_LEVEL",
    "WEAPON_REFINEMENT_MAX",
    "WEAPON_REFINEMENT_CRIT_DAMAGE",
    "WEAPON_REFINEMENT_ATK_RATE",
    "WEAPON_REFINEMENT_DUST_BASE_COST",
    "FRAGMENT_SLOTS",
    "FRAGMENT_MAIN_STATS",
    "FRAGMENT_SUBSTAT_RANGES",
    "FRAGMENT_PERCENT_STATS",
    "FRAGMENT_OFFENSIVE_SCALE",
    "FRAGMENT_BONUS_SCALES",
    "FRAGMENT_SETS",
    "ITEM_UPGRADE_BASE_COSTS",
    "INVENTORY_COMPARISON_CATEGORIES",
}

FUNCTIONS = {
    "get_item_max_level",
    "clamp_item_level",
    "required_player_level_for_item",
    "update",
    "read",
    "_clear_object",
    "normalize_fragment_stat",
    "compact_number",
    "format_fragment_stat",
    "format_fragment_set_effect",
    "get_fragment_main_stat_value",
    "get_fragment_main_stat_base",
    "generate_fragment_main_stat",
    "get_fragment_substats",
    "generate_fragment_substat",
    "apply_fragment_substats",
    "fragment_item_parts",
    "load_fragment_item_fields",
    "create_fragment",
    "spawn_fragment",
    "fragment_slot_path",
    "get_scaled_equipment_stat",
    "get_actual_atk",
    "get_actual_defense",
    "scale_fragment_bonus",
    "scale_fragment_stat",
    "fragment_stat_icon",
    "get_fragment_bonuses",
    "effective_def",
    "refresh_player_core_stats",
    "refresh_player_secondary_stats",
    "character_exp_progress",
    "inv_active_path",
    "inv_active_paths",
    "inv_item_number_marker",
    "inv_category_supports_comparison",
    "inv_compare_value",
    "round_upgrade_price",
    "item_upgrade_cost_for_level",
    "item_upgrade_cost",
    "max_item_level_for_player",
    "max_affordable_upgrade_levels",
    "apply_item_upgrade",
    "weapon_refinement_cost",
    "weapon_refinement_preview",
    "apply_weapon_refinement",
    "remove_inventory_item",
    "duplicate_inventory_item",
    "get_ability",
}


def load_fragment_namespace():
    source = Path(__file__).parents[2] / "main.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = {
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            }
            if names & CONSTANTS:
                selected.append(node)
        elif isinstance(node, ast.ClassDef) and node.name == "FragmentData":
            selected.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS:
            selected.append(node)

    namespace = {
        "os": os,
        "random": random,
        "re": re,
        "shutil": shutil,
        "Path": Path,
        "xlyellow": "",
        "bold": "",
        "reset": "",
    }
    module = ast.Module(body=selected, type_ignores=[])
    exec(compile(module, str(source), "exec"), namespace)
    return namespace


class FragmentSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = load_fragment_namespace()

    def setUp(self):
        random.seed(2026)
        fragment_type = self.ns["FragmentData"]
        self.ns["FRAGMENT_EQUIPPED_OBJECTS"] = {
            slot: fragment_type()
            for slot in self.ns["FRAGMENT_SLOTS"]
        }
        self.ns["player"] = SimpleNamespace(level=100, money=0, dust=10_000)

    def test_generation_serialization_and_fixed_unique_substats(self):
        create_fragment = self.ns["create_fragment"]
        original = create_fragment("Ring", "Crit Rate", "Assassin", 15)
        substats = self.ns["get_fragment_substats"](original)

        self.assertEqual(len(substats), 3)
        self.assertEqual(len({name for name, _ in substats}), 3)
        self.assertNotIn(original.main_stat, {name for name, _ in substats})

        parts = self.ns["fragment_item_parts"](original)
        loaded = self.ns["FragmentData"]()
        self.ns["load_fragment_item_fields"](loaded, parts)
        self.assertEqual(loaded.slot, original.slot)
        self.assertEqual(loaded.set, "Assassin")
        self.assertEqual(
            self.ns["get_fragment_main_stat_value"](loaded),
            self.ns["get_fragment_main_stat_value"](original),
        )
        self.assertEqual(self.ns["get_fragment_substats"](loaded), substats)

    def test_fragment_stat_formatting_distinguishes_flat_and_percent(self):
        formatter = self.ns["format_fragment_stat"]
        self.assertEqual(formatter("ATK", 18, signed=True), "+18 ATK")
        self.assertEqual(formatter("HP", 220, signed=True), "+220 HP")
        self.assertEqual(formatter("DEF", 14, signed=True), "+14 DEF")
        self.assertEqual(formatter("Speed", 6, signed=True), "+6 Speed")
        self.assertEqual(formatter("ATK %", 5, signed=True), "+5% ATK")
        self.assertEqual(
            formatter("Crit Rate", 3, signed=True),
            "+3% Crit Rate",
        )

    def test_empty_equipment_ability_is_safe(self):
        self.assertIn(
            "No ability",
            self.ns["get_ability"](None),
        )

    def test_comparison_is_limited_to_weapons_and_armor(self):
        supports_comparison = self.ns["inv_category_supports_comparison"]
        self.assertTrue(supports_comparison("Weapons"))
        self.assertTrue(supports_comparison("Bodywear"))
        self.assertTrue(supports_comparison("Helmets"))
        self.assertFalse(supports_comparison("Fragments"))
        with self.assertRaises(ValueError):
            self.ns["inv_compare_value"](SimpleNamespace(), "Fragments")

    def test_equipped_fragments_use_checkmark_list_marker(self):
        previous_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                fragment = SimpleNamespace(slot="Ring")
                self.ns["update"]("Items/active_fragment_ring", 7)
                marker = self.ns["inv_item_number_marker"]

                self.assertEqual(marker("Fragments", 7, fragment), "✓")
                self.assertEqual(marker("Fragments", 8, fragment), "›")
                self.assertEqual(marker("Weapons", 7, fragment), "›")
            finally:
                os.chdir(previous_cwd)

    def test_upgrade_rolls_substats_only_inside_validated_transaction(self):
        source_path = Path(__file__).parents[2] / "main.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }
        upgrade = functions["_upgrade_selected_item_flow"]
        calls = {
            node.func.id: node.lineno
            for node in ast.walk(upgrade)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("generate_fragment_substat", calls)
        self.assertNotIn("apply_fragment_substats", calls)
        self.assertNotIn("hold_for_confirmation", calls)
        self.assertIn("apply_item_upgrade", calls)

    def test_fragment_page_uses_shared_weapon_inventory_renderer(self):
        source_path = Path(__file__).parents[2] / "main.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }

        def named_calls(function_name):
            return {
                node.func.id
                for node in ast.walk(functions[function_name])
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
            }

        self.assertIn(
            "draw_equipment_title_bar",
            named_calls("character2"),
        )
        self.assertNotIn(
            "draw_equipment_title_bar",
            named_calls("inventory_prep"),
        )
        self.assertIn(
            "item_pager",
            named_calls("inventory_prep"),
        )
        self.assertNotIn("draw_equipped_fragments_panel", functions)

    def test_upgrade_and_delete_confirmation_routes_are_isolated(self):
        source_path = Path(__file__).parents[2] / "main.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }

        def confirmation_actions(function_name):
            actions = []
            for node in ast.walk(functions[function_name]):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "hold_for_confirmation"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                ):
                    actions.append(node.args[0].value)
            return actions

        self.assertEqual(
            confirmation_actions("_upgrade_selected_item_flow"),
            [],
        )
        self.assertEqual(
            confirmation_actions("_delete_selected_item_flow"),
            ["delete"],
        )
        upgrade_source = ast.get_source_segment(
            source_path.read_text(encoding="utf-8"),
            functions["upgrade_selected_item"],
        )
        delete_source = ast.get_source_segment(
            source_path.read_text(encoding="utf-8"),
            functions["delete_selected_item"],
        )
        self.assertIn('d.inventory_action_mode = "upgrade"', upgrade_source)
        self.assertIn('d.inventory_action_mode = "delete"', delete_source)

        upgrade_flow_source = ast.get_source_segment(
            source_path.read_text(encoding="utf-8"),
            functions["_upgrade_selected_item_flow"],
        )
        self.assertNotIn("game.goto = reload_items", upgrade_flow_source)
        self.assertIn("draw_refinement_menu", upgrade_flow_source)

    def test_character_attributes_have_no_inline_addition_markers(self):
        source_path = Path(__file__).parents[2] / "main.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        character = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "character"
        )
        character_source = ast.get_source_segment(source, character)
        self.assertNotIn("(+{", character_source)
        self.assertIn("player.bonus_atk", character_source)
        self.assertIn("player.bonus_def", character_source)
        self.assertIn("player.bonus_hp", character_source)

    def test_character_exp_progress_stops_at_level_cap(self):
        progress = self.ns["character_exp_progress"]

        self.assertIsNone(progress(100, 0, 10_000))
        self.assertIsNone(progress(101, 0, 10_000))
        self.assertEqual(progress(99, 500, 1_000), (50, 15))

    def test_spawn_fragment_creates_inventory_file(self):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                created = self.ns["create_fragment"](
                    "Bracelet", "Speed", "Titan", 5
                )
                item_id = self.ns["spawn_fragment"](created)
                path = Path("Items/Fragments") / f"item{item_id}.txt"
                self.assertTrue(path.exists())

                loaded = self.ns["FragmentData"]()
                self.ns["load_fragment_item_fields"](
                    loaded,
                    path.read_text(encoding="utf-8").split(";;"),
                )
                self.assertEqual(loaded.slot, "Bracelet")
                self.assertEqual(loaded.set_name, "Titan")
                self.assertEqual(len(self.ns["get_fragment_substats"](loaded)), 1)
            finally:
                os.chdir(original_cwd)

    def test_fragment_content_library_covers_slots_sets_and_main_stats(self):
        fragments_dir = Path(__file__).parents[2] / "Items" / "Fragments"
        paths = sorted(
            fragments_dir.glob("item*.txt"),
            key=lambda path: int(re.search(r"\d+", path.stem).group()),
        )
        self.assertGreaterEqual(len(paths), 36)

        slots = set()
        sets = set()
        main_stats = set()
        for path in paths:
            loaded = self.ns["FragmentData"]()
            self.ns["load_fragment_item_fields"](
                loaded,
                path.read_text(encoding="utf-8").strip().split(";;"),
            )
            slots.add(loaded.slot)
            sets.add(loaded.set_name)
            main_stats.add(loaded.main_stat)

        self.assertEqual(slots, set(self.ns["FRAGMENT_SLOTS"]))
        self.assertEqual(sets, set(self.ns["FRAGMENT_SETS"]))
        self.assertEqual(main_stats, set(self.ns["FRAGMENT_MAIN_STATS"]))

    def test_legacy_fragment_format_is_migrated_in_memory(self):
        legacy = self.ns["FragmentData"]()
        self.ns["load_fragment_item_fields"](
            legacy,
            "Bracelet of Dreams;;15;;ATK;;230;;ATKP;;2;;HP;;45;;DEF;;10".split(";;"),
        )
        self.assertEqual(legacy.slot, "Bracelet")
        self.assertEqual(legacy.main_stat_value, 174)
        self.assertEqual(self.ns["get_fragment_main_stat_value"](legacy), 230)
        self.assertEqual(
            [name for name, _ in self.ns["get_fragment_substats"](legacy)],
            ["ATK %", "HP", "DEF"],
        )

    def test_three_slots_and_stacking_set_bonuses(self):
        for slot in self.ns["FRAGMENT_SLOTS"]:
            self.ns["FRAGMENT_EQUIPPED_OBJECTS"][slot] = self.ns[
                "create_fragment"
            ](slot, "HP", "Warrior", 1)

        bonuses = self.ns["get_fragment_bonuses"]()
        self.assertEqual(
            bonuses["active_sets"],
            ["Warrior 2pc", "Warrior 3pc"],
        )
        self.assertEqual(bonuses["atk_percent"], 6)
        self.assertEqual(bonuses["speed"], 8)

        self.ns["FRAGMENT_EQUIPPED_OBJECTS"]["Ring"].set_name = "Titan"
        bonuses = self.ns["get_fragment_bonuses"]()
        self.assertEqual(bonuses["active_sets"], ["Warrior 2pc"])
        self.assertEqual(bonuses["atk_percent"], 6)
        self.assertEqual(bonuses["speed"], 0)

    def test_offensive_fragment_bonuses_are_halved_except_speed(self):
        fragment_stats = {
            "Bracelet": ("ATK", 11),
            "Necklace": ("Crit Rate", 5),
            "Ring": ("Speed", 5),
        }
        for slot, (stat_name, value) in fragment_stats.items():
            equipped = self.ns["FragmentData"]()
            equipped.slot = slot
            equipped.name = f"Test {slot}"
            equipped.level = 1
            equipped.main_stat = stat_name
            equipped.main_stat_value = value
            equipped.set_name = "No Set"
            self.ns["FRAGMENT_EQUIPPED_OBJECTS"][slot] = equipped

        bonuses = self.ns["get_fragment_bonuses"]()

        self.assertEqual(bonuses["atk_flat"], 5.5)
        self.assertEqual(bonuses["crit_rate"], 2.5)
        self.assertEqual(bonuses["speed"], 5)

    def test_hp_and_def_fragment_scaling_and_stat_icons(self):
        scale_stat = self.ns["scale_fragment_stat"]
        stat_icon = self.ns["fragment_stat_icon"]

        self.assertEqual(scale_stat("HP", 101), 50.5)
        self.assertEqual(scale_stat("HP %", 7), 5)
        self.assertIsInstance(scale_stat("HP %", 7), int)
        self.assertEqual(scale_stat("DEF", 7), 3.5)
        self.assertEqual(scale_stat("Speed", 7), 7)
        self.assertEqual(stat_icon("HP"), "♥")
        self.assertEqual(stat_icon("DEF"), "🛡")
        self.assertEqual(stat_icon("ATK"), "⚔")

    def test_fragment_bonuses_feed_core_and_secondary_stats(self):
        fragments = {
            "Bracelet": ("ATK", 10),
            "Necklace": ("HP", 100),
            "Ring": ("DEF", 5),
        }
        for slot, (main_stat, value) in fragments.items():
            equipped = self.ns["FragmentData"]()
            equipped.slot = slot
            equipped.name = f"Warrior {slot}"
            equipped.level = 1
            equipped.main_stat = main_stat
            equipped.main_stat_value = value
            equipped.set_name = "Warrior"
            self.ns["FRAGMENT_EQUIPPED_OBJECTS"][slot] = equipped

        self.ns["player"] = SimpleNamespace(level=10)
        self.ns["item"] = SimpleNamespace(
            atk=100,
            level=0,
            level_power=0,
            atkcrit=50,
            substat=None,
            substat_value=0,
        )
        self.ns["armor"] = SimpleNamespace(name=None)
        self.ns["head"] = SimpleNamespace(name=None)

        stats = self.ns["refresh_player_core_stats"](False)
        self.assertEqual(stats["total_dmg"], 211)
        self.assertEqual(stats["total_hp"], 307)
        self.assertEqual(self.ns["player"].fragment_atk_bonus, 11)
        self.assertEqual(self.ns["player"].fragment_hp_bonus, 50)
        self.assertEqual(self.ns["player"].bonus_atk, 11)
        self.assertEqual(self.ns["player"].bonus_hp, 50)
        self.assertEqual(self.ns["player"].fragment_speed_bonus, 8)
        self.assertEqual(self.ns["player"].speed, 113)
        self.assertEqual(self.ns["player"].crit_damage, 50)

    def test_level_restrictions_and_dust_upgrade(self):
        max_level = self.ns["max_item_level_for_player"]
        self.assertEqual(max_level("Fragments", 19), 3)
        self.assertEqual(max_level("Fragments", 20), 6)
        self.assertEqual(max_level("Fragments", 40), 9)
        self.assertEqual(max_level("Fragments", 60), 12)
        self.assertEqual(max_level("Fragments", 80), 15)

        fragment = self.ns["create_fragment"](
            "Necklace", "ATK", "Guardian", 1
        )
        initial_dust = self.ns["player"].dust
        expected_cost = self.ns["item_upgrade_cost"](
            fragment, "Fragments", 14
        )
        upgraded, charged = self.ns["apply_item_upgrade"](
            fragment, "Fragments", 14
        )
        self.assertTrue(upgraded)
        self.assertEqual(charged, expected_cost)
        self.assertEqual(self.ns["player"].dust, initial_dust - expected_cost)
        self.assertEqual(fragment.level, 15)
        self.assertEqual(len(self.ns["get_fragment_substats"](fragment)), 3)

        dust_after_upgrade = self.ns["player"].dust
        upgraded, _ = self.ns["apply_item_upgrade"](
            fragment, "Fragments", 1
        )
        self.assertFalse(upgraded)
        self.assertEqual(self.ns["player"].dust, dust_after_upgrade)

    def test_weapon_refinement_has_three_persistent_stat_stages(self):
        weapon = SimpleNamespace(
            level=25,
            refine=0,
            atk=100,
            atkcrit=20,
            level_power=0,
            rarity="02",
        )
        self.ns["player"] = SimpleNamespace(
            level=100,
            money=1_000_000,
            dust=10_000,
        )

        starting_money = self.ns["player"].money
        starting_dust = self.ns["player"].dust
        total_gold_cost = 0
        total_dust_cost = 0
        for expected_stage in range(1, 4):
            refined, costs = self.ns["apply_weapon_refinement"](weapon)
            self.assertTrue(refined)
            total_gold_cost += costs["gold"]
            total_dust_cost += costs["dust"]
            self.assertEqual(weapon.refine, expected_stage)
            self.assertEqual(
                weapon.atkcrit,
                20 + expected_stage * self.ns["WEAPON_REFINEMENT_CRIT_DAMAGE"],
            )

        self.assertGreater(weapon.atk, 100)
        self.assertEqual(weapon.atk, 133)
        self.assertEqual(
            self.ns["player"].money,
            starting_money - total_gold_cost,
        )
        self.assertEqual(
            self.ns["player"].dust,
            starting_dust - total_dust_cost,
        )

        refined, costs = self.ns["apply_weapon_refinement"](weapon)
        self.assertFalse(refined)
        self.assertEqual(costs, {"gold": 0, "dust": 0})
        self.assertEqual(weapon.refine, 3)

    def test_seed_weapons_start_unrefined(self):
        weapons_dir = Path(__file__).parents[2] / "Items" / "Weapons"
        weapon_paths = list(weapons_dir.glob("item*.txt"))

        self.assertTrue(weapon_paths)
        for path in weapon_paths:
            fields = path.read_text(encoding="utf-8").strip().split(";;")
            self.assertEqual(
                fields[12],
                "0",
                f"{path.name} should start at refinement 0",
            )

    def test_refinement_costs_are_deducted_atomically(self):
        weapon = SimpleNamespace(
            level=25,
            refine=0,
            atk=100,
            atkcrit=20,
            level_power=0,
            rarity="02",
        )
        preview = self.ns["weapon_refinement_preview"](weapon)
        self.ns["player"] = SimpleNamespace(
            level=100,
            money=preview["gold_cost"],
            dust=preview["dust_cost"] - 1,
        )

        refined, costs = self.ns["apply_weapon_refinement"](weapon)

        self.assertFalse(refined)
        self.assertEqual(costs["gold"], preview["gold_cost"])
        self.assertEqual(costs["dust"], preview["dust_cost"])
        self.assertEqual(self.ns["player"].money, preview["gold_cost"])
        self.assertEqual(self.ns["player"].dust, preview["dust_cost"] - 1)
        self.assertEqual(weapon.refine, 0)

    def test_upgrade_rejects_player_level_and_insufficient_dust(self):
        fragment = self.ns["create_fragment"](
            "Bracelet", "DEF", "Guardian", 1
        )
        self.ns["player"].level = 19
        upgraded, _ = self.ns["apply_item_upgrade"](
            fragment, "Fragments", 3
        )
        self.assertFalse(upgraded)
        self.assertEqual(fragment.level, 1)

        self.ns["player"].level = 20
        self.ns["player"].dust = 0
        upgraded, _ = self.ns["apply_item_upgrade"](
            fragment, "Fragments", 1
        )
        self.assertFalse(upgraded)
        self.assertEqual(fragment.level, 1)

    def test_duplicate_and_delete_keep_all_slot_ids_aligned(self):
        original_cwd = os.getcwd()
        original_refresh = self.ns["refresh_player_core_stats"]
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                fragments_dir = Path("Items/Fragments")
                fragments_dir.mkdir(parents=True)
                for item_id in range(1, 4):
                    (fragments_dir / f"item{item_id}.txt").write_text(
                        f"fragment-{item_id}",
                        encoding="utf-8",
                    )
                self.ns["update"]("Items/active_fragment_bracelet", 2)
                self.ns["update"]("Items/active_fragment_necklace", 3)
                self.ns["update"]("Items/active_fragment_ring", "none")
                self.ns["refresh_player_core_stats"] = lambda: None

                self.assertTrue(
                    self.ns["duplicate_inventory_item"](
                        1, "Fragments", 3
                    )
                )
                self.assertEqual(
                    self.ns["read"]("Items/active_fragment_bracelet"), 3
                )
                self.assertEqual(
                    self.ns["read"]("Items/active_fragment_necklace"), 4
                )

                self.assertTrue(
                    self.ns["remove_inventory_item"](
                        3, "Fragments", 4
                    )
                )
                self.assertEqual(
                    self.ns["read"]("Items/active_fragment_bracelet"), "none"
                )
                self.assertEqual(
                    self.ns["read"]("Items/active_fragment_necklace"), 3
                )
                self.assertEqual(
                    len(list(fragments_dir.glob("item*.txt"))), 3
                )
            finally:
                self.ns["refresh_player_core_stats"] = original_refresh
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
