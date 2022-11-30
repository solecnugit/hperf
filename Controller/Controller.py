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
        self.__parse__()
        self.__print_profile_cmd__()
        self.__profile__()
        self.__print_profile_result__()
        self.__print_profile_err__()
        self.__clear__()
        

    def __parse__(self):
        self.configs = self.parser.parse_args(self.argv)
        self.connector = self.__get_connector__()

    def __profile__(self):
        self.profiler = self.__get_profiler__()
        self.profiler.profile()

    def __print_profile_cmd__(self):
        self.profiler = self.__get_profiler__()
        print(self.profiler.__profile_cmd__())

    def __print_profile_result__(self):
        self.profiler.result_output()

    def __print_profile_err__(self):
        self.profiler.err_output()

    """
        remove all tmp files and kill perf(sometimes perf will not killed by the script.)
    """
    def __clear__(self):
        self.profiler.clear()

    def __get_connector__(self) -> Connector:
        if self.configs["host_type"] == "local":
            return LocalConnector(self.configs)
        else:
            return RemoteConnector(self.configs)

    def __get_profiler__(self) -> Profiler:
        return Profiler(self.connector, self.configs)

    def __get_analyzer__(self) -> Analyzer:
        pass