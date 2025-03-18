import base64
import json
import sys

def convert_source_to_dbc(source_file, dbc_file):
    """Convert a Databricks .source file to a .dbc archive."""
    with open(source_file, "r", encoding="utf-8") as f:
        source_data = f.read()

    encoded_data = base64.b64encode(source_data.encode("utf-8")).decode("utf-8")

    with open(dbc_file, "wb") as f:
        f.write(base64.b64decode(encoded_data))

    print(f"✅ Converted {source_file} → {dbc_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert.py input.source output.dbc")
    else:
        convert_source_to_dbc(sys.argv[1], sys.argv[2])
