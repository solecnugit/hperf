import numpy as np
import pandas as pd
import pmdarima as pm
from pmdarima.pipeline import Pipeline
from pmdarima.preprocessing import BoxCoxEndogTransformer

from ..data import Dataset
from .base import BasePredictor


class ArimaPredictor(BasePredictor):

    def __init__(self, dataset: Dataset) -> None:
        super().__init__(dataset)

        self.model = None

    def predict(self, **kwargs) -> pd.DataFrame:
        assert self.model, "Model is not fitted"
        assert "predict_len" in kwargs, "predict_len is required"

        predict_len = kwargs.pop("predict_len")

        poffset: float = self.dataset.get_timestamp().iloc[-1]
        pstep = self.dataset.get_freq_in_secs()

        prange = np.arange(
            poffset + pstep,
            poffset + pstep * (predict_len + 1),
            pstep,
        ).reshape(-1, 1)

        py = self.model.predict(predict_len)

        data = {
            self.dataset.get_time_col(): pd.to_datetime(
                prange.flatten(), unit="s"  # type: ignore
            ),
            self.dataset.get_target_col(): py,
        }

        return pd.DataFrame(data)

    def fit(self, **kwargs) -> None:
        x = self.dataset.get_timestamp().values.reshape(-1, 1)  # type: ignore
        y = self.dataset.get_target()

        use_box_cox = False
        if "use_box_cox" in kwargs:
            use_box_cox = kwargs.pop("use_box_cox")

        if use_box_cox:
            pipeline = Pipeline(
                [
                    ("boxcox", BoxCoxEndogTransformer(lmbda2=1e-6)),  # type: ignore
                    (
                        "arima",
                        pm.AutoARIMA(seasonal=False, suppress_warnings=True),
                    ),
                ]
            )
        else:
            pipeline = pm.AutoARIMA(seasonal=False, suppress_warnings=True)

        pipeline.fit(y)

        self.model = pipeline
