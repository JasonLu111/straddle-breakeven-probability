import pandas as pd
import pytest

from src.models.walk_forward import generate_folds


def make_weekly_dates(start="2013-01-04", end="2020-12-31"):
    return pd.Series(pd.date_range(start, end, freq="7D"))


def test_folds_are_strictly_time_ordered_no_overlap():
    dates = make_weekly_dates()
    folds = generate_folds(dates, initial_train_years=6, test_window_years=1)
    assert len(folds) > 0
    for fold in folds:
        assert fold.train_end < fold.test_start
        train_dates = dates[fold.train_mask]
        test_dates = dates[fold.test_mask]
        assert train_dates.max() < test_dates.min()
        assert (train_dates < pd.Timestamp("2013-01-04") + pd.Timedelta(0)).sum() >= 0  # sanity: no exception


def test_expanding_window_train_set_only_grows():
    dates = make_weekly_dates()
    folds = generate_folds(dates, initial_train_years=6, test_window_years=1)
    train_sizes = [f.train_mask.sum() for f in folds]
    assert train_sizes == sorted(train_sizes)  # monotonically non-decreasing
    assert all(b > a for a, b in zip(train_sizes, train_sizes[1:]))  # strictly increasing (new data each fold)


def test_no_row_is_ever_in_both_train_and_test_within_a_fold():
    dates = make_weekly_dates()
    folds = generate_folds(dates, initial_train_years=6, test_window_years=1)
    for fold in folds:
        assert not (fold.train_mask & fold.test_mask).any()


def test_test_periods_across_folds_do_not_overlap():
    dates = make_weekly_dates()
    folds = generate_folds(dates, initial_train_years=6, test_window_years=1)
    for a, b in zip(folds, folds[1:]):
        assert a.test_end <= b.test_start


def test_first_fold_train_window_matches_initial_train_years():
    dates = make_weekly_dates(start="2013-01-04", end="2022-12-31")
    folds = generate_folds(dates, initial_train_years=6, test_window_years=1)
    first = folds[0]
    assert first.test_start.year == 2013 + 6
    assert first.train_end.year <= first.test_start.year - 1


def test_no_folds_when_data_shorter_than_initial_train_window():
    dates = make_weekly_dates(start="2020-01-03", end="2022-06-01")
    folds = generate_folds(dates, initial_train_years=6, test_window_years=1)
    assert folds == []
