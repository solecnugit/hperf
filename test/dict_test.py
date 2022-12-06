
def foo(d: dict):
    d["d"] = 6
    d["b"] = 5


def script(d: dict):
    script = rf'''TMP_DIR={d["a"]}
perf_result=$(mktemp -t -p $TMP_DIR hperf_perf_result.XXXXXX)
perf_error=$(mktemp -t -p $TMP_DIR hperf_perf_error.XXXXXX)
3>"$perf_result" perf stat -e {d["b"]} -A -a -x, --log-fd 3 2>"$perf_error"'''
    print(script)
    return script


if __name__ == "__main__":
    configs = { "a": "/tmp/hperf/", "b": 2, "c": 3}
    print(configs)
    foo(configs)
    print(configs)

    script(configs)
