import os
import glue_db

# Self-Healing: Build DB and Model if missing
if not os.path.exists("disney_complete.db") or not os.path.exists("disney_model.joblib"):
    print("🧩 Critical files missing. Starting emergency reconstruction...")
    glue_db.reconstruct_all()
    print("✅ Reconstruction complete. Launching app...")

import streamlit as st
import os
import glob

st.set_page_config(page_title="Debug Mode", layout="wide")

st.title("🛠️ Render Diagnostic Tool")

st.write("I am checking the server's hard drive to see if your files made it...")

# 1. CHECK DATABASE
db_files = glob.glob("*.db")
db_parts = glob.glob("*.db.part*")
st.subheader(f"📂 Database Files (Found {len(db_files)} DBs, {len(db_parts)} Parts)")

if os.path.exists("disney_complete.db"):
    size_mb = os.path.getsize("disney_complete.db") / (1024 * 1024)
    st.success(f"✅ disney_complete.db EXISTS! Size: {size_mb:.2f} MB")
else:
    st.error("❌ disney_complete.db is MISSING. The 'Glue' script did not run.")

# 2. CHECK MODEL
model_files = glob.glob("*.joblib")
model_parts = glob.glob("*.joblib.part*")
st.subheader(f"🧠 Model Files (Found {len(model_files)} Models, {len(model_parts)} Parts)")

if os.path.exists("disney_model.joblib"):
    size_mb = os.path.getsize("disney_model.joblib") / (1024 * 1024)
    st.success(f"✅ disney_model.joblib EXISTS! Size: {size_mb:.2f} MB")
else:
    st.error("❌ disney_model.joblib is MISSING.")

# 3. LIST ALL FILES
st.subheader("Example of Files in Current Directory:")
files = os.listdir('.')
st.code(files)