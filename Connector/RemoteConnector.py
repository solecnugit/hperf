from Connector.Connector import Connector


class RemoteConnector(Connector):
    def __init__(self, configs, host_address: str) -> None:
        super(RemoteConnector, self).__init__(configs)
        self.host_address = host_address

    def run_command(self, command: str) -> str:
        pass
