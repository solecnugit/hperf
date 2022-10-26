from argparse import ArgumentParser
from typing import Sequence

class Parser:
    def __init__(self) -> None:
        self.parser = ArgumentParser()
        self.parser.add_argument("command", 
        help="Any command you can specify in a shell")

    def parse_args(self, argv: Sequence[str]):
        args = self.parser.parse_args(argv)
        print("Workload:", args.command)