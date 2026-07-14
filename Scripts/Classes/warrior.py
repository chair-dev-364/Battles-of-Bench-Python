"""-------------------------------------------------------------------------
DAMAGE - how often do you go to the gym? (from level 1 to 10)
-------------------------------------------------------------------------"""

main_damage = [
    100, 105, 110, 115, 120,
    130, 140, 150, 160, 170
]

skill_damage = [
    150, 160, 170, 180, 190,
    200, 215, 230, 255, 270
]

ult_damage = [
    15, 18, 21, 24, 27,
    30, 32, 34, 36, 40
]

"""-------------------------------------------------------------------------
SKILL UNLOCKS - can I even use this? Let's find out! (unlocked at level 3, 6, and 8)
-------------------------------------------------------------------------"""

double_tap = [
    False,
    False,
    True, # unlocked at level 3
    True,
    True, 
    True,
    True,
    True,
    True,
    True,
]

stronger_skill = [
    False,
    False,
    False,
    False,
    False,
    True, # unlocked at level 6
    True,
    True,
    True,
    True
]

stronger_ult = [
    False,
    False,
    False,
    False,
    False,
    False,
    False,
    True, # unlocked at level 8
    True,
    True
]

"""-------------------------------------------------------------------------
ATTACK COSTS - how much AV are you willing to spend?
-------------------------------------------------------------------------"""

main_cost = [ # in AV
    100, 100, 100, 100, 100,
    99, 98, 97, 96, 95
]

skill_cost = [
    125, 125, 125, 125, 125,
    124, 123, 122, 121, 120
]

ult_cost = [
    150, 150, 150, 150, 150,
    148, 146, 144, 142, 140
]

double_tap_cost = [ 
    180, 180, 180, 180, 180,
    175, 170, 165, 160, 155
]

"""-------------------------------------------------------------------------
SUBSKILL VALUES - how strong do you like your subskills? ;)
-------------------------------------------------------------------------"""

double_tap_crit = [ # subskill 1
    5, 6, 7, 8, 9,
    10, 11, 12, 13, 15
]

skill_atk_decrease = [ # subskill 2
    5, 7, 8, 9, 10,
    11, 12, 13, 14, 15
]

ult_crit_percent = [ # subskill 3
    20, 22, 24, 26, 28,
    29, 30, 31, 32, 33
]