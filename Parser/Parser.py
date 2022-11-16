from argparse import ArgumentParser
from typing import Sequence

from Analyzer.Analyzer import Analyzer
from Connector.Connector import Connector
from Connector.LocalConnector import LocalConnector
from Connector.RemoteConnector import RemoteConnector
import json

from Profiler.Profiler import Profiler
from Task.Task import Task


class Parser:
    """
    Parser: parse arguments passed from command line and instantiate Task, Profiler and Connector
    """

    def __init__(self) -> None:
        """
        constructor of `Parser`
        """
        self.parser = ArgumentParser()
        # define options
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument("-l", "--local",
                           help="profile on local host",
                           action="store_true")
        group.add_argument("-r", "--remote",
                           type=str,
                           help="profile on remote host")
        self.parser.add_argument("-C", "--config",
                                 type=str,
                                 help="specify a configuration file with JSON format")
        self.parser.add_argument("-t", "--time",
                                 type=int,
                                 help="time of profiling (s)")
        self.parser.add_argument("--verbose",
                                 help="increase output verbosity",
                                 action="store_true")
        self.parser.add_argument("-p",
                                 "--pid",
                                 help="pid of the process that hperf profile")
        self.parser.add_argument("-c",
                                 "--cpu",
                                 help="specify core(s) id to profile")
        self.parser.add_argument("--tmp",
                                 help="the temporary directory to store results and logs")

    def parse_args(self, argv: Sequence[str]) -> dict:
        """
        parse arguments passed from command line and return an instance of Connector
        :param argv: a list of arguments
        :return configs: configure of this hperf run
        """
        configs = {}
        args = self.parser.parse_args(argv)
        # if -c option is specified, load the JSON file and initialize config dict
        if args.config:
            with open(args.config) as f:
                configs.update(json.load(f))
        # parse other options and arguments and update config dict
        # config specified in command line will overwrite the config defined in JSON file
        if args.verbose:
            print("Verbosity turned on.")
        if args.remote:
            configs["host_type"] = "remote"
            configs["host_address"] = args.remote
        else:
            configs["host_type"] = "local"
        if args.pid:
            configs["pid"] = args.pid
        if args.tmp:
            configs["tmp_dir"] = args.tmp
        return configs
 