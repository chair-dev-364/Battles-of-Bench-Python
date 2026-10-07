import difflib
import re

from Scripts.Settings.schema import SETTINGS_PAGES, CATEGORY_NAMES

# names aren't always what you remember, so try these too
SEARCH_TERMS = {
    # battles
    "battle_difficulty": "easy normal hard extreme enemy strength challenge combat difficulty enemies",
    "battle_turn_delay": "wait pause delay time seconds battle turn pacing combat speed",
    "player_health_display": "my hp player health hit points number bar healthbar life",
    "battle_details": "basic detailed battle info information stats damage combat details",
    "battle_short_action_log": "shorten compact battle messages combat log action text",
    "battle_action_history_length": "history previous recent last actions turns log messages combat",
    "victory_celebration": "win winning victory reward stars celebration small regular extreme minimal end battle",
    # look and feel
    "number_format": "numbers commas digits thousand million billion compact full k m b rounding",
    "battle_health_display": "enemy hp health hit points healthbar bar number monster life",
    "menu_background_decoration": "night stars nighttime background decoration scenery menu sky",
    "rainbow_text": "rainbow colorful colourful colours colors spectrum multicolor text letters",
    "text_shine": "shine shining glow shimmer sparkle sweep highlight bright text letters",
    "flipboard_animations": "flipboard flipping flip letters scramble scrambler changing text animation typewriter",
    "animation_speed": "animation animations speed fast faster slow slower multiplier playback timing 0.5x 1x 2x",
    "menu_transitions": "transition transitions screen wipe fade menu switching movement",
    "disable_startup_animation": "skip startup boot intro opening launch animation start faster",
    # sound and music
    "master": "master volume loudness all overall audio sound quiet louder softer",
    "disable_audio_completely": "mute silent silence disable audio off all sound music",
    "music": "music songs soundtrack bgm volume background tunes",
    "sound": "ui menu interface sound effects reward volume clicks buttons",
    "menu_feedback_sounds": "click clicks navigation buttons menu feedback sound toggle beep",
    "sfx": "sfx effects combat battle attack hit hits damage sound volume",
    "ambient": "ambient ambience atmosphere environmental background sound volume",
    "dialogue": "dialogue dialog speech voice voices talking spoken volume",
    "spatial": "spatial stereo left right pan panning positioning speakers headphones",
    "test_audio": "test audio sound speaker speakers headphones check preview beep play",
    # keys
    "back": "back return exit leave menu key keyboard binding shortcut",
    "confirm": "confirm accept enter submit yes key keyboard binding shortcut",
    "deny": "cancel deny reject escape esc no key keyboard binding shortcut",
    "attack": "attack hit normal strike damage battle key keyboard binding shortcut",
    "skill": "skill ability special battle key keyboard binding shortcut",
    "ult": "ultimate ult super special ability battle key keyboard binding shortcut",
    "heal": "heal healing potion restore hp health battle key keyboard binding shortcut",
    "forfeit": "forfeit surrender give up quit flee escape battle key keyboard shortcut",
    # accessibility
    "high_contrast_colors": "high contrast visibility readable legibility bright palette colorblind colours colors",
    "simplify_tutorials": "simple simplify tutorials help easy explanations instructions tips",
    "reduce_motion": "reduce motion accessibility disable animations static movement stop animation",
    "flash_effects": "flash flashes flashing flicker bright screen effects accessibility",
    "double_tap_confirmation": "double tap press twice confirmation hold safety delete upgrade",
    "confirmation_hold_duration": "hold duration confirmation time seconds long press delete upgrade",
    "auto_advance_dialogue": "auto advance dialogue dialog continue text speech talking automatically",
    # inventory
    "sort_items_automatically": "sort sorting auto automatically organize organise inventory bag equipment items",
    "inventory_sorting": "sort by criteria order inventory bag rarity name level sorting",
    "inventory_sort_order": "ascending descending highest lowest first order a to z alphabetical rarity levels",
    "remember_last_inventory_selection": "remember last selected selection item inventory bag position cursor session",
    "compare_equipped_item": "compare comparison equipped wearing gear better worse upgrade equipment inventory",
    "weapon_comparison_metric": "weapon compare comparison metric damage average critical crit normal dps",
    "item_level_up_mode": "upgrade upgrading level up equipment item one all bulk multiple levels",
    # controls
    "mouse_controls": "mouse pointer clicking clicks cursor wheel scroll touchpad trackpad controls",
    "menu_up": "up arrow navigation menu movement key keyboard binding",
    "menu_down": "down arrow navigation menu movement key keyboard binding",
    "menu_left": "left arrow navigation menu movement key keyboard binding",
    "menu_right": "right arrow navigation menu movement key keyboard binding",
    "open_inventory": "open inventory bag backpack equipment shortcut key keyboard",
    "open_character": "open character player profile stats attributes shortcut key keyboard",
    "open_settings": "open settings options preferences configuration shortcut key keyboard",
    # saves and developer tools
    "backup_count": "backup backups count keep automatic autosave snapshots recovery retention limit restore save data",
    "manual_backup": "backup now manual permanent named name snapshot create save archive zip recovery restore",
    "reset_settings": "reset settings default defaults factory restore preferences options keybinds start over",
    "debug_shortcuts": "developer dev debug debugging cheats cheat console editor tools shortcuts testing",
}


def search_words(text):
    text = str(text).casefold().replace('_', ' ')
    return ' '.join(re.findall(r'\w+', text))


def find_settings(query):
    query = search_words(query)
    if not query:
        return []
    words = query.split()
    matches = []

    for category, page in enumerate(SETTINGS_PAGES):
        items = list(page)
        if category == 2:
            items.append({
                'name': 'Test audio', 'attr': 'test_audio', 'type': 'action',
                'description': 'Play the configured audio test sound.',
                'accepted': ['Enter', 'Click'],
            })
        for index, item in enumerate(items):
            name = search_words(item['name'])
            aliases = search_words(SEARCH_TERMS.get(item['attr'], ''))
            description = search_words(item.get('description', ''))
            category_name = search_words(CATEGORY_NAMES[category])
            attr = search_words(item['attr'])
            choices = search_words(' '.join(str(choice) for choice in item.get('choices', [])))
            fields = [(name, 20), (aliases, 12), (attr, 8), (description, 4), (category_name, 3), (choices, 3)]
            score = 0
            found = True
            for word in words:
                word_score = 0
                for text, weight in fields:
                    if word in text:
                        word_score = max(word_score, weight)
                if word_score == 0:
                    # allow a small typo too
                    for text, weight in fields[:2]:
                        for candidate in text.split():
                            if len(word) >= 4 and difflib.SequenceMatcher(None, word, candidate).ratio() >= 0.8:
                                word_score = max(word_score, weight // 2)
                if word_score == 0:
                    found = False
                    break
                score += word_score
            if not found:
                continue
            if query == name:
                score += 100
            elif name.startswith(query):
                score += 60
            elif query in name:
                score += 40
            matches.append((score, category, index, item))

    matches.sort(key=lambda result: (-result[0], result[1], result[2]))
    return matches
