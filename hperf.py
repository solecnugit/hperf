import sys
from Parser import Parser

if __name__ == "__main__":
    hperf_parser = Parser()
    hperf_parser.parse_args(sys.argv[1:])
