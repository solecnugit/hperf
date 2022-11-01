import sys
from Parser.Parser import Parser


if __name__ == "__main__":
    # Initialize Parser.
    parser = Parser()

    # sys.argv[] is an array of arguments passed from command line.
    # Considering hperf is a Python script, when invoking hperf, the first argument is the script name 'hperf.py'.
    # The arguments need to be parsed should exclude the first one.
    parser.parse_args(sys.argv[1:])

    # Parser will parse all arguments and get required configurations.
    # Based on that, Connector, Profiler and Task will be instantiated.
    # Connector should be instantiated first,
    # and the instance should be a parameter for the constructor of Profiler and Task.
    connector = parser.get_connector()
    profiler = parser.get_profiler(connector=connector)
    task = parser.get_task(connector=connector)
    analyzer = parser.get_analyzer(connector=connector)

    print(task.run_workload())
    profiler.profile()
    print(analyzer.get_raw_dataframe())


