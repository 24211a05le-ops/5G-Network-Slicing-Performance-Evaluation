import sys
import os

# Add root directory to sys.path so pytest can locate top-level modules like config
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
