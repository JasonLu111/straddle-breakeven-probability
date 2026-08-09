"""Probability calibration, fit strictly inside a fold's training data.

CalibratedClassifierCV(cv=k) internally k-fold cross-validates within whatever
X/y it's given -- since it's only ever given the training-fold data here, the
test period is never touched during calibration.
"""
from __future__ import annotations

from sklearn.calibration import CalibratedClassifierCV


def fit_calibrated(estimator, X_train, y_train, method: str, cv_folds: int) -> CalibratedClassifierCV:
    calibrated = CalibratedClassifierCV(estimator, method=method, cv=cv_folds)
    calibrated.fit(X_train, y_train)
    return calibrated
