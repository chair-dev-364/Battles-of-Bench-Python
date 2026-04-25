import os
import shutil
import sys

# Define the working directory
folder = os.path.join(os.getcwd(), "Items", "Weapons")

# Get the sorting method from command-line arguments
if len(sys.argv) != 2 or sys.argv[1] not in ("1", "2", "3", "4", "5", "6"):
    print("Usage: sort.py [1-6]")
    print("1: Ascending by ilevel (token 4)")
    print("2: Descending by ilevel (token 4)")
    print("3: Alphabetical A-Z by name (token 3)")
    print("4: Alphabetical Z-A by name (token 3)")
    print("5: Custom order by token 2 (0e, 0d, 03, 02, 08)")
    print("6: Reverse custom order by token 2 (08, 02, 03, 0d, 0e)")
    sys.exit(1)

sort_mode = int(sys.argv[1])

# Get all item*.txt files
files = [f for f in os.listdir(folder) if f.startswith("item") and f.endswith(".txt")]

# Dictionary to store file names and sorting values
file_data = {}

# Custom order for token 2 sorting
custom_order = ["0e", "0d", "03", "02", "08"]

# Read relevant tokens from each file
for file in files:
    file_path = os.path.join(folder, file)
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(";;")
            if len(parts) >= 4:
                token2 = parts[1] if len(parts) > 1 else ""  # Token 2
                token3 = parts[2] if len(parts) > 2 else ""  # Token 3 (name)
                try:
                    token4 = int(parts[3])  # ilevel (token 4)
                except ValueError:
                    token4 = float('inf')  # If no valid number, put it at the end

                # Store relevant data
                file_data[file] = (token2, token3, token4)
                break  # Only need the first valid line

# Sorting logic based on mode
if sort_mode == 1:  # Ascending by ilevel
    sorted_files = sorted(file_data.items(), key=lambda x: x[1][2])
elif sort_mode == 2:  # Descending by ilevel
    sorted_files = sorted(file_data.items(), key=lambda x: x[1][2], reverse=True)
elif sort_mode == 3:  # Alphabetical A-Z by token 3 (name)
    sorted_files = sorted(file_data.items(), key=lambda x: x[1][1])
elif sort_mode == 4:  # Alphabetical Z-A by token 3 (name)
    sorted_files = sorted(file_data.items(), key=lambda x: x[1][1], reverse=True)
elif sort_mode == 5:  # Custom order for token 2
    sorted_files = sorted(file_data.items(), key=lambda x: custom_order.index(x[1][0]) if x[1][0] in custom_order else len(custom_order))
elif sort_mode == 6:  # Reverse custom order for token 2
    sorted_files = sorted(file_data.items(), key=lambda x: custom_order.index(x[1][0]) if x[1][0] in custom_order else len(custom_order), reverse=True)

# Rename files sequentially based on sorted order
temp_folder = os.path.join(folder, "temp_sort")
os.makedirs(temp_folder, exist_ok=True)

for i, (old_name, _) in enumerate(sorted_files, start=1):
    new_name = f"item{i}.txt"
    shutil.move(os.path.join(folder, old_name), os.path.join(temp_folder, new_name))

# Move sorted files back
for file in os.listdir(temp_folder):
    shutil.move(os.path.join(temp_folder, file), folder)

os.rmdir(temp_folder)  # Clean up temp folder

