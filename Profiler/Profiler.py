from Connector.Connector import Connector


class Profiler:
    def __init__(self,
                 connector: Connector,
                 interval: int = 1000,
                 interval_count: int = 5):
        self.connector = connector
        self.interval = interval  # sampling interval (ms)
        self.interval_count = interval_count  # the number of sampling, profiling time (ms) = interval * interval_count
        self.event_list = "cycles,instructions"
        self.perf_output_path = "/tmp/hperf_tmp"  # output of perf command
        self.cpu_list = "0-3"  # the index of CPUs to be monitored

    def runtime_check(self) -> bool:
        """
        check if any other profiler already running on the system under test
        :return:
        """
        process_check_list = ["perf", "vtune"]
        for process in process_check_list:
            check_cmd = f"ps -ef | grep {process} | grep -v grep"
            output = self.connector.run_command(check_cmd)
            if output.strip() != "":
                return False
            else:
                continue
        return True

    def get_system_info(self) -> dict:
        """
        obtain various information of the system under test through Connector
        :return: a dict of information
        """

    def profile(self):
        perf_cmd = f"3>{self.perf_output_path} " \
                   f"perf stat -e {self.event_list} -x, " \
                   f"-C {self.cpu_list} -A -I {self.interval} " \
                   f"--interval-count {self.interval_count} --log-fd 3"
        self.connector.run_command(perf_cmd)
        print("profiling completed.")
