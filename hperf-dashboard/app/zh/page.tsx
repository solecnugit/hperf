'use client'


import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"

import { streamingMetricsJSON, TimeSeriesData } from "@/api/metrics"
import { useTranslations } from "next-intl"
import { useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Label,
  Line,
  LineChart,
  PolarGrid,
  PolarRadiusAxis,
  RadialBar,
  RadialBarChart,
  Rectangle,
  XAxis,
  YAxis
} from "recharts"
import { computeAverage, computeMax } from "./metrics"
import HperfCard from "../components/cards/hperf"
import LinePlotCard from "../components/cards/lineplot"
import BarplotCard from "../components/cards/barplot"
import RadialPlotCard from "../components/cards/radialplot"

export default function Home() {
  const t = useTranslations("cards");

  const [metrics, setMetrics] = useState<TimeSeriesData[] | null>(null);

  useEffect(() => {
    let started = true;

    streamingMetricsJSON((data) => {
      if (!started)
        return;

      setMetrics(prev => {
        if (prev != null) {
          return [...prev, data];
        } else {
          return [data];
        }
      })
    }, 1000)

    return () => {
      started = false;
    }
  }, []);

  const formatFrequency = (value: number) => {
    // Convert from Hz to GHz
    return (value / 1000000000).toFixed(2) + " GHz";
  }

  return (
    <div className=" mx-auto flex max-w-6xl flex-col flex-wrap items-start justify-center gap-6 p-6 sm:flex-row sm:p-8">
      <div className="grid w-full gap-6 grid-cols-12">
        {/* Hperf Logo Card */}
        <HperfCard />
        {/* CPU Utilization Card */}
        {metrics && (<LinePlotCard metricName="cpuUtilization" avgI18nKey="avgCpuUtilization" descriptionI18nKey="cpuUtilization" unit="%" maxI18nKey="maxCpuUtilization" metrics={metrics} />)}
        {/* CPU Freq Card */}
        {metrics && (<RadialPlotCard metricName="frequency" descriptionI18nKey="frequencyDescription" metrics={metrics} valueFormatter={
          formatFrequency
        } />)}
        {/* CPU CPI Card */}
        {metrics && (<BarplotCard metricName="cpi" descriptionI18nKey="cpiDescription" unit="" metrics={metrics}  />)}
      </div>
    </div>
  );
}