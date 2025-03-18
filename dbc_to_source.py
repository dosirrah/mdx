import base64
import json
import sys

def convert_dbc_to_source(dbc_file, output_file):
    """Decode a Databricks .dbc archive into a readable JSON .source file."""
    with open(dbc_file, "rb") as f:
        data = f.read()

    # Databricks .dbc files are base64-encoded
    decoded_data = base64.b64decode(data).decode("utf-8")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(decoded_data)

    print(f"✅ Converted {dbc_file} → {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python decode_dbc.py input.dbc output.source")
    else:
        convert_dbc_to_source(sys.argv[1], sys.argv[2])
