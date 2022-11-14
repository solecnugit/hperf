from Connector.Connector import Connector


def get_output_cmd() -> str:
    output_cmd = f'echo "perf result:"\n' \
                 f"cat $perf_result\n" \
                 f'echo "perf error:"\n' \
                 f"cat $perf_error\n"
    return output_cmd


class Profiler:
    def __init__(self, connector: Connector, configs: dict):
        self.connector = connector
        self.interval = 1000  # sampling interval (ms)
        self.interval_count = 5  # the number of sampling, profiling time (ms) = interval * interval_count
        self.event_list = "cycles,instructions"
        self.perf_output_path = "/tmp/hperf_tmp"  # output of perf command
        self.cpu_list = "1"  # the index of CPUs to be monitored
        self.pid = configs["pid"]

    def runtime_check(self) -> bool:
        """
        check if any other profiler already running on the system under test
        :return:
        """
        process_check_list = ["perf", "vtune"]
        for process in process_check_list:
            check_cmd = f"pgrep {process}"
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
        perf_cmd = self.profile_cmd()
        self.connector.run_command(perf_cmd)
        print("profiling completed.")

    def profile_cmd(self) -> str:
        perf_cmd = self.pre_perf_dir_cmd()
        perf_cmd += "nohup 3>$perf_result perf stat -e {0} -C {1} ".format(self.event_list, self.cpu_list)
        perf_cmd += "-A -x, --log-fd 3 >/dev/null 2>$perf_error &\n"
        perf_cmd += self.get_wait_cmd()
        perf_cmd += get_output_cmd()
        return perf_cmd

    def pre_perf_dir_cmd(self) -> str:
        pre_dir_cmd = 'TMPDIR="{0}"'.format(self.perf_output_path)
        pre_dir_cmd += f"perf_result=$(mktemp -t hperf_perf_result.XXXXXX)" \
                       f"perf_error=$(mktemp -t hperf_perf_error.XXXXXX)"
        return pre_dir_cmd

    def get_wait_cmd(self) -> str:
        wait_cmd = f"perf_pid=$!\n" \
                   f'echo "Please wait for the benchmark end."\n'
        wait_cmd += "wait {0}\n".format(self.pid)
        wait_cmd += f'echo "Workload completed."\n' \
                    f"kill -INT $perf_pid"
        return wait_cmd
