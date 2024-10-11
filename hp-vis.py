import argparse

from io import StringIO
import logging
import os
from typing import Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def main():
    parser = make_parser()
    args = parser.parse_args()

    check_if_pnpm_installed()

    test_dir = args.test_dir
    data, cpu_info = load_dataset_and_cpu_info(test_dir)

    target_dir = "hperf-dashboard/public"
    if not os.path.exists(target_dir):
        raise FileNotFoundError(f"Directory {target_dir} does not exist")

    with open(os.path.join(target_dir, "data.csv"), "w") as f:
        f.write(data)

    with open(os.path.join(target_dir, "cpu_info"), "w") as f:
        f.write(cpu_info)

    # run the dashboard
    ret = os.system("cd hperf-dashboard && pnpm install && pnpm run dev")
    if ret != 0:
        logger.error("Failed to run the dashboard")
        exit(1)


def check_if_pnpm_installed():
    ret = os.system("pnpm --version")
    if ret != 0:
        logger.error(
            "pnpm is not installed. Please install it by running `npm install -g pnpm`"
        )
        exit(1)


def load_dataset_and_cpu_info(test_dir: str) -> Tuple[str, str]:
    target_files = [
        "sw_timeseries.csv",
        "hw_timeseries.csv",
    ]

    target_files = [
        os.path.join(test_dir, "analysis_results", file) for file in target_files
    ]

    df = []

    for file in target_files:
        if not os.path.exists(file):
            logger.error(f"File {file} does not exist")
            exit(1)

        data = pd.read_csv(file)
        # skip first column
        data = data.iloc[:, 1:]

        df.append(data)

    df = pd.concat(df, axis=1)

    next_timestamp_col_index = list(df.columns).index("timestamp", 1)
    # Deduplicate the timestamp column
    df = df.iloc[
        :, [i for i in range(len(df.columns)) if i != next_timestamp_col_index]
    ]

    # Reset timestamp from 1
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S %Z")
    df["timestamp"] = (df["timestamp"] - df["timestamp"].iloc[0]).dt.total_seconds()

    str_io = StringIO("")
    df.to_csv(str_io, index=False)

    with open(os.path.join(test_dir, "cpu_info"), "r") as f:
        cpu_info = f.read()

    return str_io.getvalue(), cpu_info


def make_parser():
    parser = argparse.ArgumentParser(description="Visualize the forecasted data")
    parser.add_argument(
        "--test-dir",
        type=str,
        required=True,
        help="The directory containing the test data",
    )

    return parser


if __name__ == "__main__":
    main()
