import logging
from typing import Sequence
from opt_parser import OptParser
from profiler import Profiler
from analyzer import Analyzer
from connector import Connector, LocalConnector, RemoteConnector
from event_group import EventGroup


class Controller:
    """
    'Controller' is responsible for process control of hperf.
    Users can conduct profiling by calling 'hperf()' method after instantiate 'Controller'.
    """
    VERSION = "v1.0.1"

    def __init__(self, argv: Sequence[str]):
        """
        Constructor of 'Controller'.
        :param argv: options and parameters passed from command line when invoke 'hperf'. 
        Usually, it should be 'sys.argv[1:]' (since 'sys.argv[0]' is 'hperf.py').
        """
        self.argv = argv    # the original command line options and parameters

        self.configs = {}    # a dict contains parsed configurations for the following steps
        self.parser = OptParser()

        self.connector: Connector = None    # an instance of 'Connector'
        self.profiler: Profiler = None    # an instance of 'Profiler'
        self.analyzer: Analyzer = None    # an instance of 'Analyzer'
        self.event_groups: EventGroup = None    # an instancce of 'EventGroup'

        # TODO: Set more configs for logging, such as the path of log file.
        logging.basicConfig(format="%(asctime)-15s %(levelname)-8s %(message)s", level=logging.INFO)
        logging.info(f"hperf {Controller.VERSION}")    # show the version of hperf

        # TODO: using global 'logging' instead of bringing in a reference of 'Logger' for convinience
        # e.g. logging.debug("some message") / logging.warning("some message") / logging.error("some message")

    def hperf(self):
        """
        This method covers the whole process of profiling.
        """
        # Step 1. parse the original command line options and parameters
        self.__parse()
        # TODO: If the '--verbose' or '-v' option declared, print corresponding command in console for debugging 
        # by adjusting 'logging.basicConfig(level=...)'

        # Step 2. conduct profiling by executing script with 'perf stat ...' command
        # raw performance data will be saved in the temporary directory
        self.__profile()

        # Step 3. analyze the raw performance data and output realiable performance metrics
        self.__analyze()
    
    def __parse(self):
        """
        Parse the original command line options and parameters and get the configuration dict.
        Based on the configuration dict, initialze a 'Connector' for 'Profiler' and 'Analyzer'.
        """
        self.configs = self.parser.parse_args(self.argv)
        # if command is empty, exit the program
        if "command" not in self.configs:
            logging.error("workload is not specified")
            exit(-1)

        self.connector = self.__get_connector()

    def __get_connector(self) -> Connector:
        """
        Depend on the parsed configurations, initialize a 'LocalConnector' or 'RemoteConnector'
        """
        # Note: the instantiation of 'Connector' may change the value of 'self.configs["tmp_dir"]' 
        # if the parsed temporary directory is invalid (cannot be accessed).
        if self.configs["host_type"] == "local":
            logging.debug("SUT is on local host")
            return LocalConnector(self.configs)
        else:
            logging.debug("SUT is on remote host")
            # TODO: 'RemoteConnect' has not been fully implemented, when it is ready, remove the follwing exit()
            logging.error("RemoteConnector has not been implemented yet")
            exit(-1)
            return RemoteConnector(self.configs)

    def __profile(self):
        """
        Firstly run sanity check, then enerate and execute profiling script, where the raw performance data is saved in the temporary directory.
        """
        self.event_groups = EventGroup(self.connector)
        self.profiler = Profiler(self.connector, self.configs, self.event_groups)
        if not self.profiler.sanity_check():
            select = input("Detected some problems which may interfere profiling. Continue profiling? [y|N] ")
            while True:
                if select == "y" or select == "Y":
                    break
                elif select == "n" or select == "N":
                    logging.info("program exits")
                    exit(0)
                else:
                    select = input("please select: [y|N] ")
        else:
            logging.info("sanity check passed.")
        self.profiler.profile()

    def __analyze(self):
        """
        Analyze the raw performance data, then output the report of performance metrics.
        """
        self.analyzer = Analyzer(self.connector, self.configs, self.event_groups)
        print(self.analyzer.get_aggregated_metrics(to_csv=True))

