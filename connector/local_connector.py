from Connector.Connector import Connector
from datetime import datetime
import subprocess
import os


class LocalConnector(Connector):
    def __init__(self, configs: dict) -> None:
        """
        constructor of `LocalConnector`, extended from `Connector`
        """
        super(LocalConnector, self).__init__(configs)
        self.tmp_dir = self.configs["tmp_dir"]
        self.file_name = "hperf_{}.sh".format(datetime.now().strftime('%Y-%m-%d'))
        self.path = self.tmp_dir + self.file_name

    def run_command_with_file(self, command: str):
        self.__pre_bash_file__(command)
        perf_process =  subprocess.Popen(["bash", "{}".format(self.path)], stdout=subprocess.PIPE)
        perf_process.wait()

    def get_result(self) -> str:
        ls_res = subprocess.Popen("cd {} && ls".format(self.tmp_dir), stdout=subprocess.PIPE, shell=True)
        grep_res = subprocess.Popen("grep hperf_perf_re", stdin=ls_res.stdout, stdout=subprocess.PIPE, shell=True)
        ls_res.stdout.close()
        res = grep_res.stdout
        result_path = res.read()
        result_path = result_path.decode("utf-8")
        result_path = result_path.strip()
        result_path = self.tmp_dir + "/" + result_path
        with open(result_path, 'r') as f:
            result_lines = f.readlines()
        result = ""
        for line in result_lines:
            result += line
        return result

    def get_err(self) -> str:
        return " "

    def clear(self):
        subprocess.Popen("cd {} && rm hperf* && kill -2 $(pgrep perf)".format(self.tmp_dir), shell=True)

    """
        Undone! Just return Icelacke.
    """

    def get_cpu_architecture(self) -> str:
        return "Icelake"

    def runtime_check(self) -> bool:
        raise NotImplemented("Undone!")

    def __pre_bash_file__(self, command: str):
        with open(self.path, 'w') as f:
            f.write(command)