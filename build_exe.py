# TLL OS Agent EXE Build Script
# Usage: python build_exe.py

import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
LAUNCHER = PROJECT_ROOT / "tll-agent-desktop" / "launcher" / "start_agent.py"
OUTPUT_DIR = PROJECT_ROOT / "tll-agent-desktop" / "dist"

print("=" * 60)
print("TLL OS Agent EXE Builder")
print("=" * 60)
print()

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--name", "TLL-Agent",
    "--distpath", str(OUTPUT_DIR),
    "--workpath", str(PROJECT_ROOT / "build"),
    "--specpath", str(PROJECT_ROOT / "build"),
    "--add-data", str(PROJECT_ROOT / "tll-agent-desktop" / "config") + os.pathsep + "config",
    str(LAUNCHER)
]

print(f"Launcher: {LAUNCHER}")
print(f"Output: {OUTPUT_DIR}")
print()
print("Building...")
print()

result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

if result.returncode == 0:
    exe_path = OUTPUT_DIR / "TLL-Agent.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n✅ Build successful!")
        print(f"EXE: {exe_path}")
        print(f"Size: {size_mb:.1f} MB")
    else:
        print("\n⚠️ Build completed but EXE not found")
else:
    print(f"\n❌ Build failed with code {result.returncode}")
