#!/bin/bash
TMP_DIR=/home/tongyu/project/hperf/tmp/20230612_test001
sar_binary="$TMP_DIR"/sar.log
date +%Y-%m-%d" "%H:%M:%S.%N | cut -b 1-23 > "$TMP_DIR"/sar_start_timestamp
sar -A -o "$sar_binary" 1 10 > /dev/null 2>&1
sadf -d "$sar_binary" -- -P 2,3 -u | sed 's/;/,/g' > "$TMP_DIR"/sar_u
sadf -d "$sar_binary" -- -n DEV | sed 's/;/,/g' > "$TMP_DIR"/sar_n_dev
rm -f "$sar_binary"
