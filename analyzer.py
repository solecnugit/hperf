import pandas as pd
import numpy as np
from event_group import EventGroup
import os
import logging


class Analyzer:
    """
    `Analyzer` is responsible for handling the raw performance data generated by `Profiler` and output the report of performance metrics. 
    """

    def __init__(self, test_dir: str, configs: dict, event_groups: EventGroup) -> None:
        """
        Constructor of `Analyzer`
        :param `test_dir_path`: a string of the path of test directory, 
        which can be obtained by `Connector.get_test_dir_path()`
        :param `configs`: a dict of parsed configurations (the member `configs` in `Controller`)
        :param `event_group`: an instance of `EventGroup`
        """
        self.logger = logging.getLogger("hperf")
        
        self.test_dir = test_dir
        self.configs = configs
        self.event_groups = event_groups

        self.cpu_topo: pd.DataFrame = None    # for cpu topo (mapping of cpu id and socket id)
        
        self.hw_timeseries: pd.DataFrame = None    # for perf timeseries result
        self.sw_timeseries: pd.DataFrame = None    # for sar timeseries result
        
        self.aggregated_metrics: pd.DataFrame = None    # for aggregated results, hw event counts, metrics, sw avg. util.

    def __analyze_cpu_topo(self):
        """
        """
        self.cpu_topo = pd.read_csv(os.path.join(self.test_dir, "cpu_topo"),
                                    sep="\t",
                                    header=None,
                                    names=["unit", "socket"],
                                    usecols=[0, 1])

    def analyze(self):
        """
        
        """
        self.__analyze_cpu_topo()

        # read the raw performance data file generated by `Profiler` and convert to DataFrame
        perf_raw_data = pd.read_csv(os.path.join(self.test_dir, "perf_result"),
                                    sep="\t",
                                    header=None, 
                                    names=["timestamp", "unit", "value", "metric"], 
                                    usecols=[0, 1, 2, 4])
        sar_u_raw_data = pd.read_csv(os.path.join(self.test_dir, "sar_u"), header=0)    # CPU util. ["%user", "%system"]
        sar_r_raw_data = pd.read_csv(os.path.join(self.test_dir, "sar_r"), header=0)    # mem. util. ["%memused"]
        sar_n_dev_raw_data = pd.read_csv(os.path.join(self.test_dir, "sar_n_dev"), header=0)    # network util ["%ifutil"]
        sar_d_raw_data = pd.read_csv(os.path.join(self.test_dir, "sar_d"), header=0)    # storage util. ["%util"]
        
        # ------------ for perf data --------------
        # rename 'unit' according to self.event_groups.events[..]['type']
        # e.g. 'duration_time' is a system-wide event, where in each timestamp there is only a value (attribute to CPU0)
        # timestamp | unit | value | metric         -> timestamp | unit   | value | metric
        # 1.0000    | CPU0 | 1.001 | duration_time     1.0000    | system | 1.001 | duration_time
        # 1.0000    | CPU0 | 12345 | cycles            1.0000    | CPU0   | 12345 | cycles
        # 1.0000    | CPU1 | 23456 | cycles            1.0000    | CPU1   | 23456 | cycles
        # ...
        system_event_flag = False
        socket_event_flag = False

        def cpu2socket(x):
            cpu_id = int(x["unit"][3:])
            return "SOCKET" + str(self.cpu_topo.loc[self.cpu_topo.unit == cpu_id]["socket"].values[0])

        for item in self.event_groups.events:
            if "type" in item:
                if item["type"] == "SYSTEM":
                    perf_raw_data.loc[perf_raw_data.metric == item["perf_name"], ["unit"]] = "SYSTEM"
                    system_event_flag = True
                elif item["type"] == "SOCKET":
                    # TODO: for some socket-wide events, such as events from SLC shared by a socket, perf will report its value 
                    # attributed to a CPU in this socket.
                    # e.g. SOCKET 0: CPU 0-15, 32-47 ... SOCKET 1: CPU 16-31, 48-63 ...
                    # timestamp | unit  | value | metric
                    # 1.0000    | CPU0  | 12345 | uncore_cha_xxx    // CPU0 -> SOCKET 0
                    # 1.0000    | CPU16 | 23456 | uncore_cha_xxx    // CPU16 -> SOCKET 1
                    # 1.0000    | CPU0  | 23456 | cycles
                    # 1.0000    | CPU1  | 34567 | cycles
                    # ... 
                    # -------------- faulty --------------
                    perf_raw_data.loc[perf_raw_data.metric == item["perf_name"], ["unit"]] \
                        = perf_raw_data.loc[perf_raw_data.metric == item["perf_name"], ["unit"]].apply(cpu2socket, axis=1)
                    socket_event_flag = True
                    # -------------- faulty --------------

        # in every timestamp, aggregate performance data for selected cpus (aggregate 'unit')
        # timestamp | unit | value | metric -> timestamp | value=sum(value) | metric
        if self.configs["cpu_list"] == 'all':
            scoped_raw_data = perf_raw_data.groupby(["timestamp", "metric"]).agg({
                "value": "sum"
                }).reset_index()
        else:
            unit_list = [ f"CPU{i}" for i in self.configs["cpu_list"] ]
            # besides CPUs, there are also some system-wide and socket-wide events need to be added in 'unit_list'
            # e.g. CPU 0, 2, 4, 6 are specified, these 4 CPUs are belong to SOCKET0, so that SOCKET0 and SYSTEM should be added in 'unit_list'.
            if system_event_flag:
                unit_list.append("SYSTEM")
            if socket_event_flag:
                for i in self.configs["cpu_list"]:
                    socket = f'SOCKET{self.cpu_topo.loc[self.cpu_topo.unit == i]["socket"].values[0]}'
                    if socket not in unit_list:
                        unit_list.append(socket)
            self.logger.debug(f"Unit list: {unit_list}")

            scoped_raw_data = perf_raw_data[perf_raw_data["unit"].isin(unit_list)].groupby(["timestamp", "metric"]).agg(
                value=("value", np.sum)
            ).reset_index()

        # rename event names used in perf by the generic event names defined by hperf
        # e.g. 
        # timestamp | value | metric -> timestamp | value | metric
        # 1.0000    | 98765 | r08d1     1.0000    | 98765 | L1 CACHE MISSES
        # 1.0000    | 87654 | r10d1     1.0000    | 87654 | L2 CACHE MISSES
        # ...
        mapping_perf_name_to_name = {}
        mapping_name_to_id = {}
        for item in self.event_groups.events:
            mapping_perf_name_to_name[item["perf_name"]] = item["name"]
            mapping_name_to_id[item["name"]] = item["id"]

        scoped_raw_data["metric"] = scoped_raw_data["metric"].apply(
            lambda x: mapping_perf_name_to_name[x.split(":")[0]]
        )

        perf_timeseries = pd.DataFrame()    # for final results
        # timestamp | <event> | ... | <event> | <metric> | ... | <metric>

        timestamps = scoped_raw_data.groupby(["timestamp"]).groups.keys()    # get all timestamps

        for t in timestamps:
            metric_results = {}
            metric_results["timestamp"] = t    # col. 0
            
            mapping_id_to_value = {}
            for item in self.event_groups.events:
                val = scoped_raw_data.query(f'metric=="{item["name"]}" & timestamp=={t}')["value"].iloc[0]
                metric_results[item["name"]] = val    # col. event count
                mapping_id_to_value[f"e{item['id']}"] = val
                
            for item in self.event_groups.metrics:
                val = eval(item["expression"], mapping_id_to_value)
                metric_results[item["metric"]] = val    # col. metric result
            
            perf_timeseries = pd.concat([perf_timeseries, pd.DataFrame(metric_results, index=[0])], ignore_index=True)
        
        self.hw_timeseries = perf_timeseries
        
        # ------------ for sar data --------------
        sar_u_timeseries = sar_u_raw_data[["timestamp", r"%user", r"%system"]].groupby(["timestamp"]).agg(
            CPU_UTIL_USER=(r"%user", np.average),
            CPU_UTIL_SYS=(r"%system", np.average)
        ).reset_index()    # CPU util. (user and system)
        sar_r_timeseries = sar_r_raw_data[["timestamp", r"%memused"]].groupby(["timestamp"]).agg(
            MEM_UTIL=(r"%memused", np.average)
        ).reset_index().drop("timestamp", axis=1)    # Mem. util.
        sar_n_dev_timeseries = sar_n_dev_raw_data[["timestamp", r"%ifutil"]].groupby(["timestamp"]).agg(
            NET_UTIL=(r"%ifutil", np.average)
        ).reset_index().drop("timestamp", axis=1)    # Network util.
        sar_d_timeseries = sar_d_raw_data[["timestamp", r"%util"]].groupby(["timestamp"]).agg(
            STORAGE_UTIL=(r"%util", np.average)
        ).reset_index().drop("timestamp", axis=1)
        
        self.sw_timeseries = pd.concat([sar_u_timeseries, sar_r_timeseries, sar_n_dev_timeseries, sar_d_timeseries], axis=1)        

    def get_timeseries(self, to_csv: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        """
        if to_csv:
            hw_timeseries_path = os.path.join(self.test_dir, "hw_timeseries.csv")
            self.hw_timeseries.to_csv(hw_timeseries_path, header=True)
            self.logger.info(f"save timeseries DataFrame to CSV file: {hw_timeseries_path}")
            
            sw_timeseries_path = os.path.join(self.test_dir, "sw_timeseries.csv")
            self.sw_timeseries.to_csv(sw_timeseries_path, header=True)
            self.logger.info(f"save timeseries DataFrame to CSV file: {sw_timeseries_path}")
        
        return self.hw_timeseries, self.sw_timeseries

    def get_timeseries_plot(self):
        """
        """
        perf_metrics = [ item["metric"] for item in self.event_groups.metrics ]
        sar_metrics = ["CPU_UTIL_USER", "CPU_UTIL_SYS", "MEM_UTIL", "NET_UTIL", "STORAGE_UTIL"]
        
        axes = self.hw_timeseries.plot(x="timestamp", 
                                       y=perf_metrics,
                                       subplots=True,
                                       figsize=(10, 2 * len(perf_metrics)))
        fig = axes[0].get_figure()
        
        hw_timeseries_plot_path = os.path.join(self.test_dir, "hw_timeseries.png")
        fig.savefig(hw_timeseries_plot_path)
        self.logger.info(f"timeseries figure saved in: {hw_timeseries_plot_path}")
        
        axes = self.sw_timeseries.plot(x="timestamp", 
                                       y=sar_metrics,
                                       subplots=True,
                                       figsize=(10, 2 * len(sar_metrics)))
        fig = axes[0].get_figure()
        
        sw_timeseries_plot_path = os.path.join(self.test_dir, "sw_timeseries.png")
        fig.savefig(sw_timeseries_plot_path)
        self.logger.info(f"timeseries figure saved in: {sw_timeseries_plot_path}")

    def get_aggregated_metrics(self, to_csv: bool = False) -> pd.DataFrame:
        """
        """
        # use timeseries to get aggregated metrics.  
        # Hardware metrics
        # for events, get the sum of values in differenet timestamps; for metrics, get the average of values in different timestamps. 
        metric_results = {}
        for item in self.event_groups.events:
            sum = self.hw_timeseries[item["name"]].sum()
            metric_results[item["name"]] = sum
        for item in self.event_groups.metrics:
            avg = self.hw_timeseries[item["metric"]].mean()
            metric_results[item["metric"]] = avg
            
        # Software metrics
        for col_index, (col, series) in enumerate(self.sw_timeseries.items()):
            if col_index != 0:
                avg = series.mean()
                metric_results[col] = avg

        self.aggregated_metrics = pd.DataFrame(metric_results, index=[0])

        if to_csv:
            aggregated_metrics_path = os.path.join(self.test_dir, "aggregated_metrics.csv")
            self.aggregated_metrics.to_csv(aggregated_metrics_path, header=True)
            self.logger.info(f"save aggregated metrics DataFrame to CSV file: {aggregated_metrics_path}")
        return self.aggregated_metrics
