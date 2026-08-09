"""Baseline predictors, fit strictly on a fold's training data.

`unconditional historical rate` and sklearn's `DummyClassifier(strategy="prior")`
are mathematically identical (both just predict the training-set base rate for
every test row) -- rather than reporting the same number under two names, this
project reports it once as "dummy_prior" and documents the equivalence.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier


def fit_predict_dummy(y_train: pd.Series, n_test: int) -> np.ndarray:
    clf = DummyClassifier(strategy="prior")
    clf.fit(np.zeros((len(y_train), 1)), y_train)
    return clf.predict_proba(np.zeros((n_test, 1)))[:, 1]


def fit_predict_compression_rule(y_train: pd.Series, regime_train: pd.Series, regime_test: pd.Series) -> np.ndarray:
    """Predicts P(target=1) = the training-set event rate conditional on the
    test row's own compression-regime flag (a simple, fully interpretable rule
    -- exactly what a trader eyeballing the compression indicator would do).
    """
    regime_train = regime_train.astype(bool)
    p_compression = y_train[regime_train].mean() if regime_train.any() else y_train.mean()
    p_normal = y_train[~regime_train].mean() if (~regime_train).any() else y_train.mean()

    regime_test = regime_test.astype(bool)
    return np.where(regime_test, p_compression, p_normal)
