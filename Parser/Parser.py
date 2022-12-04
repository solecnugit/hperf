from argparse import ArgumentParser
from typing import Sequence
import json
import os


class Parser:
    """
    Parser is responsible for parsing arguments passed from command line and instantiate Task, Profiler and Connector
    """
    def __init__(self) -> None:
        """
        Constructor of 'Parser'
        """
        self.parser = ArgumentParser()
        # Define options:
        # [--local | --remote REMOTE]: Specify the system under test, local host or remote host.
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument("-l", "--local",
                           help="profile on local host",
                           action="store_true")
        group.add_argument("-r", "--remote",
                           type=str,
                           help="profile on remote host and specify a connect string.")
        # [--config CONFIG]
        self.parser.add_argument("-C", "--config",
                                 type=str,
                                 help="specify a configuration file with JSON format.")
        # [--time TIME]
        self.parser.add_argument("-t", "--time",
                                 type=int,
                                 help="time of profiling (s).")
        # [--pid PID]: Specify a process to monitor by PID.
        # 
        self.parser.add_argument("-p",
                                 "--pid",
                                 help="pid of the process that hperf profile.")
        # [--cpu CPU]: Specify a list of cpu ids.
        # hperf will conduct a system-wide profiling so that the list will only affect the output.
        # If not specified, it will output performance data of all cpus.
        self.parser.add_argument("-c",
                                 "--cpu",
                                 help="specify a list of cpu ids to profile.")
        # [--tmp-dir]: 
        self.parser.add_argument("--tmp-dir", type=str,
                                 help="the temporary directory to store results and logs.")
        self.parser.add_argument("--metrics", type=str,
                                 help="metrics you want to profile.")
        self.parser.add_argument(
            "--port", type=int, help="the remote ssh port")
        self.parser.add_argument(
            "--nmi", help="Whether to turn off NMI watchdog.", action="store_true")

    def parse_args(self, argv: Sequence[str]) -> dict:
        """
        Parse the options and parameters passed from command line and return an instance of Connector
        :param argv: a list of arguments
        :return configs: configure of this hperf run
        """
        configs = {}
        args = self.parser.parse_args(argv)
        # if -C option is specified, load the JSON file and initialize config dict
        if args.config:
            with open(args.config) as f:
                configs.update(json.load(f))
        # parse other options and arguments and update config dict
        # config specified in command line will overwrite the config defined in JSON file
        if args.remote:
            configs["host_type"] = "remote"
            self.__parse_remote_str__(args.remote, configs)
            if args.port:
                configs["port"] = args.port
        else:
            configs["host_type"] = "local"
        if args.pid:
            configs["pid"] = args.pid
        if args.cpu:
            configs["cpu_list"] = args.cpu
        if args.tmp_dir:
            configs["tmp_dir"] = args.tmp_dir
        if args.metrics:
            configs["metrics"] = args.metrics
        return configs

    """
        Parse string including username, hostname, password or private key file.
        The string format is 'username@hostname:password(private key file)'
    """

    def __parse_remote_str__(self, remote_str: str, configs: dict):
        remote_str.strip()
        remote_strs = remote_str.split("@", 1)
        configs["user_name"] = remote_strs[0]
        remote_strs = remote_strs[1].split(":", 1)
        configs["host_name"] = remote_strs[0]
        if os.path.exists(remote_strs[1]):
            configs["private_key"] = remote_strs[1]
        else:
            configs["password"] = remote_strs[1]
