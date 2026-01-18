import os
import subprocess
import time

PART_PREFIX = 'disney_complete.db.part'

# 1. Undo last commit but keep files
print("Running: git reset --soft HEAD~1")
subprocess.run(["git", "reset", "--soft", "HEAD~1"])

print("Running: git reset")
subprocess.run(["git", "reset"])

# 2. Find all part files and sort
parts = [f for f in os.listdir('.') if f.startswith(PART_PREFIX)]
parts.sort(key=lambda x: int(x.split('part')[-1]))
if not parts:
    print("No part files found.")
    exit(1)

# 3. Loop through one file at a time
for i, part in enumerate(parts):
    print(f"\nUploading {part} ({i+1}/{len(parts)})...")
    subprocess.run(["git", "add", part])
    subprocess.run(["git", "commit", "-m", f"Upload Part [{i+1}]"], check=True)
    result = subprocess.run(["git", "push"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        print("❌ Push failed. Stopping script.")
        exit(1)
    print(f"Success: Part [{i+1}] uploaded")
    time.sleep(10)

print("\nAdding and pushing remaining files...")
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Uploading remaining project files"], check=False)
subprocess.run(["git", "push"], check=False)
print("✅ All parts and remaining files pushed.")
