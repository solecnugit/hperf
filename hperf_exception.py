"""
This module includes user-defined exceptions in hperf.
Hierarchy of user-defined exceptions: 
```
BaseException
|- ...
|- Exception
   |- HperfError
      |- ParserError
      |- ConnectorError
      |- ProfilerError
      |- AnalyzerError
      |- LoggerError
```
""" 

class HperfError(Exception):
    def __init__(self, message) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message

class ParserError(HperfError):
    pass

class ConnectorError(HperfError):
    pass

class ProfilerError(HperfError):
    pass

class AnalyzerError(HperfError):
    pass

class LoggerError(HperfError):
    pass