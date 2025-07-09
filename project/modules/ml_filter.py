import numpy as np
from pathlib import Path
import pickle

class MLFilter:
    """Lightweight ML probability filter (logistic regression).
    Expects pickled dict with keys 'coef_' and 'intercept_' for sklearn LogisticRegression.
    If weight file not found he returns True (pass-through).
    """

    def __init__(self, weight_file: str = "ml_weights.pkl", threshold: float = 0.55):
        self.threshold = threshold
        self.model = None
        if Path(weight_file).exists():
            try:
                with open(weight_file, "rb") as f:
                    self.model = pickle.load(f)
            except Exception:
                self.model = None

    def _sigmoid(self, z):
        return 1 / (1 + np.exp(-z))

    def _predict_prob(self, features: np.ndarray) -> float:
        if self.model is None:
            return 1.0  # always pass if no model
        coef = self.model['coef_']
        intercept = self.model['intercept_']
        return float(self._sigmoid(features.dot(coef) + intercept))

    def pass_filter(self, features: np.ndarray) -> bool:
        return self._predict_prob(features) >= self.threshold