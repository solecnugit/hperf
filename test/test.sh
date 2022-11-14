#!/bin/bash

echo "Script Process ID: $$"

# Step 1. start the workload
workload_output=$(mktemp -t hperf_workload_output.XXXXXX)
nohup taskset -c 1 ./mat_mul 128 > "$workload_output" 2>&1 &

workload_pid=$!
echo "Workload Process ID: $workload_pid"

# Step 2. start profiling
perf_result=$(mktemp -t hperf_perf_result.XXXXXX)
perf_error=$(mktemp -t hperf_perf_error.XXXXXX)
nohup 3>"$perf_result" perf stat -e cycles,instructions -C 1,2 -A -x, --log-fd 3 >/dev/null 2>"$perf_error" &

perf_pid=$!
echo "perf Process ID: $perf_pid"

# Step 3. wait for workload finished, then terminate perf process
wait $workload_pid
echo "Workload completed."
kill -INT $perf_pid

# Step 4. output
echo "Workload output:"
cat "$workload_output"
echo "perf result:"
cat "$perf_result"
echo "perf error:"
cat "$perf_error"
