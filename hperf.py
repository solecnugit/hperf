import sys
from controller import Controller


# The entrance of hperf. Users can invoke hperf from command line, like:
# $ python hperf.py <params>
if __name__ == "__main__":
    # Initialize Controller, which controls the process of hperf.
    controller = Controller(sys.argv[1:])
    # method 'hperf()' encapsulates the process of workload profiling.
    controller.hperf()