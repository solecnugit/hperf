import logging
import os
import sys
from datetime import datetime
import re
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
    Beside this, it also responsible for unified exception handling and logging. 
    Users can conduct profiling for workload by calling `hperf()` method.
    """

    def __init__(self, argv: Sequence[str]):
        """
        Constructor of `Controller`.
        :param `argv`: Options and arguments passed from command line when invoke `hperf`. 
        Usually, it should be `sys.argv[1:]` (since `sys.argv[0]` is `hperf.py`). 
        """
        self.__argv = argv    # (private) the original command line options and parameters

        self.configs = {}    # a dict contains parsed configurations for the following steps
        self.parser = OptParser()

        self.connector: Connector = None
        self.profiler: Profiler = None
        self.analyzer: Analyzer = None
        self.event_groups: EventGroup = None

        # Initialize `Logger`
        # **Note**: Since `Logger` follows singleton pattern,
        # it is unnecessary to pass the reference of the instance of `Logger` to other classes throught their constructor.
        # When we need to log records, use the method `logging.getLogger(<name>)` provided by module logging to get the instance of `Logger`,
        # where it will get the very same instance of `Logger` as long as the `<name>` is the same.
        self.logger: logging.Logger = logging.getLogger("hperf")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)-15s %(levelname)-8s %(message)s")

        # Logs will output to both console and file
        # [1] For console output of logs
        self.__handler_stream = logging.StreamHandler()
        self.__handler_stream.setFormatter(formatter)
        self.__handler_stream.setLevel(logging.INFO)    # logs with level above INFO will be printed to console by default
        self.logger.addHandler(self.__handler_stream)

        # [2] For file output of logs
        self.log_file_path = "/tmp/hperf/hperf.log"
        try:
            os.makedirs("/tmp/hperf/", exist_ok=True)
            self.__handler_file = logging.FileHandler(self.log_file_path, "w")
        except Exception:
            print("Initialization failure.")
            sys.exit(-1)
        self.__handler_file.setLevel(logging.DEBUG)    # all logs will be writen to the log file by default
        self.__handler_file.setFormatter(formatter)
        self.logger.addHandler(self.__handler_file)

        # SEE: `Controller.__prework()`
        self.tmp_dir: str = ""    # user-specified temporary directory for saving files for different runs
        self.test_id: str = ""    # a sub-directory in temporary directory for a single run

    def hperf(self):
        """
        This method covers the whole process of profiling.
        Call this method to start profiling for workloads.
        """
        try:
            # step 1.
            self.__parse()    # may raise `SystemExit` or `ParserError`
            # step 2.
            self.__prework()
            # step 3.
            self.__profile()    # may raise `SystemExit`, `ConnectorError` or `ProfilerError`
            # step 4.
            self.__analyze()
        # `Controller` is responsible for unified exceptional handling ... 
        except SystemExit as e:
            self.__system_exit_handler(e)
        except KeyboardInterrupt:
            self.__keyboard_interrupt_handler()
        except Exception as e:
            self.__exception_handler(e)
        finally: 
            # if the `.connector` is an instance of `RemoteConnector`, close SSH / SFTP connection between remote SUT and local host, 
            # no matter whether the program exit normally or abnormally.  
            if isinstance(self.connector, RemoteConnector):
                self.connector.close()
                self.logger.debug("RemoteConnector closed.")
            if self.connector:
                self.__save_log_file()

    def __parse(self):
        """
        Parse and validate the original command line options and arguments (`.argv`) 
        and then get the configuration dict (`.configs`). 
        If `-v`/`--verbose` option is declared, the threshold of log level will change. 
        :raises:
            `SystemExit`: If `-V` and `-h` options is declared. In that case, hperf will print corrsponding information and exit. 
            `ParserError`: If options and arguments are invalid
        """
        # step 1.1. parse and validate the original command line options and arguments
        self.configs = self.parser.parse_args(self.__argv)    # may raise `SystemExit` or `ParserError`

        # step 1.2. if verbosity is declared (`-v` option), change the threshold of log level to print to console:
        # log level: DEBUG < INFO < WARNING < ERROR < CRITICAL
        # for file: always > DEBUG, not affected by `-v` option
        # for console: > INFO (default), > DEBUG (if verbosity is declared)
        if "verbose" in self.configs:
            self.__handler_stream.setLevel(logging.DEBUG)

    def __prework(self):
        """
        Complete some preworks based on the valid configurations (`.configs`) before profiling. 
        The following steps will be conducted based on the parsed configurations: 
        1) create an unique test directory in the temporary directory (`.tmp_dir`)
        2) instantiate a `LocalConnector` or `RemoteConnector` (`.connector`)

        The temporary directory (`.configs["tmp_dir"]`) specified by command line options `--tmp-dir` (`/tmp/hperf/` by default). 
        The test directory is for this run of hperf and used to save profiling scripts, raw performance data, analysis results, log file, etc. 
        `LocalConnector` and `RemoteConnector` are extended from interface `Connector`, which implement some useful methods for other modules 
        to interact with SUT, where the former is for local SUT while the latter is for remote SUT. 

        :raises:
            `ConnectorError`: For `RemoteConnector`, if fail to establish connection to remote SUT
        """
        # step 2.1. create an unique test directory in the temporary directory
        #   step 2.1.1 access or create the temporary directory specified by user
        selected_tmp_dir = self.configs["tmp_dir"]
        #     [case 1] if the temporary directory exists, check the R/W permission
        if os.path.exists(selected_tmp_dir):
            if os.access(selected_tmp_dir, os.R_OK | os.W_OK):
                self.tmp_dir = os.path.abspath(selected_tmp_dir)
                self.logger.debug(f"set temporary directory: {self.tmp_dir} (already exists)")
            else:
                bad_tmp_dir = os.path.abspath(selected_tmp_dir)
                self.logger.warning(f"invalid temporary directory: {bad_tmp_dir} (already exists but has no R/W permission)")
                self.logger.warning("reset temporary directory: '/tmp/hperf/'")
                os.makedirs("/tmp/hperf/", exist_ok=True)
                # **Note**: this action will change the value of `configs["tmp_dir"]`
                self.tmp_dir = self.configs["tmp_dir"] = "/tmp/hperf/"
        #     [case 2] if the temporary directory does not exist, try to create the directory
        else:
            try:
                os.makedirs(selected_tmp_dir)
                self.tmp_dir = os.path.abspath(selected_tmp_dir)
                self.logger.debug(f"success to create the temporary directory {self.tmp_dir}")
            except OSError:
                bad_tmp_dir = os.path.abspath(selected_tmp_dir)
                self.logger.warning(f"invalid temporary directory: {bad_tmp_dir} (fail to create the temporary directory)")
                self.logger.warning("reset temporary directory: '/tmp/hperf/'")
                os.makedirs("/tmp/hperf/", exist_ok=True)
                # **Note**: this action will change the value of 'configs["tmp_dir"]'
                self.tmp_dir = self.configs["tmp_dir"] = "/tmp/hperf/"
        
        #   step 2.1.2. find a unique test id (`.__find_test_id()`) and create test directory
        # search the temporary directory (`.tmp_dir`) and get a string with an unique test id, 
        # then create a sub-directory named by this string in the temporary directory for saving files and results.
        self.test_id = self.__find_test_id()
        os.makedirs(self.get_test_dir_path())
        self.logger.info(f"local test directory: {self.get_test_dir_path()}")

        # step 2.2. instantiate a `LocalConnector` or `RemoteConnector`
        if self.configs["host_type"] == "local":
            self.logger.debug("SUT is on local")
            self.connector = LocalConnector(self.get_test_dir_path())
        else:
            self.logger.debug("SUT is on remote")
            self.connector = RemoteConnector(self.get_test_dir_path(), 
                                             hostname=self.configs["hostname"],
                                             username=self.configs["username"],
                                             password=self.configs["password"])    # may raise `ConnectorError`

    def __find_test_id(self) -> str:
        """
        Search the temporary directory (`.tmp_dir`) and return a string with an unique test directory.

        e.g. In the temporary directory, there are many sub-directory named `<date>_test<id>` for different runs.
        If `20221206_test001` and `202211206_test002` are exist, it will return `202211206_test003`.
        :return: a directory name with an unique test id for today
        """
        today = datetime.now().strftime("%Y%m%d")
        max_id = 0
        pattern = f"{today}_test(\d+)"
        for item in os.listdir(self.tmp_dir):
            path = os.path.join(self.tmp_dir, item)
            if os.path.isdir(path):
                obj = re.search(pattern, path)
                if obj:
                    found_id = int(obj.group(1))
                    if found_id > max_id:
                        max_id = found_id
        test_id = f"{today}_test{str(max_id + 1).zfill(3)}"
        return test_id

    def get_test_dir_path(self) -> str:
        """
        Get the abusolute path of the unique test directory for this test. 
        :return: an abusolute path of the unique test directory for this test
        """
        return os.path.join(self.tmp_dir, self.test_id)

    def __profile(self):
        """
        Instantiate `EventGroup` (`.event_groups`) and `Profiler` (`.profiler`) based on the parsed configurations (`.configs`). 
        Then it will call the methods of `Profiler`. The following steps will be conducted: 
        1) run sanity check, 
        2) generate and execute profiling script on SUT and save the raw performance data in the test directory 
        (a sub-directory in the temporary directory which can be obtained by `.connector.get_test_dir_path()` method), 

        :raises:
            `SystemExit`: if user choose not to continue profiling when sanity check fails 
            `ConnectorError`: if encounter errors when executing command or script on SUT
            `ProfilerError`: if the profiling is not successful on SUT
        """
        self.event_groups = EventGroup(self.connector)
        self.profiler = Profiler(self.connector, self.configs, self.event_groups)

        # step 3.1. sanity check
        # if sanity check does not pass, let user choose whether to continue profiling.
        if not self.profiler.sanity_check():
            select = input("Detected some problems which may interfere profiling. Continue profiling? [y|N] ")
            while True:
                if select == "y" or select == "Y":
                    break
                elif select == "n" or select == "N":
                    sys.exit(0)    # raise `SystemExit`
                else:
                    select = input("please select: [y|N] ")
        else:
            self.logger.info("sanity check passed.")

        # step 3.2. profile
        self.profiler.profile()    # may raise `ProfilerError` or `ConnectorError` (for `RemoteConnector`)

    def __analyze(self):
        """
        Analyze the raw performance data which is generated by `Profiler`. 
        Then output the report of performance metrics to the test directory. 
        """
        self.analyzer = Analyzer(self.get_test_dir_path(), self.configs, self.event_groups)
        self.analyzer.analyze()
        
        hw_timeseries, sw_timeseries = self.analyzer.get_timeseries(to_csv=True)
        print(hw_timeseries)
        print(sw_timeseries)
        print(self.analyzer.get_aggregated_metrics(to_csv=True))
        self.analyzer.get_timeseries_plot()

    def __save_log_file(self):
        """
        Copy the log file from `self.log_filed_path` to the test directory for this run. 
        The `Logger` will temporarily write logs to this file (since `Logger` is instantiated before `Connector`) 
        and copy to the test directory for the convenience of users. 
        """
        source = self.log_file_path
        target = os.path.join(self.get_test_dir_path(), "hperf.log")
        try:
            copyfile(source, target)
        except IOError:
            self.logger.warning(f"fail to copy log file {source} to the test directory {target}")
            self.logger.info(f"logs for this run are saved in {source} temporarily")
        else:
            self.logger.info(f"logs for this run are saved in {target}")

    # the following method is responsible for unified exception handling ... 
    
    def __system_exit_handler(self, e: SystemExit):
        """
        Handle all possible `SystemExit` exceptions during the whole process of hperf.
        `SystemExit` is triggered by `sys.exit(code)` statement, 
        where `code == 0` represents the program exits normally. 
        """
        if e.args[0] == 0:
            self.logger.debug("Program exits normally.")
        else:
            self.logger.error("Program exits abnormally.")

    def __keyboard_interrupt_handler(self):
        """
        Handle all possible `KeyboardInterrupt` exceptions during the whole process of hperf. 
        `KeyboardInterrupt` is triggered by `Ctrl + C` in terminal. 
        """
        self.logger.error("Keyboard Interrupt.")
    
    def __exception_handler(self, e: Exception):
        """
        Handle all possible Exceptions (Errors) during the whole process of hperf. 
        When an error is catched, the following code will not be executed and finally the program exits. 
        So that this method is to print error message and do some cleaning works. 
        `Exception` has an attribute `args` where `args[0]` is the message. 
        """
        self.logger.error(f"{e.args[0]}")
