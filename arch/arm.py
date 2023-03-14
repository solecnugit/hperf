events = [
    # OS
    { "id": 0, "perf_name": "cpu-clock", "name": "CPU TIME" },
    { "id": 1, "perf_name": "duration_time", "name": "WALL CLOCK TIME", "type": "SYSTEM" },
    { "id": 2, "perf_name": "cs", "name": "CONTEXT SWITCH" },
    # PMU - General
    { "id": 20, "perf_name": "cycles", "name": "CYCLES" },
    { "id": 21, "perf_name": "instructions", "name": "INSTRUCTIONS" },
    # PMU - Cache
    { "id": 30, "perf_name": "r01", "name": "L1I CACHE MISSES" },
    { "id": 31, "perf_name": "r14", "name": "L1I CACHE ACCESSES" },
    { "id": 32, "perf_name": "r03", "name": "L1D CACHE MISSES" },
    { "id": 33, "perf_name": "r04", "name": "L1D CACHE ACCESSES" },
    { "id": 34, "perf_name": "r17", "name": "L2 CACHE MISSES" },
    { "id": 35, "perf_name": "r16", "name": "L2 CACHE ACCESSES" },
    # PMU - LLC (uncore)
    { "id": 100, "perf_name": "arm_cmn_0/hnf_cache_miss/", "name": "LL CACHE MISSES", "type": "SYSTEM" },
    { "id": 101, "perf_name": "arm_cmn_0/hnf_slc_sf_cache_access/", "name": "LL CACHE ACCESSES", "type": "SYSTEM" },
    # PMU - Branch
    { "id": 40, "perf_name": "r22", "name": "BRANCH MISSES" }, 
    { "id": 41, "perf_name": "r21", "name": "BRANCHES" },
    # PMU - TLB
    { "id": 50, "perf_name": "r35", "name": "ITLB WALKS" }, 
    { "id": 51, "perf_name": "r26", "name": "ITLB ACCESSES" },
    { "id": 52, "perf_name": "r34", "name": "DTLB WALKS" },
    { "id": 53, "perf_name": "r25", "name": "DTLB ACCESSES" },
    # PMU - Other
    { "id": 60, "perf_name": "r23", "name": "FRONTEND STALLS" }, 
    { "id": 61, "perf_name": "r24", "name": "BACKEND STALLS" }
]

other_events = [0, 1, 2, 100, 101]

pinned_events = [20, 21]

# left 5 counters for other events
event_groups = [
    [30, 31, 32, 33],
    [34, 35, 40, 41, 60],
    [50, 51, 52, 53, 61]
]

metrics = [
    # General
    { "metric": "CPU UTILIZATION", "expression": "e0 / (e1 / 1000000)" },
    { "metric": "CPI", "expression": "e20 / e21" },
    { "metric": "FREQUENCY", "expression": "e20 / (e1 / 1000000000)" },
    # Cache
    { "metric": "L1I CACHE MPKI", "expression": "(1000 * e30) / e21" },
    { "metric": "L1I CACHE MISS RATE", "expression": "e30 / e31" },
    { "metric": "L1D CACHE MPKI", "expression": "(1000 * e32) / e21" },
    { "metric": "L1D CACHE MISS RATE", "expression": "e32 / e33" },
    { "metric": "L2 CACHE MPKI", "expression": "(1000 * e34) / e21" },
    { "metric": "L2 CACHE MISS RATE", "expression": "e34 / e35" },
    { "metric": "L3 CACHE MPKI", "expression": "(1000 * e100) / e21" },
    { "metric": "L3 CACHE MISS RATE", "expression": "e100 / e101" },
    # Branch
    { "metric": "BRANCH MPKI", "expression": "(1000 * e40) / e21" },
    { "metric": "BRANCH MISS RATE", "expression": "e40 / e41" },
    # TLB
    { "metric": "ITLB MPKI", "expression": "(1000 * e50) / e21" },
    { "metric": "DTLB MPKI", "expression": "(1000 * e52) / e21" },
    { "metric": "ITLB WALK RATE", "expression": "e50 / e51" },
    { "metric": "DTLB WALK RATE", "expression": "e52 / e53" },
    # Stall
    { "metric": "FRONTEND STALL RATE", "expression": "e60 / e20" },
    { "metric": "BACKEND STALL RATE", "expression": "e61 / e20" }
]