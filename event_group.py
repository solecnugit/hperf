from connector import Connector
import logging

class EventGroup:
    """
    'EventGroup' is responsible for detecting the architecture of the SUT 
    and generating the string of event groups, which can be accepted by '-e' options of 'perf'.
    """
    def __init__(self, connector: Connector) -> None:
        """
        Constructor of 'EventGroup'.
        It will firstly determine the architecture of the SUT through 'Connector', 
        then it will dynamic import the pre-defined configurations in 'profiler/arch/<arch_name>.py'.
        :param connector: an instance of 'Connector' ('LocalConnector' or 'RemoteConnector')
        """
        self.connector = connector

        self.arch = self.__get_architecture()
        logging.debug(f"architecture model: {self.arch}")

        # dynamic import event configurations based on the architecture of the SUT
        arch_module = __import__(f"arch.{self.arch}", fromlist=[0])
        self.events: list = getattr(arch_module, "events")
        self.other_events: list = getattr(arch_module, "other_events")
        self.pinned_events: list = getattr(arch_module, "pinned_events")
        self.event_groups: list = getattr(arch_module, "event_groups")
        self.metrics: list = getattr(arch_module, "metrics")    

    def __get_architecture(self) -> str:
        """
        Determine the architecture of the SUT by analyzing the output of 'lscpu' command.
        :return: a string of architecture
        """
        processor = self.connector.run_command("lscpu | grep 'Model name:' | awk -F: '{print $2}'").strip().decode("utf-8")
        logging.debug(f"processor model: {processor}")
        # TODO: the following logic is simple, it should be refined in future
        if processor.find("Intel") != -1:
            # determine the microarchitecture code of intel processor by lscpu 'Model'
            model = self.connector.run_command("lscpu | grep 'Model:' | awk -F: '{print $2}'").strip().decode("utf-8")
            try:
                model = int(model)
                if model == 106:
                    arch = "intel_icelake"
                elif model == 85:
                    arch = "intel_cascadelake"
                else:
                    arch = "intel_cascadelake"
            except ValueError:
                logging.warning(f"unrecongized Intel processor model: {model}, assumed as intel_cascadelake")
                arch = "intel_cascadelake"
        else:
            arch = "arm"
        return arch
    
    def get_event_groups_str(self) -> str:
        """
        Get the string of event groups, which can be accepted by '-e' options of 'perf'.
        """
        def get_event_by_id(id: int) -> str:
            """
            Traverse the list of events and find the 'perf_name' by 'id'.
            """
            for item in self.events:
                if item["id"] == id:
                    return item["perf_name"]
            return ""

        event_groups_str = ""
        for other_event_id in self.other_events:
            event_groups_str += (get_event_by_id(other_event_id) + ",")
        for pinned_event_id in self.pinned_events:
            event_groups_str += (get_event_by_id(pinned_event_id) + ":D" + ",")
        for group in self.event_groups:
            event_groups_str += "'{"
            for event_id in group:
                event_groups_str += (get_event_by_id(event_id) + ",")
            event_groups_str = event_groups_str[:-1]
            event_groups_str += "}',"
        event_groups_str = event_groups_str[:-1]

        logging.debug(f"generated string of event groups: {event_groups_str}")
        return event_groups_str