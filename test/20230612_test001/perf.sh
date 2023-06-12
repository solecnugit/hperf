#!/bin/bash
TMP_DIR=/home/tongyu/project/hperf/tmp/20230612_test001
perf_result="$TMP_DIR"/perf_result
perf_error="$TMP_DIR"/perf_error
date +%Y-%m-%d" "%H:%M:%S.%N | cut -b 1-23 > "$TMP_DIR"/perf_start_timestamp
3>"$perf_result" perf stat -e cpu-clock,duration_time,cs,msr/tsc/,cha/event=0x34,umask=0x1fe001/,cha/event=0x34,umask=0x1fffff/,imc/event=0x04,umask=0x0f/,imc/event=0x04,umask=0x30/,cycles:D,instructions:D,ref-cycles:D,'{r08d1,r01d1,r10d1,r02d1}','{r0e85,r0e08,r0e49,r83d0,r00c5,r00c4}' -A -a -x "	" -I 1000 --log-fd 3 sleep 10 2>"$perf_error"
