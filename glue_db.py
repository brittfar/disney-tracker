import os

def glue_file(output_file, part_prefix):
    parts = [f for f in os.listdir('.') if f.startswith(part_prefix)]
    parts.sort(key=lambda x: int(x.split('part')[-1]))
    if not parts:
        print(f"No part files found for {output_file}.")
        return False
    print(f"[GLUE] Found {len(parts)} parts for {output_file}. Stitching...")
    with open(output_file, 'wb') as outfile:
        for part in parts:
            with open(part, 'rb') as pf:
                chunk = pf.read()
                outfile.write(chunk)
            print(f"[GLUE] Added {part} ({len(chunk) / (1024 * 1024):.2f} MB)")
    print(f"[GLUE] Done! Created {output_file}.")
    return True

def reconstruct_all():
    print("[GLUE] Running reconstruct_all()...")
    if not os.path.exists('disney_complete.db'):
        print("[GLUE] disney_complete.db missing. Attempting to reconstruct...")
        glue_file('disney_complete.db', 'disney_complete.db.part')
    else:
        print("[GLUE] disney_complete.db already exists.")
    if not os.path.exists('disney_model.joblib'):
        print("[GLUE] disney_model.joblib missing. Attempting to reconstruct...")
        glue_file('disney_model.joblib', 'disney_model.joblib.part')
    else:
        print("[GLUE] disney_model.joblib already exists.")
    print("[GLUE] Reconstruction complete.")

if __name__ == "__main__":
    reconstruct_all()
