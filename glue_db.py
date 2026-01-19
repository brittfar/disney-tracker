import glob
import os

def reconstruct_all():
    print("🧩 STARTING EMERGENCY RECONSTRUCTION...")
    
    # 1. Rebuild Database
    db_parts = sorted(glob.glob("disney_complete.db.part*"))
    if db_parts:
        print(f"   Found {len(db_parts)} database chunks. Stitching...")
        with open("disney_complete.db", "wb") as dest:
            for part in db_parts:
                with open(part, "rb") as source:
                    dest.write(source.read())
        print("   ✅ Database Rebuilt!")
    else:
        print("   ⚠️ No database chunks found!")

    # 2. Rebuild Model
    model_parts = sorted(glob.glob("disney_model.joblib.part*"))
    if model_parts:
        print(f"   Found {len(model_parts)} model chunks. Stitching...")
        with open("disney_model.joblib", "wb") as dest:
            for part in model_parts:
                with open(part, "rb") as source:
                    dest.write(source.read())
        print("   ✅ Model Rebuilt!")
    else:
        print("   ⚠️ No model chunks found!")

if __name__ == "__main__":
    reconstruct_all()
