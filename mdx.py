#!/usr/bin/env python

import re
import argparse
import os
import sys

class UndefinedReferenceError(KeyError):
    """Custom exception for undefined references in the Markdown file."""
    pass

class MarkdownProcessor:
    """
    Processes numbered references in Markdown text.
    Supports a two-pass system: (1) Collect and enumerate labels, (2) Replace references.
    """

    def __init__(self):
        """Initialize state for tracking labels and references."""
        self.reset()

    def reset(self):
        """Resets the processor state, allowing reuse for a new document."""
        self.label_map = {}  # Maps labels to assigned numbers
        self.group_counters = {}  # Stores counters for named groups
        self.global_counter = 1  # Counter for ungrouped labels
        self.line_num = 0

    def collect_labels(self, markdown_lines):
        """
        First pass: Assign numbers to labels in a Markdown text.
        Updates internal state but does not modify the text.
        """
        def replace_named_label(match):
            group, label = match.groups()
            label_key = f"{group}:{label}"
    
            if label_key not in self.label_map:
                if group not in self.group_counters:
                    self.group_counters[group] = 1
                self.label_map[label_key] = str(self.group_counters[group])
                self.group_counters[group] += 1
    
            label_number = self.label_map[label_key]
            return label_number.ljust(len(match.group(0))) if inside_table else label_number


        def replace_global_label(match):
            
            label = match.group(1)

            if label not in self.label_map:
                self.label_map[label] = str(self.global_counter)
                self.global_counter += 1
    
            label_number = self.label_map[label]

            return label_number.ljust(len(match.group(0))) if inside_table else label_number

        labelled_lines = []
        
        # Apply label collection but do not replace anything yet
        for markdown_text in markdown_lines:
            # self.line_num +=1   # only inc line numbers in second pass, iee., replace_references

            # Detect if we're inside a table row (line starts and ends
            # with | and contains non-whitespace characters)
            inside_table = re.match(r"^\s*\|.*\S.*\|\s*$", markdown_text) is not None

            markdown_text = re.sub(r"@([a-zA-Z0-9_]+):([a-zA-Z0-9_]+)",
                                   replace_named_label, markdown_text)
            markdown_text = re.sub(r"@([a-zA-Z0-9_]+)", replace_global_label, markdown_text)
            labelled_lines.append(markdown_text)

        return labelled_lines

    def replace_references(self, markdown_lines):
        """
        Second pass: Replace #references with assigned numbers.
        Returns modified Markdown text.
        """

        def replace_reference(match):
            group, label, global_label = match.groups()
            
            # Determine the correct reference key (named or global)
            if group and label:
                ref_key = f"{group}:{label}"
            else:
                ref_key = global_label
    
            # Check if reference exists
            if ref_key in self.label_map:
                replacement = self.label_map[ref_key]
            else:
                print(f"Warning: Undefined reference '{ref_key}' on line {self.line_num}", file=sys.stderr)
                missing_references.append((self.line_num, ref_key))
                return match.group(0)  # Keep the original reference if it's undefined
    
            # Preserve alignment in tables
            if inside_table:
                return replacement.ljust(len(match.group(0)))
            return replacement

        missing_references = []
        final_lines = []

        # Apply label collection but do not replace anything yet
        for markdown_text in markdown_lines:
            self.line_num +=1

            # Detect if we're inside a table row (line starts and ends
            # with | and contains non-whitespace characters)
            inside_table = re.match(r"^\s*\|.*\S.*\|\s*$", markdown_text) is not None

            re.sub(r"(?<!^)#(\w+):(\w+)|(?<!^)#(\w+)", replace_reference, markdown_text)

            # Replace all references in the line
            line = re.sub(r"(?<!^)#(\w+):(\w+)|(?<!^)#(\w+)", replace_reference, markdown_text)
    
            final_lines.append(line)

        # If there are undefined references, raise a custom exception at the end
        if missing_references:
            error_message = f"\nSummary: {len(missing_references)} undefined references found!\n"
            for line_num, label in missing_references:
                error_message += f"  - Undefined reference '{label}' on line {line_num}\n"
            raise UndefinedReferenceError(error_message)

        return final_lines
            
    def process_markdown(self, markdown_lines):
        """
        Processes a Markdown document in two passes.
        Returns processed text with assigned numbers and replaced references.
        """
        self.reset()
        labelled_lines = self.collect_labels(markdown_lines)
        return self.replace_references(labelled_lines)

def process_mdx_file(input_file):
    """
    Reads a .mdx file, applies MarkdownProcessor, and writes the processed .md file.
    """
    base_name, ext = os.path.splitext(input_file)
    if ext.lower() != ".mdx":
        raise ValueError("Error: Input file must have a .mdx extension.")

    output_file = f"{base_name}.md"

    with open(input_file, "r", encoding="utf-8") as file:
        markdown_lines = file.readlines()
    
    #with open(input_file, "r", encoding="utf-8") as file:
    #    markdown_text = file.read()

    processor = MarkdownProcessor()
    processed_text = processor.process_markdown(markdown_lines)

    with open(output_file, "w", encoding="utf-8") as file:
        file.write(f"<!-- Generated by mdx.py from {input_file}. You can obtain mdx.py from https://github.com/dosirrah/mdx -->\n")
        file.writelines(processed_text)

    print(f"Processed file saved as: {output_file}")

def main():
    """Handles command-line arguments and runs the reference processor."""
    parser = argparse.ArgumentParser(description="Process .mdx Markdown references and numbering.")
    parser.add_argument("input_file", help="Path to the .mdx file.")

    args = parser.parse_args()

    try:
        process_mdx_file(args.input_file)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except UndefinedReferenceError as e:
        print(f"Reference Error:\n{e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
