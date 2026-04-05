import sys

def get_digit_art(digit):
    """Returns the 5-line ASCII art for a single digit (0-9)"""
    art = {
        '0': [
            "  ████  ",
            "██    ██",
            "██    ██",
            "██    ██",
            "  ████  "
        ],
        '1': [
            "    ██  ",
            "  ████  ",
            "██  ██  ",
            "    ██  ",
            "  ██████"
        ],
        '2': [
            "  ████  ",
            "██    ██",
            "    ██  ",
            "  ██    ",
            "████████"
        ],
        '3': [
            "  ████  ",
            "██    ██",
            "   ███  ",
            "██    ██",
            "  ████  "
        ],
        '4': [
            "██    ██",
            "██    ██",
            "████████",
            "      ██",
            "      ██"
        ],
        '5': [
            "████████",
            "██      ",
            "██████  ",
            "      ██",
            "██████  "
        ],
        '6': [
            "  █████ ",
            "██      ",
            "██████  ",
            "██    ██",
            "  ████  "
        ],
        '7': [
            "████████",
            "      ██",
            "    ██  ",
            "  ██    ",
            "  ██    "
        ],
        '8': [
            "  ████  ",
            "██    ██",
            "  ████  ",
            "██    ██",
            "  ████  "
        ],
        '9': [
            "  ████  ",
            "██    ██",
            "  ██████",
            "      ██",
            " █████  "
        ]
    }
    return art.get(digit, ["        "] * 5)

def bignumber(number_str, display=False):
    """
    Convert a number (1-3 digits) to ASCII art.
    
    Args:
        number_str: String containing 1-3 digits
        display: If True, print the ASCII art
        
    Returns:
        String with ASCII art (newlines included), or None if invalid input
    """
    # Validate input
    if not number_str.isdigit() or len(number_str) < 1 or len(number_str) > 3:
        return None
    
    # Get ASCII art for each digit
    digit_arts = [get_digit_art(digit) for digit in number_str]
    
    # Combine horizontally (join each line with a space)
    result_lines = []
    for line_idx in range(5):
        line_parts = [art[line_idx] for art in digit_arts]
        result_lines.append(" ".join(line_parts))
    
    result = "\n".join(result_lines)
    
    if display:
        print(result)
    
    return result

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python bignumber.py <number> [/d]")
        sys.exit(1)
    
    number = sys.argv[1]
    display_flag = len(sys.argv) > 2 and sys.argv[2].lower() == '/d'
    
    result = bignumber(number, display_flag)
    sys.exit(0 if result is not None else 1)
