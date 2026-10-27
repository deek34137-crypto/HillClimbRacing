#!/usr/bin/env python3
"""
Package the Godot Web export into a CrazyGames-ready ZIP.
- Verifies index.html is at root
- Checks total file count (<= 1500)
- Checks total size (<= 250 MB)
- Injects CrazyGames SDK if not already present
- Creates hill-climb-moddy-crazygames.zip

Usage:
    python3 scripts/package_crazygames.py
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path

WEB_EXPORT_DIR = Path("export/web")
OUTPUT_ZIP     = Path("hill-climb-moddy-crazygames.zip")
MAX_SIZE_MB    = 250
MAX_FILES      = 1500

def check_prerequisites():
    if not WEB_EXPORT_DIR.exists():
        print("❌ export/web/ not found. Run Godot web export first.")
        sys.exit(1)

    index = WEB_EXPORT_DIR / "index.html"
    if not index.exists():
        print("❌ export/web/index.html not found!")
        sys.exit(1)

    print("✅ Web export directory found")

def inject_sdk_if_needed():
    index = WEB_EXPORT_DIR / "index.html"
    content = index.read_text(encoding="utf-8")
    if "crazygames-sdk" not in content:
        print("💉 Injecting CrazyGames SDK...")
        os.system(f"python3 scripts/inject_crazygames_sdk.py {index}")
    else:
        print("✅ CrazyGames SDK already injected")

def check_size_and_count():
    total_size = 0
    file_count = 0
    for f in WEB_EXPORT_DIR.rglob("*"):
        if f.is_file():
            total_size += f.stat().st_size
            file_count += 1

    size_mb = total_size / (1024 * 1024)
    print(f"\n📊 Build stats:")
    print(f"   Files : {file_count} / {MAX_FILES}")
    print(f"   Size  : {size_mb:.1f} MB / {MAX_SIZE_MB} MB")

    ok = True
    if file_count > MAX_FILES:
        print(f"❌ Too many files! ({file_count} > {MAX_FILES})")
        ok = False
    if size_mb > MAX_SIZE_MB:
        print(f"❌ Build too large! ({size_mb:.1f} MB > {MAX_SIZE_MB} MB)")
        ok = False
    if ok:
        print("✅ Size and file count OK")
    return ok

def create_zip():
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in WEB_EXPORT_DIR.rglob("*"):
            if f.is_file():
                arcname = f.relative_to(WEB_EXPORT_DIR)
                zf.write(f, arcname)

    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"\n📦 Created: {OUTPUT_ZIP} ({size_mb:.1f} MB)")
    print("🚀 Ready to upload to developer.crazygames.com!")

if __name__ == "__main__":
    print("=== CrazyGames Packager ===\n")
    check_prerequisites()
    inject_sdk_if_needed()
    ok = check_size_and_count()
    if not ok:
        print("\n⚠️  Fix the issues above before uploading.")
        sys.exit(1)
    create_zip()
