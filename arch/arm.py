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
    { "id": 61, "perf_name": "r24", "name": "BACKEND STALLS" },
    # PMU - instruction mix
    { "id": 70, "perf_name": "r70", "name": "LD SPEC" }, 
    { "id": 71, "perf_name": "r71", "name": "ST SPEC" }, 
    { "id": 72, "perf_name": "r74", "name": "ASE SPEC" }, 
    { "id": 73, "perf_name": "r75", "name": "VFP SPEC" }, 
    { "id": 74, "perf_name": "r73", "name": "DP IMMED SPEC" }, 
    { "id": 75, "perf_name": "r78", "name": "BR IMMED SPEC" }, 
    { "id": 76, "perf_name": "r7A", "name": "BR INDIRECT SPEC" }, 
    { "id": 77, "perf_name": "r79", "name": "BR RETURN SPEC" },
    { "id": 78, "perf_name": "r1B", "name": "INSTRUCTIONS SPEC" },
    # PMU - memory access
    { "id": 80, "perf_name": "r31", "name": "REMOTE ACCESS" },
    { "id": 81, "perf_name": "r66", "name": "MEM ACCESS RD" },
    { "id": 82, "perf_name": "r67", "name": "MEM ACCESS WR" }
]

other_events = [0, 1, 2, 100, 101]

pinned_events = [20, 21]

# left 5 counters for other events
event_groups = [
    [30, 31, 32, 33],
    [34, 35, 40, 41, 60],
    [50, 51, 52, 53, 61], 
    [70, 71, 72, 73, 74],
    [75, 76, 77, 78],
    [80, 81, 82]
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
    { "metric": "BACKEND STALL RATE", "expression": "e61 / e20" },
    # Instruction Mix
    { "metric": "LD PERCENTAGE", "expression": "e70 / e78" },
    { "metric": "ST PERCENTAGE", "expression": "e71 / e78" },
    { "metric": "ASE PERCENTAGE", "expression": "e72 / e78" },
    { "metric": "VFP PERCENTAGE", "expression": "e73 / e78" },
    { "metric": "DP PERCENTAGE", "expression": "e74 / e78" },
    { "metric": "BR IMMED PERCENTAGE", "expression": "e75 / e78" },
    { "metric": "BR INDIRECT", "expression": "e76 / e78" },
    { "metric": "BR RETURN", "expression": "e77 / e78" }
]

available_GP = 6