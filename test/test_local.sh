#!/bin/bash

TMP_DIR=/home/tongyu/tmp
workload_output=$(mktemp -p $TMP_DIR -t hperf_workload_output.XXXXXX)
nohup taskset -c 6 ./mat_mul 128 > "$workload_output" 2>&1 &
workload_pid=$!

python ../hperf.py -l -p $workload_pid -c 6 --tmp-dir $TMP_DIR --metrics CPI,MPI 