from argparse import ArgumentParser, REMAINDER
from typing import Sequence
import json
import os
import logging


class OptParser:
    """
    'OptParser' is responsible for parsing arguments passed from command line and instantiate Task, Profiler and Connector
    """

    def __init__(self) -> None:
        """
        Constructor of 'OptParser'
        """
        self.parser = ArgumentParser(prog="python hperf.py",
                                     description="hperf: an easy-to-use microarchitecture performance data collector")

        # positional arguments:
        self.parser.add_argument("command",
                                 # if option 'nargs' not set, command with arguments will not be accepted.
                                 nargs=REMAINDER,
                                 metavar="COMMAND",
                                 help="workload command you can specify in a shell")

        # required options:
        # TODO: some required options can be added in future

        # optional options:
        # [--remote SSH_CONN_STR]
        self.parser.add_argument("-r", "--remote",
                                 metavar="SSH_CONN_STR",
                                 type=str,
                                 help="profiling on remote host by specifying a SSH connection string (default on local host).")

        # TODO: add more options

        # [--config FILE_PATH]
        self.parser.add_argument("-f", "--config-file",
                                 metavar="FILE_PATH",
                                 type=str,
                                 help="specify a configuration file with JSON format.")
        # [--time SECOND]
        self.parser.add_argument("-t", "--time",
                                 metavar="SECOND",
                                 type=int,
                                 help="time of profiling (s).")
        # [--pid PID]: Specify a process to monitor by PID.
        # self.parser.add_argument("-p", "--pid",
        #                          metavar="PID",
        #                          type=str,
        #                          help="pid of the process that hperf profile.")
        # [--cpu CPU]: Specify a list of cpu ids.
        # hperf will conduct a system-wide profiling so that the list will only affect the output.
        # If not specified, it will output performance data of all cpus.
        # self.parser.add_argument("-c",
        #                          "--cpu",
        #                          help="specify a list of cpu ids to profile.")
        # [--tmp-dir]
        self.parser.add_argument("--tmp-dir",
                                 metavar="TMP_DIR_PATH",
                                 type=str,
                                 default="/tmp/hperf/",
                                 help="temporary directory to store profiling results and logs (default '/tmp/hperf/').")
        # self.parser.add_argument("--metrics", type=str,
        #                          help="metrics you want to profile.")
        # self.parser.add_argument(
        #     "--port", type=int, help="the remote ssh port")
        # self.parser.add_argument(
        #     "--nmi", help="Whether to turn off NMI watchdog.", action="store_true")

    def parse_args(self, argv: Sequence[str]) -> dict:
        """
        Parse the options and parameters passed from command line and return an instance of Connector
        :param argv: a list of arguments
        :return configs: configure of this hperf run
        """
        configs = {}

        args = self.parser.parse_args(argv)
        logging.debug(f"options and arguments passed from command line: {args}")

        # if -f/--config-file option is specified, load the JSON file and initialize config dict
        # if args.config:
        #     with open(args.config) as f:
        #         configs.update(json.load(f))

        # parse other options and arguments and update config dict
        # config specified in command line will overwrite the config defined in JSON file
        # step 1. workload command
        if args.command:
            configs["command"] = " ".join(args.command)
        
        # step 2. local / remote SUT (default local)
        if args.remote:
            configs["host_type"] = "remote"
            remote_configs = self.__parse_remote_str__(args.remote)
            configs.update(remote_configs)
            # if args.port:
            #     configs["port"] = args.port
        else:
            configs["host_type"] = "local"

        # if args.pid:
        #     configs["pid"] = args.pid
        # if args.cpu:
        #     configs["cpu_list"] = args.cpu
        
        # step 3. temporary directory
        if args.tmp_dir:
            configs["tmp_dir"] = args.tmp_dir

        # if args.metrics:
        #     configs["metrics"] = args.metrics

        logging.debug(f"parsed configurations: {configs}")

        return configs

    def __parse_remote_str__(self, ssh_conn_str: str) -> dict:
        """
        Parse the SSH connection string with the format of 'username@hostname:password(private key file)'
        :param ssh_conn_str: SSH connection string
        :return: a dict of remote host informations
        """
        # TODO: try to parse all information for the remote SSH connection from the parameter of -r / --remote option.

        remote_configs = {}
        # mock data
        remote_configs["username"] = "tongyu"
        remote_configs["hostname"] = "gpu2.solelab.tech"
        remote_configs["private_key"] = "~/.ssh/id_rsa"
        remote_configs["password"] = "123456"
        return remote_configs

        # remote_str.strip()
        # remote_strs = remote_str.split("@", 1)
        # configs["user_name"] = remote_strs[0]
        # remote_strs = remote_strs[1].split(":", 1)
        # configs["host_name"] = remote_strs[0]
        # if os.path.exists(remote_strs[1]):
        #     configs["private_key"] = remote_strs[1]
        # else:
        #     configs["password"] = remote_strs[1]
