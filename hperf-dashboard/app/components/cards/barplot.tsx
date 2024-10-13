"use client";

import { TimeSeriesData } from "@/api/metrics";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { ChartContainer } from "@/components/ui/chart";
import { useTranslations } from "next-intl";
import { useMemo } from "react";
import { BarChart, Bar, Rectangle, XAxis } from "recharts";
import { autoFormat, formatBandwidth } from "./utils";

export default function BarplotCard({
  metricName,
  unit = "",
  metrics,
  barColorStyle = "hsl(var(--chart-2))",
  valueFormatter
}: {
  metrics: TimeSeriesData[];
  metricName: string;
  unit?: string;
  barColorStyle?: string;
    valueFormatter?: "bandwidth" | "percentage";
}) {
  const t = useTranslations("cards");

  const lastMetric = useMemo(() => {
    if (metrics.length === 0) {
      return 0.0;
    }

    const metric = metrics[metrics.length - 1];

    // @ts-ignore
    return metric[metricName] || 0.0;
  }, [metrics]);

  const value = useMemo(() => {
    if (valueFormatter && valueFormatter === "bandwidth") {
      return formatBandwidth(lastMetric);
    }

    if (valueFormatter && valueFormatter === "percentage") {
      return lastMetric.toFixed(2) + "%";
    }

    return autoFormat(lastMetric);
  }, [lastMetric]);

  const last5Metrics = useMemo(() => {
    return metrics.slice(-5);
  }, [metrics]);

  return (
    <Card className="w-full h-full p-2 pt-2">
      <div className="px-4 drag-handle w-full h-[6px] bg-primary rounded-md opacity-0 hover:opacity-5 transition-all "></div>
      <CardHeader className="px-4 pb-0 pt-2">
        <CardTitle>{t(metricName)}</CardTitle>
        <CardDescription>{t(`desc.${metricName}`)}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-row items-baseline gap-4 p-4 pt-2">
        <div className="flex items-baseline gap-2 text-3xl font-bold tabular-nums leading-none">
          {value}
          <span className="text-sm font-normal text-muted-foreground">
            {unit}
          </span>
        </div>
        <ChartContainer
          config={{
            [metricName]: {
              label: t(metricName),
              color: barColorStyle,
            },
          }}
          className="ml-auto w-[64px]"
        >
          <BarChart
            accessibilityLayer
            margin={{
              left: 0,
              right: 0,
              top: 0,
              bottom: 0,
            }}
            data={last5Metrics}
          >
            <Bar
              dataKey={metricName}
              fill={`var(--color-${metricName})`}
              radius={2}
              fillOpacity={0.2}
              activeIndex={6}
              activeBar={<Rectangle fillOpacity={0.9} />}
            />
            <XAxis
              dataKey="timestamp"
              tickLine={false}
              axisLine={false}
              tickMargin={4}
              hide
            />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
