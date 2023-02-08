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
        "id": 20,
        "perf_name": "cycles",
        "name": "CYCLES"
    },
    {
        "id": 30,
        "perf_name": "instructions",
        "name": "INSTRUCTIONS"
    },
    {
        "id": 31,
        "perf_name": "r01",
        "name": "L1I CACHE MISSES"
    },
    {
        "id": 32,
        "perf_name": "r03",
        "name": "L1D CACHE MISSES"
    },
    {
        "id": 33,
        "perf_name": "r17",
        "name": "L2 CACHE MISSES"
    },
    {
        "id": 34,
        "perf_name": "r2a",
        "name": "L3 CACHE MISSES"
    },
    {
        "id": 35,
        "perf_name": "r21",
        "name": "BRANCHES"
    },
    {
        "id": 36,
        "perf_name": "r22",
        "name": "BRANCH MISSES"
    }
]

other_events = [0, 1]

pinned_events = [20]

event_groups = [
    [30, 31, 32, 33, 34],
    [35, 36]
]

metrics = [
    {
        "metric": "CPU UTILIZATION",
        "expression": "e0 / (e1 / 1000000)"
    },
    {
        "metric": "CPI",
        "expression": "e20 / e30"
    },
    {
        "metric": "FREQUENCY",
        "expression": "e20 / (e1 / 1000000000)"
    },
    {
        "metric": "L1I CACHE MPKI",
        "expression": "(1000 * e31) / e30"
    },
    {
        "metric": "L1D CACHE MPKI",
        "expression": "(1000 * e32) / e30"
    },
    {
        "metric": "L2 CACHE MPKI",
        "expression": "(1000 * e33) / e30"
    },
    {
        "metric": "L3 CACHE MPKI",
        "expression": "(1000 * e34) / e30"
    },
    {
        "metric": "BRANCH MISS RATE",
        "expression": "e36 / e35"
    }
]