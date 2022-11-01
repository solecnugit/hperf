from Connector.Connector import Connector


class Task:
    def __init__(self, connector: Connector, workload_command: str) -> None:
        self.connector = connector
        self.workload_command = workload_command

    def run_workload(self) -> str:
        return self.connector.run_command(self.workload_command)
