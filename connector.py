from datetime import datetime
import subprocess
import os
import logging
import re
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
        Constructor of 'LocalConnector', extended from 'Connector'.
        'Connector' provides various useful method for executing commands or shell scripts.
        """
        super(LocalConnector, self).__init__(configs)
        
        # if the temporary directory is not exist, try to create the directory
        self.tmp_dir = ""
        if not os.path.exists(configs["tmp_dir"]):
            try:
                os.makedirs(configs["tmp_dir"])
                self.tmp_dir = os.path.abspath(configs["tmp_dir"])
                logging.debug(f"success to create the temporary directory {self.tmp_dir}")
            except OSError:
                logging.error("fail to create the temporary directory, reset to '/tmp/hperf/'")
                os.makedirs("/tmp/hperf/")
                self.tmp_dir = configs["tmp_dir"] = "/tmp/hperf/"
        else:
            self.tmp_dir = os.path.abspath(configs["tmp_dir"])
            logging.debug(f"temporary directory {self.tmp_dir} already exists")
        
        # search the temporary directory 'self.tmp_dir' and get a string with an unique test id,
        # then create a sub-directory named with this string in 'self.tmp_dir' for saving files for profiling.
        self.test_id = self.__find_test_id()
        os.makedirs(os.path.join(self.tmp_dir, self.test_id))
        
        # self.file_name = "hperf_{}.sh".format(datetime.now().strftime('%Y-%m-%d'))
        # self.path = self.tmp_dir + self.file_name

    def __find_test_id(self) -> str:
        """
        Search the temporary directory and return a string with an unique test id for today.
        e.g. in temporary directory, there are many directory named '<date>_test<id>' for different runs.
        If '20221206_test001' and '202211206_test002' are exist, the method will return '202211206_test002'.
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

    def get_test_dir_path(self):
        """
        Get the path of the unique temporary directory for this test.
        It should be <tmp_dir>/<test_id>, where <tmp_dir> is specified by user and <test_id> is unique in the <tmp_dir>. 
        """
        return os.path.join(self.tmp_dir, self.test_id)
    
    def run_script(self, script: str):
        """
        Create and run a script on SUT, then wait for the script finished.
        :param script: the string of shell script
        """
        script_path = self.__generate_script(script)
        perf_process = subprocess.Popen(["bash", f"{script_path}"], stdout=subprocess.PIPE)
        perf_process.wait()

    def __generate_script(self, script: str):
        """
        Generate a profiling script on the SUT.
        :param script: the string of shell script
        :return: path of the script
        """
        script_path = os.path.join(self.tmp_dir, self.test_id, "perf.sh")
        with open(script_path, 'w') as f:
            f.write(script)
        return script_path

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

    # TODO: undone. 
    # maybe it can be understood as a profiler to get static information on the SUT
    def get_cpu_architecture(self) -> str:
        return "Icelake"

    # TODO: undone. 
    # maybe it can be understood as a profiler to get static information on the SUT
    def runtime_check(self) -> bool:
        pass


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
