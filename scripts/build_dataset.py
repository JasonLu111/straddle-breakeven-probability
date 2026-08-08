"""CLI entry point: build the Phase 1 feature/target dataset for each ticker."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.build_features import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, default=1)
    parser.add_argument("--tickers", nargs="*", default=["SPY", "QQQ"])
    args = parser.parse_args()

    if args.phase != 1:
        raise NotImplementedError("Only Phase 1 (price-data-only) is implemented so far.")

    for ticker in args.tickers:
        run(ticker)
