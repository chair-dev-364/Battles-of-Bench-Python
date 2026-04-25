"""_sound_validator.py — lightweight sound name validation.

Extracted into its own module so it can be imported independently of
sound_player.py (which has aggressive module-level side effects).
"""
import re

_SAFE_SOUND_NAME_RE = re.compile(r'^[A-Za-z0-9_\-]{1,128}$')


def is_safe_sound_name(name: str) -> bool:
    """Return True if *name* is a safe sound identifier.

    Accepts only alphanumeric characters, underscores, and hyphens.
    Rejects anything that could enable path traversal (slashes, dots,
    null bytes, whitespace, etc.).
    """
    return bool(_SAFE_SOUND_NAME_RE.match(name))
