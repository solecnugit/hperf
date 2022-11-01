class Connector:
    """
    the interface of Connector
    """
    def __init__(self) -> None:
        pass

    def run_command(self, command: str) -> str:
        pass

    def get_tmp_file_path(self, tmp_file_path: str) -> str:
        pass
