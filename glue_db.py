import os

OUTPUT_FILE = 'disney_complete.db'
PART_PREFIX = 'disney_complete.db.part'

def glue_parts():
    # Find all part files and sort them by part number
    parts = [f for f in os.listdir('.') if f.startswith(PART_PREFIX)]
    parts.sort(key=lambda x: int(x.split('part')[-1]))
    if not parts:
        print("No part files found.")
        return
    print(f"Found {len(parts)} parts. Stitching into {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'wb') as outfile:
        for part in parts:
            with open(part, 'rb') as pf:
                chunk = pf.read()
                outfile.write(chunk)
            print(f"Added {part} ({len(chunk) / (1024 * 1024):.2f} MB)")
    print(f"Done! Created {OUTPUT_FILE}.")

if __name__ == "__main__":
    glue_parts()
