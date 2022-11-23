import logging
from typing import Sequence
from Parser.Parser import Parser
from Profiler.Profiler import Profiler
from Analyzer.Analyzer import Analyzer
from Connector.Connector import Connector
from Connector.LocalConnector import LocalConnector
from Connector.RemoteConnector import RemoteConnector


class Controller:
    def __init__(self, argv: Sequence[str]):
        self.configs = None
        self.connector = None
        self.profiler = None
        self.analyzer = None
        self.configs = {}
        self.parser = Parser()
        self.argv = argv
        self.logger = logging.getLogger("hperf")
    
    def hperf(self):
        """
        run hperf.
        """
        self.__parse()
        self.__print_profile_cmd()
        self.__profile()

    def __parse(self):
        self.configs = self.parser.parse_args(self.argv)
        self.connector = self.__get_connector()

    def __profile(self):
        self.profiler = self.__get_profiler()
        self.profiler.profile()

    def __print_profile_cmd(self):
        self.profiler = self.__get_profiler()
        print(self.profiler.profile_cmd())

    def __get_connector(self) -> Connector:
        """
        instantiate a Connector based on the parsed configuration
        :return: an instance of Connector
        """
        if self.configs["host_type"] == "local":
            return LocalConnector(self.configs)
        else:
            return RemoteConnector(self.configs, host_address=self.configs["host_address"])

    def __get_profiler(self) -> Profiler:
        """
        instantiate a Profiler which has a reference to an instance of Connector and a reference to an instance of configs.
        Profiler will call the methods provided by Connector to execute command on system under test
        :return: 
        """
        return Profiler(self.connector, self.configs)

    def __get_analyzer(self) -> Analyzer:
        pass