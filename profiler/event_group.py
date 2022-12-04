from connector import Connector

class EventGroup:
    def __init__(self, metrics: str, connector: Connector) -> None:
        metrics = metrics.strip()
        metrics = metrics.split(",")
        self.metrics = metrics
        self.connector = connector

    def get_event_groups(self) -> str:
        architecture =  self.connector.get_cpu_architecture()
        return " instructions:D,cycles:D,'{r8D1,r10D1}','{rc4,rc5}' "