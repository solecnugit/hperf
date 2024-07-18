from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from hyperopt import STATUS_OK, fmin, hp, tpe
from sklearn.linear_model import LinearRegression

from ..data import Dataset
from .base import BasePredictor


class EwmPredictor(BasePredictor):

    def __init__(self, dataset: Dataset, train_size: float = 0.98) -> None:
        super().__init__(dataset)

        self.train_size = train_size
        self.best_params: Optional[Dict[str, Any]] = None

    def get_params(self) -> Dict[str, Any]:
        assert self.best_params, "Model is not fitted"

        return self.best_params

    def predict(self, **kwargs) -> pd.DataFrame:
        assert self.best_params, "Model is not fitted"
        assert "predict_len" in kwargs, "predict_len is required"

        predict_len = kwargs.pop("predict_len")

        poffset: float = self.dataset.get_timestamp().iloc[-1]
        pstep = self.dataset.get_freq_in_secs()
        prange = np.arange(
            poffset + pstep,
            poffset + pstep * (predict_len + 1),
            pstep,
        ).reshape(-1, 1)

        y = self.dataset.get_target()
        alpha = self.best_params["alpha"]
        for _ in range(predict_len):
            next_y: float = y.ewm(alpha=alpha, adjust=True).mean().iloc[-1]
            y = pd.concat([y, pd.Series([next_y])])

        py = y.iloc[-predict_len:].values

        data = {
            self.dataset.get_time_col(): pd.to_datetime(prange.flatten(), unit="s"),  # type: ignore
            self.dataset.get_target_col(): py,
        }

        return pd.DataFrame(data)

    def fit(self, **kwargs) -> None:
        y = self.dataset.get_target()

        train_size, test_size = int(len(y) * self.train_size), int(
            len(y) * (1 - self.train_size)
        )
        train_y, test_y = y[:train_size], y[train_size:]

        params = {
            "alpha": hp.uniform("alpha", 1e-3, 1),
        }

        def objective(params):
            alpha = params["alpha"]
            data = train_y

            for _ in range(test_size + 1):
                next_y: float = data.ewm(alpha=alpha, adjust=True).mean().iloc[-1]
                data = pd.concat([data, pd.Series([next_y])])

            error = np.mean((data[train_size:].values - test_y.values) ** 2)  # type: ignore

            return {
                "status": STATUS_OK,
                "loss": error,
            }

        if "max_evals" in kwargs:
            max_evals = kwargs.pop("max_evals")
        else:
            max_evals = 100

        best = fmin(objective, params, algo=tpe.suggest, max_evals=max_evals, **kwargs)
        assert best, "Optimization failed"

        self.best_params = best
