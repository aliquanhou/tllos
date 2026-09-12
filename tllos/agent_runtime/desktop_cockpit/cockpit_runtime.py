#!/usr/bin/env python3
"""
TLL OS Desktop Cockpit - Runtime Entry
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from main_window import main

if __name__ == "__main__":
    main()
