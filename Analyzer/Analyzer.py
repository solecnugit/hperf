import pandas as pd
from Connector.Connector import Connector


class Analyzer:
    def __init__(self, connector: Connector) -> None:
        self.connector = connector
        self.raw_data_path = "/tmp/hperf_tmp"

    def get_raw_dataframe(self) -> pd.DataFrame:
        """

        """
        local_raw_data_path = self.connector.get_tmp_file_path(self.raw_data_path)
        raw_data = pd.read_csv(local_raw_data_path,
                               header=None,
                               names=["timestamp", "unit", "value", "event"],
                               usecols=[0, 1, 2, 4])
        return raw_data
