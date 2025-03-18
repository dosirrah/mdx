import pytest
import json
import tempfile
import os
from mdx import process_notebook, MarkdownProcessor


# format of a jupyter notebook.
#
# {
#   "cells": [
#     {
#       "cell_type": "markdown",
#       "source": ["This is a Markdown cell.\n", "It has multiple lines."]
#     },
#     {
#       "cell_type": "code",
#       "execution_count": 1,
#       "source": ["print('Hello, World!')\n"],
#       "outputs": [],
#       "metadata": {}
#     }
#   ],
#   "metadata": {
#     "kernelspec": {
#       "display_name": "Python 3",
#       "language": "python",
#       "name": "python3"
#     }
#   },
#   "nbformat": 4,
#   "nbformat_minor": 2
# }


@pytest.fixture
def temp_notebook_file():
    """Creates a temporary Jupyter notebook file and returns its path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ipynb") as temp_file:
        return temp_file.name

def normalize_cell(cell, notebook_type):
    """Normalize a Markdown cell for Jupyter (`.ipynb`) or Databricks (`.source`)."""
    if isinstance(cell, list):
        lines = cell  # Already a list of lines
    elif isinstance(cell, str):
        lines = cell.splitlines()  # Convert single string to list of lines
    else:
        raise ValueError("Each Markdown cell must be either a string or a list of strings.")

    if notebook_type == "ipynb":
        # Jupyter format: List of strings, each ending with '\n' except last
        return [line.rstrip("\n") + "\n" for line in lines[:-1]] + [lines[-1].rstrip("\n")] if lines else []
    
    elif notebook_type == "source":
        # Databricks format: Single string with embedded newlines
        return "\n".join(line.rstrip("\n") for line in lines)
    
    else:
        raise ValueError("Invalid notebook type. Must be 'ipynb' or 'source'.")

def write_test_notebook(file_path, markdown_cells):
    """Helper function to write a properly formatted Jupyter (`.ipynb`) or
       Databricks (`.source`) notebook.
    """
    assert isinstance(markdown_cells, list), "markdown_cells must be a list of Markdown content."

    # Determine the notebook type based on file extension
    ext = os.path.splitext(file_path)[1].lower()
    notebook_type = "ipynb" if ext == ".ipynb" else "source" if ext == ".source" else None
    if not notebook_type:
        raise ValueError("File extension must be '.ipynb' or '.source'.")

    # Normalize each Markdown cell
    normalized_cells = [{"cell_type": "markdown", "source": normalize_cell(cell, notebook_type)}
                        for cell in markdown_cells]

    notebook_data = {
        "cells": normalized_cells,
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 2
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(notebook_data, f, indent=2)

    print(f"Test notebook saved as: {file_path}")


def read_processed_notebook(file_path):
    """Helper function to read processed notebook Markdown cells and normalize them to Jupyter format."""
    with open(file_path, "r", encoding="utf-8") as f:
        notebook_data = json.load(f)

    # Determine notebook type based on file extension
    ext = os.path.splitext(file_path)[1].lower()
    notebook_type = "ipynb" if ext == ".ipynb" else "source" if ext == ".source" else None

    if not notebook_type:
        raise ValueError("File extension must be '.ipynb' or '.source'.")

    markdown_cells = []

    for cell in notebook_data.get("cells", []):
        if cell.get("cell_type") == "markdown":
            source = cell.get("source")

            if notebook_type == "ipynb":
                # Validate: Jupyter should store source as a list of strings
                if not isinstance(source, list) or not all(isinstance(line, str) for line in source):
                    raise ValueError(f"Invalid format in {file_path}: Expected list of strings for Jupyter (.ipynb)")

                # Ensure proper newline formatting (each line except last should have '\n')
                normalized = [line.rstrip("\n") + "\n" for line in source[:-1]] + [source[-1].rstrip("\n")]
                markdown_cells.append(normalized)

            elif notebook_type == "source":
                # Validate: Databricks should store source as a single string
                if not isinstance(source, str):
                    raise ValueError(f"Invalid format in {file_path}: Expected a single string for Databricks (.source)")

                # Convert to Jupyter format: split into a list of strings with correct newline endings
                lines = source.splitlines()
                normalized = [line + "\n" for line in lines[:-1]] + [lines[-1]] if lines else []
                markdown_cells.append(normalized)

    return markdown_cells

### **Unit Tests for Processing Jupyter Notebooks**
@pytest.mark.parametrize("file_extension", [".ipynb", ".source"])
def test_basic_label_resolution(temp_notebook_file, file_extension):
    """Test that labels are correctly assigned and referenced in a notebook."""
    print(f"1 test_basic_label_reslution: file_extension={file_extension}")
    temp_file = temp_notebook_file.replace(".ipynb", file_extension)  # Adjust filename for test type
    processed_file = temp_file.replace(file_extension, f"_processed{file_extension}")

    markdown_cells = ["This is problem @prob:one.\nSee #prob:one for reference."]

    print(f"2 test_basic_label_reslution: temp_notebook_file={temp_file}")
    write_test_notebook(temp_file, markdown_cells)
    process_notebook(temp_file, processed_file)

    processed_cells = read_processed_notebook(processed_file)

    expected_output = [["This is problem 1.\n", "See 1 for reference."]]
    
    assert processed_cells == expected_output

@pytest.mark.parametrize("file_extension", [".ipynb", ".source"])
def test_global_enumeration(temp_notebook_file, file_extension):
    """Test global enumeration when no named enumeration is used in a notebook."""

    temp_file = temp_notebook_file.replace(".ipynb", file_extension)  # Adjust filename for test type
    processed_file = temp_file.replace(file_extension, f"_processed{file_extension}")

    markdown_cells = ["First label: @alpha\nAnother reference: #alpha"]
    
    write_test_notebook(temp_file, markdown_cells)
    process_notebook(temp_file, processed_file)

    processed_cells = read_processed_notebook(processed_file)

    expected_output = [["First label: 1\n", "Another reference: 1"]]
    
    assert processed_cells == expected_output

@pytest.mark.parametrize("file_extension", [".ipynb", ".source"])
def test_named_enumeration(temp_notebook_file, file_extension):
    """Test that separate enumerations are assigned different sequences in a notebook."""
    temp_notebook_file = temp_notebook_file.replace(".ipynb", file_extension)  
    processed_file = temp_notebook_file.replace(file_extension, f"_processed{file_extension}")

    markdown_cells = ["First problem: @prob:first\nFirst figure: @fig:first\nSee #prob:first and #fig:first"]
    
    write_test_notebook(temp_notebook_file, markdown_cells)
    process_notebook(temp_notebook_file, processed_file)

    processed_cells = read_processed_notebook(processed_file)

    expected_output = [["First problem: 1\n", "First figure: 1\n", "See 1 and 1"]]
    
    assert processed_cells == expected_output

@pytest.mark.parametrize("file_extension", [".ipynb", ".source"])
def test_undefined_reference(temp_notebook_file, file_extension):
    """Test that an undefined reference raises an UndefinedReferenceError."""
    temp_notebook_file = temp_notebook_file.replace(".ipynb", file_extension)  
    processed_file = temp_notebook_file.replace(file_extension, f"_processed{file_extension}")
    markdown_cells = ["Reference to #undefined_label"]
    
    write_test_notebook(temp_notebook_file, markdown_cells)
    
    with pytest.raises(KeyError):
        process_notebook(temp_notebook_file, processed_file)

@pytest.mark.parametrize("file_extension", [".ipynb", ".source"])
def test_later_referenced_labels(temp_notebook_file, file_extension):
    """Ensure labels can be referenced before they are defined (two-pass)."""
    temp_notebook_file = temp_notebook_file.replace(".ipynb", file_extension)  
    processed_file = temp_notebook_file.replace(file_extension, f"_processed{file_extension}")
    markdown_cells = ["Reference to #topic:intro.\nLater, the label is defined: @topic:intro."]
    
    write_test_notebook(temp_notebook_file, markdown_cells)
    process_notebook(temp_notebook_file, processed_file)

    processed_cells = read_processed_notebook(processed_file)

    expected_output = [["Reference to 1.\n", "Later, the label is defined: 1."]]
    
    assert processed_cells == expected_output

@pytest.mark.parametrize("file_extension", [".ipynb", ".source"])
def test_multiple_references_to_same_label(temp_notebook_file, file_extension):
    """Ensure multiple references to the same label resolve correctly."""
    temp_notebook_file = temp_notebook_file.replace(".ipynb", file_extension)  
    processed_file = temp_notebook_file.replace(file_extension, f"_processed{file_extension}")
    markdown_cells = ["@step:one\nNow referring back to #step:one and again #step:one."]
    
    write_test_notebook(temp_notebook_file, markdown_cells)
    process_notebook(temp_notebook_file, processed_file)

    processed_cells = read_processed_notebook(processed_file)

    expected_output = [["1\n", "Now referring back to 1 and again 1."]]
    
    assert processed_cells == expected_output

@pytest.mark.parametrize("file_extension", [".ipynb", ".source"])
def test_multiple_labels_in_table(temp_notebook_file, file_extension):
    """Ensure references within a Markdown table are correctly replaced while maintaining alignment."""
    temp_notebook_file = temp_notebook_file.replace(".ipynb", file_extension)  
    processed_file = temp_notebook_file.replace(file_extension, f"_processed{file_extension}")
    markdown_cells = [
      [
        "| x       | y            | References    |\n",
        "|---------|--------------|---------------|\n",
        "| @a:x    | @a:y         | #a:x, #a:y    |\n",
        "| @a:x2   | Compute int. | #a:x, #a:x2   |"
      ]
    ]

    write_test_notebook(temp_notebook_file, markdown_cells)
    process_notebook(temp_notebook_file, processed_file)

    processed_cells = read_processed_notebook(processed_file)
    print(f"######processed_cells:\n{processed_cells}\n######")
    
    
    expected_output = [
      [
        "| x       | y            | References    |\n",
        "|---------|--------------|---------------|\n",
        "| 1       | 2            | 1   , 2       |\n",
        "| 3       | Compute int. | 1   , 3       |"
      ]
    ]

    assert processed_cells == expected_output

@pytest.mark.parametrize("file_extension", [".ipynb", ".source"])
def test_reference_on_last_line(temp_notebook_file, file_extension):
    """Test handling of references appearing on the last line of a Markdown cell."""
    temp_notebook_file = temp_notebook_file.replace(".ipynb", file_extension)  
    processed_file = temp_notebook_file.replace(file_extension, f"_processed{file_extension}")
    markdown_cells = [
        [
            "**Problem @XIII5**  (15 points) You are given a **PySpark DataFrame**.\n",
            "(continuation of Problem #XIII5)"
        ]
    ]

    write_test_notebook(temp_notebook_file, markdown_cells)
    process_notebook(temp_notebook_file, processed_file)

    processed_cells = read_processed_notebook(processed_file)

    expected_output = [[
            "**Problem 1**  (15 points) You are given a **PySpark DataFrame**.\n",
            "(continuation of Problem 1)"
        ]
    ]

    assert processed_cells == expected_output

@pytest.mark.parametrize("file_extension", [".ipynb", ".source"])
def test_jupyter_notebook_multiple_markdown_cells(temp_notebook_file, file_extension):
    """Ensure multiple Markdown cells are processed correctly."""
    temp_notebook_file = temp_notebook_file.replace(".ipynb", file_extension)  
    processed_file = temp_notebook_file.replace(file_extension, f"_processed{file_extension}")
    markdown_cells = [
        [
            "### Section @sec:one\n",
            "Content for section 1."
        ],
        [
            "See #sec:one for reference."
        ],
        [
            "### Section @sec:two\n",
            "Content for section 2.\n",
            "Referencing both #sec:one and #sec:two."
        ]
    ]

    write_test_notebook(temp_notebook_file, markdown_cells)
    process_notebook(temp_notebook_file, processed_file)

    processed_cells = read_processed_notebook(processed_file)

    expected_output = [
        [
            "### Section 1\n",
            "Content for section 1."
        ],
        [
            "See 1 for reference."
        ],
        [
            "### Section 2\n",
            "Content for section 2.\n",
            "Referencing both 1 and 2."
        ]
    ]

    assert processed_cells == expected_output
