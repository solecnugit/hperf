from connector import Connector
from profiler.event_group import EventGroup

class Profiler:
    def __init__(self, connector: Connector, configs: dict):
        self.connector = connector
        event_groups = EventGroup(configs["metrics"], connector)
        self.event_groups = event_groups.get_event_groups()
        self.tmp_dir = configs["tmp_dir"]
        self.cpu_list = configs["cpu_list"]
        self.pid = configs["pid"]

    def profile(self):
        command = self.__profile_cmd__()
        self.connector.run_command_with_file(command)

    def result_output(self):
        result = self.connector.get_result()
        print("perf_result:")
        print(result)

    def err_output(self):
        print("perf_err:")

    def clear(self):
        self.connector.clear()

    def __profile_cmd__(self) -> str:
        return self.__create_tmp_file__() + self.__perf_cmd__() + self.__wait_cmd__()

    def __create_tmp_file__(self):
        cmd = "TMP_DIR={}\n".format(self.tmp_dir)
        cmd += "perf_result=$(mktemp -t -p $TMP_DIR hperf_perf_result.XXXXXX)\n"
        cmd += "perf_error=$(mktemp -t -p $TMP_DIR hperf_perf_error.XXXXXX)\n"
        return cmd

    def __perf_cmd__(self):
        cmd = "nohup 3>\"$perf_result\" perf stat -e {} -C {} -A -x, --log-fd 3 2>\"$perf_error\" &\n".format(
            self.event_groups, self.cpu_list)
        cmd += "perf_pid=$!\n"
        return cmd

    def __wait_cmd__(self):
        cmd = "tail -f --pid={} /dev/null\n".format(self.pid)
        cmd += "kill -2 $perf_pid\n"
        return cmd
