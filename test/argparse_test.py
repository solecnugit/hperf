import argparse


parser = argparse.ArgumentParser(prog="python hperf.py",
                                 description="hperf: an easy-to-use microarchitecture performance data collector")

# positional arguments:
parser.add_argument("COMMAND",
                    nargs="*",    # if option 'nargs' not set, command with arguments will not be accepted.
                    help="workload command you can specify in a shell")

# required options:
sut_group = parser.add_mutually_exclusive_group()
sut_group.add_argument("-l", "--local",
                       help="(default) profile on local host",
                       action="store_true")
sut_group.add_argument("-r", "--remote",
                       metavar="SSH_CONNECTION",
                       type=str,
                       help="profile on remote host and specify a SSH connection string.")



args = parser.parse_args()
print(type(args), args)
