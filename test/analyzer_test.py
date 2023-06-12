import sys, importlib, os

if __name__ == "__main__":
    # modify `tmp_dir` and `test_id` to the test directory in ./test/
    tmp_dir = "/home/tongyu/project/hperf/test"
    test_id = "test_dir"
    
    test_dir_path = os.path.join(tmp_dir, test_id)

    configs = {
        "verbose": True,
        "command": "sleep 10",
        "host_type": "local", 
        "cpu_list": "all", 
        "tmp_dir": tmp_dir,
        "time": 10
    }

    sys.path.append("/home/tongyu/project/hperf")
    event_group_module = importlib.import_module("event_group")
    analyzer_module = importlib.import_module("analyzer")
    
    EventGroup = getattr(event_group_module, "EventGroup")

    event_groups = EventGroup.get_event_group(isa="x86_64", arch="intel_icelake")

    print(event_groups.get_event_groups_str())

    Analyzer = getattr(analyzer_module, "Analyzer")

    analyzer = Analyzer(test_dir_path, configs, event_groups)

    analyzer.analyze()
    print(analyzer.get_timeseries(to_csv=True))
    print(analyzer.get_aggregated_metrics(to_csv=True))
    analyzer.get_timeseries_plot()
