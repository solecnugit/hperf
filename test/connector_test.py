import sys, importlib, os

if __name__ == "__main__":
    sys.path.append("/home/tongyu/project/hperf")
    connector_module = importlib.import_module("connector")

    LocalConnector = getattr(connector_module, "LocalConnector")
    # RemoteConnector = getattr(connector_module, "RemoteConnector")
    
    # modify test_dir_path, any directory is fine. 
    test_dir_path = "/home/tongyu/project/hperf/tmp"
    
    local_connector = LocalConnector(test_dir_path)
    # remote_connector = RemoteConnector()

    command_str = "lscpu"
    script_str = "#!/bin/bash\nsleep 5\n"
    script_path = os.path.join(test_dir_path, "test_script.sh")

    print(local_connector.run_command([command_str]))
    print(local_connector.run_script(script_str, script_path))
    