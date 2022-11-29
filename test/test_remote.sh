TMP_DIR=/home/huanlun/tmp/test
workload_output=$(mktemp -p $TMP_DIR -t hperf_workload_output.XXXXXX)
nohup taskset -c 6 ./mat_mul 128 > "$workload_output" 2>&1 &
workload_pid=$!

python ../hperf.py -r huanlun@gpu1.solelab.tech:kid2/kn/IPC -p $workload_pid -c 6 --tmp_dir $TMP_DIR --metrics CPI,MPI 