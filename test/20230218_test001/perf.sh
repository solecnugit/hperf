#!/bin/bash
TMP_DIR=/home/tongyu/project/hperf/tmp/20230218_test001
perf_result="$TMP_DIR"/perf_result
perf_error="$TMP_DIR"/perf_error
3>"$perf_result" perf stat -e cpu-clock,duration_time,cycles:D,'{instructions,r01,r03,r17,r2a}','{r21,r22}' -A -a -x, -I 1000 --log-fd 3 sleep 5 2>"$perf_error"
