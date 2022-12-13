from connector import Connector
from event_group import EventGroup
import os
import logging

class Profiler:
    """
    'Profiler' is responsible for collecting raw microarchitecture performance data.
    """
    def __init__(self, connector: Connector, configs: dict, event_groups: EventGroup):
        """
        Constructor of 'Profiler'
        :param connector: an instance of 'Connector' ('LocalConnector' or 'RemoteConnector')
        :param configs: a dict of parsed configurations (the member 'configs' in 'Controller')
        :param event_group: an instance of 'EventGroup'
        """
        self.connector = connector
        self.configs = configs
        # event_groups = EventGroup(configs["metrics"], connector)
        # self.event_groups = event_groups.get_event_groups()
        self.event_groups = event_groups
        # self.event_groups = "cycles:D,instructions:D,ref-cycles:D,'{r8D1,r10D1}','{rc4,rc5}'"
        # self.tmp_dir = configs["tmp_dir"]
        # self.cpu_list = configs["cpu_list"]
        # self.pid = configs["pid"]

    def profile(self):
        script = self.__get_profile_script()
        logging.info("start profiling")
        self.connector.run_script(script)
        logging.info("end profiling")

    def __get_profile_script(self) -> str:
        """
        Based on the parsed configuration, generate the string of shell script for profiling.
        :return: the string of shell script for profiling
        """
        script = "#!/bin/bash\n"
        script += f'TMP_DIR={self.connector.get_test_dir_path()}\n'
        script += 'perf_result="$TMP_DIR"/perf_result\n'
        script += 'perf_error="$TMP_DIR"/perf_error\n'
        script += f'3>"$perf_result" perf stat -e {self.event_groups.get_event_groups_str()} -A -a -x, -I 1000 --log-fd 3 {self.configs["command"]} 2>"$perf_error"\n'

        logging.debug("profiling script: \n" + script)
        return script
