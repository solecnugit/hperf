from datetime import datetime
from typing import Sequence, Union
import subprocess
import os
import logging
import re
# from paramiko import SSHClient, SFTPClient, AutoAddPolicy


class Connector:
    """
    the Abstract class of all Connectors.
    'Connector' provides various useful method for executing commands or shell scripts.
    """

    def __init__(self, configs: dict) -> None:
        """
        Constructor of 'Connector'.
        When a 'Connector' is instantiated, it will try to access the temporary directory (configs["tmp_dir"])
        specified by command line options (default /tmp/hperf/) 
        and create an unique test directory in the temporary directory.
        The test directory is for this run of hperf and used to save profiling scripts and their outputs, 
        log file, raw performance data, etc.
        # Note: this action may change the value of 'configs["tmp_dir"]' if it cannot be accessed.
        """
        # common initialization shared by 'LocalConnector' and 'RemoteConnector'
        self.configs = configs

    # interfaces of 'Connector'
    def get_test_dir_path(self) -> str:
        """
        Get the abusolute path of the unique test directory for this test on the SUT.
        For 'LocalConnector', the returned path can be accessed on local host.
        For 'RemoteConnector', the returned path are in the remote host so that cannot be accessed locally.
        """
        pass

    def run_script(self, script: str) -> int:
        """
        Create and run a script on SUT, then wait for the script finished 
        and return the returned value of executing the shell script.
        :param script: the string of shell script
        :return: the returned value of executing the shell script
        """
        pass

    def run_command(self, command_args: Union[Sequence[str], str]) -> str:
        """
        Run a command on SUT, then return the returned value of executing the command.
        :param command_args: a sequence of program arguments, e.g. ["ls", "/home"], 
        or just a string of command line, e.g "ls /home"
        :return: the returned value of executing the command
        """
        pass


class LocalConnector(Connector):
    """
    'LocalConnector' is extended from 'Connector'.
    """

    def __init__(self, configs: dict) -> None:
        """
        Constructor of 'Connector'.
        When a 'Connector' is instantiated, it will try to access the temporary directory (configs["tmp_dir"])
        specified by command line options (default /tmp/hperf/) 
        and create an unique test directory in the temporary directory.
        The test directory is for this run of hperf and used to save profiling scripts and their outputs, 
        log file, raw performance data, etc.
        # Note: this action may change the value of 'configs["tmp_dir"]' if it cannot be accessed.
        """
        super(LocalConnector, self).__init__(configs)

        self.tmp_dir = ""
        # if the temporary directory is not exist, try to create the directory
        if os.path.exists(configs["tmp_dir"]):
            if os.access(configs["tmp_dir"], os.R_OK | os.W_OK):
                self.tmp_dir = os.path.abspath(configs["tmp_dir"])
                logging.debug(
                    f"set temporary directory: {self.tmp_dir} (already exists)")
            else:
                bad_tmp_dir = os.path.abspath(configs["tmp_dir"])
                logging.warning(
                    f"invalid temporary directory: {bad_tmp_dir} (already exists but has no R/W permission)")
                logging.warning("reset temporary directory: '/tmp/hperf/'")
                os.makedirs("/tmp/hperf/", exist_ok=True)
                # Note: this action will change the value of 'configs["tmp_dir"]'
                self.tmp_dir = configs["tmp_dir"] = "/tmp/hperf/"
        else:
            try:
                os.makedirs(configs["tmp_dir"])
                self.tmp_dir = os.path.abspath(configs["tmp_dir"])
                logging.debug(
                    f"success to create the temporary directory {self.tmp_dir}")
            except OSError:
                bad_tmp_dir = os.path.abspath(configs["tmp_dir"])
                logging.warning(
                    f"invalid temporary directory: {bad_tmp_dir} (fail to create the temporary directory)")
                logging.warning("reset temporary directory: '/tmp/hperf/'")
                os.makedirs("/tmp/hperf/", exist_ok=True)
                # Note: this action will change the value of 'configs["tmp_dir"]'
                self.tmp_dir = configs["tmp_dir"] = "/tmp/hperf/"

        # search the temporary directory (self.tmp_dir) and get a string with an unique test id,
        # then create a sub-directory named by this string in  for saving files for profiling.
        self.test_id = self.__find_test_id()
        os.makedirs(self.get_test_dir_path())
        logging.info(f"test directory: {self.get_test_dir_path()}")

    def __find_test_id(self) -> str:
        """
        Search the temporary directory (configs["tmp_dir"]) and return a string with an unique test directory.
        e.g. in temporary directory, there are many directory named '<date>_test<id>' for different runs.
        If '20221206_test001' and '202211206_test002' are exist, the method will return '202211206_test003'.
        :return: a directory name with an unique test id for today
        """
        today = datetime.now().strftime("%Y%m%d")
        max_id = 0
        pattern = f"{today}_test(\d+)"
        for item in os.listdir(self.tmp_dir):
            path = os.path.join(self.tmp_dir, item)
            if os.path.isdir(path):
                obj = re.search(pattern, path)
                if obj:
                    found_id = int(obj.group(1))
                    if found_id > max_id:
                        max_id = found_id
        test_id = f"{today}_test{str(max_id + 1).zfill(3)}"
        return test_id

    def get_test_dir_path(self) -> str:
        """
        Get the abusolute path of the unique test directory for this test on the SUT.
        For 'LocalConnector', the returned path can be accessed on local host.
        For 'RemoteConnector', the returned path are in the remote host so that cannot be accessed locally.
        """
        return os.path.join(self.tmp_dir, self.test_id)

    def run_script(self, script: str) -> int:
        """
        Create and run a script on SUT, then wait for the script finished.
        :param script: the string of shell script
        :return: the returned value of executing the shell script
        """
        script_path = self.__generate_script(script)
        logging.debug(f"run script: {script_path}")
        process = subprocess.Popen(
            ["bash", f"{script_path}"], stdout=subprocess.PIPE)
        returned_value = process.wait()
        logging.debug(f"finish script: {script_path}")
        return returned_value

    def __generate_script(self, script: str) -> str:
        """
        Generate a profiling script on the SUT.
        :param script: the string of shell script
        :return: path of the script on the SUT
        """
        script_path = os.path.join(self.tmp_dir, self.test_id, "perf.sh")
        with open(script_path, 'w') as f:
            f.write(script)
        logging.debug(f"generate script: {script_path}")
        return script_path

    def run_command(self, command_args: Union[Sequence[str], str]) -> str:
        """
        Run a command on SUT, then return the stdout output of executing the command.
        :param command_args: a sequence of program arguments, e.g. ["ls", "/home"]
        :return: stdout output
        """
        if isinstance(command_args, list):
            output = subprocess.Popen(command_args, stdout=subprocess.PIPE).communicate()[0]
        else:
            output = subprocess.Popen(command_args, shell=True, stdout=subprocess.PIPE).communicate()[0]
        return output

    # def get_result(self) -> str:
    #     ls_res = subprocess.Popen("cd {} && ls".format(self.tmp_dir), stdout=subprocess.PIPE, shell=True)
    #     grep_res = subprocess.Popen("grep hperf_perf_re", stdin=ls_res.stdout, stdout=subprocess.PIPE, shell=True)
    #     ls_res.stdout.close()
    #     res = grep_res.stdout
    #     result_path = res.read()
    #     result_path = result_path.decode("utf-8")
    #     result_path = result_path.strip()
    #     result_path = self.tmp_dir + "/" + result_path
    #     with open(result_path, 'r') as f:
    #         result_lines = f.readlines()
    #     result = ""
    #     for line in result_lines:
    #         result += line
    #     return result

    # def get_err(self) -> str:
    #     return " "

    # def clear(self):
    #     subprocess.Popen("cd {} && rm hperf* && kill -2 $(pgrep perf)".format(self.tmp_dir), shell=True)

    # TODO: undone.
    # maybe it can be understood as a profiler to get static information on the SUT
    # def get_cpu_architecture(self) -> str:
    #     return "Icelake"

    # TODO: undone.
    # maybe it can be understood as a profiler to get static information on the SUT
    # def runtime_check(self) -> bool:
    #     pass


class RemoteConnector(Connector):
    def __init__(self, configs: dict) -> None:
        """
        Constructor of 'Connector'.
        When a 'Connector' is instantiated, it will try to access the temporary directory (configs["tmp_dir"])
        specified by command line options (default /tmp/hperf/) 
        and create an unique test directory in the temporary directory.
        The test directory is for this run of hperf and used to save profiling scripts and their outputs, 
        log file, raw performance data, etc.
        # Note: this action may change the value of 'configs["tmp_dir"]' if it cannot be accessed.
        """
        super(RemoteConnector, self).__init__(configs)

        self.remote_tmp_dir = ""
        self.local_tmp_dir = ""

        # paramiko SSH connection configurations
        self.hostname = self.configs["hostname"]
        self.port = self.configs["port"]
        self.username = self.configs["username"]
        self.password = self.configs["password"]

        self.tmp_dir = self.configs["tmp_dir"]

        self.file_name = "hperf_{}.sh".format(
            datetime.now().strftime('%Y-%m-%d'))
        self.path = self.tmp_dir + "/" + self.file_name  # the remote path
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy)

    def run_command(self, command_args: Sequence[str]) -> str:
        """
        Run a command on SUT, then return the stdout output of executing the command.
        :param command_args: a sequence of program arguments, e.g. ["ls", "/home"]
        :return: stdout output
        """

    
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
        self.__run__command__(
            "cd {} && rm hperf* && kill -INT $(pgrep perf)".format(self.tmp_dir))
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
