#!/bin/bash
TMP_DIR=/home/ningli/hperf/tools/test_res
sar_binary="$TMP_DIR"/sar.log
sar -A -o "$sar_binary" 1 30 > /dev/null 2>&1

# CPU Utilization
sadf -d "$sar_binary" --  -u | sed 's/;/,/g' > "$TMP_DIR"/sar_u

# Network Utilization | %ifutil: 网络接口的利用率百分比(有一些 sar 版本没有该列) | rxkB/s: 每秒接收的千字节数 txkB/s: 每秒发送的千字节数
# sadf -d "$sar_binary" -- -n DEV | sed 's/;/,/g' > "$TMP_DIR"/sar_n_dev
# 只保留 eth0 的信息
# sadf -d "$sar_binary" -- -n DEV | sed 's/;/,/g' | grep ',eth0,' > "$TMP_DIR"/sar_n_dev

# 只保留活跃网卡信息，依赖 ip 命令
output_file="$TMP_DIR"/sar_n_dev
# 保留第一行的列名称
sadf -d "$sar_binary" -- -n DEV | sed -n '1p' | sed 's/;/,/g' > "$output_file"
active_interfaces=$(ip link show | grep -e "state UP" | sed 's/://g' | awk '{print $2}')
for interface in $active_interfaces; do
    sadf -d "$sar_binary" -- -n DEV | sed 's/;/,/g' | grep ",$interface," >> "$output_file"
done

# Memory Utilization | %memused 内存利用率
sadf -d "$sar_binary" -- -r | sed 's/;/,/g' > "$TMP_DIR"/sar_r

# I/O和传送速率的统计信息 | bread/s 和 bwrtn/s: 每秒读和写的块数
sadf -d "$sar_binary" -- -b | sed 's/;/,/g' > "$TMP_DIR"/sar_b

# 磁盘设备利用情况 | %util 磁盘设备利用率
# sadf -d "$sar_binary" -- -d | sed 's/;/,/g' > "$TMP_DIR"/sar_d
# 只保留 sda 设备的信息
output_file="$TMP_DIR"/sar_d
sadf -d "$sar_binary" -- -d | sed -n '1p' | sed 's/;/,/g' > "$output_file"
sadf -d "$sar_binary" -- -d | sed 's/;/,/g' | grep ',sda,' >> "$output_file"


# Memory Pages Statistics | %vmeff 虚拟内存效率
sadf -d "$sar_binary" -- -B | sed 's/;/,/g' > "$TMP_DIR"/sar_B


rm -f "$sar_binary"