import pandas as pd
import numpy as np
from event_group import EventGroup
import os
import sys
import logging

from argparse import ArgumentParser, REMAINDER, Namespace
from typing import Sequence, Union

import subprocess


class AnalyzerParser:
    """
    `AnalyzerParser` is responsible for parsing and validating options and arguments passed from command line for 'hp-analyze'.
    """
    
    def __init__(self) -> None:
        """
        Constructor
        """
        self.logger = logging.getLogger("hp-analyze")
        
        # initialize `ArgumentParser`
        self.parser = ArgumentParser(prog="python hp-analyze.py",
                                     description="a data analyzer to process raw performance data")

        # options:
        #   [--test-dir]
        self.parser.add_argument("--test-dir",
                                 metavar="TEST_DIR_PATH",
                                 type=str,
                                 help="test directory which stores the profiling raw data (can be found from the output of hp-collect)")
        
        #   [-V/--version]
        self.parser.add_argument("-V", "--version",
                                 action="store_true",
                                 help="show the version and exit")
        
        #   [-v/--verbose]
        self.parser.add_argument("-v", "--verbose",
                                 action="store_true",
                                 help="increase output verbosity")
        
        #   [--cpu CPU]
        # hperf will conduct a system-wide profiling so that the list will not affect performance data collection
        # but will affect the aggregation of raw performance data.
        # If not specified, 'Analyzer' will aggregate performance data of all CPUs.
        self.parser.add_argument("-c", "--cpu",
                                 metavar="CPU_ID_LIST",
                                 type=str,
                                 default="all",
                                 help="specify the scope of performance data aggregation by passing a list of cpu ids.")
        
    def parse_args(self, argv: Sequence[str]) -> Namespace: 
        """
        Parse the command line options and return a Namespace. 
        
        :param `argv`: a list of arguments
        :return: a Namespace of configurations for this run
        :raises:
            `SystemExit`: for `-V` and `-h` options, it will print corresponding information and exit program 
            `ParserError`: if options and arguments are invalid 
        """
        argv_namespace: Namespace = self.parser.parse_args(argv)
        
        if argv_namespace.cpu != "all":
            try:
                cpus: list = self.__parse_cpu_list(argv_namespace.cpu)
                argv_namespace.cpu = cpus
            except Exception as e:
                print(e)
                sys.exit(-1)
        
        return argv_namespace
        
    def __parse_cpu_list(self, cpu_list: str) -> list:
        """
        Parse the string of cpu list with comma (`,`) and hyphen (`-`), and get the list of cpu ids. 
        
        e.g. if `cpu_list = '2,4-8'`, the method will return `[2, 4, 5, 6, 7, 8]`
        :param `cpu_list`: a string of cpu list
        :return: a list of cpu ids (the elements are non-negative and non-repetitive)
        :raises:
            `ParserError`: if the string of cpu list is invalid (e.g. negative cpu id)
        """
        cpu_ids = []
        cpu_id_slices = cpu_list.split(",")
        try:
            for item in cpu_id_slices:
                if item.find("-") == -1:
                    cpu_ids.append(int(item))
                else:
                    start_cpu_id = int(item.split("-")[0])
                    end_cpu_id = int(item.split("-")[1])
                    for i in range(start_cpu_id, end_cpu_id + 1):
                        cpu_ids.append(i)
        except ValueError:
            raise Exception(f"Invalid argument {cpu_list} for -c/--cpu option")

        # make the list non-repetitive
        reduced_cpu_ids = list(set(cpu_ids))
        reduced_cpu_ids.sort(key=cpu_ids.index)

        # check if all cpu ids are valid (non-negative)
        for cpu_id in reduced_cpu_ids:
            if cpu_id < 0:
                raise Exception(f"Invalid argument {cpu_list} for -c/--cpu option")
        return reduced_cpu_ids


class Connector:
    """
    `Connector` provides useful methods for executing commands or shell scripts on local SUT.
    """

    def __init__(self, test_dir: str) -> None:
        """
        Constructor of `LocalConnector`. 
        
        :param `test_dir`: path of the test directory for this run, which can be obtained by `Controller.get_test_dir_path()`
        """
        self.logger = logging.getLogger("hp-analyze")
        self.test_dir = test_dir

    def run_script(self, script: str, file_name: str) -> int:
        """
        Create and run a script on SUT, then wait for the script finished. 
        If the returned code is not equal to 0, it will generate a error log message. 
        
        :param `script`: a string of shell script
        :param `file_name`: file name of the shell script generated in test directory
        :return: the returned code of executing the shell script
        """
        script_path = self.__generate_script(script, file_name)
        self.logger.debug(f"run script: {script_path}")
        process = subprocess.Popen(
            ["bash", f"{script_path}"], stdout=subprocess.PIPE)
        ret_code = process.wait()
        self.logger.debug(f"script {script_path} finished with exit code {ret_code}")
        if ret_code != 0:
            self.logger.error(f"script {script_path} finished with exit code {ret_code}")
        return ret_code

    def __generate_script(self, script: str, file_name: str) -> str:
        """
        Generate a profiling script on SUT. 
        
        :param `script`: a string of shell script
        :param `file_name`: file name of the shell script generated in test directory
        :return: path of the script on the SUT
        """
        script_path = os.path.join(self.test_dir, file_name)
        with open(script_path, 'w') as f:
            f.write(script)
        self.logger.debug(f"generate script: {script_path}")
        return script_path

    def run_command(self, command_args: Union[Sequence[str], str]) -> str:
        """
        Run a command on SUT, then return the stdout output of executing the command. 
        
        **Note**: The output is decoded by 'utf-8'. 
        
        :param `command_args`: a sequence of program arguments, e.g. `["ls", "/home"]`, or a string of command, e.g. `"ls /home"`
        :return: stdout output
        """
        self.logger.debug(f"run command: {command_args}")
        
        if isinstance(command_args, list):
            output = subprocess.Popen(command_args, stdout=subprocess.PIPE).communicate()[0]
        else:
            output = subprocess.Popen(command_args, shell=True, stdout=subprocess.PIPE).communicate()[0]
        output = output.decode("utf-8")
        
        self.logger.debug(f"output: {output}")
        
        return output
    

class EventGroup:
    """
    'EventGroup' is responsible for detecting the architecture of the SUT 
    and generating the string of event groups, which can be accepted by '-e' options of 'perf'.
    """
    def __init__(self, isa: str, arch: str) -> None:
        """
        Constructor of 'EventGroup'.
        It will firstly determine the architecture of the SUT through 'Connector', 
        then it will dynamic import the pre-defined configurations in 'profiler/arch/<arch_name>.py'.
        
        :param isa: 
        :param arch: 
        """
        self.isa = isa
        self.arch = arch
        
        # dynamic import event configurations based on the architecture of the SUT
        arch_module = __import__(f"arch.{self.arch}", fromlist=[0])
        self.events: list = getattr(arch_module, "events")
        self.other_events: list = getattr(arch_module, "other_events")
        self.pinned_events: list = getattr(arch_module, "pinned_events")
        self.event_groups: list = getattr(arch_module, "event_groups")
        self.metrics: list = getattr(arch_module, "metrics")

        self.available_GP: int = getattr(arch_module, "available_GP")


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
        self.logger = logging.getLogger("hp-analyze")
        
        self.test_dir = test_dir
        
        analysis_dir = os.path.join(test_dir, "analysis_results")
        try:
            os.makedirs(analysis_dir)
        except:
            self.logger.error("fail to create the directory for the analysis results")
            sys.exit(-1)
        self.analysis_dir = analysis_dir
        
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

        # in every timestamp, aggregate performance data for selected CPUs (aggregate 'unit')
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
            hw_timeseries_path = os.path.join(self.analysis_dir, "hw_timeseries.csv")
            self.hw_timeseries.to_csv(hw_timeseries_path, header=True)
            self.logger.info(f"save timeseries DataFrame to CSV file: {hw_timeseries_path}")
            
            sw_timeseries_path = os.path.join(self.analysis_dir, "sw_timeseries.csv")
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
        
        hw_timeseries_plot_path = os.path.join(self.analysis_dir, "hw_timeseries.png")
        fig.savefig(hw_timeseries_plot_path)
        self.logger.info(f"timeseries figure saved in: {hw_timeseries_plot_path}")
        
        axes = self.sw_timeseries.plot(x="timestamp", 
                                       y=sar_metrics,
                                       subplots=True,
                                       figsize=(10, 2 * len(sar_metrics)))
        fig = axes[0].get_figure()
        
        sw_timeseries_plot_path = os.path.join(self.analysis_dir, "sw_timeseries.png")
        fig.savefig(sw_timeseries_plot_path)
        self.logger.info(f"timeseries figure saved in: {sw_timeseries_plot_path}")

    def get_aggregated_metrics(self, to_csv: bool = False) -> pd.DataFrame:
        """
        """
        # use timeseries to get aggregated metrics.  
        # Hardware metrics
        # for events, get the sum of values in different timestamps; for metrics, get the average of values in different timestamps. 
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
            aggregated_metrics_path = os.path.join(self.analysis_dir, "aggregated_metrics.csv")
            self.aggregated_metrics.to_csv(aggregated_metrics_path, header=True)
            self.logger.info(f"save aggregated metrics DataFrame to CSV file: {aggregated_metrics_path}")
        return self.aggregated_metrics

"""
The entrance of hperf. Users can invoke hperf from command line, like:
```
$ python hperf.py [options] <command>
```
refer to README.md for supported options
"""
if __name__ == "__main__":
    parser = AnalyzerParser()
    argv_namespace = parser.parse_args(sys.argv[1:])
    # Note: if `ArgumentParser` detect `-h`/`--help` option, 
    # it will print help message and raise a `SystemExit` exception to exit the program.
    
    # validate the options and arguments
    
    # check `-V`/`--version` option
    # if it is declared, print the version and exit
    if argv_namespace.version:
        with open("./VERSION") as f:
            print(f.read())
        sys.exit(0)
    
    # step 0. check verbosity and initialize `Logger`
    # Note: Since `Logger` follows singleton pattern,
    # it is unnecessary to pass the reference of the instance of `Logger` to other classes through their constructor.
    # When we need to log records, use the method `logging.getLogger(<name>)` provided by module logging to get the instance of `Logger`,
    # where it will get the very same instance of `Logger` as long as the `<name>` is the same.
    logger: logging.Logger = logging.getLogger("hp-analyze")
    logger.setLevel(logging.DEBUG)
    __formatter = logging.Formatter("%(asctime)-15s %(levelname)-8s %(message)s")
    __handler_stream = logging.StreamHandler()
    __handler_stream.setFormatter(__formatter)
    if argv_namespace.verbose:
        __handler_stream.setLevel(logging.DEBUG)
    else:
        __handler_stream.setLevel(logging.INFO)
    logger.addHandler(__handler_stream)
    
    # step 1. check the test directory
    try:
        if argv_namespace.test_dir:
            test_dir = argv_namespace.test_dir
            if os.path.exists(test_dir):
                filenames = ["perf_result", "cpu_topo", "sar_d", "sar_n_dev", "sar_r", "sar_u", "isa", "arch"]
                for filename in filenames:
                    file_path = os.path.join(test_dir, filename)
                    if not os.path.exists(file_path):
                        raise Exception(f"file {filename} does not exist in the test directory.")
            else:
                raise Exception("test directory does not exist.")
        else:
            raise Exception("test directory is not specified.")
    except Exception as e:
        logger.error(e)
        sys.exit(-1)
    
    logger.info(f"test directory specified: {argv_namespace.test_dir}")
    
    # step 2. get the event group
    with open(os.path.join(argv_namespace.test_dir, "isa"), 'r') as f:
        isa = f.read().strip()
    with open(os.path.join(argv_namespace.test_dir, "arch"), 'r') as f:
        arch = f.read().strip()
    
    logger.info(f"SUT information: {isa}, {arch}")
    
    event_groups = EventGroup(isa, arch)
    
    analyzer = Analyzer(test_dir=argv_namespace.test_dir,
                        configs={"cpu_list": argv_namespace.cpu},
                        event_groups=event_groups)
    
    analyzer.analyze()
    
    hw_timeseries, sw_timeseries = analyzer.get_timeseries(to_csv=True)
    print(hw_timeseries)
    print(sw_timeseries)
    print(analyzer.get_aggregated_metrics(to_csv=True))
    analyzer.get_timeseries_plot()