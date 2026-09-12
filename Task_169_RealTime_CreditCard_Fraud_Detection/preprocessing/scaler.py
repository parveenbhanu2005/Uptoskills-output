import os
import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler


SCALER_PATH = "saved_models/feature_scaler.pkl"


class FeatureScaler:

    def __init__(self):
        self.scaler = StandardScaler()

    def fit(self, X):
        self.scaler.fit(X)
        return self

    def transform(self, X):
        return self.scaler.transform(X)

    def fit_transform(self, X):
        return self.scaler.fit_transform(X)

    def transform_single(self, vector):
        vector = np.array(vector, dtype=np.float32).reshape(1, -1)
        return self.scaler.transform(vector)

    def save(self):
        os.makedirs("saved_models", exist_ok=True)
        joblib.dump(self.scaler, SCALER_PATH)

    def load(self):
        self.scaler = joblib.load(SCALER_PATH)
        return self