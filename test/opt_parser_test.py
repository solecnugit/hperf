import sys, importlib

if __name__ == "__main__":
    sys.path.append("/home/tongyu/project/hperf")
    opt_parser_module = importlib.import_module("opt_parser")

    OptParser = getattr(opt_parser_module, "OptParser")

    parser = OptParser()

    argv = [ "-v", "-t", "10", "--tmp-dir", "./tmp/", "-c", "2,3", "sleep", "10" ]
    configs = parser.parse_args(argv)
    print(configs)

    argv = [ "-v", "-t", "10", "-r", "tongyu@ampere01.solelab.tech", "--tmp-dir", "./tmp/", "-c", "2,3", "sleep", "10" ]
    configs = parser.parse_args(argv)
    print(configs)
    