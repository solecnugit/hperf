from Connector.Connector import Connector
from datetime import datetime
import os


class LocalConnector(Connector):
    def __init__(self, configs: dict) -> None:
        """
        constructor of `LocalConnector`, extended from `Connector`
        """
        super(LocalConnector, self).__init__(configs)
        self.tmp_dir = self.configs["tmp_dir"]
        self.file_name = "hperf_{}.sh".format(datetime.now)
        self.path = self.tmp_dir + "/hperf.sh"

    def run_command_with_file(self, command: str):
        self.__pre_bash_file__(command)
        os.system("cd {} && bash bash.sh".format(self.tmp_dir))

    def get_result(self) -> str:
        result_lines = ""
        result_path = ""
        with open(result_path, 'r') as f:
            result_lines = f.readlines()
        result = ""
        for line in result_lines:
            result += line
        return result

    def get_err(self) -> str:
        raise NotImplemented("Undone!")

    def clear(self):
        pass

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