"""Expanding-window walk-forward fold generator.

Train window always starts at the beginning of the sample and grows by one
test window each fold (expanding=true in configs/model.yaml). This means every
fold's training data is strictly earlier than its test data -- no fold's model
selection, scaling, or calibration is allowed to see a single observation from
its own test period or later.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Fold:
    fold_id: int
    train_mask: pd.Series
    test_mask: pd.Series
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


def generate_folds(dates: pd.Series, initial_train_years: int, test_window_years: int) -> list[Fold]:
    dates = pd.to_datetime(dates)
    start_year = dates.min().year
    last_date = dates.max()

    folds = []
    fold_id = 0
    test_start_year = start_year + initial_train_years

    while True:
        test_start = pd.Timestamp(year=test_start_year, month=1, day=1)
        test_end = pd.Timestamp(year=test_start_year + test_window_years, month=1, day=1)

        if test_start > last_date:
            break

        train_mask = dates < test_start
        test_mask = (dates >= test_start) & (dates < test_end)

        if train_mask.sum() > 0 and test_mask.sum() > 0:
            folds.append(Fold(
                fold_id=fold_id,
                train_mask=train_mask,
                test_mask=test_mask,
                train_start=dates[train_mask].min(),
                train_end=dates[train_mask].max(),
                test_start=dates[test_mask].min(),
                test_end=dates[test_mask].max(),
            ))
            fold_id += 1

        test_start_year += test_window_years

    return folds
