import sys
from controller import Controller


"""
The entrance of hperf. Users can invoke hperf from command line, like:
```
$ python hperf.py [options] <command>
```
refer to README.md for supported options
"""
if __name__ == "__main__":
    # initialize `Controller`, which controls the process of hperf.
    controller = Controller(sys.argv[1:])

    # method `hperf()`` encapsulates the whole process of profiling.
    controller.hperf()