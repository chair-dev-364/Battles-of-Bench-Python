import re


def apply_difficulty(enemy, difficulty):
    strength = (0.75, 1.0, 1.25, 1.25)[difficulty]
    speed = (0.9, 1.0, 1.1, 1.1)[difficulty]
    enemy.difficulty = ("Easy", "Normal", "Hard", "Extreme")[difficulty]
    if difficulty == 1:
        return
    enemy.hp = max(1, round(enemy.hp * strength))
    enemy.attack = round(enemy.attack * strength, 2)
    enemy.speed = round(enemy.speed * speed, 1)


def attack_damage(player, enemy):
    damage = round(max(0, int(player.total_dmg * (100 - enemy.defense) / 100)))
    critical_damage = round(damage * (1 + getattr(player, "crit_damage", 0) / 100))
    return damage, critical_damage


def short_action_log(text):
    text = re.sub(r'\x1b\[[0-9;?]*[A-Za-z]', '', text)
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or set(line) <= {"─", "-"} or line.startswith("→"):
            continue
        line = re.sub(r'✴\s+CRIT!\s+(\d[\d,]*(?:\.\d+)?[kmb]?)\s+DMG', r'Crit: \1 damage', line)
        line = re.sub(r'⚔\s+(\d[\d,]*(?:\.\d+)?[kmb]?)\s+DMG RCV', r'Enemy hit: \1 damage', line)
        line = re.sub(r'⚔\s+(\d[\d,]*(?:\.\d+)?[kmb]?)\s+DMG', r'Hit: \1 damage', line)
        line = re.sub(r'🩸 Life steal: (\d[\d,]*(?:\.\d+)?[kmb]?) HP stolen!', r'Heal: \1 HP', line)
        line = re.sub(r'💧\s+Regenerated (\d[\d,]*(?:\.\d+)?[kmb]?) HP', r'Regen: \1 HP', line)
        line = line.replace("are not available yet.", "unavailable.")
        lines.append(line)
    return lines[-4:]
