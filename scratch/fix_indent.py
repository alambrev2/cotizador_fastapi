import re

with open(r"c:\Users\HP\OneDrive\sin título\cotizador\app\api\v1\endpoints\customers.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "row_number = index + 2" in line:
        start_idx = i + 1
    elif "except ValueError as ve:" in line and start_idx != -1:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx]
    new_lines.append("                try:\n")
    for i in range(start_idx, end_idx):
        if lines[i].strip() == "":
            new_lines.append("\n")
        else:
            new_lines.append("    " + lines[i])
    new_lines.extend(lines[end_idx:])
    
    with open(r"c:\Users\HP\OneDrive\sin título\cotizador\app\api\v1\endpoints\customers.py", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("File updated successfully.")
else:
    print(f"Indices not found: start_idx={start_idx}, end_idx={end_idx}")
