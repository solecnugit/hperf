#!/bin/bash
TMP_DIR=/home/tongyu/project/hperf/tmp/20230218_test001
sar_binary="$TMP_DIR"/sar_binary
sar_result="$TMP_DIR"/sar_result
sar -o "$sar_binary" -r 1 5
sadf -d "$sar_binary" | sed 's/;/,/g' > "$sar_result"
rm -f "$sar_binary"
