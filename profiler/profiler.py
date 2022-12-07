from connector import Connector
from profiler.event_group import EventGroup
import os
import logging

class Profiler:
    """
    'Profiler' is responsible for collecting raw microarchitecture performance data.
    """
    def __init__(self, connector: Connector, configs: dict):
        """
        Constructor of 'Profiler'
        :param connector: an instance of 'Connector' ('LocalConnector' or 'RemoteConnector')
        :param configs: a dict of parsed configurations (the member 'configs' in 'Controller')
        """
        self.connector = connector
        self.configs = configs
        # event_groups = EventGroup(configs["metrics"], connector)
        # self.event_groups = event_groups.get_event_groups()
        self.event_groups = "cycles:D,instructions:D,ref-cycles:D,'{r8D1,r10D1}','{rc4,rc5}'"
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
        script += f'3>"$perf_result" perf stat -e {self.event_groups} -A -a -x, -I 1000 --log-fd 3 {self.configs["command"]} 2>"$perf_error"\n'

        logging.debug("profiling script: \n" + script)
        return script
    
    def result_output(self):
        result = self.connector.get_result()
        print("perf_result:")
        print(result)

    def err_output(self):
        print("perf_err:")

    def clear(self):
        self.connector.clear()

    # def __create_tmp_file__(self):
    #     cmd = "TMP_DIR={}\n".format(self.tmp_dir)
    #     cmd += "perf_result=$(mktemp -t -p $TMP_DIR hperf_perf_result.XXXXXX)\n"
    #     cmd += "perf_error=$(mktemp -t -p $TMP_DIR hperf_perf_error.XXXXXX)\n"
    #     return cmd

    # def __perf_cmd__(self):
    #     cmd = "nohup 3>\"$perf_result\" perf stat -e {} -C {} -A -x, --log-fd 3 2>\"$perf_error\" &\n".format(
    #         self.event_groups, self.cpu_list)
    #     cmd += "perf_pid=$!\n"
    #     return cmd

    # def __wait_cmd__(self):
    #     cmd = "tail -f --pid={} /dev/null\n".format(self.pid)
    #     cmd += "kill -2 $perf_pid\n"
    #     return cmd
