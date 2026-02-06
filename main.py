#!/usr/bin/env python3
"""
NSC Mathematics Study Program
CAPS Curriculum - Grade 12

A comprehensive study tool for NSC Mathematics exam preparation.
"""

import sys
import os

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add the package directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli.menu import main

if __name__ == "__main__":
    main()
