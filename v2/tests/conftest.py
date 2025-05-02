"""
Configuration for pytest.
"""
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path so we can import from app modules
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root) 