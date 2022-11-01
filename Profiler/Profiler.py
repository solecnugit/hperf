from Connector.Connector import Connector


class Profiler:
    def __init__(self, connector: Connector, profiling_time: int):
        self.connector = connector
        self.profiling_time = profiling_time
        self.event_list = "cycles,instructions"
        self.tmp_file_path = "/tmp/hperf_tmp"
        self.cpu_list = "0-3"

    def profile(self):
        perf_cmd = f"3>{self.tmp_file_path} " \
                   f"perf stat -e {self.event_list} -x, " \
                   f"-C {self.cpu_list} -A -I 1000 " \
                   f"--interval-count {self.profiling_time} --log-fd 3"
        self.connector.run_command(perf_cmd)
        print("profiling completed.")
