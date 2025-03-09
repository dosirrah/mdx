import pytest
import tempfile
import os
from mdx import process_mdx_file, UndefinedReferenceError

@pytest.fixture
def temp_mdx_file():
    """Creates a temporary .mdx file and returns its path."""
    yield "test.mdx"
#    with tempfile.TemporaryDirectory() as temp_dir:
#        file_path = os.path.join(temp_dir, "test.mdx")
#        yield file_path

def write_test_file(file_path, content):
    """Helper function to write test content to a file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def read_output_file(file_path):
    """Helper function to read the processed .md file."""
    output_file = file_path.replace(".mdx", ".md")
    with open(output_file, "r", encoding="utf-8") as f:
        return f.readlines()

def strip_leading_comment(lines):
    """Helper function to ignore the first comment line when comparing outputs."""
    if lines and lines[0].startswith("<!-- Generated by mdx.py"):
        return lines[1:]  # Ignore the first line
    return lines

def test_leading_comment(temp_mdx_file):
    """Test that the generated Markdown file contains a proper leading comment."""
    content = "Some example text."
    
    write_test_file(temp_mdx_file, content)
    process_mdx_file(temp_mdx_file)

    output_lines = read_output_file(temp_mdx_file)
    
    assert output_lines[0].startswith("<!-- Generated by mdx.py"), "Missing or incorrect leading comment."
    assert "https://github.com/dosirrah/mdx" in output_lines[0], "Missing reference to the mdx repository."

def test_basic_label_resolution(temp_mdx_file):
    """Test that labels are correctly assigned and referenced."""
    content = """This is problem @prob:one.
See #prob:one for reference.
"""
    
    write_test_file(temp_mdx_file, content)
    process_mdx_file(temp_mdx_file)
    
    expected_output = """This is problem 1.
See 1 for reference.
"""
    
    output_lines = strip_leading_comment(read_output_file(temp_mdx_file))
    
    assert "".join(output_lines) == expected_output

def test_global_enumeration(temp_mdx_file):
    """Test global enumeration when no named enumeration is used."""
    content = """First label: @alpha
Another reference: #alpha"""
    
    write_test_file(temp_mdx_file, content)
    process_mdx_file(temp_mdx_file)
    
    expected_output = """First label: 1
Another reference: 1"""
    
    output_lines = strip_leading_comment(read_output_file(temp_mdx_file))
    
    assert "".join(output_lines).strip() == expected_output

def test_named_enumeration(temp_mdx_file):
    """Test that separate enumerations are assigned different sequences."""
    content = """First problem: @prob:first
First figure: @fig:first
See #prob:first and #fig:first"""
    
    write_test_file(temp_mdx_file, content)
    process_mdx_file(temp_mdx_file)
    
    expected_output = """First problem: 1
First figure: 1
See 1 and 1"""
    
    output_lines = strip_leading_comment(read_output_file(temp_mdx_file))
    
    assert "".join(output_lines).strip() == expected_output

def test_undefined_reference(temp_mdx_file):
    """Test that an undefined reference raises UndefinedReferenceError."""
    content = """Reference to #undefined_label"""
    
    write_test_file(temp_mdx_file, content)
    
    with pytest.raises(KeyError):
        process_mdx_file(temp_mdx_file)

def test_markdown_table_preserves_spacing(temp_mdx_file):
    """Ensure references in a Markdown table do not disrupt formatting."""
    content = """
| Label     | Reference |
|-----------|-----------|
| @tbl:test | #tbl:test |
"""
    
    write_test_file(temp_mdx_file, content)
    process_mdx_file(temp_mdx_file)
    
    expected_output = """
| Label     | Reference |
|-----------|-----------|
| 1         | 1         |
"""
    
    output_lines = strip_leading_comment(read_output_file(temp_mdx_file))
    
    assert "".join(output_lines) == expected_output

def test_later_referenced_labels(temp_mdx_file):
    """Ensure labels can be referenced before they are defined (two-pass)."""

    content = """Reference to #topic:intro.
Later, the label is defined: @topic:intro."""
    
    write_test_file(temp_mdx_file, content)
    process_mdx_file(temp_mdx_file)
    
    expected_output = """Reference to 1.
Later, the label is defined: 1."""
    
    output_lines = strip_leading_comment(read_output_file(temp_mdx_file))
    
    assert "".join(output_lines).strip() == expected_output

def test_multiple_references_to_same_label(temp_mdx_file):
    """Ensure multiple references to the same label resolve correctly."""
    content = """@step:one
Now referring back to #step:one and again #step:one."""
    
    write_test_file(temp_mdx_file, content)
    process_mdx_file(temp_mdx_file)
    
    expected_output = """1
Now referring back to 1 and again 1."""
    
    output_lines = strip_leading_comment(read_output_file(temp_mdx_file))
    
    assert "".join(output_lines).strip() == expected_output
    

def test_multiple_references_single_line(temp_mdx_file):
    """Test that multiple references on the same line are correctly replaced."""
    content = """This is problem @prob:one and @prob:two.
See #prob:one and #prob:two for reference.
"""

    write_test_file(temp_mdx_file, content)
    process_mdx_file(temp_mdx_file)

    expected_output = """This is problem 1 and 2.
See 1 and 2 for reference.
"""

    output_lines = strip_leading_comment(read_output_file(temp_mdx_file))
    assert "".join(output_lines) == expected_output


def test_multiple_references_in_table(temp_mdx_file):
    """Test that multiple references within the same table row are correctly replaced while maintaining alignment."""
    content = """
| Problem    | Description      | References            |
|------------|------------------|-----------------------|
| @prob:one  | Solve for X      | #prob:one, #prob:two  |
| @prob:two  | Compute integral | #prob:two, #prob:one  |
"""

    write_test_file(temp_mdx_file, content)
    process_mdx_file(temp_mdx_file)

    expected_output = """
| Problem    | Description      | References            |
|------------|------------------|-----------------------|
| 1          | Solve for X      | 1        , 2          |
| 2          | Compute integral | 2        , 1          |
"""

    output_lines = strip_leading_comment(read_output_file(temp_mdx_file))
    assert "".join(output_lines) == expected_output


def test_multiple_labels_in_table(temp_mdx_file):
    """Test that multiple references within the same table row are correctly replaced while maintaining alignment."""
    content = """
| x          | y                | References     |
|------------|------------------|----------------|
| @a:x       | @a:y             | #a:x, #a:y     |
| @a:x2      | Compute integral | #a:x, #a:x2    |
"""

    write_test_file(temp_mdx_file, content)
    process_mdx_file(temp_mdx_file)

    expected_output = """
| x          | y                | References     |
|------------|------------------|----------------|
| 1          | 2                | 1   , 2        |
| 3          | Compute integral | 1   , 3        |
"""

    output_lines = strip_leading_comment(read_output_file(temp_mdx_file))
    assert "".join(output_lines) == expected_output

    
def test_reference_on_last_line(temp_mdx_file):
    content = """
**Problem @XIII5**  (15 points) You are given a **PySpark DataFrame** containing sales transactions with the following schema:

(continuation of Problem #XIII5)"""

    write_test_file(temp_mdx_file, content)
    process_mdx_file(temp_mdx_file)

    expected_output = """
**Problem 1**  (15 points) You are given a **PySpark DataFrame** containing sales transactions with the following schema:

(continuation of Problem 1)"""

    output_lines = strip_leading_comment(read_output_file(temp_mdx_file))
    assert "".join(output_lines) == expected_output
    
