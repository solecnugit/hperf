import logging
from typing import Sequence
from opt_parser import OptParser
from profiler.profiler import Profiler
from analyzer import Analyzer
from connector import Connector, LocalConnector, RemoteConnector


class Controller:
    """
    'Controller' is responsible for process control of hperf.
    Users can conduct profiling by calling 'hperf()' method after instantiate 'Controller'.
    """
    VERSION = "v1.0.0"
    LOG_FORMAT = "%(asctime)-15s %(levelname)-8s %(message)s"    # log format for 'loggging'

    def __init__(self, argv: Sequence[str]):
        """
        Constructor of 'Controller'.
        :param argv: options and parameters passed from command line when invoke 'hperf'. 
        Usually, it should be 'sys.argv[1:]'.
        """
        self.argv = argv    # the original command line options and parameters

        self.configs = {}    # a dict contains parsed configurations for the following steps
        self.parser = OptParser()

        self.connector = None    # an instance of 'Connector'
        self.profiler = None    # an instance of 'Profiler'
        self.analyzer = None    # an instance of 'Analyzer'

        # TODO: Set more configs for logging, such as the path of log file.
        logging.basicConfig(format=Controller.LOG_FORMAT, level=logging.DEBUG)
        logging.info(f"hperf {Controller.VERSION}")    # show the version of hperf

        # TODO: using global 'logging' instead of bringing in a reference of 'Logger' for convinience
        # e.g. logging.debug("some message") / logging.warning("some message") / logging.error("some message")

    def hperf(self):
        """
        Conduct profiling.
        This method covers the whole process of profiling.
        """
        # Step 1. parse the original command line options and parameters
        self.__parse()
        # TODO: If the '--verbose' or '-v' option declared, print corresponding command in console for debugging

        # Step 2. conduct profiling by executing 'perf stat ...' command
        self.__profile()

        # Step 3. 
        # self.__print_profile_result__()
        # self.__print_profile_err__()
        # self.__clear__()
    
    def __parse(self):
        """
        Parse the original command line options and parameters and get the configuration dict.
        Based on the configuration dict, initialze a 'Connector'.
        """
        self.configs = self.parser.parse_args(self.argv)
        self.connector = self.__get_connector()

    def __profile(self):
        """

        """
        self.profiler = self.__get_profiler()
        self.profiler.profile()

    # TODO: this method can be subsituted by adjusting the level of 'logging.basicConfig'
    # def __print_profile_cmd__(self):
    #     self.profiler = self.__get_profiler__()
    #     print(self.profiler.__profile_cmd__())

    def __print_profile_result__(self):
        self.profiler.result_output()

    def __print_profile_err__(self):
        self.profiler.err_output()

    """
        remove all tmp files and kill perf(sometimes perf will not killed by the script.)
    """

    def __clear__(self):
        self.profiler.clear()

    def __get_connector(self) -> Connector:
        """
        Depend on the parsed configurations, initialize a 'LocalConnector' or 'RemoteConnector'
        """
        if self.configs["host_type"] == "local":
            logging.debug("SUT is local host")
            return LocalConnector(self.configs)
        else:
            logging.debug("SUT is remote host")
            return RemoteConnector(self.configs)

    def __get_profiler(self) -> Profiler:
        """

        """
        return Profiler(self.connector, self.configs)

    def __get_analyzer__(self) -> Analyzer:
        pass
