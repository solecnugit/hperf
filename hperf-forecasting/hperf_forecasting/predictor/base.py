import datetime as dt
from abc import abstractmethod

import pandas as pd

from ..data import Dataset


class BasePredictor:

    def __init__(self, dataset: Dataset) -> None:
        self.dataset = dataset

    @abstractmethod
    def predict(self, **kwargs) -> pd.DataFrame:
        pass

    @abstractmethod
    def fit(self, **kwargs) -> None:
        pass
