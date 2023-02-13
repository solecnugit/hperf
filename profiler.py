from connector import Connector, LocalConnector, RemoteConnector
from event_group import EventGroup
import logging
from hperf_exception import ProfilerError

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
        script = self.__get_profile_script()
        self.logger.info("start profiling")
        ret_code = self.connector.run_script(script)    # may raise `ConnectorError`
        if ret_code != 0:
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
    
    def __get_profile_script(self) -> str:
        """
        Based on the parsed configuration, generate the string of shell script for profiling.
        :return: a string of shell script for profiling
        """
        # for local SUT, output raw performance data to the test directory directly will be fine. 
        # however, for remote SUT, raw performance data should be output to the remote temporary which can be accessd on remote SUT, 
        # then pull the data to the local test directory. 
        if isinstance(self.connector, LocalConnector):
            perf_dir = self.connector.test_dir
        else:
            perf_dir = self.connector.remote_test_dir

        script = "#!/bin/bash\n"
        script += f'TMP_DIR={perf_dir}\n'
        script += 'perf_result="$TMP_DIR"/perf_result\n'
        script += 'perf_error="$TMP_DIR"/perf_error\n'
        script += f'3>"$perf_result" perf stat -e {self.event_groups.get_event_groups_str()} -A -a -x, -I 1000 --log-fd 3 {self.configs["command"]} 2>"$perf_error"\n'

        self.logger.debug("profiling script: \n" + script)
        return script
