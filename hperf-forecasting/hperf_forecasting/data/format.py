from abc import abstractmethod
from typing import Any, List, Literal, Optional, Union

import pandas as pd


class DataFormat:

    def __init__(
        self,
        target_col: str,
        time_col: str = "time",
        freq: Union[
            str, pd.Timedelta, None
        ] = "1s",  # NOTE: must be pandas compatible, see: https://pandas.pydata.org/docs/user_guide/timeseries.html#timeseries-period-aliases
    ):
        self.target_col = target_col
        self.time_col = time_col
        self.freq = pd.Timedelta(freq) if freq else None

    def get_target_col(self) -> str:
        return self.target_col

    def get_time_col(self) -> str:
        return self.time_col

    def get_freq(self) -> Optional[pd.Timedelta]:
        return self.freq

    @abstractmethod
    def get_feature_cols(self) -> List[str]:
        pass


class Multivariate(DataFormat):

    def __init__(
        self,
        target_col: str,
        feature_cols: List[str],
        time_col: str = "time",
        freq: str = "1s",
    ):
        super().__init__(target_col, time_col, freq)

        self.feature_cols = feature_cols

    def get_feature_cols(self) -> List[str]:
        return self.feature_cols


class Univariate(DataFormat):

    def __init__(self, target_col: str, time_col: str = "time", freq: str = "1s"):
        super().__init__(target_col, time_col, freq)

    def get_feature_cols(self) -> List[str]:
        return []


def mk_univariate(
    target_col: str, time_col: str = "time", freq: str = "1s"
) -> Univariate:
    return Univariate(target_col, time_col, freq)


def mk_multivariate(
    target_col: str,
    feature_cols: List[str],
    time_col: str = "time",
    freq: str = "1s",
) -> Multivariate:
    return Multivariate(target_col, feature_cols, time_col, freq)
