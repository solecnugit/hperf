# hperf

hperf (Hierarchical Performance Profiling Tools) is a microarchitectural performance data collection tool across platforms on Linux operating system that can be used to characterize workloads at the microarchitectural level with features such as

- Efficient collection of performance data for components at the microarchitectural level during workload runtime, including aspects such as instruction pipelines, caches, branch predictors, etc.
- Output reliable and easily digestible microarchitecture performance metrics to provide a comprehensive workload performance characterization to identify optimization opportunities.

> Chinese version of README is available. Check [here](README.zh.md).

## Publications

Efficient Cross-platform Multiplexing of Hardware Performance Counters via Adaptive Grouping

Tong-yu Liu, Jianmei Guo, Bo Huang

ACM Trans. Arch. Code Optim. 

https://dl.acm.org/doi/10.1145/3629525

## Background

hperf is developed based on Linux perf, which is implemented by building a layer of encapsulation on top of perf. Our purposes are: 

- Collecting comprehensive microarchitectural performance data by perf requires users to know about microarchitecture performance events across different platforms. hperf generalizes the differences between platforms to provide cross-platform support. Users can use hperf to obtain uniform microarchitectural performance metrics without caring about the differences in performance events across different microarchitectures.
- Using perf to efficiently and reliably collect microarchitectural performance data requires users to understand the architecture of the Performance Monitoring Units (PMU) of different microarchitectures, especially the types and numbers of Performance Monitoring Counters (PMC) included; they also need to understand how to handle the problem when the number of required performance events is more than the number of available PMCs. Understanding how to leverage the Linux perf_event subsystem's scheduling strategy for events when the number of required performance events is more than the number of available PMCs, to achieve more efficient scheduling while ensuring reliable derived performance metrics. This requires a high level of domain-specific knowledge from the user, so hperf encapsulates the corresponding measurement scheme for each platform. Therefore, the user does not have to understand the internal details and can obtain the corresponding performance metrics directly through hperf.

## Installation

First, clone the source code of hperf from the code repository.

hperf is developed using Python and does not require the execution of a specific installer. The current version has the following dependencies

* Data processing
    * numpy
    * pandas
* Visualization
    * matplotlib
* remote SSH connection
    * paramiko

The user can use Python's package management tools (pip or Anaconda) to enable the current system's Python environment to import the appropriate dependency packages.

The `environment.yml` file in the code repository records the relevant dependencies, and in the case of Anaconda, the following command can be used to create and activate the environment named hperf.

```
$ conda env create --file environment.yml
$ conda activate hperf
```

In addition to this, hperf needs to invoke perf for performance profiling tasks, so you need to ensure that the machine to be tested has perf installed and can execute the `perf` command from the command line.

Since perf is part of the Linux kernel tools, the version of perf is the same as the kernel version. For newer machines, it is recommended to upgrade the kernel to a higher version.

## Usage

In the code repository, `hperf.py` is the entry point for hperf, so the way to use hperf is

```
$ python hperf.py [options] <command> 
```

The options parameter `[options]` is non-required, and if not specified, hperf performs performance profiling according to the default behavior, while the positional parameter `<command>` is required and must be located at the end of the command line.

### Supported options

Options supported by the current version of hperf.

| options               | description            |
| :-------------------: | :--------------------: |
| `-h` \| `-help`       | show hperf help information, including supported options and usage. |
| `-V` \| `--version`   | show the version of hperf. |
| `-tmp-dir TMP_DIR_PATH`            | specify a temporary folder to store scripts for performance analysis and the corresponding output, log files, raw performance data, results files, etc. If not declared, the default is `/tmp/hperf/`. |
| `-r SSH_CONN_STR` \| `--remote SSH_CONN_STR` | specify the system under test as a remote host. You need to specify the host address and username to be used to establish the SSH connection, in the format of `<username>@<hostname>`. If not declared, the system under test is the local host. |
| `-v` \| `--verbose`   | show DEBUG information, if not declared, the default is not output. |
| `-c CPU_ID_LIST` \| `--cpu CPU_ID_LIST`       | specify the aggregated range of the performance metric, declared as a list of processor IDs, which can be concatenated (`-`) with a comma (`,`), e.g. `5-8,9,10`. |

Note: The `-c` option does not affect the measurement, only the processing of the raw performance data after the measurement.

### Pre-run environment check

The purpose of the environment check of hperf for the SUT before performing measurements is to ensure that hperf has exclusive access to the hardware PMCs, which ensures the reliability and accuracy of microarchitecture performance data.

The checks for the current version of hperf include: 

* whether other profilers are already running, such as Intel VTune, perf, etc. (since performance profilers are highly likely to occupy PMCs)
* whether the NMI watchdog has been disabled for x86 architecture (because the NMI watchdog will occupy a generic PMC)

If hperf checks for the above issues, it will prompt accordingly, at which point the command line will wait for the user to type in a command to determine whether to proceed with the measurement in such a case.

For example, if the machine to be measured has VTune running at this point, then hperf will give the following output:

```
2023-01-05 15:24:52,767 INFO     hperf v1.0.0
2023-01-05 15:24:52,767 INFO     test directory: /tmp/hperf/20230105_test003
2023-01-05 15:24:52,937 WARNING  sanity check: process may interfere with measurement exists. /opt/intel/oneapi/vtune/2023.0.0/bin64/emon

Detected some problems which may interfere with profiling. Continue profiling? [y|N] 
```

If the user types `n`/`N`, then hperf runs to the end; if the user types `y`/`Y`, then hperf will perform the measurement.

### Remote SUT Connection

If the `-r SSH_CONN_STR` option is specified, then hperf will establish an SSH connection to the remote system under test. 
For example, if you need to log in to the machine under test with hostname `example.com` using the username `john`, then the command to invoke hperf should be: 

```
$ python hperf.py -r john@example.com sleep 5
```

At this point, hperf will interactively prompt the user for a password on the command line, and the user types the password on the command line, for example:

```
2023-02-04 16:39:59,255 INFO     hperf v1.1.0
connect to john@example.com, and enter the password for user john:
```

If the connection is successful, the subsequent measurement tasks are executed; if the connection fails, a relevant message is prompted, and the run ends.

### Measurements

hperf measures the entire system of the machine under test during workload execution, in other words, it collects performance data for all processors of the entire system.

hperf starts performance monitoring when the workload starts, and stops performance monitoring when the workload finishes running.

For real applications that run continuously, such as a Redis database service running continuously on a server, if you need to measure the real application for a period of time, you can use `sleep <n>` as the workload while it is running normally, where `<n>` is the measured event (in s).

Microarchitecture performance metrics supported by the current version of hperf: 

* Instruction pipeline effectiveness
    * Cycles Per Instruction (CPI)
* Cache
    * L1 Cache Misses Per Kilo Instructions (L1 Cache MPKI)
    * L2 Cache Misses Per Kilo Instructions (L2 Cache MPKI)
    * L3 Cache Misses Per Kilo Instructions (L3 Cache MPKI)
* Branch Prediction
    * Branch Misprediction Rate
* Memory Controller
    * Memory Bandwith
* Instruction Mix

### Cases

#### Workload characterization of single- or multi-threaded programs

For a matrix multiplication executable with the path `. /test/mat_mul`, a parameter needs to be passed at runtime to measure its runtime microarchitectural performance metrics using hperf, where the temporary folder is specified as `. /tmp/`, then the command to invoke hperf is

```
$ python hperf.py --tmp-dir . /tmp -c 5 taskset -c 5 . /test/mat_mul 128
```

Where, since the `mat_mul` program is tied to processor 5, and although hperf is measuring the entire system, the analysis only needs to use the performance data collected on processor 5, the option `-c 5` is used.

Execution of this command should display the following output.

```
2022-12-13 16:32:17,226 INFO     hperf v1.0.0
2022-12-13 16:32:17,226 INFO     test directory: /home/tongyu/project/hperf/tmp/20221213_test006
2022-12-13 16:32:17,288 INFO     start profiling
2022-12-13 16:32:43,874 INFO     end profiling
2022-12-13 16:32:43,908 INFO     save DataFrame to CSV file: /home/tongyu/project/hperf/tmp/20221213_test006/results.csv
              metric        result
0           CPU TIME  2.654691e+04
1             CYCLES  8.739400e+10
2       INSTRUCTIONS  1.834493e+11
3                TSC  7.680475e+10
4           BRANCHES  1.051103e+10
5      BRANCH MISSES  5.461876e+06
6    L1 CACHE MISSES  4.168072e+09
7    L2 CACHE MISSES  3.434293e+09
8    L3 CACHE MISSES  3.709443e+08
9   REFERENCE CYCLES  7.679803e+10
10   CPU UTILIZATION  9.999126e-01
11               CPI  4.763933e-01
12     L1 CACHE MPKI  2.272057e+01
13     L2 CACHE MPKI  1.872067e+01
14     L3 CACHE MPKI  2.022054e+00
15  BRANCH MISS RATE  5.196326e-04
```

From the output, the path to the file where this measurement is stored can be obtained, and the user can look up the files in the relevant directory to understand the execution process of the performance profiling and the intermediate and result files.

For multi-threaded programs, similarly, you should use commands such as `taskset` or `numactl` to bind the corresponding processor, NUMA node, or SOCKET, and then set the option `-c` with a list of corresponding processor IDs as an argument.

#### Workload Characterization for Real Applications

For real workload characterization, you should first start the workload and determine whether to bind processors, NUMA nodes, or SOCKETs as needed. hperf is invoked after the workload has been started to perform performance checks over time.

For example, for the redis-server service, if you bind the specified 4 processors, you can use

```
$ taskset -c 1,3,5,7 . /redis-server
```

After completing the startup, if you wish to use hperf to analyze the workload for 1 minute, then the command to invoke hperf is

```
$ python hperf.py -c 1,3,5,7 sleep 60
```

The output is similar to the previous case, so we won't go over it again.

## People

* System Optimization Lab, East China Normal University (SOLE)

    * Tong-yu Liu
    * Huanlun Cheng
    * Jianmei Guo
    * Bo Huang

### Contact Information

If you have any questions or suggestions, please contact Tong-yu Liu via tyliu@stu.ecnu.edu.cn . 
