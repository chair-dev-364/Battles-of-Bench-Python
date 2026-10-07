"""Save recovery preferences."""

SETTINGS = [{'name': 'Backup count',
  'attr': 'backup_count',
  'type': 'slider',
  'display': 'number',
  'min': 0,
  'max': 10,
  'step': 1,
  'default': 3,
  'description': 'Battles of Bench backs up your most important data automatically. How many recent automatic backups do you want to keep?',
  'suffix': '',
  'accepted': '0-10'}]


SETTINGS += [
    {
        "name": "Back up now",
        "attr": "manual_backup",
        "type": "action",
        "default": "",
        "persistent": False,
        "description": "If you don't trust autosave, create a manual backup here. This will NEVER get deleted automatically.",
        "accepted": ["Enter", "Click"],
    },
    {
        "name": "Reset all settings",
        "attr": "reset_settings",
        "type": "action",
        "default": "",
        "persistent": False,
        "description": "Like to live life dangerously? Select this to trash every change you ever made to your settings.",
        "accepted": ["Enter", "Click"],
    },
]
