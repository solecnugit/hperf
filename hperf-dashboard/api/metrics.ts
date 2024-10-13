export interface TimeSeriesData {
  timestamp: Date;
  cpuTime: number;
  wallClockTime: number;
  contextSwitches: number;
  tsc: number;
  cycles: number;
  instructions: number;
  referenceCycles: number;
  l1CacheMisses: number;
  l1CacheHits: number;
  l2CacheMisses: number;
  l2CacheHits: number;
  llCacheMisses: number;
  llCacheAccesses: number;
  memAccessesRd: number;
  memAccessesWr: number;
  branchMisses: number;
  branches: number;
  itlbWalks: number;
  dtlbLoadWalks: number;
  dtlbStoreWalks: number;
  dtlbAccesses: number;
  cpuUtilization: number;
  frequency: number;
  cpi: number;
  l1CacheMpki: number;
  l1CacheMissRate: number;
  l2CacheMpki: number;
  l2CacheMissRate: number;
  llCacheMpki: number;
  llCacheMissRate: number;
  memBandwidthRd: number;
  memBandwidthWr: number;
  memBandwidth: number;
  branchMpki: number;
  branchMissRate: number;
  itlbMpki: number;
  dtlbMpki: number;
  dtlbWalkRate: number;
  user: number;
  nice: number;
  system: number;
  iowait: number;
  steal: number;
  idle: number;
}

const csvToJsMapping: Record<string, keyof TimeSeriesData> = {
  timestamp: "timestamp",
  "CPU TIME": "cpuTime",
  "WALL CLOCK TIME": "wallClockTime",
  "CONTEXT SWITCHES": "contextSwitches",
  TSC: "tsc",
  CYCLES: "cycles",
  INSTRUCTIONS: "instructions",
  "REFERENCE CYCLES": "referenceCycles",
  "L1 CACHE MISSES": "l1CacheMisses",
  "L1 CACHE HITS": "l1CacheHits",
  "L2 CACHE MISSES": "l2CacheMisses",
  "L2 CACHE HITS": "l2CacheHits",
  "LL CACHE MISSES": "llCacheMisses",
  "LL CACHE ACCESSES": "llCacheAccesses",
  "MEM ACCESSES RD": "memAccessesRd",
  "MEM ACCESSES WR": "memAccessesWr",
  "BRANCH MISSES": "branchMisses",
  BRANCHES: "branches",
  "ITLB WALKS": "itlbWalks",
  "DTLB LOAD WALKS": "dtlbLoadWalks",
  "DTLB STORE WALKS": "dtlbStoreWalks",
  "DTLB ACCESSES": "dtlbAccesses",
  "CPU UTILIZATION": "cpuUtilization",
  FREQUENCY: "frequency",
  CPI: "cpi",
  "L1 CACHE MPKI": "l1CacheMpki",
  "L1 CACHE MISS RATE": "l1CacheMissRate",
  "L2 CACHE MPKI": "l2CacheMpki",
  "L2 CACHE MISS RATE": "l2CacheMissRate",
  "LL CACHE MPKI": "llCacheMpki",
  "LL CACHE MISS RATE": "llCacheMissRate",
  "MEM BANDWITH RD": "memBandwidthRd",
  "MEM BANDWITH WR": "memBandwidthWr",
  "MEM BANDWITH": "memBandwidth",
  "BRANCH MPKI": "branchMpki",
  "BRANCH MISS RATE": "branchMissRate",
  "ITLB MPKI": "itlbMpki",
  "DTLB MPKI": "dtlbMpki",
  "DTLB WALK RATE": "dtlbWalkRate",
  "CPU_UTIL_USER": "user",
  NICE: "nice",
  "CPU_UTIL_SYS": "system",
  IOWAIT: "iowait",
  STEAL: "steal",
  IDLE: "idle",
};

export type NumericFields = Exclude<keyof TimeSeriesData, "timestamp">;

export const numericFields = Object.values(csvToJsMapping).filter(
  (key) => key !== "timestamp",
) as NumericFields[];

export async function fetchMetricsCSV(): Promise<string> {
  const res = await fetch("/data.csv");
  return await res.text();
}

export async function fetchMetricsJSON(): Promise<TimeSeriesData[]> {
  const data = await fetchMetricsCSV();
  return parseMetrics(data);
}

function parseMetrics(rawData: string): TimeSeriesData[] {
  const lines = rawData.split("\n");
  const header = lines[0].split(",");

  const now = new Date().getTime();
  const validKeys = Object.keys(csvToJsMapping);

  const data = lines
    .slice(1)
    .map((line) => {
      line = line.trim();

      if (line.length === 0) return;

      const values = line.split(",");
      const obj: TimeSeriesData = {} as TimeSeriesData;
      for (let i = 0; i < header.length; i++) {
        const key = header[i] as keyof typeof csvToJsMapping;
        const value = values[i];
        if (key === "timestamp") {
          const timestamp = 1000 * parseInt(value) + now;
          const time = new Date(timestamp);
          obj[key] = time;
        } else if (key) {
          const mappedKey = csvToJsMapping[key] as Exclude<
            keyof TimeSeriesData,
            "timestamp"
          >;
          obj[mappedKey] = parseFloat(value);
        }
      }

      obj.cpuUtilization *= 100;
      // ns to ms
      obj.wallClockTime /= 1e6;
      // byte to bit
      obj.memBandwidthRd *= 8;
      obj.memBandwidthWr *= 8;
      obj.memBandwidth *= 8;
      obj.l1CacheMissRate *= 100;
      obj.l2CacheMissRate *= 100;
      obj.llCacheMissRate *= 100;
      obj.branchMissRate *= 100;

      for (const key of validKeys) {
        if (obj[key] === undefined) {
          obj[key] = 0.0;
          console.warn(`Key ${key} is missing in the data`);
        }
      }

      return obj;
    })
    .filter((obj) => obj !== undefined);

  return data;
}

export async function streamingMetricsJSON(
  onData: (data: TimeSeriesData) => void,
  interval: number = 1000,
) {
  const data = await fetchMetricsJSON();
  let i = 0;

  const intervalId = setInterval(() => {
    onData(data[i]);
    i++;
    if (i >= data.length) {
      clearInterval(intervalId);
    }
  }, interval);
}
