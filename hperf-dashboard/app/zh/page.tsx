"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

import { streamingMetricsJSON, TimeSeriesData } from "@/api/metrics";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";
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
  YAxis,
} from "recharts";
import HperfCard from "../components/cards/hperf";
import LinePlotCard from "../components/cards/lineplot";
import BarplotCard from "../components/cards/barplot";
import RadialPlotCard from "../components/cards/radialplot";

import RGL, { WidthProvider } from "react-grid-layout";
import { CpuInfo, fetchCpuInfoJson } from "@/api/cpuInfo";
import CpuInfoCard from "../components/cards/cpuInfo";
import { RichLinePlotCard } from "../components/cards/richLinePlot";
import { useLocalStorage } from "./storage";
import { BarplotCardProps, BaseCardLayout, BaseCardProps, CardProps, CpuInfoCardProps, HperfCardProps, LineplotCardProps, RadialplotCardProps, RichLinePlotCardProps } from "../components/cards/types";

const ReactGridLayout = WidthProvider(RGL);

export default function Home() {
  const t = useTranslations("cards");

  const [metrics, setMetrics] = useState<TimeSeriesData[] | null>(null);
  const [cpuInfo, setCpuInfo] = useState<CpuInfo | null>(null);

  useEffect(() => {
    let started = true;

    streamingMetricsJSON((data) => {
      if (!started) return;

      setMetrics((prev) => {
        if (prev != null) {
          return [...prev, data];
        } else {
          return [data];
        }
      });
    }, 1000);

    return () => {
      started = false;
    };
  }, []);

  useEffect(() => {
    fetchCpuInfoJson().then(setCpuInfo);
  }, []);

  const formatFrequency = (value: number) => {
    // Convert from Hz to GHz
    return (value / 1000000000).toFixed(2) + " GHz";
  };

  const [cardStorages, setCardStorages] = useLocalStorage<CardProps[]>("cardStorages", [
    { type: "hperf", id: "hperf", layout: { i: "hperf", x: 0, y: 0, w: 2, h: 2, resizable: false } },
    // { i: "cpuUtilization", x: 1, y: 1, w: 3, h: 5 },
    // { i: "frequency", x: 3, y: 0, w: 3, h: 4 },
    // { i: "cpi", x: 5, y: 0, w: 2, h: 2 },
    // { i: "cpuInfoCache", x: 7, y: 0, w: 3, h: 3 },
    // { i: "cpuInfoFreq", x: 9, y: 0, w: 2, h: 2 },
    // { i: "cpuInfoModel", x: 11, y: 0, w: 3, h: 4 },
    // { i: "lineplot", x: 0, y: 0, w: 12, h: 6 },
  ]);

  const layouts = useMemo(() => {
    return cardStorages.map((card) => {
      return card.layout;
    });
  }, [cardStorages])

  const mergeLayouts = (props: BaseCardLayout[]) => {
    setCardStorages((prev) => {
      return prev.map((card) => {
        let layout = props.find((prop) => prop.i === card.layout.i);

        if (layout) {
          return {
            ...card,
            layout,
          }
        }

        return card;
      });
    });
  }

  const cards = useMemo(() => {
    if (!metrics || !cpuInfo) {
      return null;
    }

    const factories = {
      "hperf": (props: HperfCardProps) => <HperfCard />,
      "lineplot": (props: LineplotCardProps) => <LinePlotCard metrics={metrics} {...props} />,
      "barplot": (props: BarplotCardProps) => <BarplotCard metrics={metrics} {...props} />,
      "radialplot": (props: RadialplotCardProps) => <RadialPlotCard metrics={metrics} {...props} />,
      "cpuInfo": (props: CpuInfoCardProps) => <CpuInfoCard cpuInfo={cpuInfo} type={props.infoType} />,
      "richLinePlot": (props: RichLinePlotCardProps) => <RichLinePlotCard metrics={metrics} onMetricChange={(metricName) => {
        // @ts-ignore
        setCardStorages((prev) => {
          return prev.map((card) => {
            if (card.type === "richLinePlot" && card.i == props.i) {
              return {
                ...card,
                metricName,
              }
            }

            return card;
          });
        });
      }} onTableStateChange={(state) => {
        setCardStorages((prev) => {
          return prev.map((card) => {
            if (card.type === "richLinePlot" && card.i == props.i) {
              return {
                ...card,
                tableExpanded: state,
              }
            }

            return card;
          });
        });
      }} {...props} />,
    }

    return cardStorages.map((card) => {
      console.log(card)

      // @ts-ignore
      let cardComponent = factories[card.type](card);

      return (
        <div key={card.i}>
          {cardComponent}
        </div>
      )
    })
  }, [cardStorages, metrics, cpuInfo]);

  return (
    <div className="p-8">
      <ReactGridLayout
        className="layout mx-auto gap-8"
        cols={12}
        layout={layouts}
        rowHeight={60}
        compactType="vertical"
        preventCollision={false}
        draggableHandle=".drag-handle"
        width={1920}
        onLayoutChange={mergeLayouts}
      >
        <div key="hperf">
          <HperfCard metrics={metrics} cpuInfo={cpuInfo} />
        </div>
        {/* <div key="cpuUtilization">
          {metrics && (
            <LinePlotCard
              metricName="cpuUtilization"
              avgI18nKey="avgCpuUtilization"
              descriptionI18nKey="cpuUtilization"
              unit="%"
              maxI18nKey="maxCpuUtilization"
              metrics={metrics}
            />
          )}
        </div> */}
        {/* <div key="frequency">
          {metrics && (
            <RadialPlotCard
              metricName="frequency"
              descriptionI18nKey="frequencyDescription"
              metrics={metrics}
              valueFormatter={formatFrequency}
            />
          )}
        </div> */}
        {/* <div key="cpi">
          {metrics && (
            <BarplotCard
              metricName="cpi"
              descriptionI18nKey="cpiDescription"
              unit=""
              metrics={metrics}
            />
          )}
        </div> */}
        {/* <div key="cpuInfoFreq">
          {cpuInfo && <CpuInfoCard cpuInfo={cpuInfo} type="frequency" />}
        </div>
        <div key="cpuInfoCache">
          {cpuInfo && <CpuInfoCard cpuInfo={cpuInfo} type="cache" />}
        </div>
        <div key="cpuInfoModel">
          {cpuInfo && <CpuInfoCard cpuInfo={cpuInfo} type="model" />}
        </div>
        <div key="lineplot">
          {metrics && <RichLinePlotCard metrics={metrics}></RichLinePlotCard>}
        </div> */}
      </ReactGridLayout>
    </div>
  );
}

{
  /* <div className="grid w-full gap-6 grid-cols-12">
        <HperfCard />
        {metrics && (<LinePlotCard metricName="cpuUtilization" avgI18nKey="avgCpuUtilization" descriptionI18nKey="cpuUtilization" unit="%" maxI18nKey="maxCpuUtilization" metrics={metrics} />)}
        {metrics && (<RadialPlotCard metricName="frequency" descriptionI18nKey="frequencyDescription" metrics={metrics} valueFormatter={
          formatFrequency
        } />)}
        {metrics && (<BarplotCard metricName="cpi" descriptionI18nKey="cpiDescription" unit="" metrics={metrics}  />)}
      </div> */
}
