events = [
    {
        "id": 0,
        "perf_name": "cpu-clock",
        "name": "CPU TIME"
    },
    {
        "id": 1,
        "perf_name": "duration_time",
        "name": "WALL CLOCK TIME",
        "type": "SYSTEM"
    },
    {
        "id": 10,
        "perf_name": "msr/tsc/",
        "name": "TSC",
    },
    {
        "id": 20,
        "perf_name": "cycles",
        "name": "CYCLES"
    },
    {
        "id": 21,
        "perf_name": "instructions",
        "name": "INSTRUCTIONS"
    },
    {
        "id": 22,
        "perf_name": "ref-cycles",
        "name": "REFERENCE CYCLES"
    },
    {
        "id": 30,
        "perf_name": "r08d1",
        "name": "L1 CACHE MISSES"
    },
    {
        "id": 31,
        "perf_name": "r10d1",
        "name": "L2 CACHE MISSES"
    },
    {
        "id": 32,
        "perf_name": "r20d1",
        "name": "L3 CACHE MISSES"
    },
    {
        "id": 33,
        "perf_name": "r00c4",
        "name": "BRANCHES"
    },
    {
        "id": 34,
        "perf_name": "r00c5",
        "name": "BRANCH MISSES"
    }
]

other_events = [0, 1, 10]

pinned_events = [20, 21, 22]

event_groups = [
    [30, 31, 32],
    [33, 34]
]

metrics = [
    {"metric": "CPU UTILIZATION", "expression": "e22 / e10"},
    {"metric": "FREQUENCY", "expression": "e20 / (e1 / 1000000000)"},
    {"metric": "CPI", "expression": "e20 / e21"},
    {"metric": "L1 CACHE MPKI", "expression": "(1000 * e30) / e21"},
    {"metric": "L2 CACHE MPKI", "expression": "(1000 * e31) / e21"},
    {"metric": "L3 CACHE MPKI", "expression": "(1000 * e32) / e21"},
    {"metric": "BRANCH MISS RATE", "expression": "e34 / e33"},
]

available_GP = 4
