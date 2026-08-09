"""CLI entry point: build the Phase 1 feature/target dataset for each ticker."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.build_features import run as run_phase1
from src.targets.build_breakeven_dataset import run as run_phase2

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, default=1, choices=[1, 2])
    parser.add_argument("--tickers", nargs="*", default=["SPY", "QQQ"])
    args = parser.parse_args()

    for ticker in args.tickers:
        if args.phase == 1:
            run_phase1(ticker)
        elif args.phase == 2:
            run_phase2(ticker)
