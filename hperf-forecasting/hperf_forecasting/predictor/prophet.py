import numpy as np
import pandas as pd
from prophet import Prophet

from ..data import Dataset
from .base import BasePredictor


class ProphetPredictor(BasePredictor):

    def __init__(self, dataset: Dataset) -> None:
        super().__init__(dataset)

        self.model = None

    def predict(self, **kwargs) -> pd.DataFrame:
        assert self.model, "Model is not fitted"
        assert "predict_len" in kwargs, "predict_len is required"

        predict_len = kwargs.pop("predict_len")

        future = self.model.make_future_dataframe(
            periods=predict_len, freq=self.dataset.get_freq_str(), include_history=False
        )

        forecast = self.model.predict(future)
        forecast = forecast[["ds", "yhat"]]

        forecast = forecast.rename(
            columns={
                "ds": self.dataset.get_time_col(),
                "yhat": self.dataset.get_target_col(),
            }
        )

        return forecast

    def fit(self, **kwargs) -> None:
        x = self.dataset.get_time()
        y = self.dataset.get_target()

        data = pd.DataFrame(
            {
                "ds": x,
                "y": y,
            }
        )

        model = Prophet(
            yearly_seasonality=False,  # type: ignore
            weekly_seasonality=False,  # type: ignore
            daily_seasonality=False,  # type: ignore
            **kwargs,
        )
        model = model.fit(data)

        self.model = model
