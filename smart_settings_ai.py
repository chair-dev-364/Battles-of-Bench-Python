import sys
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression

# Ensure UTF-8 output on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# === TRAINING DATA ===
data = {
    ":adjust_ui": [
        "adjust ui volume", "change menu volume", "ui sounds are too loud",
        "make button clicks quieter", "how to lower ui sounds", "menu sfx too loud",
        "quiet interface sounds", "reduce ui sound level", "adjust interface volume", "turn down ui effects"
    ],
    ":adjust_sfx": [
        "adjust battle sfx volume", "lower sound effects", "battle sounds too loud",
        "quiet combat sounds", "turn down attack sounds", "make sfx quieter",
        "combat sound too loud", "reduce battle sfx", "lower effect volume", "adjust fx audio"
    ],
    ":adjust_music": [
        "adjust music volume", "make background music softer", "turn off music",
        "lower game music", "adjust bgm", "reduce music volume", "mute game music",
        "game music too loud", "how to turn down the bgm", "volume of music setting"
    ],
    ":change_engine": [
        "change audio engine", "switch audio driver", "pick different sound engine",
        "select another audio mode", "use alternate audio engine", "set audio backend",
        "update audio system", "replace audio processor", "change how audio works", "change sound engine"
    ],
    ":change_music": [
        "change menu music", "switch title screen song", "choose different menu bgm",
        "change startup music", "menu theme select", "title song change",
        "music for menus", "edit menu music", "adjust startup tune", "main menu music"
    ],
    ":perform_sound_test": [
        "perform sound test", "test sound effects", "check sfx", "play sound test",
        "hear the sound effects", "listen to sfx samples", "trigger sound effects",
        "run sfx demo", "audio sfx test mode", "sound test option"
    ],
    ":perform_music_test": [
        "perform music test", "test background music", "play all music", "music test",
        "preview game music", "listen to game songs", "bgm test", "soundtrack preview",
        "try music samples", "demo the bgm"
    ],
    ":keybindsset": [
        "change keybinds", "edit control keys", "set custom keybinds", "rebind keys",
        "adjust key configuration", "customize inputs", "remap buttons", "set game controls",
        "edit input mapping", "change keyboard setup"
    ],
    ":uisettings": [
        "change ui appearance", "customize interface", "edit window style", "ui theme settings",
        "adjust game interface", "change how game looks", "ui settings menu", "customize ui visuals",
        "edit ui layout", "ui customization"
    ],
    ":uisettings_invsort": [
        "sort inventory weapons", "change weapon order", "adjust inventory sorting", "weapon list order",
        "sort item list", "inventory arrangement", "sort your gear", "change item order", "edit inventory sorting", "reorder inventory"
    ],
    ":uisettings_type": [
        "change character screen info", "toggle character data", "adjust what is shown on character screen",
        "switch stats view", "character info options", "status screen layout", "edit char screen data", "status screen type",
        "what shows on character screen", "change displayed stats"
    ],
    ":uisettings_defdiff": [
        "change battle difficulty", "default difficulty", "set combat level", "make battles harder",
        "adjust fight difficulty", "easy or hard mode", "battle level setting", "default challenge level",
        "combat difficulty slider", "battle difficulty menu"
    ],
    ":uisettings_ilevelup": [
        "change item level up mode", "item level system", "leveling mode for items", "adjust item upgrade style",
        "how items level up", "item improvement settings", "upgrade item options", "choose item growth mode",
        "level system for gear", "item xp method"
    ],
    ":settingsplayername": [
        "change player name", "edit my name", "rename character", "player name change",
        "set new username", "change what I’m called", "edit in-game name", "rename myself",
        "update profile name", "set player identity"
    ],
    ":uisettings_pronouns": [
        "change pronouns", "edit your pronouns", "set custom pronouns", "update character pronouns",
        "pronoun settings", "adjust how you're referred to", "select your pronouns",
        "edit pronoun preference", "choose identity pronouns", "pronouns configuration"
    ],
    ":backupsettings_pwd": [
        "backup and restore", "save game backup", "restore save file", "backup manager",
        "recover my data", "game backup settings", "load old save", "backup system",
        "restore from backup", "save data restore"
    ],
    ":systeminfo": [
        "view system info", "about the game", "system version info", "game information",
        "game version and details", "check about section", "see system specs",
        "info about current version", "view build number", "show system details"
    ],
    ":checkvariablesall": [
        "view all variables", "debug variables", "show internal variables", "check all flags",
        "see debug values", "view global vars", "internal variable viewer",
        "game variable list", "inspect game flags", "open variable log"
    ],
    ":update_game": [
        "update the game", "check for update", "download latest version", "patch the game",
        "get new version", "game update settings", "install update", "look for patch",
        "software update", "fetch game update"
    ]
}

# === FLATTEN & TRAIN ===
phrases, labels = [], []
for label, examples in data.items():
    phrases.extend(examples)
    labels.extend([label] * len(examples))

vectorizer = CountVectorizer(ngram_range=(1, 3))
X = vectorizer.fit_transform(phrases)

model = LogisticRegression(max_iter=1000)
model.fit(X, labels)

def predict_label(user_input):
    vec = vectorizer.transform([user_input])
    probs = model.predict_proba(vec)[0]
    top_index = probs.argmax()
    return model.classes_[top_index], probs[top_index]

# === CLI ENTRY POINT ===
if __name__ == "__main__":
    user_input = " ".join(sys.argv[1:]).strip().lower()
    label, confidence = predict_label(user_input)
    if confidence < 0.1:
        print("NO_CONFIDENCE")
    else:
        print(label)
