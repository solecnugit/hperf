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
        # a dict stored parsed configurations, initialized by default configurations
        self.configs = {
            "workload_command": "cd ~/code/hperf/test/ ./mat_mul.c 128"
        }
        # define arguments: workload_command
        self.parser.add_argument("workload_command",
                                 help="Any command you can specify in a shell")
        # define options
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument("-l", "--local",
                           help="profile on local host",
                           action="store_true")
        group.add_argument("-r", "--remote",
                           type=str,
                           help="profile on remote host")
        self.parser.add_argument("-c", "--config",
                                 type=str,
                                 help="specify a configuration file with JSON format")
        self.parser.add_argument("-t", "--time",
                                 type=int,
                                 help="time of profiling (s)")
        self.parser.add_argument("--verbose",
                                 help="increase output verbosity",
                                 action="store_true")


    def parse_args(self, argv: Sequence[str]) -> None:
        """
        parse arguments passed from command line and return an instance of Connector
        :param argv: a list of arguments
        """
        args = self.parser.parse_args(argv)
        # if -c option is specified, load the JSON file and initialize config dict
        if args.config:
            with open(args.config) as f:
                self.configs.update(json.load(f))
        # parse other options and arguments and update config dict
        # config specified in command line will overwrite the config defined in JSON file
        self.configs["workload_command"] = args.workload_command
        if args.verbose:
            print("Verbosity turned on.")
        if args.remote:
            if args.local:
                raise Exception("Cannot set both remote and local!")
            self.configs["host_type"] = "remote"
            self.configs["host_address"] = args.remote
        else:
            self.configs["host_type"] = "local"

    def get_args(self) -> dict:
        """
        return a dict of configurations
        :return: a dict of configurations
        """
        return self.configs

    def get_connector(self) -> Connector:
        """
        instantiate a Connector based on the parsed configuration
        :return: an instance of Connector
        """
        if self.configs["host_type"] == "local":
            return LocalConnector()
        else:
            return RemoteConnector(host_address=self.configs["host_address"])

    def get_profiler(self, connector: Connector) -> Profiler:
        """
        instantiate a Profiler based on the parsed configuration
        a instance of Profiler has a member of a reference to an instance of Connector.
        Profiler will call the methods provided by Connector to execute command on system under test
        :param connector: an instance of Connector
        :return:
        """
        return Profiler(connector=connector)

    def get_task(self, connector: Connector) -> Task:
        """
        instantiate a Task based on the parsed configuration
        :param connector: an instance of Connector
        :return:
        """
        return Task(connector=connector,
                    workload_command=self.configs["workload_command"])

    def get_analyzer(self, connector: Connector) -> Analyzer:
        """
        instantiate an Analyzer based on the parsed configuration
        :param connector: an instance of Connector
        :return:
        """
        return Analyzer(connector=connector)
