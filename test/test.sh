TMPDIR="$HOME/tmp/"
echo "Script Process ID: $$"
workload_output=$(mktemp -t hperf_workload_output.XXXXXX)
nohup taskset -c 1 ./mat_mul 128 > "$workload_output" 2>&1 &
workload_pid=$!
echo "Workload Process ID: $workload_pid"
python ../hperf.py -l -p "$workload_pid" -c 1