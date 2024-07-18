from abc import abstractmethod
from typing import Callable, Optional

import numpy as np
import pandas as pd

from .format import DataFormat


class Dataset:
    def __init__(self, df: pd.DataFrame, format: DataFormat) -> None:
        self.time_col = format.get_time_col()
        self.target_col = format.get_target_col()
        self.feature_cols = format.get_feature_cols()

        self.df = df.sort_values(self.time_col).reset_index()

        freq = format.get_freq()

        if not freq:
            freq = pd.infer_freq(self.df[self.time_col])
            assert freq, "Frequency must be set"
            self.freq = pd.Timedelta(freq)
        else:
            self.freq = freq

        self._match_data_format()

    def _match_data_format(self) -> None:
        if self.time_col not in self.df.columns:
            raise ValueError(f"Time column '{self.time_col}' not found")

        # check if time column is pd.Timestamp -> mapping to datetime64[ns]
        time_col_type = self.df[self.time_col].dtype
        if time_col_type not in [
            np.dtype("datetime64[ns]"),
        ]:
            raise ValueError(
                f"Time column '{self.time_col}' must be either datetime64[ns]"
            )

        if self.target_col not in self.df.columns:
            raise ValueError(f"Target column '{self.target_col}' not found")

        for col in self.feature_cols:
            if col not in self.df.columns:
                raise ValueError(f"Feature column '{col}' not found")

        # check whether the time column is unique
        if not self.df[self.time_col].is_unique:
            raise ValueError(f"Time column '{self.time_col}' is not unique")

        # check whether the time column has the correct delta
        deltas = self.df[self.time_col].diff()
        common_delta = deltas.mode().values[0]

        if common_delta != self.freq:
            raise ValueError(
                f"Time column '{self.time_col}' does not have the correct period, expected '{self.freq}', got '{common_delta}'"
            )

        # check whether the time column is continuous
        start_time: pd.Timestamp
        end_time: pd.Timestamp

        start_time, end_time = (
            self.df[self.time_col].iloc[0],
            self.df[self.time_col].iloc[-1],
        )

        if (end_time - start_time) != (len(self.df) - 1) * self.freq:
            raise ValueError("Time column is not continuous")

    def get_format(self) -> DataFormat:
        return DataFormat(
            target_col=self.target_col,
            time_col=self.time_col,
            freq=self.freq,
        )

    def get_freq(self) -> pd.Timedelta:
        return self.freq

    def get_freq_str(self) -> str:
        from pandas.tseries.frequencies import to_offset

        offset = to_offset(self.freq)
        assert offset, "Invalid frequency"

        return offset.freqstr

    def get_dataframe(self) -> pd.DataFrame:
        return self.df

    def get_target_col(self) -> str:
        return self.target_col

    def get_time_col(self) -> str:
        return self.time_col

    def get_feature_cols(self) -> list[str]:
        return self.feature_cols

    def get_target(self) -> pd.Series:
        return self.df[self.target_col]

    def get_time(self) -> pd.Series:
        return self.df[self.time_col]

    def get_timestamp(self) -> pd.Series:
        return self.df[self.time_col].apply(lambda x: x.timestamp())

    def get_freq_in_secs(self) -> float:
        return self.freq.total_seconds()

    def get_features(self) -> pd.DataFrame:
        return self.df[self.feature_cols]

    def __len__(self) -> int:
        return len(self.df)

    def __repr__(self) -> str:
        return repr(self.df)
