import os

import os

def glue_file(output_file, part_prefix):
    parts = [f for f in os.listdir('.') if f.startswith(part_prefix)]
    parts.sort(key=lambda x: int(x.split('part')[-1]))
    if not parts:
        print(f"No part files found for {output_file}.")
        return False
    print(f"Found {len(parts)} parts for {output_file}. Stitching...")
    with open(output_file, 'wb') as outfile:
        for part in parts:
            with open(part, 'rb') as pf:
                chunk = pf.read()
                outfile.write(chunk)
            print(f"Added {part} ({len(chunk) / (1024 * 1024):.2f} MB)")
    print(f"Done! Created {output_file}.")
    return True

if __name__ == "__main__":
    glue_file('disney_complete.db', 'disney_complete.db.part')
    glue_file('disney_model.joblib', 'disney_model.joblib.part')
