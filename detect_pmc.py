import subprocess


def is_appro_equal(arr: list, err: float) -> bool:
    if arr:
        upperbound = arr[0]
        lowerbound = arr[0]
    else:
        return False
    
    if len(arr) == 1:
        return True
    
    for i in arr[1:]:
        if i > upperbound:
            upperbound = i
        if i < lowerbound:
            lowerbound = i
        if upperbound - lowerbound >= err:
            return False
    
    return True

def is_all_100(arr: list) -> bool:
    for i in arr:
        if i < 100.0:
            return False
    return True

if __name__ == "__main__":    
    event_pool = ["L1-dcache-loads",
                  "L1-dcache-load-misses",
                  "L1-dcache-stores",
                  "L1-icache-load-misses",
                  "dTLB-loads",
                  "dTLB-load-misses",
                  "dTLB-stores",
                  "dTLB-store-misses",
                  "iTLB-loads",
                  "iTLB-load-misses",
                  "branch-loads",
                  "branch-load-misses",
                  "branch-instructions",
                  "branch-misses",
                  "bus-cycles",
                  "cache-misses",
                  "cache-references"
                  ]

    program = "~/prog/test"
    
    pinned_events = ["cycles", "instructions", "ref-cycles"]
    pinned_event_str = ",".join([ i + ":D" for i in pinned_events])
    
    selected_events = []
    
    while True:
        selected_events.append(event_pool.pop(0))
        
        output = subprocess.Popen(f"perf stat -e {pinned_event_str},{','.join(selected_events)} -x, -- {program}", 
                                  shell=True, 
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE).communicate()[1].decode("utf-8")
        
        sampling_ratios = []
        
        for i, line in enumerate(output.split("\n")):
            if len(pinned_events) <= i < len(pinned_events) + len(selected_events):
                sampling_ratio = float(line.split(",")[4])
                sampling_ratios.append(sampling_ratio)
        
        if  (not is_all_100(arr=sampling_ratios)) and is_appro_equal(arr=sampling_ratios, err=3.0):
            break
    
    print(f"Detected number of PMC: {len(selected_events) - 1}")