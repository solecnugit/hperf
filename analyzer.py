import pandas as pd
import numpy as np
from connector import Connector
from event_group import EventGroup
import os
import logging


class Analyzer:
    """
    `Analyzer` is responsible for handling the raw performance data generated by `Profiler` and output the report of performance metrics. 
    """

    def __init__(self, connector: Connector, configs: dict, event_groups: EventGroup) -> None:
        """
        Constructor of `Analyzer`
        :param `connector`: an instance of `Connector` (`LocalConnector` or `RemoteConnector`)
        :param `configs`: a dict of parsed configurations (the member `configs` in `Controller`)
        :param `event_group`: an instance of `EventGroup`
        """
        self.logger = logging.getLogger("hperf")
        
        self.connector = connector
        self.configs = configs
        self.event_groups = event_groups
        
        self.raw_data_path = os.path.join(self.connector.get_test_dir_path(), "perf_result")

        # read the raw performance data file generated by `Profiler` and convert to DataFrame
        self.raw_data = pd.read_csv(self.raw_data_path,
                                    header=None,
                                    names=["timestamp", "unit",
                                           "value", "metric"],
                                    usecols=[0, 1, 2, 4])

    def get_aggregated_metrics(self, to_csv: bool = False) -> pd.DataFrame:
        """
        Aggregate raw performance data by timestamp and calculate performance metrics. 
        The results represent the overall performance of the workload during the measurement. 
        :param `to_csv`: whether to save as CSV file in the directory `.raw_data_path`
        """
        # rename 'unit' according to self.event_groups.events[..]['type']
        # e.g. 'duration_time' is a system-wide event, where in each timestamp there is only a value (attribute to CPU0)
        # timestamp | unit | value | metric         -> timestamp | unit   | value | metric
        # 1.0000    | CPU0 | 1.001 | duration_time     1.0000    | system | 1.001 | duration_time
        # 1.0000    | CPU0 | 12345 | cycles            1.0000    | CPU0   | 12345 | cycles
        # 1.0000    | CPU1 | 23456 | cycles            1.0000    | CPU1   | 23456 | cycles
        # ...
        for item in self.event_groups.events:
            if "type" in item:
                if item["type"] == "SYSTEM":
                    self.raw_data.loc[self.raw_data.metric == item["perf_name"], ["unit"]] = "SYSTEM"
                    system_event_flag = True
                elif item["type"] == "SOCKET":
                    # TODO: for some socket-wide events, such as events from SLC shared by a socket, perf will report its value 
                    # attributed to a CPU in this socket.
                    # e.g. SOCKET 0: CPU 0,2,4,6 ... SOCKET 1: CPU 1,3,5,7 ...
                    # timestamp | unit | value | metric
                    # 1.0000    | CPU0 | 12345 | uncore_cha_xxx    // CPU0 -> SOCKET 0
                    # 1.0000    | CPU1 | 23456 | uncore_cha_xxx    // CPU1 -> SOCKET 1
                    # 1.0000    | CPU0 | 23456 | cycles
                    # 1.0000    | CPU1 | 34567 | cycles
                    # ... 
                    self.raw_data.loc[self.raw_data.metric == item["perf_name"], ["unit"]] = "SOCKET0"
                    socket_event_flag = True
        
        # aggregate performance data for the whole measurement (aggregate 'timestamp')
        # timestamp | unit | value | metric -> unit | metric | result
        event_per_cpu = self.raw_data.groupby(["unit", "metric"]).agg(
            result=("value", np.sum)
        )

        # aggregate performance data for selected cpus (aggregate 'unit')
        if self.configs["cpu_list"] == 'all':
            scoped_event_per_cpu = event_per_cpu.reset_index()
            # unit | metric | result -> metric | result
            scoped_event_per_cpu = scoped_event_per_cpu.groupby(["metric"]).agg(
                result=("result", np.sum)
            ).reset_index()
        else:
            unit_list = [ f"CPU{i}" for i in self.configs["cpu_list"] ]
            # TODO: besides CPUs, there are also some system-wide and socket-wide events need to be added in 'unit_list'
            # e.g. CPU 0, 2, 4, 6 are specified, these 4 CPUs are belong to SOCKET0, so that SOCKET0 and SYSTEM should be added in 'unit_list'.
            if system_event_flag:
                unit_list.append("SYSTEM")
            scoped_event_per_cpu = event_per_cpu.loc[unit_list, :].reset_index()
            # unit | metric | result -> metric | result
            scoped_event_per_cpu = scoped_event_per_cpu.groupby(["metric"]).agg(
                result=("result", np.sum)
            ).reset_index()

        mapping_perf_name_to_name = {}
        for item in self.event_groups.events:
            mapping_perf_name_to_name[item["perf_name"]] = item["name"]
        
        scoped_event_per_cpu["metric"] = scoped_event_per_cpu["metric"].apply(
            lambda x: mapping_perf_name_to_name[x.split(":")[0]]
        )

        mapping_name_to_id = {}
        for item in self.event_groups.events:
            mapping_name_to_id[item["name"]] = item["id"]

        mapping_id_to_value = {}
        for item in self.event_groups.events:
            val = scoped_event_per_cpu[scoped_event_per_cpu["metric"]==item["name"]]["result"].iloc[0]
            mapping_id_to_value[f"e{item['id']}"] = val

        metric_results = {"metric": [], "result": []}

        for metric in self.event_groups.metrics:
            metric_results["metric"].append(metric["metric"])
            val = eval(metric["expression"], mapping_id_to_value)
            metric_results["result"].append(val)

        scoped_event_per_cpu = pd.concat([scoped_event_per_cpu, pd.DataFrame(metric_results)], ignore_index=True)

        if to_csv:
            results_path = os.path.join(self.connector.get_test_dir_path(), "results.csv")
            scoped_event_per_cpu.to_csv(results_path, header=True)
            self.logger.info(f"save DataFrame to CSV file: {results_path}")
        return scoped_event_per_cpu


