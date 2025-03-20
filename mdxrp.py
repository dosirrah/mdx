#!/usr/bin/env python
"""This modules contains tools for preprocessing markdown files. This preprocessor adds
   support for references and labels.   See READE.md in this directory for details."""

import re
import argparse
import os
import json
import sys

class UndefinedReferenceError(KeyError):
    """Custom exception for undefined references in the Markdown file."""

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
            #
            # |--------|--------------------------------------|
            # |   ^    |  start of line                       |
            # |  \s*   |  zero-or-more whitespaces.           |
            # |   |    |  literal pipe                        |
            # |  .*    |  any characters (including spaces)   |
            # |  \S    |  at least one whitespace.            |
            # |   $    |  end of line                         |
            # |--------|--------------------------------------|
            inside_table = re.match(r"^\s*\|.*\S.*\|\s*$", markdown_text) is not None
            #print("1 !@#!@# collect_labels inside_table %s" % inside_table)

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
                print(f"Warning: Undefined reference '{ref_key}' on line {self.line_num}",
                      file=sys.stderr)
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
            #print("1 !@#!@# replace_references inside_table %s" % inside_table)

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
        #self.reset()
        labelled_lines = self.collect_labels(markdown_lines)
        return self.replace_references(labelled_lines)

def process_mdx_file(input_file, output_file):
    """
    Reads a .mdx file, applies MarkdownProcessor, and writes the processed .md file.
    """
    _, ext = os.path.splitext(input_file)
    if ext.lower() != ".mdx":
        raise ValueError("Error: Input file must have a .mdx extension.")

    _, ext = os.path.splitext(output_file)
    if ext.lower() != ".md":
        raise ValueError("Error: Output file must have a .md extension.")

    with open(input_file, "r", encoding="utf-8") as file:
        markdown_lines = file.readlines()

    processor = MarkdownProcessor()
    processed_text = processor.process_markdown(markdown_lines)

    with open(output_file, "w", encoding="utf-8") as file:
        file.write(f"<!-- Generated by mdxrp from {input_file}. "
                   "You can obtain mdxrp.py from https://github.com/dosirrah/mdx -->\n")
        file.writelines(processed_text)


# HEREPOOP.  This function processes each cell independently rather than first
# performing a full pass across all cells to find and replace labels and then performing
# a full path on the cells to find and replace references.
#
# This needs to be fixed.
def process_notebook(input_file, output_file):
    """
    Reads a Jupyter or Databricks notebook (`.ipynb`, `.source`),
    processes Markdown cells, and writes the modified notebook.
    """
    _, ext = os.path.splitext(input_file)
    ext = ext.lower()
    if ext not in {".ipynb", ".source"}:
        raise ValueError("Error: Input file must be a .ipynb or .source notebook.")

    _, oext = os.path.splitext(output_file)
    oext = oext.lower()
    if ext != oext:
        raise ValueError(f"Error: Output file {output_file} must match input file type:"
                         f"it must have {ext} file extension.")

    with open(input_file, "r", encoding="utf-8") as file:
        notebook_json = json.load(file)

    processor = MarkdownProcessor()

    # Process each cell in place
    for cell in notebook_json.get("cells", []):
        if cell.get("cell_type") == "markdown":
            if isinstance(cell["source"], list):
                # Jupyter format: list of strings
                lines = [line.rstrip("\n") for line in cell["source"]]
                processed_lines = processor.process_markdown(lines)
                cell["source"] = \
                    [line + "\n" for line in processed_lines[:-1]] + [processed_lines[-1]]
            else:
                # Databricks format: single string
                lines = cell["source"].splitlines()
                processed_lines = processor.process_markdown(lines)
                cell["source"] = "\n".join(processed_lines)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(notebook_json, file, indent=2)

    print(f"Processed notebook saved as: {output_file}")

### **Main CLI Handler**
def main():
    """Handles command-line arguments and runs the reference preprocessor."""
    parser = argparse.ArgumentParser(description="Process Markdown references and numbering.")
    parser.add_argument("input_file", help="Path to the input file (.mdx, .ipynb, .source).")
    parser.add_argument("output_file", nargs="?", default="",
                        help="Path to the output file (.md, .ipynb, .source).")

    args = parser.parse_args()

    base_name, ext = os.path.splitext(args.input_file)

    try:
        output_file = args.output_file
        if args.input_file.endswith(".mdx"):
            output_file = f"{base_name}.md" if not output_file else output_file
            process_mdx_file(args.input_file, output_file)
        elif args.input_file.endswith((".ipynb", ".source")):
            output_file = f"{base_name}_processed{ext}" if not output_file else output_file
            process_notebook(args.input_file, output_file)
        else:
            raise ValueError("Unsupported file format. Use .mdx, .ipynb, or .source.")
        print(f"Processed file saved as: {output_file}")

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
