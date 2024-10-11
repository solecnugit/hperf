import argparse
import datetime
import logging
import os
from tkinter import Y
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)


def check_if_prophet_installed():
    try:
        import prophet
    except ImportError:
        logger.error(
            "Prophet is not installed. Please install it by running `pip install prophet`"
        )
        exit(1)


def check_if_sklearn_installed():
    try:
        import sklearn
    except ImportError:
        logger.error(
            "Scikit-learn is not installed. Please install it by running `pip install scikit-learn`"
        )
        exit(1)


def check_if_pmdarima_installed():
    try:
        import pmdarima
    except ImportError:
        logger.error(
            "pmdarima is not installed. Please install it by running `pip install pmdarima`"
        )
        exit(1)


def check_if_autots_installed():
    try:
        import autots
    except ImportError:
        logger.error(
            "AutoTS is not installed. Please install it by running `pip install autots`"
        )
        exit(1)


def main():
    parser = make_parser()
    args = parser.parse_args()

    df = load_data(args.test_dir)
    models = args.model.split(",")
    steps = args.steps

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    for model in models:
        output_file = os.path.join(output_dir, f"{model}_forecast.csv")

        data = forecast(df, model, steps)
        if data is not None:
            data["timestamp"] = data["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S %Z")
            data.to_csv(output_file, index=False)


def extract_features(df: pd.DataFrame):
    return [col for col in df.columns if col != "timestamp"]


def forecast(df: pd.DataFrame, model: str, steps: int):
    features = extract_features(df)

    if model == "lr":
        check_if_sklearn_installed()
        return do_lr_forecast(df.copy(), steps, features)

    if model == "prophet":
        check_if_prophet_installed()
        return do_prophet_forecast(df.copy(), steps, features)

    if model == "arima":
        check_if_pmdarima_installed()
        return do_arima_forecast(df.copy(), steps, features)

    if model == "autots":
        check_if_autots_installed()

        try:
            return do_autots_forecast(df.copy(), steps, features)
        except ValueError as e:
            logger.error(f"Error in AutoTS: {e}")
            return None

    if model == "ewm":
        return do_ewm_forecast(df.copy(), steps, features)


def mk_timestamp(start: datetime.datetime, steps: int, freq: str = "s") -> pd.Series:
    return pd.Series(pd.date_range(start, periods=steps, freq=freq))


def merge_forecast(df: pd.DataFrame, forecast_df: pd.DataFrame):
    df["type"] = "actual"
    forecast_df["type"] = "forecast"

    return pd.concat([df, forecast_df])


def do_lr_forecast(df: pd.DataFrame, steps: int, features: List[str]):
    from sklearn.linear_model import LinearRegression

    cols = {}

    for feat in features:
        x = df.index.values.reshape(-1, 1)
        y = df[feat]

        model = LinearRegression()
        model.fit(x, y)

        px = list(range(len(df), len(df) + steps))
        px = pd.Series(px)

        py = model.predict(px.to_frame())

        cols[feat] = py

    forecast_df = pd.DataFrame(cols)
    forecast_df["timestamp"] = mk_timestamp(df["timestamp"].iloc[-1], steps)

    df = merge_forecast(df, forecast_df)
    return df


def do_ewm_forecast(df: pd.DataFrame, steps: int, features: List[str]):
    cols = {}

    for feat in features:
        y = df[feat]

        py = []
        for _ in range(steps):
            ny = y.ewm(alpha=0.3).mean().iloc[-1]
            py.append(ny)
            y = pd.concat([y, pd.Series([ny])])

        cols[feat] = py

    forecast_df = pd.DataFrame(cols)
    forecast_df["timestamp"] = mk_timestamp(df["timestamp"].iloc[-1], steps)

    df = merge_forecast(df, forecast_df)
    return df


def do_prophet_forecast(df: pd.DataFrame, steps: int, features: List[str]):
    from prophet import Prophet

    cols = {}

    # remove timezone from timestamp column
    df["timestamp"] = df["timestamp"].dt.tz_localize(None)

    for feat in features:
        data = df[["timestamp", feat]]
        data.columns = ["ds", "y"]

        model = Prophet()
        model.fit(data)

        future = model.make_future_dataframe(periods=steps, freq="s")
        forecast = model.predict(future)

        cols[feat] = forecast["yhat"].tail(steps).values

    forecast_df = pd.DataFrame(cols)
    forecast_df["timestamp"] = mk_timestamp(df["timestamp"].iloc[-1], steps)

    df = merge_forecast(df, forecast_df)
    return df


def do_arima_forecast(df: pd.DataFrame, steps: int, features: List[str]):
    from pmdarima import auto_arima

    cols = {}

    for feat in features:
        y = df[feat]

        model = auto_arima(y)
        forecast = model.predict(n_periods=steps)

        cols[feat] = forecast

    forecast_df = pd.DataFrame(cols)
    forecast_df["timestamp"] = mk_timestamp(df["timestamp"].iloc[-1], steps)

    df = merge_forecast(df, forecast_df)
    return df


def do_autots_forecast(df: pd.DataFrame, steps: int, features: List[str]):
    from autots import AutoTS

    cols = {}

    df = df.set_index("timestamp")

    for feat in features:
        y = df[feat]

        model = AutoTS(forecast_length=steps, frequency="s")
        model = model.fit(y)

        forecast = model.predict()
        forecast = forecast.iloc[-steps:]

        cols[feat] = forecast

    forecast_df = pd.DataFrame(cols)
    forecast_df["timestamp"] = mk_timestamp(df["timestamp"].iloc[-1], steps)

    df = merge_forecast(df, forecast_df)
    return df


def load_data(target_dir: str):
    # Check if aggregated_metrics.csv exists in the test directory
    if not os.path.exists(target_dir):
        logger.error(
            f"Test directory {target_dir} does not exist. Run hp-collect first"
        )
        exit(1)

    target_dir = os.path.join(target_dir, "analysis_results")
    if not os.path.exists(target_dir):
        logger.error(
            f"analysis_results directory does not exist in the test directory {target_dir}"
        )
        exit(1)

    target_files = [
        "sw_timeseries.csv",
        "hw_timeseries.csv",
    ]

    timeseries = []

    for file in target_files:
        file_path = os.path.join(target_dir, file)
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist")
            exit(1)

        df = pd.read_csv(file_path)
        # skip first column
        df = df.iloc[:, 1:]
        timeseries.append(df)

    # Merge the two timeseries by index
    timeseries = pd.concat(timeseries, axis=1)

    next_timestamp_col_index = list(timeseries.columns).index("timestamp", 1)
    # Deduplicate the timestamp column
    timeseries = timeseries.iloc[
        :, [i for i in range(len(timeseries.columns)) if i != next_timestamp_col_index]
    ]

    # Timestamp format: 2024-10-11 06:56:38 UTC
    timeseries["timestamp"] = pd.to_datetime(
        timeseries["timestamp"], format="%Y-%m-%d %H:%M:%S %Z"
    )
    timeseries = timeseries.infer_objects()

    return timeseries


def make_parser():
    parser = argparse.ArgumentParser(description="Hperf Forecast")

    parser.add_argument(
        "--test-dir",
        metavar="TEST_DIR_PATH",
        type=str,
        help="test directory which stores the profiling raw data (can be found from the output of hp-collect)",
        required=True,
    )

    parser.add_argument(
        "--output-dir",
        metavar="OUTPUT_DIR_PATH",
        type=str,
        help="output directory to store the forecast results",
        required=True,
    )

    parser.add_argument(
        "--model",
        metavar="MODEL",
        type=str,
        help="model to use for forecasting. Available models: lr, prophet, arima, ewm, autots",
        default="lr",
    )

    parser.add_argument(
        "--steps",
        metavar="STEPS",
        type=int,
        help="number of steps to forecast",
        default=60,
    )

    return parser


if __name__ == "__main__":
    main()
