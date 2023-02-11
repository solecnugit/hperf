"""
This module includes user-defined exceptions in hperf
""" 

class HperfError(Exception):
    def __init__(self, message) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message

class ParamikoError(HperfError):
    pass

class ProfilerError(HperfError):
    pass

class ParserError(HperfError):
    pass

class LoggerError(HperfError):
    pass