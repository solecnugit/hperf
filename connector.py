from datetime import datetime
from typing import Sequence, Union
import subprocess
import os
import socket
import logging
import re
import paramiko
from hperf_exception import ConnectorError


class Connector:
    """
    The interface of `Connector`.
    `Connector` provides various useful method for executing commands or shell scripts.
    """

    def __init__(self, test_dir: str, **conn_info) -> None:
        pass

    def run_script(self, script: str) -> int:
        pass

    def run_command(self, command_args: Union[Sequence[str], str]) -> str:
        pass


class LocalConnector(Connector):
    """
    `LocalConnector` is extended from `Connector`, which provide useful method for executing commands or shell scripts on local SUT.
    """

    def __init__(self, test_dir: str) -> None:
        """
        Constructor of `LocalConnector`. 
        :param `test_dir`: path of the test directory for this run, which can be obtained by `Controller.get_test_dir_path()`
        """
        self.logger = logging.getLogger("hperf")
        self.test_dir = test_dir

    def run_script(self, script: str) -> int:
        """
        Create and run a script on SUT, then wait for the script finished. 
        If the returned code is not eqaul to 0, it will generate a debug log message. 
        :param `script`: a string of shell script
        :return: the returned code of executing the shell script
        """
        script_path = self.__generate_script(script)
        self.logger.debug(f"run script: {script_path}")
        process = subprocess.Popen(
            ["bash", f"{script_path}"], stdout=subprocess.PIPE)
        ret_code = process.wait()
        self.logger.debug(f"finished with exit code {ret_code}")
        if ret_code != 0:
            self.logger.debug(f"executing script {script_path} with an exit code of {ret_code}")
        self.logger.debug(f"finish script: {script_path}")
        return ret_code

    def __generate_script(self, script: str) -> str:
        """
        Generate a profiling script on SUT. 
        :param `script`: a string of shell script
        :return: path of the script on the SUT
        """
        script_path = os.path.join(self.test_dir, "perf.sh")
        with open(script_path, 'w') as f:
            f.write(script)
        self.logger.debug(f"generate script: {script_path}")
        return script_path

    def run_command(self, command_args: Union[Sequence[str], str]) -> str:
        """
        Run a command on SUT, then return the stdout output of executing the command. 
        **Note**: The output is decoded by 'utf-8'. 
        :param `command_args`: a sequence of program arguments, e.g. `["ls", "/home"]`, or a string of command, e.g. `"ls /home"`
        :return: stdout output
        """
        if isinstance(command_args, list):
            output = subprocess.Popen(command_args, stdout=subprocess.PIPE).communicate()[0]
        else:
            output = subprocess.Popen(command_args, shell=True, stdout=subprocess.PIPE).communicate()[0]
        output = output.decode("utf-8")
        return output


class RemoteConnector(Connector):
    """
    `RemoteConnector` is extended from `Connector`, which provide useful method for executing commands or shell scripts on remote SUT. 
    The remote SUT is can not be accessed locally, so that the operations rely on SSH / SFTP connection to remote SUT. 
    """

    def __init__(self, test_dir: str, **conn_info) -> None:
        """
        Constructor of `LocalConnector`.  

        Unlike `LocalConnector`, `RemoteConnector` relies on SSH / SFTP connection to operate remote SUT. 
        So that the SSH and SFTP session will be opened by paramiko. 
        The local test directory is named `.local_test_dir`
        Besides, a remote test directory will be created (`~/.hperf/`) because scripts need to upload to remote SUT before executing 
        and the output need to download from remote SUT. The remote directory is for these temporary files. 
        The remote temporary directory is named `.remote_test_dir`

        :param `test_dir`: path of the test directory for this run, which can be obtained by `Controller.get_test_dir_path()` 
        :param `conn_info`: keyword arguments for remote SSH connection
        :raises:
            `ConnectorError`: if encounter errors during the SSH / SFTP connection to remote SUT by `paramiko` module
        """
        self.logger = logging.getLogger("hperf")
        
        # step 1. record the local test directory
        self.local_test_dir: str = test_dir

        # step 2. open a SSH session
        # paramiko SSH connection configurations
        self.hostname: str = conn_info["hostname"]
        self.username: str = conn_info["username"]
        self.password: str = conn_info["password"]
        # TODO: the port of SSH is 22 by default. in future, the port can be specified explictly by command line option '-p'.
        self.port: int = 22

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy)   # for the first connection
        
        try:
            # may raise exceptions: 
            # - paramiko.BadHostKeyException: the server's host key could not be verified
            # - paramiko.AuthenticationException: authentication failed
            # - paramiko.SSHException: connecting or establishing an SSH session failed
            self.client.connect(self.hostname, self.port, self.username, self.password)
        except (paramiko.BadHostKeyException, paramiko.AuthenticationException, paramiko.SSHException) as e:
            self.client.close()
            # format of `e.args`: `(message, )`
            raise ConnectorError(f"SSH connection failed: {e.args[0]}")
        except socket.error as e:
            self.client.close()
            # format of `e.args`: `(err_code, message)`
            raise ConnectorError(f"SSH connection failed: {e.args[1]}")

        # step 3. open a SFTP session
        self.sftp = self.client.open_sftp()
        
        # step 4. create a test directory on the remote SUT through SFTP session
        # the test directory is './.hperf/' by default. if it does not exist, hperf will create the directory.
        default_remote_test_dir = "./.hperf/"
        # the initial working directory is "~/" 
        file_list = self.sftp.listdir(".")    # list all files (including directories) in current working directory
        if ".hperf" in file_list:    # directory ./.hperf/ exists on the remote SUT
            self.logger.debug(f"directory {default_remote_test_dir} exists on the remote SUT")
            try:
                self.sftp.chdir(default_remote_test_dir)    # change working directory: ./.hperf/
            except IOError as e:
                self.close()
                raise ConnectorError(f"SFTP session failed: {e.args[0]}")
            else:
                for file in self.sftp.listdir("."):    # delete all files in ./.hperf/
                    try:
                        self.sftp.remove(file)
                    except IOError as e:   # if fail to remove (the `file` is a directory), just ignore
                        pass
            finally:
                self.sftp.chdir()    # reset working directory to ./
        else:    # directory ./.hperf/ does not exist on the remote SUT
            self.logger.debug(f"directory {default_remote_test_dir} does not exist on the remote SUT")
            self.sftp.mkdir(default_remote_test_dir)

        # step 5. record the remote test directory
        self.remote_test_dir = default_remote_test_dir

        self.logger.debug(f"remote test directory: {self.remote_test_dir}")
    
    def run_command(self, command_args: Sequence[str]) -> str:
        """
        Run a command on SUT, then return the stdout output of executing the command. 
        The output is decoded by 'utf-8'. 
        :param `command_args`: a sequence of program arguments, e.g. `["ls", "/home"]`, or a string of command, e.g. `"ls /home"`
        :return: stdout output
        :raises:
            `ConnectorError`: if fail to execute command on remote SUT
        """
        if isinstance(command_args, list):
            command: str = " ".join(command_args)
        else:
            command: str = command_args
        
        try:
            self.logger.debug(f"execute command on remote: {command}")
            _, stdout, _ = self.client.exec_command(command)    # may raise paramiko.SSHException
            ret_code = stdout.channel.recv_exit_status()
            self.logger.debug(f"finished with exit code {ret_code}")
            if ret_code != 0:
                self.logger.debug(f"executing command {command} with an exit code of {ret_code}")
            else:
                output = stdout.read().decode("utf-8")
                self.logger.debug(f"stdout of command {command}: \n{output}")
                return output
        except paramiko.SSHException as e:
            self.close()
            raise ConnectorError(f"Executing command {command} failed on remote SUT: {e.args[0]}")
    
    def run_script(self, script: str) -> int:
        """
        Create and run a script on SUT, then wait for the script finished. 
        If the returned code is not eqaul to 0, it will generate a debug log message. 
        :param `script`: a string of shell script
        :return: the returned code of executing the shell script
        :raises:
            `ConnectorError`: if fail to generate or execute script on remote SUT, or fail to pull raw performance data from remote SUT
        """
        # step 1. generate a script on remote SUT
        remote_script_path = self.__generate_script(script)    # may raise `ConnectorError`

        # step 2. run the script by bash
        try:
            self.logger.debug(f"run script on remote SUT: {remote_script_path}")
            _, stdout, _ = self.client.exec_command(f"bash {remote_script_path}")    # may raise `paramiko.SSHException`
            ret_code = stdout.channel.recv_exit_status()
            self.logger.debug(f"finished with exit code {ret_code}")
        except paramiko.SSHException as e:
            self.close()
            raise ConnectorError(f"Executing script {remote_script_path} failed on remote SUT: {e.args[0]}")
        
        # if the returned code of executing script does not equal to 0, log a warning message
        if ret_code != 0:
            self.logger.debug(f"executing script {remote_script_path} with an exit code of {ret_code}")
        self.logger.debug(f"finish script: {remote_script_path}")

        # step 3. pull files from remote SUT for following analyzing
        self.__pull_remote()    # may raise `ConnectorError`
        
        return ret_code

    def __generate_script(self, script: str) -> str:
        """
        Generate a profiling script on SUT. 
        :param `script`: the string of shell script
        :return: path of the script on the SUT
        :raises:
            `ConnectorError`: if script fails to be generated on remote SUT
        """
        remote_script_path = os.path.join(self.remote_test_dir, "perf.sh")
        try:
            with self.sftp.open(remote_script_path, "w") as f:    # may raise `IOError`
                f.write(script)
        except IOError:
            raise ConnectorError(f"Fail to generate script {remote_script_path} on remote SUT")
        self.logger.debug(f"generate script in remote temporary directory: {remote_script_path}")
        return remote_script_path

    def __pull_remote(self):
        """
        Pull all files to the test directory (a sub-directory in local temporary directory) from remote temporary directory. 
        :raises:
            `ConnectorError`: if fail to pull raw performance data from remote SUT
        """
        try:
            for file in self.sftp.listdir(self.remote_test_dir):
                remote_file_path = os.path.join(self.remote_test_dir, file)
                local_file_path = os.path.join(self.local_test_dir, file)
                self.sftp.get(remote_file_path, local_file_path)    # may raise `IOError`
                self.logger.debug(f"get file from remote SUT to local test directory: {remote_file_path} -> {local_file_path}")
        except IOError:
            raise ConnectorError(f"Fail to pull raw performance data from remote SUT.")

    def close(self):
        """
        Close SSH / SFTP connection if it exists. 
        This method is useful in `finally` blocks for releasing resources. 
        """
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
