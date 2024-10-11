from connector import Connector, LocalConnector, RemoteConnector
from event_group import EventGroup
import logging
from hperf_exception import ProfilerError
from concurrent.futures import ThreadPoolExecutor, as_completed
from string import Template

class HperfTemplete(Template):
    delimiter = r"%%"

class Profiler:
    """
    `Profiler` is responsible for collecting raw microarchitecture performance data. 
    It will collect raw performance data by other profilers (such as perf, sar, etc.) on SUTs through `Connector`. 
    """
    def __init__(self, connector: Connector, configs: dict, event_groups: EventGroup):
        """
        Constructor of 'Profiler'
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
            if fail to generate or execute script on remote SUT, or fail to pull raw performance data from remote SUT
            `ProfilerError`: if the returned code of executing script does not equal to 0 
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
        
        if isinstance(self.connector, RemoteConnector):
            self.connector.pull_remote()
        
        if abnormal_flag:
            raise ProfilerError("Executing profiling script on the SUT failed.")
        
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
            `ConnectorError`: for `RemoteConnector`, if fail to execute command for sanity check on remote SUT
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
        if isinstance(self.connector, LocalConnector):
            output_dir = self.connector.test_dir
        elif isinstance(self.connector, RemoteConnector):
            output_dir = self.connector.remote_test_dir
        else:
            raise ProfilerError("Fail to get test directory path on SUT when generating profiling script.")
        
        self.connector.run_command("lscpu > " + f"{output_dir}/cpu_info")
    
    def get_cpu_topo(self):
        """
        """
        if isinstance(self.connector, LocalConnector):
            output_dir = self.connector.test_dir
        elif isinstance(self.connector, RemoteConnector):
            output_dir = self.connector.remote_test_dir
        else:
            raise ProfilerError("Fail to get test directory path on SUT when generating profiling script.")

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
            raise ProfilerError("Unsupported ISA.")
        
        self.connector.run_command(get_topo_cmd)
    
    def __get_perf_script(self) -> str:
        """
        Based on the parsed configuration, generate the string of shell script for profiling by perf.
        :return: a string of shell script for profiling
        """
        # for local SUT, output raw performance data to the test directory directly will be fine. 
        # however, for remote SUT, raw performance data should be output to the remote temporary which can be accessd on remote SUT, 
        # then pull the data to the local test directory. 
        if isinstance(self.connector, LocalConnector):
            perf_dir = self.connector.test_dir
        elif isinstance(self.connector, RemoteConnector):
            perf_dir = self.connector.remote_test_dir
        else:
            raise ProfilerError("Fail to get test directory path on SUT when generating profiling script.")
        
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
        # for local SUT, output raw performance data to the test directory directly will be fine. 
        # however, for remote SUT, raw performance data should be output to the remote temporary which can be accessd on remote SUT, 
        # then pull the data to the local test directory. 
        if isinstance(self.connector, LocalConnector):
            sar_dir = self.connector.test_dir
        elif isinstance(self.connector, RemoteConnector):
            sar_dir = self.connector.remote_test_dir
        else:
            raise ProfilerError("Fail to get test directory path on SUT when generating profiling script.")
        
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
