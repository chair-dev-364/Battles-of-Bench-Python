"""Keyboard-driven edit state for the settings screen.

The renderer owns layout, the data objects own persistence, and this module
owns only the short-lived state of an edit (focused value, save, or cancel).
"""

RESERVED_KEYBINDS = {"esc", "up", "down", "left", "right"}


def setting_index_at(x, y, count, col, row, width, height):
    """Return the zero-based setting box under a zero-based mouse position."""
    col_start = col - 1
    col_end = col + width
    if not col_start <= x <= col_end:
        return None

    for index in range(count):
        box_top = row - 1 + index * height
        box_bottom = box_top + height - 1
        if box_top <= y <= box_bottom:
            return index
    return None


def category_index_at(x, y, count=6):
    """Return the category button under a zero-based mouse position."""
    col_start = 2
    col_end = col_start + 19
    if not col_start <= x <= col_end:
        return None

    for index in range(count):
        button_top = 7 + index * 4
        button_bottom = button_top + 2
        if button_top <= y <= button_bottom:
            return index
    return None


def back_button_contains(x, y):
    """Return whether a zero-based mouse position is over Back to house."""
    return 2 <= x <= 21 and 31 <= y <= 34


def volume_slider_parts(item, value):
    """Return the track segments and label for a fixed-width volume slider."""
    minimum = item.get("min", 0)
    maximum = item.get("max", 10)
    span = max(1, maximum - minimum)
    position = round((value - minimum) * 10 / span)
    position = max(0, min(10, position))
    label = "Off" if value <= minimum else f"{round((value - minimum) * 100 / span)}%"
    return "─" * position, "●", "─" * (10 - position), label


def boolean_slider_parts(value):
    """Return a compact three-position-looking toggle for a boolean value."""
    if value:
        return "──", "●", "", "On"
    return "", "●", "──", "Off"


def setting_is_off(item, value):
    """Return whether a setting value represents its disabled/off state."""
    if item["type"] == "bool":
        return not value
    if item.get("display") == "volume":
        return value <= item.get("min", 0)
    return False


def volume_value_at_mouse(x, item, col, box_width, clamp=False):
    """Map a zero-based mouse column onto the rendered volume track."""
    display_width = 16
    track_start = col + box_width - display_width - 1
    track_end = track_start + 10
    if not clamp and not track_start <= x <= track_end:
        return None

    position = max(0, min(10, x - track_start))
    minimum = item.get("min", 0)
    maximum = item.get("max", 10)
    raw_value = minimum + (maximum - minimum) * position / 10
    step = item.get("step", 1)
    stepped = round((raw_value - minimum) / step) * step + minimum
    stepped = max(minimum, min(maximum, stepped))
    if isinstance(step, int) and isinstance(stepped, float) and stepped.is_integer():
        return int(stepped)
    return stepped


def boolean_control_contains(x, col, box_width):
    """Return whether a zero-based column is over the tiny boolean control."""
    display_width = 7
    control_start = col + box_width - display_width - 1
    return control_start <= x < control_start + display_width


def format_setting_value(item, value):
    """Return a compact display value for one declarative setting."""
    if item.get("disabled"):
        return "Coming soon"
    if item["type"] == "bool":
        return "On" if value else "Off"
    if item["type"] == "keybind":
        return str(value).capitalize()
    if item.get("display") == "volume":
        return volume_slider_parts(item, value)[3]
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


class SettingEditor:
    def __init__(self):
        self.active = False
        self.item = None
        self.owner = None
        self.value = None
        self.original_value = None
        self.message = ""

    def clear(self):
        self.active = False
        self.item = None
        self.owner = None
        self.value = None
        self.original_value = None
        self.message = ""

    def begin(self, item, owner):
        if item.get("disabled"):
            self.message = "This option is not implemented yet."
            return "disabled"

        self.active = True
        self.item = item
        self.owner = owner
        self.value = getattr(owner, item["attr"])
        self.original_value = self.value
        if item["type"] == "keybind":
            self.message = "Press a new key. Escape cancels."
        elif item["type"] == "bool":
            self.message = "Press Enter to toggle. Escape cancels."
        elif item["type"] == "choice":
            self.message = "Use left/right, then Enter to save or Escape to cancel."
        else:
            self.message = "Use left/right, then Enter to save or Escape to cancel."
        return "focused"

    def cancel(self):
        if not self.active:
            return "ignored"
        self.active = False
        self.message = "Changes discarded."
        return "cancelled"

    def commit(self):
        setattr(self.owner, self.item["attr"], self.value)
        self.owner.save()
        self.active = False
        self.message = ""
        return "saved"

    def _keybind_conflict(self, candidate):
        current_attr = self.item["attr"]
        fields = getattr(
            self.owner,
            "_keybind_fields",
            getattr(self.owner, "_persistent_fields", {}),
        )
        for attr in fields:
            if attr == current_attr:
                continue
            existing = str(getattr(self.owner, attr, "")).lower()
            if existing == candidate:
                return attr
        return None

    def handle_key(self, pressed):
        """Apply one key event and return a small UI action string."""
        if not self.active or not isinstance(pressed, str):
            return "ignored"

        key_name = pressed.lower()
        setting_type = self.item["type"]

        # key(mouse=True) can return this sentinel after consuming a mouse-only
        # console event. It is not a key the player attempted to bind.
        if key_name == "timeout":
            return "ignored"

        if setting_type == "keybind":
            if key_name == "esc":
                return self.cancel()
            if key_name in RESERVED_KEYBINDS or key_name.startswith("ctrl/"):
                self.message = f"{pressed!r} is reserved; press another key."
                return "error"
            conflict = self._keybind_conflict(key_name)
            if conflict:
                self.message = f"That key is already assigned to {conflict}."
                return "error"
            self.value = key_name
            return self.commit()

        if key_name == "esc":
            return self.cancel()

        if setting_type == "bool":
            if key_name not in ("enter", "space"):
                return "ignored"
            self.value = not self.value
            return self.commit()

        if key_name == "enter":
            return self.commit()

        if setting_type == "choice":
            choices = self.item.get("choices", [])
            if not choices:
                self.message = "This setting has no available choices."
                return "error"

            direction = 0
            if key_name in ("left", "a"):
                direction = -1
            elif key_name in ("right", "d"):
                direction = 1
            if not direction:
                return "ignored"

            try:
                current_index = choices.index(self.value)
            except ValueError:
                current_index = 0
            new_index = max(0, min(len(choices) - 1, current_index + direction))
            if new_index == current_index:
                return "ignored"
            self.value = choices[new_index]
            self.message = "Press Enter to save or Escape to cancel."
            return "changed"

        if setting_type == "slider":
            direction = 0
            if key_name in ("left", "a"):
                direction = -1
            elif key_name in ("right", "d"):
                direction = 1
            if not direction:
                return "ignored"

            step = self.item.get("step", 1)
            minimum = self.item.get("min", self.value)
            maximum = self.item.get("max", self.value)
            new_value = max(
                minimum,
                min(maximum, self.value + direction * step),
            )
            if isinstance(step, float):
                decimals = max(0, len(str(step).partition(".")[2]))
                new_value = round(new_value, decimals)
            self.value = new_value
            self.message = "Press Enter to save or Escape to cancel."
            return "changed"

        self.message = f"Unsupported setting type: {setting_type}."
        return "error"
