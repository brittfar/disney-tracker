import os

CHUNK_SIZE = 90 * 1024 * 1024  # 90MB
INPUT_FILE = 'disney_model.joblib'

def split_file(input_file, chunk_size):
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        return
    file_size = os.path.getsize(input_file)
    print(f"Splitting {input_file} ({file_size / (1024 * 1024):.2f} MB)...")
    part_num = 0
    with open(input_file, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            part_name = f"{input_file}.part{part_num:03d}"
            with open(part_name, 'wb') as pf:
                pf.write(chunk)
            print(f"Created: {part_name} ({len(chunk) / (1024 * 1024):.2f} MB)")
            part_num += 1
    print(f"Done. Total parts: {part_num}")

if __name__ == "__main__":
    split_file(INPUT_FILE, CHUNK_SIZE)
