import logging
import os
import sys
from datetime import datetime
import re
from shutil import copyfile
from typing import Sequence, Union

import logging
from argparse import ArgumentParser, REMAINDER

import subprocess

from concurrent.futures import ThreadPoolExecutor, as_completed
from string import Template


class OptParser:
    """
    `OptParser` is responsible for parsing and validating options and arguments passed from command line. 
    It will create a dict containing all configurations may used by other modules such as `Connector`, `Profiler` and `Analyzer`, etc. 
    """

    def __init__(self) -> None:
        """
        Constructor of `OptParser`
        """
        self.logger = logging.getLogger("hperf")

        # initialize `ArgumentParser`
        self.parser = ArgumentParser(prog="python hperf.py",
                                     description="hperf: an easy-to-use microarchitecture performance data collector")
        # [1] positional arguments:
        # COMMAND
        self.parser.add_argument("command",
                                 # if option 'nargs' not set, command with arguments will not be accepted.
                                 nargs=REMAINDER,
                                 metavar="COMMAND",
                                 help="workload command you can specify in a shell")

        # [2] required options:
        # TODO: some required options can be added in future

        # [3] optional options:
        #   [-V/--version]
        self.parser.add_argument("-V", "--version",
                                 action="store_true",
                                 help="show the version and exit")
        #   [--tmp-dir]
        self.parser.add_argument("--tmp-dir",
                                 metavar="TMP_DIR_PATH",
                                 type=str,
                                 default="/tmp/hperf/",
                                 help="temporary directory to store profiling results and logs (default '/tmp/hperf/')")
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
        #   [--time SECOND]
        # TODO: this option is currently used for profiling by sar, because sar needs to specify the time of profiling.
        # the profiling time of sar should equal to the time of workload running, 
        # however, we are unable to know the time of workload running in advance.
        # so this option is a workaround. users should set this value to the estimated workload running time.
        self.parser.add_argument("-t", "--time",
                                 metavar="SECOND",
                                 type=int,
                                 default=10,
                                 help="time of profiling")

    def parse_args(self, argv: Sequence[str]) -> dict:
        """
        Parse and validate the options and arguments passed from command line and return an instance of `Connector`. 
        
        :param `argv`: a list of arguments
        :return: a dict of configurations for this run
        :raises:
            `SystemExit`: for `-V` and `-h` options, it will print corresponding information and exit program 
            `ParserError`: if options and arguments are invalid 
        """
        configs = {}

        args = self.parser.parse_args(argv)
        # Note: if `ArgumentParser` detect `-h`/`--help` option, 
        # it will print help message and raise a `SystemExit` exception to exit the program.

        # check `-V`/`--version` option
        # if it is declared, print the version and exit
        if args.version:
            with open("./VERSION") as f:
                print(f.read())
            sys.exit(0)
        
        # step 0. check verbosity
        if args.verbose:
            configs["verbose"] = True

        # step 1. workload command
        # if command is empty, raise an exception and exit the program
        if args.command:
            configs["command"] = " ".join(args.command)
        else:
            raise Exception("Workload is not specified.")

        # step 3. scope of performance data aggregation
        if args.cpu != "all":
            configs["cpu_list"] = self.__parse_cpu_list(args.cpu)
        else:
            configs["cpu_list"] = "all"

        # step 4. temporary directory
        if args.tmp_dir:
            configs["tmp_dir"] = args.tmp_dir
            
        # step 5. profiling time
        if args.time:
            configs["time"] = args.time

        self.logger.debug(f"parsed configurations: {configs}")

        return configs

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
        self.logger = logging.getLogger("hperf")
        self.test_dir = test_dir

    def run_script(self, script: str, file_name: str) -> int:
        """
        Create and run a script on SUT, then wait for the script finished. 
        If the returned code is not equal to 0, it will generate a debug log message. 
        
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
        if isinstance(command_args, list):
            output = subprocess.Popen(command_args, stdout=subprocess.PIPE).communicate()[0]
        else:
            output = subprocess.Popen(command_args, shell=True, stdout=subprocess.PIPE).communicate()[0]
        output = output.decode("utf-8")
        return output


class EventGroup:
    """
    'EventGroup' is responsible for detecting the architecture of the SUT 
    and generating the string of event groups, which can be accepted by '-e' options of 'perf'.
    """
    def __init__(self, connector: Connector = None) -> None:
        """
        Constructor of 'EventGroup'.
        It will firstly determine the architecture of the SUT through 'Connector', 
        then it will dynamic import the pre-defined configurations in 'profiler/arch/<arch_name>.py'.
        :param connector: an instance of 'Connector' ('LocalConnector' or 'RemoteConnector')
        """
        self.logger = logging.getLogger("hperf")
        
        if connector:
            self.connector = connector
            
            self.isa = self.__get_isa()
            
            self.arch = self.__get_architecture()

            # dynamic import event configurations based on the architecture of the SUT
            arch_module = __import__(f"arch.{self.arch}", fromlist=[0])
            self.events: list = getattr(arch_module, "events")
            self.other_events: list = getattr(arch_module, "other_events")
            self.pinned_events: list = getattr(arch_module, "pinned_events")
            self.event_groups: list = getattr(arch_module, "event_groups")
            self.metrics: list = getattr(arch_module, "metrics")

            self.available_GP: int = getattr(arch_module, "available_GP")

            self.__optimize_event_groups()

    @classmethod
    def get_event_group(cls, isa: str, arch: str):
        """
        Constructor of 'EventGroup', without Connector.
        For unit test.
        """
        my_event_group = cls()
        my_event_group.logger = logging.getLogger("hperf")

        my_event_group.isa = isa
        my_event_group.arch = arch

        # dynamic import event configurations based on the architecture of the SUT
        arch_module = __import__(f"arch.{my_event_group.arch}", fromlist=[0])
        my_event_group.events = getattr(arch_module, "events")
        my_event_group.other_events = getattr(arch_module, "other_events")
        my_event_group.pinned_events = getattr(arch_module, "pinned_events")
        my_event_group.event_groups = getattr(arch_module, "event_groups")
        my_event_group.metrics = getattr(arch_module, "metrics")

        my_event_group.available_GP = getattr(arch_module, "available_GP")

        return my_event_group

    def __optimize_event_groups(self):
        """
        Adaptive Grouping
        """
        filtered_event_groups = []

        not_multiplexing_events = self.other_events + self.pinned_events

        for event_group in self.event_groups:
            filtered_event_group = set()
            for event in event_group: 
                if event not in not_multiplexing_events:
                    filtered_event_group.add(event)
            if len(filtered_event_group) != 0:
                filtered_event_groups.append(filtered_event_group)
        
        while True:
            if len(filtered_event_groups) <= 1:
                break

            # Find G_i
            g_size = 1000
            for i, g in enumerate(filtered_event_groups):
                if len(g) < g_size:
                    g_size = len(g)
                    g_i_index = i
                    g_i = g
            del filtered_event_groups[g_i_index]

            # Find G_j
            g_size = 1000
            for i, g in enumerate(filtered_event_groups):
                g_merged = g.union(g_i)
                if len(g_merged) < g_size:
                    g_size = len(g_merged)
                    g_j_index = i
                    g_j = g
            del filtered_event_groups[g_j_index]

            # Merge G_i and G_j
            g_merged = g_j.union(g_i)
            
            if len(g_merged) <= self.available_GP:
                filtered_event_groups.insert(0, g_merged)
            else:
                filtered_event_groups.insert(g_j_index, g_j)
                filtered_event_groups.insert(g_i_index, g_i)
                break
        
        self.event_groups = filtered_event_groups
    
    def __get_isa(self) -> str:
        """
        Determine the Instruction Set Architecture (ISA) of the SUT by analyzing the output of 'lscpu' command.
        :return: a string of ISA, such as 'x86_64', 'aarch64', etc.
        """
        isa = self.connector.run_command("lscpu | grep 'Architecture:' | awk -F: '{print $2}'").strip()
        self.logger.debug(f"ISA: {isa}")
        return isa
    
    def __get_architecture(self) -> str:
        """
        Determine the architecture of the SUT by analyzing the output of 'lscpu' command.
        :return: a string of architecture
        """
        processor = self.connector.run_command("lscpu | grep 'Model name:' | awk -F: '{print $2}'").strip()
        self.logger.debug(f"processor model: {processor}")
        # TODO: the following logic is simple, it should be refined in future
        if self.isa == "x86_64":
            if processor.find("Intel") != -1:
            # determine the microarchitecture code of intel processor by lscpu 'Model'
                model = self.connector.run_command("lscpu | grep 'Model:' | awk -F: '{print $2}'").strip()
                try:
                    model = int(model)
                    if model == 106:
                        arch = "intel_icelake"
                    elif model == 85:
                        arch = "intel_cascadelake"
                    else:
                        arch = "intel_cascadelake"
                except ValueError:
                    self.logger.warning(f"unrecognized Intel processor model: {model}, assumed as intel_cascadelake")
                    arch = "intel_cascadelake"
            elif processor.find("AMD") != -1:
                arch = "amd"
                self.logger.error(f"currently hperf does not support AMD processor: {model}")
            else:
                self.logger.error(f"unrecognized processor model: {model}")
                exit(-1)
        elif self.isa == "aarch64":
            if processor.find("Kunpeng") != -1:
                arch = "arm_kunpeng"
            else:
                arch = "arm"
        else:
            self.logger.error(f"unsupported ISA: {self.isa}")
            exit(-1)
        self.logger.debug(f"architecture model: {arch}")
        return arch
    
    def get_event_groups_str(self) -> str:
        """
        Get the string of event groups, which can be accepted by '-e' options of 'perf'.
        """
        def get_event_by_id(id: int) -> str:
            """
            Traverse the list of events and find the 'perf_name' by 'id'.
            """
            for item in self.events:
                if item["id"] == id:
                    return item["perf_name"]
            return ""

        event_groups_str = ""
        for other_event_id in self.other_events:
            event_groups_str += (get_event_by_id(other_event_id) + ",")
        for pinned_event_id in self.pinned_events:
            event_groups_str += (get_event_by_id(pinned_event_id) + ":D" + ",")
        for group in self.event_groups:
            event_groups_str += "'{"
            for event_id in group:
                event_groups_str += (get_event_by_id(event_id) + ",")
            event_groups_str = event_groups_str[:-1]
            event_groups_str += "}',"
        event_groups_str = event_groups_str[:-1]

        self.logger.debug(f"generated string of event groups: {event_groups_str}")
        return event_groups_str


class HperfTemplete(Template):
    delimiter = r"%%"


class Profiler:
    """
    `Profiler` is responsible for collecting raw microarchitecture performance data. 
    It will collect raw performance data by other profilers (such as perf, sar, etc.) on SUTs through `Connector`. 
    """
    def __init__(self, connector: Connector, configs: dict, event_groups: EventGroup):
        """
        Constructor of `Profiler`
        
        :param `connector`: an instance of `Connector` (`LocalConnector` or `RemoteConnector`)
        :param `configs`: a dict of parsed configurations by `Parser`
        :param `event_group`: an instance of 'EventGroup'
        """
        self.logger = logging.getLogger("hperf")
        
        self.connector: Connector = connector
        self.configs: dict = configs
        self.event_groups: EventGroup = event_groups

    def profile(self):
        """
        Generate and execute profiling script on SUT. 
        
        :raises:
            `ConnectorError`: for `RemoteConnector`, 
            if fail to generate or execute script on remote SUT, or fail to pull raw performance data from remote SUT. 
            `ProfilerError`: if the returned code of executing script does not equal to 0. 
        """
        self.logger.info("get static information of SUT")
        self.get_cpu_info()
        self.get_cpu_topo()
        
        perf_script = self.__get_perf_script()
        sar_script = self.__get_sar_script()

        self.logger.info("start profiling")
        
        abnormal_flag = False
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            perf_task = executor.submit(self.connector.run_script, perf_script, "perf.sh")
            sar_task = executor.submit(self.connector.run_script, sar_script, "sar.sh")
            
            tasks = [perf_task, sar_task]
            task_names = ["perf", "sar"]

            for task_id, future in enumerate(as_completed(tasks)):
                ret_code = future.result()
                if ret_code != 0:
                    self.logger.error(f"Execution error: {task_names[task_id]}")
                    abnormal_flag = True
        
        if abnormal_flag:
            raise Exception("Executing profiling script on the SUT failed.")
        
        self.logger.info("end profiling")

    def sanity_check(self) -> bool:
        """
        Check the environment on the SUT for profiling.
        Since the collection of performance data requires exclusive usage of PMCs, 
        it is necessary to check if there is any other profiler (such as VTune, perf, etc.) is already running. 
        Specifically, for x86_64 platform, the NMI watchdog will occupy a generic PMC, 
        so that it will also be checked.
        
        :return: if the SUT passes the sanity check, it will return `True`, 
        else it will return `False` and record the information through `Logger`.
        :raises:
            `ConnectorError`: for `RemoteConnector`, if fail to execute command for sanity check on remote SUT.
        """
        sanity_check_flag = True

        # 1. check if there is any other profiler (such as VTune, perf, etc.) is already running
        # TODO: add more pattern of profilers may interfere measurement
        process_check_list = [
            "linux-tools/.*/perf", 
            "/intel/oneapi/vtune/.*/emon"
        ]    # process command pattern
        for process in process_check_list:
            process_check_cmd = f"ps -ef | awk '{{print $8}}' | grep {process}"
            output = self.connector.run_command(process_check_cmd)    # may raise `ConnectorError`
            if output:
                process_cmd = output
                self.logger.warning(f"sanity check: process may interfere measurement exists. {process_cmd}")
                sanity_check_flag = False
        # 2. for x86_64 platform, check the NMI watchdog
        if self.event_groups.isa == "x86_64":
            nmi_watchdog_check_cmd = ["cat", "/proc/sys/kernel/nmi_watchdog"]
            output = self.connector.run_command(nmi_watchdog_check_cmd)    # may raise `ConnectorError`
            if int(output) == 1:
                self.logger.warning(f"sanity check: NMI watchdog is enabled.")
                sanity_check_flag = False

        return sanity_check_flag
    
    def get_cpu_info(self):
        """
        """
        output_dir = self.connector.test_dir
        self.connector.run_command("lscpu > " + f"{output_dir}/cpu_info")
    
    def get_cpu_topo(self):
        """
        """
        output_dir = self.connector.test_dir

        if self.event_groups.isa == "x86_64":
            # output format:
            # processor | socket | core id in socket
            # 0         | 0      | 0
            # 1         | 0      | 1
            # 2         | 0      | 2
            # ...
            get_topo_cmd = r"awk -F: 'BEGIN{i=0;j=0;k=0}" \
            r"/processor/{cpu[i]=$2;i++}" \
            r"/physical id/{skt[j]=$2;j++}" \
            r"/core id/{phy[k]=$2;k++}" \
            r'''END{OFS="\t";for(key in cpu)print cpu[key],skt[key],phy[key]}' '''\
            r"/proc/cpuinfo > " + f"{output_dir}/cpu_topo"
        elif self.event_groups.isa == "aarch64":
            # TODO: getting topo for arm is undone
            # output format:
            # processor | socket
            # 0         | 0
            # 1         | 0
            # 2         | 0
            # ...
            get_topo_cmd = r"awk -F: 'BEGIN{i=0}" \
            r"/processor/{cpu[i]=$2;i++}" \
            r'''END{OFS="\t";for(key in cpu)print cpu[key],0}' '''\
            r"/proc/cpuinfo > " + f"{output_dir}/cpu_topo"
        else:
            raise Exception("Unsupported ISA.")
        
        self.connector.run_command(get_topo_cmd)
    
    def __get_perf_script(self) -> str:
        """
        Based on the parsed configuration, generate the string of shell script for profiling by perf.
        
        :return: a string of shell script for profiling
        """
        perf_dir = self.connector.test_dir
        
        perf_parameters = {
            "HPERF_PERF_DIR": perf_dir,
            "HPERF_EVENT_GROUPS_STR": self.event_groups.get_event_groups_str(),
            "HPERF_COMMAND": self.configs["command"]
        }
        
        with open("./tools/perf_template", mode="r", encoding="utf-8") as f:
            script = f.read()
            
        perf_template = HperfTemplete(script)
        
        script = perf_template.safe_substitute(perf_parameters)

        self.logger.debug("profiling script by perf: \n" + script)
        return script
    
    def __get_sar_script(self) -> str:
        """
        Based on the parsed configuration, generate the string of shell script for profiling by sar.
        :return: a string of shell script for profiling
        """
        sar_dir = self.connector.test_dir
        
        if self.configs["cpu_list"] == "all":
            p_str = ""
        else:
            p_str = "-P " + ",".join([ str(item) for item in self.configs["cpu_list"]])
            
        sar_parameters = {
            "HPERF_SAR_DIR": sar_dir,
            "HPERF_P_STR": p_str,
            "HPERF_SAR_TIME": self.configs["time"]
        }
        
        with open("./tools/sar_template", mode="r", encoding="utf-8") as f:
            script = f.read()
            
        sar_template = HperfTemplete(script)
        
        script = sar_template.safe_substitute(sar_parameters)

        self.logger.debug("profiling script by sar: \n" + script)
        return script


class Controller:
    """
    `Controller` is responsible for the whole process control of hperf. 
    Beside this, it also responsible for unified exception handling and logging. 
    Users can conduct profiling for workload by calling `hperf()` method.
    """

    def __init__(self, argv: Sequence[str]):
        """
        Constructor of `Controller`.
        
        :param `argv`: Options and arguments passed from command line when invoke `hperf`. 
        Usually, it should be `sys.argv[1:]` (since `sys.argv[0]` is `hperf.py`). 
        """
        self.__argv = argv    # (private) the original command line options and parameters

        self.configs = {}    # a dict contains parsed configurations for the following steps
        self.parser = OptParser()

        self.connector: Connector = None
        self.profiler: Profiler = None
        self.event_groups: EventGroup = None

        # Initialize `Logger`
        # **Note**: Since `Logger` follows singleton pattern,
        # it is unnecessary to pass the reference of the instance of `Logger` to other classes through their constructor.
        # When we need to log records, use the method `logging.getLogger(<name>)` provided by module logging to get the instance of `Logger`,
        # where it will get the very same instance of `Logger` as long as the `<name>` is the same.
        self.logger: logging.Logger = logging.getLogger("hperf")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)-15s %(levelname)-8s %(message)s")

        # Logs will output to both console and file
        # [1] For console output of logs
        self.__handler_stream = logging.StreamHandler()
        self.__handler_stream.setFormatter(formatter)
        self.__handler_stream.setLevel(logging.INFO)    # logs with level above INFO will be printed to console by default
        self.logger.addHandler(self.__handler_stream)

        # [2] For file output of logs
        self.log_file_path = "/tmp/hperf/hperf.log"
        try:
            os.makedirs("/tmp/hperf/", exist_ok=True)
            self.__handler_file = logging.FileHandler(self.log_file_path, "w")
        except Exception:
            print("Initialization failure.")
            sys.exit(-1)
        self.__handler_file.setLevel(logging.DEBUG)    # all logs will be written to the log file by default
        self.__handler_file.setFormatter(formatter)
        self.logger.addHandler(self.__handler_file)

        # SEE: `Controller.__prework()`
        self.tmp_dir: str = ""    # user-specified temporary directory for saving files for different runs
        self.test_id: str = ""    # a sub-directory in temporary directory for a single run

    def hperf(self):
        """
        This method covers the whole process of profiling.
        Call this method to start profiling for workloads.
        """
        try:
            # step 1.
            self.__parse()    # may raise `SystemExit` or `ParserError`
            # step 2.
            self.__prework()
            # step 3.
            self.__profile()    # may raise `SystemExit`, `ConnectorError` or `ProfilerError`
        # `Controller` is responsible for unified exceptional handling ... 
        except SystemExit as e:
            self.__system_exit_handler(e)
        except KeyboardInterrupt:
            self.__keyboard_interrupt_handler()
        except Exception as e:
            self.__exception_handler(e)
        finally: 
            if self.connector:
                self.__save_log_file()

    def __parse(self):
        """
        Parse and validate the original command line options and arguments (`.argv`) 
        and then get the configuration dict (`.configs`). 
        
        If `-v`/`--verbose` option is declared, the threshold of log level will change. 
        
        :raises:
            `SystemExit`: If `-V` and `-h` options is declared. In that case, hperf will print corresponding information and exit. 
            `ParserError`: If options and arguments are invalid
        """
        # step 1.1. parse and validate the original command line options and arguments
        self.configs = self.parser.parse_args(self.__argv)    # may raise `SystemExit` or `ParserError`

        # step 1.2. if verbosity is declared (`-v` option), change the threshold of log level to print to console:
        # log level: DEBUG < INFO < WARNING < ERROR < CRITICAL
        # for file: always > DEBUG, not affected by `-v` option
        # for console: > INFO (default), > DEBUG (if verbosity is declared)
        if "verbose" in self.configs:
            self.__handler_stream.setLevel(logging.DEBUG)

    def __prework(self):
        """
        Complete some preworks based on the valid configurations (`.configs`) before profiling. 
        The following steps will be conducted based on the parsed configurations: 
        1) create an unique test directory in the temporary directory (`.tmp_dir`)
        2) instantiate a `LocalConnector` or `RemoteConnector` (`.connector`)

        The temporary directory (`.configs["tmp_dir"]`) specified by command line options `--tmp-dir` (`/tmp/hperf/` by default). 
        The test directory is for this run of hperf and used to save profiling scripts, raw performance data, analysis results, log file, etc. 
        `LocalConnector` and `RemoteConnector` are extended from interface `Connector`, which implement some useful methods for other modules 
        to interact with SUT, where the former is for local SUT while the latter is for remote SUT. 

        :raises:
            `ConnectorError`: For `RemoteConnector`, if fail to establish connection to remote SUT
        """
        # step 2.1. create an unique test directory in the temporary directory
        #   step 2.1.1 access or create the temporary directory specified by user
        selected_tmp_dir = self.configs["tmp_dir"]
        #     [case 1] if the temporary directory exists, check the R/W permission
        if os.path.exists(selected_tmp_dir):
            if os.access(selected_tmp_dir, os.R_OK | os.W_OK):
                self.tmp_dir = os.path.abspath(selected_tmp_dir)
                self.logger.debug(f"set temporary directory: {self.tmp_dir} (already exists)")
            else:
                bad_tmp_dir = os.path.abspath(selected_tmp_dir)
                self.logger.warning(f"invalid temporary directory: {bad_tmp_dir} (already exists but has no R/W permission)")
                self.logger.warning("reset temporary directory: '/tmp/hperf/'")
                os.makedirs("/tmp/hperf/", exist_ok=True)
                # **Note**: this action will change the value of `configs["tmp_dir"]`
                self.tmp_dir = self.configs["tmp_dir"] = "/tmp/hperf/"
        #     [case 2] if the temporary directory does not exist, try to create the directory
        else:
            try:
                os.makedirs(selected_tmp_dir)
                self.tmp_dir = os.path.abspath(selected_tmp_dir)
                self.logger.debug(f"success to create the temporary directory {self.tmp_dir}")
            except OSError:
                bad_tmp_dir = os.path.abspath(selected_tmp_dir)
                self.logger.warning(f"invalid temporary directory: {bad_tmp_dir} (fail to create the temporary directory)")
                self.logger.warning("reset temporary directory: '/tmp/hperf/'")
                os.makedirs("/tmp/hperf/", exist_ok=True)
                # **Note**: this action will change the value of 'configs["tmp_dir"]'
                self.tmp_dir = self.configs["tmp_dir"] = "/tmp/hperf/"
        
        #   step 2.1.2. find a unique test id (`.__find_test_id()`) and create test directory
        # search the temporary directory (`.tmp_dir`) and get a string with an unique test id, 
        # then create a sub-directory named by this string in the temporary directory for saving files and results.
        self.test_id = self.__find_test_id()
        os.makedirs(self.get_test_dir_path())
        self.logger.info(f"local test directory: {self.get_test_dir_path()}")

        # step 2.2. instantiate a `Connector`
        self.connector = Connector(self.get_test_dir_path())

    def __find_test_id(self) -> str:
        """
        Search the temporary directory (`.tmp_dir`) and return a string with an unique test directory.

        e.g. In the temporary directory, there are many sub-directory named `<date>_test<id>` for different runs.
        If `20221206_test001` and `202211206_test002` are exist, it will return `202211206_test003`.
        
        :return: a directory name with an unique test id for today
        """
        today = datetime.now().strftime("%Y%m%d")
        max_id = 0
        pattern = f"{today}_test(\d+)"
        for item in os.listdir(self.tmp_dir):
            path = os.path.join(self.tmp_dir, item)
            if os.path.isdir(path):
                obj = re.search(pattern, path)
                if obj:
                    found_id = int(obj.group(1))
                    if found_id > max_id:
                        max_id = found_id
        test_id = f"{today}_test{str(max_id + 1).zfill(3)}"
        return test_id

    def get_test_dir_path(self) -> str:
        """
        Get the absolute path of the unique test directory for this test. 
        :return: an absolute path of the unique test directory for this test
        """
        return os.path.join(self.tmp_dir, self.test_id)

    def __profile(self):
        """
        Instantiate `EventGroup` (`.event_groups`) and `Profiler` (`.profiler`) based on the parsed configurations (`.configs`). 
        Then it will call the methods of `Profiler`. The following steps will be conducted: 
        1) run sanity check, 
        2) generate and execute profiling script on SUT and save the raw performance data in the test directory 
        (a sub-directory in the temporary directory which can be obtained by `.connector.get_test_dir_path()` method), 

        :raises:
            `SystemExit`: if user choose not to continue profiling when sanity check fails 
            `ConnectorError`: if encounter errors when executing command or script on SUT
            `ProfilerError`: if the profiling is not successful on SUT
        """
        self.event_groups = EventGroup(self.connector)
        self.profiler = Profiler(self.connector, self.configs, self.event_groups)

        # step 3.1. sanity check
        # if sanity check does not pass, let user choose whether to continue profiling.
        if not self.profiler.sanity_check():
            select = input("Detected some problems which may interfere profiling. Continue profiling? [y|N] ")
            while True:
                if select == "y" or select == "Y":
                    break
                elif select == "n" or select == "N":
                    sys.exit(0)    # raise `SystemExit`
                else:
                    select = input("please select: [y|N] ")
        else:
            self.logger.info("sanity check passed.")

        # step 3.2. profile
        self.profiler.profile()    # may raise `ProfilerError` or `ConnectorError` (for `RemoteConnector`)
        self.logger.info(f"raw data saved in {self.get_test_dir_path()}")

    def __save_log_file(self):
        """
        Copy the log file from `self.log_filed_path` to the test directory for this run. 
        The `Logger` will temporarily write logs to this file (since `Logger` is instantiated before `Connector`) 
        and copy to the test directory for the convenience of users. 
        """
        source = self.log_file_path
        target = os.path.join(self.get_test_dir_path(), "hperf.log")
        try:
            copyfile(source, target)
        except IOError:
            self.logger.warning(f"fail to copy log file {source} to the test directory {target}")
            self.logger.info(f"logs for this run are saved in {source} temporarily")
        else:
            self.logger.info(f"logs for this run are saved in {target}")

    # Following methods are responsible for exception handling ... 
    
    def __system_exit_handler(self, e: SystemExit):
        """
        Handle all possible `SystemExit` exceptions during the whole process of hperf.
        `SystemExit` is triggered by `sys.exit(code)` statement, 
        where `code == 0` represents the program exits normally. 
        """
        if e.args[0] == 0:
            self.logger.debug("Program exits normally.")
        else:
            self.logger.error("Program exits abnormally.")

    def __keyboard_interrupt_handler(self):
        """
        Handle all possible `KeyboardInterrupt` exceptions during the whole process of hperf. 
        `KeyboardInterrupt` is triggered by `Ctrl + C` in terminal. 
        """
        self.logger.error("Keyboard Interrupt.")
    
    def __exception_handler(self, e: Exception):
        """
        Handle all possible Exceptions (Errors) during the whole process of hperf. 
        When an error is caught, the following code will not be executed and finally the program exits. 
        So that this method is to print error message and do some cleaning works. 
        `Exception` has an attribute `args` where `args[0]` is the message. 
        """
        self.logger.error(f"{e.args[0]}")


"""
The entrance of hperf. Users can invoke hperf from command line, like:
```
$ python hperf.py [options] <command>
```
refer to README.md for supported options
"""
if __name__ == "__main__":
    controller = Controller(sys.argv[1:])
    controller.hperf()