import os

# 🔧 change to your AdsPower data folder
BASE_DIRS = [
    r"C:\Users\mhamz\AppData\Roaming\adspower_global\cwd_global",
    r"C:\Users\mhamz\AppData\Roaming\adspower_global\IndexedDB",
]

# The profile id you want to check
TARGET_ID = "k14y5wk7"

def scan_dirs(dirs, target):
    hits = []
    print(f"🚀 Scanning for profile id: {target}")
    for d in dirs:
        if not os.path.isdir(d):
            print(f"⚠️ Directory not found: {d}")
            continue
        print(f"📂 Searching in: {d}")
        for root, _, files in os.walk(d):
            for fname in files:
                path = os.path.join(root, fname)
                try:
                    with open(path, "rb") as f:
                        data = f.read().decode(errors="ignore")
                        if target in data:
                            hits.append(path)
                            print(f"✅ Found in {path}")
                except Exception:
                    # skip unreadable/locked files
                    continue
    return hits

if __name__ == "__main__":
    results = scan_dirs(BASE_DIRS, TARGET_ID)
    if not results:
        print(f"⚠️ Did not find {TARGET_ID} in scanned directories.")
    else:
        print(f"🎯 Done. Found {TARGET_ID} in {len(results)} file(s).")
