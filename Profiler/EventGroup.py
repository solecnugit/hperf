class EventGroups:
    """
    define a set of event groups for micro-architecture events to be monitored
    """

    def __init__(self, event_groups: list = None):
        """
        constructor of EventGroups
        :param event_groups: a list contains several dicts, which describe events in event groups, related metrics
        and their expressions
        """
        if event_groups is None:
            self.event_groups = []
        else:
            self.event_groups = event_groups

    def append_event_group(self, metric: str, event_list: list, expression: str) -> None:
        """
        add an event group to the set of event groups
        :param metric: name of the metric
        :param event_list: list of events in the event group
        :param expression: expression of the metric where the variables are the names of events
        :return: None
        """
        event_group_item = {"metric": metric, "event_list": event_list, "expression": expression}
        self.event_groups.append(event_group_item)

    def append_single_event(self, event) -> None:
        """
        add a single event without event groups
        :param event: name of the event
        :return: None
        """
        event_group_item = {"metric": None, "event": event}
        self.event_groups.append(event_group_item)

    def to_perf_string(self) -> str:
        """
        convert the set of the current event groups to a string which the `-e` option in `perf` can accept.
        The events in the same event group will be enclosed between `\`{` and `}\``.
        :return: 能够被perf`的`-e`选项能够接受的性能事件字符串
        """
        perf_string = ""
        for index, event_group_item in enumerate(self.event_groups):
            if event_group_item["metric"] is None:
                perf_string += event_group_item["event"]
            else:
                perf_string += "'{" + ",".join(event_group_item["event_list"]) + "}'"
            if index != len(self.event_groups) - 1:
                perf_string += ","
        return perf_string
