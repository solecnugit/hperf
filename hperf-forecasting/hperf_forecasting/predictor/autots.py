import autots as ats
import numpy as np
import pandas as pd

from ..data import Dataset
from .base import BasePredictor


class AutoTsPredictor(BasePredictor):

    def __init__(self, dataset: Dataset) -> None:
        super().__init__(dataset)

        self.model = None

    def predict(self, **kwargs) -> pd.DataFrame:
        assert self.model, "Model is not fitted"

        prediction = self.model.predict()

        forecast = prediction.forecast  # type: ignore
        forecast[self.dataset.get_time_col()] = forecast.index
        forecast = forecast.reset_index(drop=True)

        return forecast

    def fit(self, **kwargs) -> None:
        self.predict_len = kwargs.pop("predict_len", 30)

        x = self.dataset.get_time()
        y = self.dataset.get_target()

        df = pd.concat([x, y], axis=1)
        df = df.set_index(self.dataset.get_time_col())

        model = ats.AutoTS(
            forecast_length=self.predict_len,
            frequency=self.dataset.get_freq_str(),
            prediction_interval=0.95,
            ensemble="auto",
            model_list="superfast",
            transformer_list="superfast",  # type: ignore
            drop_most_recent=1,
            max_generations=3,
            num_validations=1,
            validation_method="backwards",
        )

        model = model.fit(
            df,
        )

        self.model = model
