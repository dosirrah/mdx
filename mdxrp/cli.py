"""Command-line module for mdxrp"""

# mdxrp/cli.py

import argparse
import os
import sys
from .processor import process_mdx_file, process_notebook
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("mdxrp")
except PackageNotFoundError:
    __version__ = "unknown"


### **Main CLI Handler**
def main():
    """Handles command-line arguments and runs the reference preprocessor."""
    parser = argparse.ArgumentParser(description="Process Markdown references and numbering.")
    parser.add_argument("input_file", help="Path to the input file (.mdx, .ipynb, .source).")
    parser.add_argument("output_file", nargs="?", default="",
                        help="Path to the output file (.md, .ipynb, .source).")

    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
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
