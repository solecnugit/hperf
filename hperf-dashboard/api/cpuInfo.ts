export interface CpuInfo {
    architecture: string;
    cpuOpModes: string[];
    addressSizes: {
        physical: string;
        virtual: string;
    };
    byteOrder: string;
    cpus: number;
    onlineCpusList: string;
    vendorId: string;
    modelName: string;
    cpuFamily: number;
    model: number;
    threadsPerCore: number;
    coresPerSocket: number;
    sockets: number;
    stepping: number;
    maxMHz: number;
    minMHz: number;
    bogoMips: number;
    flags: string[];
    virtualization: string;
    cache: {
        l1d: string;
        l1i: string;
        l2: string;
        l3: string;
    };
    numaNodes: number;
    numaNodeCpus: {
        [key: string]: string;
    };
}

export async function fetchCpuInfoText(): Promise<string> {
    const res = await fetch('/cpu_info')
    return await res.text()
}

export async function fetchCpuInfoJson(): Promise<CpuInfo> {
    const data = await fetchCpuInfoText()
    return parseCPUInfo(data)
}

function parseCPUInfo(rawData: string): CpuInfo {
    const lines = rawData.split("\n");

    const cpuInfo: CpuInfo = {
        architecture: '',
        cpuOpModes: [],
        addressSizes: {
            physical: '',
            virtual: ''
        },
        byteOrder: '',
        cpus: 0,
        onlineCpusList: '',
        vendorId: '',
        modelName: '',
        cpuFamily: 0,
        model: 0,
        threadsPerCore: 0,
        coresPerSocket: 0,
        sockets: 0,
        stepping: 0,
        maxMHz: 0,
        minMHz: 0,
        bogoMips: 0,
        flags: [],
        virtualization: '',
        cache: {
            l1d: '',
            l1i: '',
            l2: '',
            l3: ''
        },
        numaNodes: 0,
        numaNodeCpus: {}
    };

    lines.forEach(line => {
        const [key, value] = line.split(":").map(s => s.trim());

        switch (key) {
            case "Architecture":
                cpuInfo.architecture = value;
                break;
            case "CPU op-mode(s)":
                cpuInfo.cpuOpModes = value.split(",").map(s => s.trim());
                break;
            case "Address sizes":
                const [physical, virtual] = value.split(",").map(s => s.trim());
                cpuInfo.addressSizes.physical = physical.split(" ")[0] + ' bits';
                cpuInfo.addressSizes.virtual = virtual.split(" ")[0] + ' bits';
                break;
            case "Byte Order":
                cpuInfo.byteOrder = value;
                break;
            case "CPU(s)":
                cpuInfo.cpus = parseInt(value, 10);
                break;
            case "On-line CPU(s) list":
                cpuInfo.onlineCpusList = value;
                break;
            case "Vendor ID":
                cpuInfo.vendorId = value;
                break;
            case "Model name":
                cpuInfo.modelName = value;
                break;
            case "CPU family":
                cpuInfo.cpuFamily = parseInt(value, 10);
                break;
            case "Model":
                cpuInfo.model = parseInt(value, 10);
                break;
            case "Thread(s) per core":
                cpuInfo.threadsPerCore = parseInt(value, 10);
                break;
            case "Core(s) per socket":
                cpuInfo.coresPerSocket = parseInt(value, 10);
                break;
            case "Socket(s)":
                cpuInfo.sockets = parseInt(value, 10);
                break;
            case "Stepping":
                cpuInfo.stepping = parseInt(value, 10);
                break;
            case "CPU max MHz":
                cpuInfo.maxMHz = parseFloat(value);
                break;
            case "CPU min MHz":
                cpuInfo.minMHz = parseFloat(value);
                break;
            case "BogoMIPS":
                cpuInfo.bogoMips = parseFloat(value);
                break;
            case "Flags":
                cpuInfo.flags = value.split(" ");
                break;
            case "Virtualization":
                cpuInfo.virtualization = value;
                break;
            case "L1d cache":
                cpuInfo.cache.l1d = value;
                break;
            case "L1i cache":
                cpuInfo.cache.l1i = value;
                break;
            case "L2 cache":
                cpuInfo.cache.l2 = value;
                break;
            case "L3 cache":
                cpuInfo.cache.l3 = value;
                break;
            case "NUMA node(s)":
                cpuInfo.numaNodes = parseInt(value, 10);
                break;
            case "NUMA node0 CPU(s)":
                cpuInfo.numaNodeCpus["node0"] = value;
                break;
            case "NUMA node1 CPU(s)":
                cpuInfo.numaNodeCpus["node1"] = value;
                break;
        }
    });

    return cpuInfo;
}