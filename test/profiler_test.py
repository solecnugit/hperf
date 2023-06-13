import sys, importlib

if __name__ == "__main__":
    sys.path.append("/home/tongyu/project/hperf")
    profiler_module = importlib.import_module("profiler")

    Profiler = getattr(profiler_module, "Profiler")

    