#!/usr/bin/env python

# This can exists in the repositor at  
#
#  https://github.com/dosirrah/mdx
#

import re
import argparse
import os

def process_references(input_file):
    """
    Parses a .mdx Markdown file with @label definitions and #label references.
    Preserves spacing for markdown tables and fixed-width text.
    Outputs a clean .md file.
    """
    base_name, ext = os.path.splitext(input_file)
    if ext.lower() != ".mdx":
        raise ValueError("Error: Input file must have a .mdx extension.")

    output_file = f"{base_name}.md"

    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    label_map = {}  # Stores {label: number}
    group_counters = {}  # Stores counters for named groups
    global_counter = 1  # Default global numbering

    updated_lines = []

    # Step 1: Assign numbers to labeled elements
    for line in lines:
        match = re.search(r"@(\w+):(\w+)", line)  # Detects @group:label
        global_match = re.search(r"@(\w+)", line)  # Detects @label (global)

        if match:
            group, label = match.groups()
            if group not in group_counters:
                group_counters[group] = 1
            label_key = f"{group}:{label}"
            label_map[label_key] = group_counters[group]
            label_width = len(f"@{group}:{label}")  # Measure label length
            line = line.replace(f"@{group}:{label}", str(group_counters[group]))
            group_counters[group] += 1
        
        elif global_match:
            label = global_match.group(1)
            label_map[label] = global_counter
            label_width = len(f"@{label}")  # Measure label length
            line = line.replace(f"@{label}", str(global_counter))
            global_counter += 1

        updated_lines.append(line)

    # Step 2: Replace references and preserve table alignment
    final_lines = []
    inside_table = False  # Track if we are inside a Markdown table

    for line in updated_lines:
        if "|" in line:  # Detect potential table row
            inside_table = True
        else:
            inside_table = False

        if inside_table:
            # Find all references in the table row
            matches = re.findall(r"(?<!^)#(\w+):(\w+)|(?<!^)#(\w+)", line)
            for match in matches:
                group_label = f"{match[0]}:{match[1]}" if match[0] else None
                global_label = match[2] if match[2] else None
                
                if group_label and group_label in label_map:
                    original_length = len(f"#{group_label}")
                    replacement = str(label_map[group_label]).ljust(original_length)
                    line = line.replace(f"#{group_label}", replacement)
                
                elif global_label and global_label in label_map:
                    original_length = len(f"#{global_label}")
                    replacement = str(label_map[global_label]).ljust(original_length)
                    line = line.replace(f"#{global_label}", replacement)
        
        final_lines.append(line)

    # Write processed content to new .md file
    with open(output_file, "w", encoding="utf-8") as file:
        file.writelines(final_lines)

    print(f"Processed file saved as: {output_file}")

# Command-line argument handling
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process .mdx Markdown references and numbering.")
    parser.add_argument("input_file", help="Path to the .mdx file.")

    args = parser.parse_args()
    process_references(args.input_file)

