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
import HperfCard from "../components/cards/hperf"
import LinePlotCard from "../components/cards/lineplot"
import BarplotCard from "../components/cards/barplot"
import RadialPlotCard from "../components/cards/radialplot"

import RGL, { WidthProvider } from "react-grid-layout";
import { CpuInfo, fetchCpuInfoJson } from "@/api/cpuInfo"
import CpuInfoCard from "../components/cards/cpuInfo"
import { RichLinePlotCard } from "../components/cards/richLinePlot"

const ReactGridLayout = WidthProvider(RGL);

export default function Home() {
  const t = useTranslations("cards");

  const [metrics, setMetrics] = useState<TimeSeriesData[] | null>(null);
  const [cpuInfo, setCpuInfo] = useState<CpuInfo | null>(null);

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

  useEffect(() => {
    fetchCpuInfoJson().then(setCpuInfo);
  }, []);

  const formatFrequency = (value: number) => {
    // Convert from Hz to GHz
    return (value / 1000000000).toFixed(2) + " GHz";
  }



  const layout = [
    { i: 'hperf', x: 0, y: 0, w: 1, h: 1 },
    { i: 'cpuUtilization', x: 1, y: 1, w: 3, h: 5 },
    { i: 'frequency', x: 3, y: 0, w: 3, h: 4 },
    { i: 'cpi', x: 5, y: 0, w: 2, h: 2 },
    { i: 'cpuInfoCache', x: 7, y: 0, w: 3, h: 3 },
    { i: 'cpuInfoFreq', x: 9, y: 0, w: 2, h: 2 },
    { i: 'cpuInfoModel', x: 11, y: 0, w: 3, h: 4 },
    { i: 'lineplot', x: 0, y: 0, w: 12, h: 6 },
  ]

  return (
    <div className="p-8">
      <ReactGridLayout className="layout mx-auto gap-8" cols={12} layout={layout}
        rowHeight={60} compactType="horizontal" preventCollision={false} draggableHandle=".drag-handle"
        width={1920}>
        <div key="hperf" >
          <HperfCard />
        </div>
        <div key="cpuUtilization">
          {metrics && (<LinePlotCard metricName="cpuUtilization" avgI18nKey="avgCpuUtilization" descriptionI18nKey="cpuUtilization" unit="%" maxI18nKey="maxCpuUtilization" metrics={metrics} />)}
        </div>
        <div key="frequency">
          {metrics && (<RadialPlotCard metricName="frequency" descriptionI18nKey="frequencyDescription" metrics={metrics} valueFormatter={
            formatFrequency
          } />)}
        </div>
        <div key="cpi">
          {metrics && (<BarplotCard metricName="cpi" descriptionI18nKey="cpiDescription" unit="" metrics={metrics} />)}
        </div>
        <div key="cpuInfoFreq">
          {cpuInfo && (<CpuInfoCard cpuInfo={cpuInfo} type="frequency" />)}
        </div>
        <div key="cpuInfoCache">
          {cpuInfo && (<CpuInfoCard cpuInfo={cpuInfo} type="cache" />)}
        </div>
        <div key="cpuInfoModel">
          {cpuInfo && (<CpuInfoCard cpuInfo={cpuInfo} type="model" />)}
        </div>
        <div key="lineplot">
          {metrics && (<RichLinePlotCard metrics={metrics}></RichLinePlotCard>)}
        </div>
      </ReactGridLayout>
    </div>
  );
}

{/* <div className="grid w-full gap-6 grid-cols-12">
        <HperfCard />
        {metrics && (<LinePlotCard metricName="cpuUtilization" avgI18nKey="avgCpuUtilization" descriptionI18nKey="cpuUtilization" unit="%" maxI18nKey="maxCpuUtilization" metrics={metrics} />)}
        {metrics && (<RadialPlotCard metricName="frequency" descriptionI18nKey="frequencyDescription" metrics={metrics} valueFormatter={
          formatFrequency
        } />)}
        {metrics && (<BarplotCard metricName="cpi" descriptionI18nKey="cpiDescription" unit="" metrics={metrics}  />)}
      </div> */}