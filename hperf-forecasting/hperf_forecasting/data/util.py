import pandas as pd

from .format import DataFormat


def fill_missing_time(
    df: pd.DataFrame, format: DataFormat, is_sorted: bool = False
) -> pd.DataFrame:
    """
    Pad missing time entries in a DataFrame

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to fill
    format : DataFormat
        DataFormat object
    is_sorted : bool, optional
        Whether the DataFrame is sorted by the time column, by default False

    Returns
    -------
    pd.DataFrame
        Padded DataFrame
    """

    time_col = format.get_time_col()
    freq = format.get_freq()
    assert freq, "Frequency must be set"

    if not is_sorted:
        df = df.sort_values(time_col)

    start_time = df[time_col].iloc[0]
    end_time = df[time_col].iloc[-1]

    expected_time = pd.date_range(start=start_time, end=end_time, freq=freq)
    expected_time = pd.DataFrame(expected_time, columns=[time_col])

    df = pd.merge(expected_time, df, on=time_col, how="left")

    return df
