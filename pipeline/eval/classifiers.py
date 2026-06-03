"""Classifiers for Phase 1: RF, logistic regression, sequence MLP."""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def make_rf(seed: int = 42) -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=100,
                    max_depth=12,
                    random_state=seed,
                    class_weight="balanced",
                ),
            ),
        ]
    )


def make_logreg(seed: int = 42) -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    random_state=seed,
                    class_weight="balanced",
                ),
            ),
        ]
    )


def make_sequence_clf(seed: int = 42) -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                MLPClassifier(
                    hidden_layer_sizes=(64, 32),
                    max_iter=500,
                    random_state=seed,
                ),
            ),
        ]
    )


def fit_predict(
    clf: Pipeline,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
) -> np.ndarray:
    clf.fit(x_train, y_train)
    return clf.predict(x_test)
