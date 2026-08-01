def volume_setting(name, attr, default, description):
    return {
        "name": name,
        "attr": attr,
        "type": "slider",
        "min": 0,
        "max": 10,
        "step": 1,
        "display": "volume",
        "default": default,
        "description": description,
        "accepted": "Off / 10%-100%",
    }


SETTINGS = [
    volume_setting("Master volume", "master", 10, "The main dial. Controls how loud the entire game is."),
    volume_setting(
        "UI sound volume",
        "sound",
        10,
        "Controls button clicks, selection chimes, and UI feedback.",
    ),
    volume_setting(
        "Ambient sound volume",
        "ambient",
        10,
        "Background atmosphere - wind, rain, room tones and more!",
    ),
    volume_setting(
        "Battle SFX volume",
        "sfx",
        10,
        "How loud should combat hits and abilities pack a punch?",
    ),
    volume_setting(
        "Dialogue volume",
        "dialogue",
        10,
        "Controls character voice lines and chatter.",
    ),
    volume_setting("Music volume", "music", 3, "Adjust the soundtrack volume."),
    {
        "name": "Mute all audio",
        "attr": "disable_audio_completely",
        "type": "bool",
        "default": False,
        "description": "Silence all game audio while preserving your volume settings.",
        "accepted": ["Off", "On"],
    },
    {
        "name": "Spatial audio",
        "attr": "spatial",
        "type": "bool",
        "default": False,
        "description": "Enables 3D directional sound cues. Hear where things are coming from!",
        "accepted": ["Off", "On"],
    },
]
