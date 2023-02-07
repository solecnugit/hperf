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
    `Controller` is responsible for the whole process control of hperf.
    Users can conduct profiling for workload by calling `hperf()` method.
    """
    VERSION = "v1.1.0"

    def __init__(self, argv: Sequence[str]):
        """
        Constructor of `Controller`.
        :param `argv`: options and arguments passed from command line when invoke `hperf`. 
        Usually, it should be `sys.argv[1:]` (since `sys.argv[0]` is `hperf.py`).
        """
        self.__argv = argv    # (private) the original command line options and parameters

        self.configs = {}    # a dict contains parsed configurations for the following steps
        self.parser = OptParser()

        self.connector: Connector = None
        self.profiler: Profiler = None
        self.analyzer: Analyzer = None
        self.event_groups: EventGroup = None

        # initialize `Logger`
        # Note: Since `Logger` follows singleton pattern, 
        # it is unnecessary to pass the reference of the instance of `Logger` to other classes throught their constructor.
        # When we need to log records, use the method `logging.getLogger(<name>)` provided by module logging to get the instance of `Logger`,
        # where it will get the very same instance of `Logger` as long as the `<name>` is the same.
        self.logger: logging.Logger = logging.getLogger("hperf")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)-15s %(levelname)-8s %(message)s")

        # logs will output to both console and file
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
        Call this method to start profiling for workloads.
        """
        # TODO: add `-v`/`--version` option to print the version
        # now it will always print at the first. 
        self.logger.info(f"hperf {Controller.VERSION}")

        # step 1.
        self.__parse()

        # step 2.
        self.__profile()

        # step 3.
        self.__analyze()

        # save logs to file in the local test directory
        # TODO: in future, `Controller` is responsible for unified exceptional handling, so that this method will be useful in `finally` blocks
        self.__save_log_file()
    
    def __parse(self):
        """
        Parse the original command line options and arguments (`.argv`) and then get the configuration dict (`.configs`). 
        Based on the configuration dict, validate the configurations. 
        If passed the validation, instantiate `Connector` (`.connector`). 
        """
        # step 1.1. parse the original command line options and arguments
        self.configs = self.parser.parse_args(self.__argv)

        # step 1.2. if verbosity is declared (`-v` option), change the threshold of log level to print to console:
        # log level: DEBUG < INFO < WARNING < ERROR < CRITICAL
        # for file: always > DEBUG, not affected by `-v` option
        # for console: > INFO (default), > DEBUG (if verbosity is declared)
        if "verbose" in self.configs:
            self.__handler_stream.setLevel(logging.DEBUG)
        
        # step 1.3. validate the configurations
        # TODO: in future, more the validation of parsed configurations should be added here or in `OptParser`
        # if command is empty, exit the program
        if "command" not in self.configs:
            self.logger.error("workload is not specified")
            exit(-1)
        
        # step 1.4. instantiate `Connector`
        self.connector = self.__get_connector()

    def __get_connector(self) -> Connector:
        """
        Depend on the parsed configurations (`.configs`), instantiate a `LocalConnector` or `RemoteConnector` (`.connector`).  
        `LocalConnector` and `RemoteConnector` are extended from interface `Connector`, which defined useful methods for other modules 
        to interact with SUT, where the former is for local SUT while the latter is for remote SUT. 
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
        Instantiate `EventGroup` (`.event_groups`) and `Profiler` (`.profiler`) based on the parsed configurations (`.configs`). 
        Then it will call the methods of `Profiler`. The following steps will be conducted: 
        1) run sanity check, 
        2) generate and execute profiling script on SUT and save the raw performance data in the test directory 
        (a sub-directory in the temporary directory which can be obtained by `.connector.get_test_dir_path()` method), 
        3) if the `.connector` is an instance of `RemoteConnector`, close SSH / SFTP connection between remote SUT and local host. 
        """
        self.event_groups = EventGroup(self.connector)
        self.profiler = Profiler(self.connector, self.configs, self.event_groups)
        
        # step 2.1. sanity check
        # if sanity check does not pass, user choose whether to continue profiling. 
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
        
        # step 2.2. profile
        self.profiler.profile()
        
        # step 2.3. for RemoteConnector, close SSH / SFTP connection between remote SUT and local host
        if isinstance(self.connector, RemoteConnector):
            self.connector.sftp.close()
            self.connector.client.close()

    def __analyze(self):
        """
        Analyze the raw performance data which is generated by `Profiler`. 
        Then output the report of performance metrics to the test directory. 
        """
        self.analyzer = Analyzer(self.connector, self.configs, self.event_groups)
        print(self.analyzer.get_aggregated_metrics(to_csv=True))

    def __save_log_file(self):
        """
        Copy the log file from `self.log_filed_path` to the test directory for this run. 
        The `Logger` will temporarily write logs to this file (since `Logger` is instantiated before `Connector`) 
        and copy to the test directory for the convenience of users. 
        """
        source = self.log_file_path
        target = os.path.join(self.connector.get_test_dir_path(), "hperf.log")
        try:
            copyfile(source, target)
        except IOError:
            self.logger.error(f"fail to copy log file {source} to the test directory {target}")
            exit(-1)
        self.logger.info(f"logs for this run are saved in {target}")

