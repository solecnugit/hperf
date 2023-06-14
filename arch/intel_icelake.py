events = [
    # OS
    { "id": 0, "perf_name": "cpu-clock", "name": "CPU TIME" },
    { "id": 1, "perf_name": "duration_time", "name": "WALL CLOCK TIME", "type": "SYSTEM" },
    { "id": 2, "perf_name": "cs", "name": "CONTEXT SWITCHES" },
    # MSR
    { "id": 10, "perf_name": "msr/tsc/", "name": "TSC" },
    # PMU - General
    { "id": 20, "perf_name": "cycles", "name": "CYCLES" },
    { "id": 21, "perf_name": "instructions", "name": "INSTRUCTIONS" },
    { "id": 22, "perf_name": "ref-cycles", "name": "REFERENCE CYCLES" },
    # PMU - Cache
    { "id": 30, "perf_name": "r08d1", "name": "L1 CACHE MISSES" },    # MEM_LOAD_RETIRED.L1_MISS
    { "id": 31, "perf_name": "r01d1", "name": "L1 CACHE HITS" },    # MEM_LOAD_RETIRED.L1_HIT
    { "id": 32, "perf_name": "r10d1", "name": "L2 CACHE MISSES" },    # MEM_LOAD_RETIRED.L2_MISS
    { "id": 33, "perf_name": "r02d1", "name": "L2 CACHE HITS" },    # MEM_LOAD_RETIRED.L2_HIT
    # PMU - LLC (uncore)
    { "id": 100, "perf_name": "cha/event=0x34,umask=0x1fe001/", "name": "LL CACHE MISSES", "type": "SOCKET" },    # LLC_LOOKUP.MISS_ALL
    { "id": 101, "perf_name": "cha/event=0x34,umask=0x1fffff/", "name": "LL CACHE ACCESSES", "type": "SOCKET" },    # LLC_LOOKUP
    # PMU - Memory (uncore)
    { "id": 110, "perf_name": "imc/event=0x04,umask=0x0f/", "name": "MEM ACCESSES RD", "type": "SOCKET" },    # CAS_COUNT.RD
    { "id": 111, "perf_name": "imc/event=0x04,umask=0x30/", "name": "MEM ACCESSES WR", "type": "SOCKET" },    # ​CAS_COUNT.WR
    # PMU - Branch 
    { "id": 40, "perf_name": "r00c5", "name": "BRANCH MISSES" },    # BR_MISP_RETIRED.ALL_BRANCHES
    { "id": 41, "perf_name": "r00c4", "name": "BRANCHES" },    # BR_INST_RETIRED.ALL_BRANCHES
    # PMU - TLB
    { "id": 50, "perf_name": "r0e85", "name": "ITLB WALKS" },     # ITLB_MISSES.WALK_COMPLETED
    #     ITLB ACCESSES = INSTRUCTIONS
    { "id": 51, "perf_name": "r0e08", "name": "DTLB LOAD WALKS" },     # DTLB_LOAD_MISSES.WALK_COMPLETED
    { "id": 52, "perf_name": "r0e49", "name": "DTLB STORE WALKS" },     # DTLB_STORE_MISSES.WALK_COMPLETED
    #     DTLB WALKS = DTLB LOAD WALKS + DTLB STORE WALKS
    { "id": 53, "perf_name": "r83d0", "name": "DTLB ACCESSES" }    # MEM_INST_RETIRED.ANY
]

other_events = [0, 1, 2, 10, 100, 101, 110, 111]

pinned_events = [20, 21, 22]

event_groups = [
    [30, 31, 32, 33],
    [50, 51, 52, 53, 40, 41]
]

metrics = [
    # General
    { "metric": "CPU UTILIZATION", "expression": "e22 / e10" },
    { "metric": "FREQUENCY", "expression": "e20 / (e1 / 1000000000)" },
    { "metric": "CPI", "expression": "e20 / e21" },
    # Cache
    { "metric": "L1 CACHE MPKI", "expression": "(1000 * e30) / e21" },
    { "metric": "L1 CACHE MISS RATE", "expression": "e30 / (e30 + e31)" },
    { "metric": "L2 CACHE MPKI", "expression": "(1000 * e32) / e21" },
    { "metric": "L2 CACHE MISS RATE", "expression": "e32 / (e32 + e33)" },
    # LLC
    { "metric": "LL CACHE MPKI", "expression": "(1000 * e100) / e21" },
    { "metric": "LL CACHE MISS RATE", "expression": "e100 / e101" },
    # Memory
    { "metric": "MEM BANDWITH RD", "expression": "(e110 * 64) / (e1 / 1000000000)" },
    { "metric": "MEM BANDWITH WR", "expression": "(e111 * 64) / (e1 / 1000000000)" },
    { "metric": "MEM BANDWITH", "expression": "((e110 + e111) * 64) / (e1 / 1000000000)"},
    # Branch
    { "metric": "BRANCH MPKI", "expression": "(1000 * e40) / e21" },
    { "metric": "BRANCH MISS RATE", "expression": "e40 / e41" },
    # TLB
    { "metric": "ITLB MPKI", "expression": "(1000 * e50) / e21" },
    { "metric": "DTLB MPKI", "expression": "(1000 * (e51 + e52)) / e21" },
    { "metric": "DTLB WALK RATE", "expression": "(e51 + e52) / e53" },
]

available_GP = 4