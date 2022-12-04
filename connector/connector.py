class Connector:
    """
    the Abstract class of all Connectors.
    """

    def __init__(self, configs: dict) -> None:
        self.configs = configs

    """
        Run profile bash script file.
        You should call this func only when you want to run a profiling command.
    """

    def run_command_with_file(self, command: str):
        pass

    """
        Call this func after call run_command_with_file to get perf result.
    """

    def get_result(self) -> str:
        pass

    """
        Call this func after call run_command_with_file to get perf err.
    """

    def get_err(self) -> str:
        pass

    """
        Check wheather pmc is occupied.
    """

    def runtime_check(self) -> bool:
        pass

    def get_cpu_architecture(self) -> str:
        pass

    def clear(self):
        pass