from Connector.Connector import Connector
import subprocess
import os


class LocalConnector(Connector):
    def __init__(self) -> None:
        """
        constructor of `LocalConnector`, extended from `Connector`
        """
        super(LocalConnector, self).__init__()

    def run_command(self, command: str) -> str:
        """
        pass command to the system under test to execute and return the output
        :param command: command to be executed
        :return: output
        """
        try:
            completed_process = subprocess.run(args=command, shell=True, check=True, capture_output=True)
            output = completed_process.stdout.decode("utf-8")
            return output
        except subprocess.CalledProcessError as e:
            print(e.args)
        return "done"

    def get_tmp_file_path(self, tmp_file_path: str) -> str:
        """
        For the implementation of LocalConnector, 
        it will check the temporary file on local host, which records the output of perf,
        If the file exists, return the same path (since Analyzer is able to access to the file);
        else it will raise an exception.
        For the implementation of RemoteConnector,
        it will check the temporary file on remote host.
        If the file exists, it will copy the file to this system through SSH connection and return the path of the copied file;
        else it will also raise an exception.
        """
        if os.access(tmp_file_path, os.R_OK):
            return tmp_file_path
        else:
            raise RuntimeError("Local temporary profiling raw data file does not exist.")

