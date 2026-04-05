import os
import sys

# Check if argument is provided
if len(sys.argv) < 2:
    sys.exit(1)

currsel = sys.argv[1]
file_path = os.path.join(os.getcwd(), "Items", "Weapons", f"item{currsel}.txt")

try:
    with open(file_path, "r", encoding="utf-8") as file:
        line = file.readline().strip()
except FileNotFoundError:
    sys.exit(1)

tokens = line.split(";;")

# Ensure the list has at least 12 tokens
while len(tokens) < 12:
    tokens.append("")

# Handle the 11th token (index 10)
if tokens[10].strip() == "":
    tokens[10] = "No ability."

# Handle the 12th token (index 11)
if tokens[11].strip() == "":
    tokens[11] = "1"
else:
    if tokens[11] == "0":
        tokens[11] = "1"
    elif tokens[11] == "1":
        tokens[11] = "0"
    else:
        sys.exit(1)  # Silent fail if unexpected value

new_line = ";;".join(tokens)

with open(file_path, "w", encoding="utf-8") as file:
    file.write(new_line)
