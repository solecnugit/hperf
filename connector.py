from datetime import datetime
import subprocess
import os
from paramiko import SSHClient, SFTPClient, AutoAddPolicy


class Connector:
    """
    the Abstract class of all Connectors.
    """
    def __init__(self, configs: dict) -> None:
        self.configs = configs

    def run_command_with_file(self, command: str):
        pass

    def get_result(self) -> str:
        pass

    def get_err(self) -> str:
        pass

    def runtime_check(self) -> bool:
        pass

    def get_cpu_architecture(self) -> str:
        pass

    def clear(self):
        pass


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


class RemoteConnector(Connector):
    def __init__(self, configs: dict) -> None:
        super(RemoteConnector, self).__init__(configs)
        self.host_name = self.configs["host_name"]
        self.user_name = self.configs["user_name"]
        self.password = self.configs["password"]
        self.port = self.configs["port"] if "port" in self.configs else 22
        self.tmp_dir = self.configs["tmp_dir"]
        self.file_name = "hperf_{}.sh".format(datetime.now().strftime('%Y-%m-%d'))
        self.path = self.tmp_dir + "/" + self.file_name  # the remote path
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy)

    def run_command_with_file(self, command: str):
        self.__connect__()
        self.__pre__bash_file__(command)
        self.__run__command__("bash {}".format(self.path))
        self.__disconnect__()

    def run_oneline_command(self, command: str) -> str:
        self.__connect__()
        self.__run__command__(command)
        self.__disconnect__()

    def get_result(self) -> str:
        self.__connect__()
        result = self.__get_result__()
        self.__disconnect__()
        return result

    def get_err(self) -> str:
        self.__connect__()
        err = self.__get_err__()
        self.__disconnect__()
        return err

    def clear(self):
        self.__connect__()
        self.__run__command__("cd {} && rm hperf* && kill -INT $(pgrep perf)".format(self.tmp_dir))
        self.__disconnect__()

    """
        Undone! Just return Icelake.
    """

    def get_cpu_architecture(self) -> str:
        return "Icelake"

    def runtime_check(self) -> bool:
        raise NotImplemented("Undone!")

    def __connect__(self):
        self.client.connect(self.host_name, self.port,
                            self.user_name, self.password)

    def __get_result__(self) -> str:
        _, stdout, _ = self.client.exec_command(
            "cd {} && ls | grep {}".format(self.tmp_dir, "hperf_perf_re"))
        result_file_name = stdout.readline()
        _, stdout, _ = self.client.exec_command(
            "cd {} && cat {}".format(self.tmp_dir, result_file_name))
        result = stdout.read()
        result = str(result, encoding="utf-8")
        return result

    def __get_err__(self) -> str:
        _, stdout, _ = self.client.exec_command(
            "cd {} && ls | grep {}".format(self.tmp_dir, self.file_name))
        err_file_name = stdout.readline()
        _, stdout, _ = self.client.exec_command(
            "cd {} && cat {}".format(self.tmp_dir, err_file_name))
        err = stdout.read()
        err = str(err, encoding="utf-8")
        return err

    def __pre__bash_file__(self, command: str):
        transport = self.client.get_transport()
        sftp = SFTPClient.from_transport(transport)
        local_path = "../tmp/bash.sh"
        with open(local_path, 'w') as f:
            f.write(command)
        sftp.put(local_path, self.path)

    def __run__command__(self, command: str):
        _, stdout, _ = self.client.exec_command(command)
        ch = stdout.channel
        ch.recv_exit_status()

    def __disconnect__(self):
        self.client.close()
