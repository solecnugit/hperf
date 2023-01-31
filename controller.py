import logging
import os
from shutil import copyfile
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

        # initialize Logger
        # Note: Since Logger follows singleton pattern, it is unnecessary to pass the reference of the instance of Logger to other modules / classes.
        # When we need to log records, use the method logging.getLogger(<name>) provided by module logging to get the instance of Logger,
        # where it will get the very same instance of Logger as long as the <name> is same.
        self.logger = logging.getLogger("hperf")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)-15s %(levelname)-8s %(message)s")

        # [1] for console output of logs
        self.__handler_stream = logging.StreamHandler()
        self.__handler_stream.setFormatter(formatter)
        self.__handler_stream.setLevel(logging.INFO)    # logs with level above INFO will be printed to console by default
        self.logger.addHandler(self.__handler_stream)

        # [2] for file output of logs
        self.log_file_path = "/tmp/hperf/hperf.log"
        self.__handler_file = logging.FileHandler(self.log_file_path, "w")
        self.__handler_file.setLevel(logging.DEBUG)    # all logs will be writen to the log file by default
        self.__handler_file.setFormatter(formatter)
        self.logger.addHandler(self.__handler_file)

    def hperf(self):
        """
        This method covers the whole process of profiling.
        """
        self.logger.info(f"hperf {Controller.VERSION}")

        # Step 1. parse the original command line options and parameters
        self.__parse()

        # Step 2. conduct profiling by executing script with 'perf stat ...' command
        # raw performance data will be saved in the temporary directory
        self.__profile()

        # Step 3. analyze the raw performance data and output realiable performance metrics
        self.__analyze()

        self.__save_log_file()
    
    def __parse(self):
        """
        Parse the original command line options and parameters and get the configuration dict.
        Based on the configuration dict, initialze a 'Connector' for 'Profiler' and 'Analyzer'.
        """
        self.configs = self.parser.parse_args(self.argv)

        # if verbosity is declared, change the threshold of log level to print to console
        if "verbose" in self.configs:
            self.__handler_stream.setLevel(logging.DEBUG)
        
        # if command is empty, exit the program
        if "command" not in self.configs:
            self.logger.error("workload is not specified")
            exit(-1)
        
        self.connector = self.__get_connector()

    def __get_connector(self) -> Connector:
        """
        Depend on the parsed configurations, initialize a 'LocalConnector' or 'RemoteConnector'
        """
        # Note: the instantiation of 'Connector' may change the value of 'self.configs["tmp_dir"]' 
        # if the parsed temporary directory is invalid (cannot be accessed).
        if self.configs["host_type"] == "local":
            self.logger.debug("SUT is on local host")
            return LocalConnector(self.configs)
        else:
            self.logger.debug("SUT is on remote host")
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
                    self.logger.info("program exits")
                    exit(0)
                else:
                    select = input("please select: [y|N] ")
        else:
            self.logger.info("sanity check passed.")
        self.profiler.profile()
        
        # for RemoteConnector, close SSH / SFTP connection between remote SUT and local host
        if isinstance(self.connector, RemoteConnector):
            self.connector.sftp.close()
            self.connector.client.close()

    def __analyze(self):
        """
        Analyze the raw performance data, then output the report of performance metrics.
        """
        self.analyzer = Analyzer(self.connector, self.configs, self.event_groups)
        print(self.analyzer.get_aggregated_metrics(to_csv=True))

    def __save_log_file(self):
        """
        Copy the log file from '/tmp/hperf/hperf.log' to the test directory for this run.
        """
        source = self.log_file_path
        target = os.path.join(self.connector.get_test_dir_path(), "hperf.log")
        try:
            copyfile(source, target)
        except IOError:
            self.logger.error(f"fail to copy log file {source} to the test directory {target}")
            exit(-1)
        self.logger.info(f"logs for this run are saved in {target}")

