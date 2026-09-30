"""Command-line entry point for cleaning the original UCI household file."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from energy_assistant.preprocess import *
from energy_assistant.preprocess import main

if __name__ == "__main__":
    main()
