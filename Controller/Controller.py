import logging
from typing import Sequence
from Parser.Parser import Parser
from Profiler.Profiler import Profiler
from Analyzer.Analyzer import Analyzer
from Connector.Connector import Connector
from Connector.LocalConnector import LocalConnector
from Connector.RemoteConnector import RemoteConnector


class Controller:
    """
    'Controller' is responsible for process control of hperf.
    Users can conduct profiling by calling 'hperf()' method after instantiate 'Controller'.
    """
    def __init__(self, argv: Sequence[str]):
        """
        Constructor of 'Controller'.
        :param argv: options and parameters passed from command line when invoke 'hperf'. 
        Usually, it should be 'sys.argv[1:]'.
        """
        self.argv = argv    # the original command line options and parameters

        self.configs = {}    # a dict contains parsed configurations for the following steps
        self.parser = Parser()

        self.connector = None    # an instance of 'Connector'
        self.profiler = None    # an instance of 'Profiler'
        self.analyzer = None    # an instance of 'Analyzer'
        
        self.logger = logging.getLogger("hperf")
    
    def hperf(self):
        """
        Conduct profiling.
        This method covers the whole process of profiling.
        """
        self.__parse__()    # Step 1. parse the original command line options and parameters
        # TODO: If the '--verbose' or '-v' option declared, print corresponding command in console for debugging
        self.__print_profile_cmd__()
        self.__profile__()    # Step 2. conduct profiling by executing 'perf stat ...' command
        self.__print_profile_result__()    # Step 3. 
        self.__print_profile_err__()
        self.__clear__()
        

    def __parse__(self):
        """
        Parse the original command line options and parameters and get the configuration dict.
        Based on the configuration dict, initialze a 'Connector'.
        """
        self.configs = self.parser.parse_args(self.argv)
        self.connector = self.__get_connector__()

    def __profile__(self):
        """
        
        """
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