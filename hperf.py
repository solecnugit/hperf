import sys
from Parser.Parser import Parser
from Controller.Controller import Controller


if __name__ == "__main__":
    # Initialize Controller, which controls the process of hperf.
    controller = Controller(sys.argv[1:])
    controller.hperf()