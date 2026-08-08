# Data directory

`raw/`, `interim/`, and `processed/` are gitignored — this project does not commit
market data (size + potential licensing restrictions on real option chain data).

- `raw/underlying/` — daily OHLCV for SPY/QQQ from `yfinance`, written by
  `scripts/download_data.py`.
- `raw/options/` — real historical option chain data (Phase 2+). Source and license
  terms must be documented here once configured in `configs/data.yaml`.
- `interim/` — cleaned/validated intermediate tables.
- `processed/` — final feature/target tables consumed by `src/models` and
  `src/backtest`.

To reproduce, run `make data` (Phase 1) — see the root `README.md` for the full
pipeline.
