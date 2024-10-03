import { TimeSeriesData, NumericFields } from "@/api/metrics";

const fnTable = {
  average: (data: number[]) =>
    data.reduce((acc, curr) => acc + curr, 0) / data.length,
  max: (data: number[]) => Math.max(...data),
  min: (data: number[]) => Math.min(...data),
  sum: (data: number[]) => data.reduce((acc, curr) => acc + curr, 0),
};

export function compute(
  data: TimeSeriesData[],
  func: "average" | "max" | "min" | "sum",
): TimeSeriesData {
  const fn = fnTable[func];

  return Object.keys(data[0])
    .filter((key) => key !== "timestamp")
    .map((key) => {
      const values = data.map((d) => d[key as NumericFields]);
      const aggregatedValue = fn(values);
      return { key, aggregatedValue };
    })
    .reduce((acc, { key, aggregatedValue }) => {
      acc[key as NumericFields] = aggregatedValue;
      return acc;
    }, {} as TimeSeriesData);
}

export function computeOne(
  data: TimeSeriesData[],
  func: "average" | "max" | "min" | "sum",
  field: NumericFields,
): number {
  const values = data.map((d) => d[field]);
  return fnTable[func](values);
}
