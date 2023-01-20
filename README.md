# hperf

hperf（Hierarchical Performance Profiling Tools）是一个在Linux操作系统上跨指令集架构的微架构性能数据采集工具，可用于工作负载的微架构层面的特征分析，其特征在于：

- 高效地收集工作负载运行时微架构层面各组件的性能数据，包括指令流水线、缓存、分支预测等方面；
- 输出可靠的、容易被消化的微架构性能指标，提供全面的工作负载性能画像，以期发现工作负载的性能优化机会。

## 背景

hperf的是基于Linux perf开发的，其本质相当于在perf之上做了一层封装，其目的在于：

- 调用perf收集全面的微架构性能数据，需要用户了解不同处理器微架构需要采集的性能事件。hperf在此之上做了泛化（generalization）以实现跨平台的支持，使用hperf则可以不关心不同微架构下性能事件的差异，获得统一微架构性能指标；
- 调用perf高效地、可靠地收集的微架构性能数据，需要用户了解不同微架构的性能监测单元（Performance Monitoring Unit，PMU）的架构，特别是包含的性能事件计数器（Performance Monitoring Counter，PMC）的种类与数量；还需要理解需要的性能事件数量大于可用的PMC数量时，如何利用Linux perf_event子系统对性能事件的调度机制，以实现更高效地调度，同时确保导出的可靠的性能指标。这对用户的特定领域知识提出了较高要求，因此hperf封装了各平台相应的测量方案，用户不必了解内部细节，能够直接通过hperf获得相应的性能指标。

hperf能够通过简单的命令行调用，输出工作负载的微架构性能事件，相较于Linux perf，选项更少、命令更加简单，用户能够快速上手使用。

## 安装

首先从代码仓库克隆hperd的源代码。

hperf是使用Python开发的，并不需要执行特定的安装程序，当前版本的依赖项有：

* 数据处理：
    * numpy
    * pandas
* 远程SSH连接：
    * paramiko

用户可以使用Python的包管理工具（pip或Anaconda）使得当前系统的Python环境能够导入相应的依赖包。

代码仓库中的`environment.yml`文件记录了相关依赖项，以Anaconda为例，可以使用下述命令创建并激活环境（环境名称为hperf）：

```
$ conda env create --file environment.yml
$ conda activate hperf
```

除此之外，由于hperf需要调用perf进行性能剖析任务，因此需要保证待测机器已经安装perf，能够从命令行执行`perf`命令。

由于perf是Linux内核工具的一部分，perf的版本与内核版本一致，对于较新的机器，推荐将内核升级至较高的版本。

## 使用方法

在代码仓库中，`hperf.py`是hperf的入口，因此使用hperf的方法是：

```
$ python hperf.py [options] <command> 
```

其中`[options]`是可选的选项，`<command>`是必要的参数，表示执行工作负载的命令。

### 支持的选项

当前版本的hperf支持的选项：

| 选项                  | 描述                    |
| :-------------------: | :--------------------: |
| `-h` \| `--help`      | 显示hperf帮助信息，包括支持的选项以及用法 |
| `--tmp-dir`            | 指定临时文件夹的目录，用于存放用于性能分析的脚本以及对应输出结果、日志文件、原始性能数据、结果文件等，若不声明则默认为`/tmp/hperf/` |
| `-v` \| `--verbose`   | 显示DEBUG信息，若不声明则默认不输出 |
| `-c` \| `--cpu`       | 指定性能指标的聚合范围，用处理器ID的列表声明，列表可以使用连词符（`-`）与逗号（`,`），例如`5-8,9,10` |

注：`-c`选项不影响测量，只影响测量后对原始性能数据的处理。

### 运行前环境检查

hperf在执行测量之前，对待测机器进行环境检查，其目的在于保证hperf能够独占使用硬件性能计数器，以确保测量数据的可靠性与准确性。

当前版本hperf的检查包括：

* 是否已经运行其他性能剖析器，例如Intel VTune，perf等（因为性能剖析器很可能占用性能计数器）
* 对于x86架构的机器，NMI看门狗是否已经关闭（因为NMI看门狗会占用一个通用性能计数器）

如果hperf检查到了上述问题，会发出相应提示，此时命令行会等待用户键入指令，确定是否在这样的情况下继续进行测量。

例如，待测机器此时已经运行了VTune，那么hperf将会给出如下输出：

```
$ python hperf.py sleep 5
2023-01-05 15:24:52,767 INFO     hperf v1.0.0
2023-01-05 15:24:52,767 INFO     test directory: /tmp/hperf/20230105_test003
2023-01-05 15:24:52,937 WARNING  sanity check: process may interfere measurement exists. /opt/intel/oneapi/vtune/2023.0.0/bin64/emon

Detected some problems which may interfere profiling. Continue profiling? [y|N] 
```

若用户键入n/N，那么hperf运行结束；若用户键入y/Y，那么hperf将执行测量。

### 测量

hperf会在工作负载执行的过程，对待测机器的整个系统进行测量，换言之会收集整个系统所有处理器的性能数据。

当工作负载启动时，hperf即开始进行性能监测，当工作负载结束运行时，hperf停止性能监测。

对于那些持续运行的真实应用，例如服务器上持续运行的Redis数据库服务等，如果需要对真实应用测量一段时间，可以在工作负载正常运行的时候，将`sleep <n>`作为工作负载，其中`<n>`是测量的事件（单位为s）。

当前版本的hperf支持的微架构性能指标：

* 基础性能指标
    * CPU利用率
    * 每条指令平均时钟周期（CPI）
* 缓存
    * 每千条指令L1缓存未命中次数（L1 CACHE MPKI）
    * 每千条指令L2缓存未命中次数（L2 CACHE MPKI）
    * 每千条指令L3缓存未命中次数（L3 CACHE MPKI）
* 分支预测
    * 分支预测错误率（BRANCH MISS RATE）

### 案例

#### 单线程或多线程程序的工作负载特征分析

对于一个矩阵乘法的可执行文件，其路径为`./test/mat_mul`，运行时需要传入一个参数，使用hperf测量其运行时的微架构性能指标，其中临时文件夹指定为当前目录下的`./tmp/`，那么调用hperf的命令为：

```
$ python hperf.py --tmp-dir ./tmp -c 5 taskset -c 5 ./test/mat_mul 128
```

其中，由于`mat_mul`程序是绑在5号处理器上运行的，尽管hperf是对整个系统进行测量的，但分析时仅需要用到5号处理器上收集的性能数据，因此使用选项`-c 5`。

执行该命令后，应当会显示如下的输出结果：

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

从输出结果中可以获得本次测量存放相关文件的路径，用户可以查找相关目录的文件以了解性能剖析的执行过程以及中间文件与结果文件。

对于多线程程序，类似的，也应当使用`taskset`或者`numactl`等命令绑定相应的处理器、NUMA节点或SOCKET，之后设置选项`-c`的参数为对应的处理器ID列表。

#### 对于真实应用的工作负载特征分析

对于真实的工作负载特征分析，应当首先启动工作负载，根据需要确定是否绑定处理器、NUMA节点或SOCKET。等工作负载已经完成启动之后，再调用hperf进行进行一段时间的性能检测。

例如，对于redis-server服务，若绑定指定的4个处理器，可以使用：

```
$ taskset -c 1,3,5,7 ./redis-server
```

完成启动后，若希望使用hperf对该工作负载进行1分钟的分析，那么调用hperf的命令为：

```
$ python hperf.py -c 1,3,5,7 sleep 60
```

输出结果与上一个案例类似，因此不再赘述。

## 开发者与联系方式

hperf的主要开发者为：

* 刘通宇 graysonliu@foxmail.com
* 程奂仑 m13955972978_2@163.com