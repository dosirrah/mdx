#!/usr/bin/env python
"""This modules contains tools for preprocessing markdown files. This preprocessor adds
   support for references and labels.   See READE.md in this directory for details."""

import re
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
        First pass: Scan Markdown text for label declarations and assign numbers.
        Updates internal state (label_map, group_counters, global_counter).
        Does not return or modify any lines.
        """
        for markdown_text in markdown_lines:

            # Find all @group:label patterns
            for match in re.finditer(r"@([a-zA-Z0-9_]+):([a-zA-Z0-9_]+)", markdown_text):
                group, label = match.groups()
                label_key = f"{group}:{label}"
                if label_key not in self.label_map:
                    if group not in self.group_counters:
                        self.group_counters[group] = 1
                    self.label_map[label_key] = str(self.group_counters[group])
                    self.group_counters[group] += 1

            # Find all global @label patterns (not part of group:label)
            for match in re.finditer(r"@([a-zA-Z0-9_]+)(?!:[a-zA-Z0-9_])\b", markdown_text):
                label = match.group(1)
                if label not in self.label_map:
                    self.label_map[label] = str(self.global_counter)
                    print(f"global_counter now {self.global_counter} for label {label}")
                    sys.stdout.flush()
                    self.global_counter += 1

    def replace(self, markdown_lines):
        """
        Second pass: Replaces both label declarations (@label, @group:label)
        and references (#label, #group:label) using self.label_map.
        Returns modified lines with numbered references and labels.
        """

        def replace_grouped_label(match):
            group, label = match.groups()
            label_key = f"{group}:{label}"
            label_number = self.label_map.get(label_key, match.group(0))
            return label_number.ljust(len(match.group(0))) if inside_table else label_number

        def replace_global_label(match):
            label = match.group(1)
            label_number = self.label_map.get(label, match.group(0))
            return label_number.ljust(len(match.group(0))) if inside_table else label_number

        def replace_reference(match):
            group, label, global_label = match.groups()

            if group and label:
                ref_key = f"{group}:{label}"
            else:
                ref_key = global_label

            if ref_key in self.label_map:
                replacement = self.label_map[ref_key]
            else:
                print(f"Warning: Undefined reference '{ref_key}' on line {self.line_num}",
                      file=sys.stderr)
                missing_references.append((self.line_num, ref_key))
                return match.group(0)

            return replacement.ljust(len(match.group(0))) if inside_table else replacement

        missing_references = []
        final_lines = []

        for markdown_text in markdown_lines:
            self.line_num += 1

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

            # Replace label declarations
            markdown_text = re.sub(r"@([a-zA-Z0-9_]+):([a-zA-Z0-9_]+)",
                                   replace_grouped_label, markdown_text)
            markdown_text = re.sub(r"@([a-zA-Z0-9_]+)", replace_global_label, markdown_text)

            # Replace references
            markdown_text = re.sub(r"(?<!^)#(\w+):(\w+)|(?<!^)#(\w+)",
                                   replace_reference, markdown_text)

            final_lines.append(markdown_text)

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
        self.collect_labels(markdown_lines)
        return self.replace(markdown_lines)


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

    # First pass: collect label definitions
    processor.collect_labels(markdown_lines)

    # Second pass: replace labels and references
    processed_text = processor.replace(markdown_lines)

    with open(output_file, "w", encoding="utf-8") as file:
        #file.write(f"<!-- Generated by mdxrp from {input_file}. "
        #           "You can obtain mdxrp.py from https://github.com/dosirrah/mdx -->\n")
        file.writelines(processed_text)


def extract_lines(cell):
    """Extract lines from a notebook Markdown cell, handling both formats."""
    if isinstance(cell.get("source"), list):
        return [line.rstrip("\n") for line in cell["source"]]
    return cell["source"].splitlines()

def set_cell_source(cell, processed_lines):
    """Replace cell content with processed Markdown lines, preserving format."""
    if isinstance(cell.get("source"), list):
        cell["source"] = [line + "\n" for line in processed_lines[:-1]] + [processed_lines[-1]]
    else:
        cell["source"] = "\n".join(processed_lines)

def process_notebook(input_file, output_file):
    """
    Reads a Jupyter or Databricks notebook (.ipynb, .source),
    performs a two-pass Markdown transformation:
      1. First pass: collects labels from all Markdown cells.
      2. Second pass: replaces labels and references in Markdown cells.
    Non-Markdown cells are preserved unmodified.
    """

    _, ext = os.path.splitext(input_file)
    ext = ext.lower()
    if ext not in {".ipynb", ".source"}:
        raise ValueError("Error: Input file must be a .ipynb or .source notebook.")

    _, oext = os.path.splitext(output_file)
    oext = oext.lower()
    if ext != oext:
        raise ValueError(f"Error: Output file {output_file} must match input file type: "
                         f"it must have {ext} extension.")

    with open(input_file, "r", encoding="utf-8") as file:
        notebook_json = json.load(file)

    processor = MarkdownProcessor()

    # --- First pass: collect labels from all Markdown cells ---
    for cell in notebook_json.get("cells", []):
        if cell.get("cell_type") == "markdown":
            lines = extract_lines(cell)
            processor.collect_labels(lines)

    # --- Second pass: apply label and reference substitutions ---
    for cell in notebook_json.get("cells", []):
        if cell.get("cell_type") == "markdown":
            lines = extract_lines(cell)
            processed_lines = processor.replace(lines)
            set_cell_source(cell, processed_lines)

    # --- Write updated notebook ---
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(notebook_json, file, indent=2)

    print(f"Processed notebook saved as: {output_file}")
