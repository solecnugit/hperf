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
        self.parser = Parser()
        self.argv = argv

    def hperf(self):
        self.parse()
        self.profile()

    def parse(self):
        self.parser.parse_args(self.argv)
        self.configs = self.parser.configs
        self.connector = self.get_connector()

    def profile(self):
        self.profiler = self.get_profiler(self.connector)
        self.profiler.profile()

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

    def get_analyzer(self, connector: Connector) -> Analyzer:
        """
        instantiate an Analyzer based on the parsed configuration
        :param connector: an instance of Connector
        :return:
        """
        return Analyzer(connector=connector)
