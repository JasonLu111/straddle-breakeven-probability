"""CLI entry point: download underlying price data (Phase 1)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.load_underlying import run

if __name__ == "__main__":
    run()
