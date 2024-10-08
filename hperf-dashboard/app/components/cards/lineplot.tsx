"use client";

import { NumericFields, TimeSeriesData } from "@/api/metrics";
import { computeOne } from "@/app/zh/metrics";
import {
  Card,
  CardHeader,
  CardDescription,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { useTranslations } from "next-intl";
import { useMemo } from "react";
import { LineChart, CartesianGrid, YAxis, XAxis, Line } from "recharts";
import { formatBandwidth, autoFormat } from "./utils";

export default function LinePlotCard({
  metricName,
  unit = "",
  metrics,
  lineColorStyle = "hsl(var(--chart-1))",
  valueFormatter,
}: {
  metrics: TimeSeriesData[];
  metricName: NumericFields;
  unit?: string;
  lineColorStyle?: string;
  valueFormatter?: "bandwidth";
}) {
  const t = useTranslations("cards");
  const mt = useTranslations("metrics");

  const avgValue = useMemo(() => {
    if (metrics.length === 0) {
      return 0.0;
    }

    const value = computeOne(metrics, "average", metricName);

    if (valueFormatter && valueFormatter === "bandwidth") {
      return formatBandwidth(value);
    }

    return autoFormat(value);
  }, [metrics]);

  const maxValue = useMemo(() => {
    if (metrics.length === 0) {
      return 0.0;
    }

    const value = computeOne(metrics, "max", metricName);

    if (valueFormatter && valueFormatter === "bandwidth") {
      return formatBandwidth(value);
    }

    return autoFormat(value);
  }, [metrics]);

  return (
    <Card className="flex flex-col w-full h-full px-2 pt-2">
      <div className="px-4 drag-handle w-full h-[6px] bg-primary rounded-md opacity-0 hover:opacity-5 transition-all "></div>
      <CardHeader className="drag-handle flex flex-row items-center gap-4 space-y-0 py-2 [&>div]:flex-1">
        <div>
          <CardDescription>{t("average") + mt(metricName)}</CardDescription>
          <CardTitle className="flex items-baseline gap-1 text-4xl tabular-nums">
            {avgValue}
            <span className="text-sm font-normal tracking-normal text-muted-foreground">
              {unit}
            </span>
          </CardTitle>
        </div>
        <div>
          <CardDescription>{t("max") + mt(metricName)}</CardDescription>
          <CardTitle className="flex items-baseline gap-1 text-4xl tabular-nums">
            {maxValue}
            <span className="text-sm font-normal tracking-normal text-muted-foreground">
              {unit}
            </span>
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="flex flex-1 items-center">
        <ChartContainer
          config={{
            [metricName]: {
              label: `${t(metricName)}`,
              color: lineColorStyle,
            },
          }}
          className="w-full min-h-[60px] max-h-[220px]"
        >
          <LineChart
            accessibilityLayer
            margin={{
              left: 14,
              right: 14,
              top: 10,
            }}
            data={metrics}
          >
            <CartesianGrid
              strokeDasharray="4 4"
              vertical={false}
              stroke="hsl(var(--muted-foreground))"
              strokeOpacity={0.5}
            />
            <YAxis hide domain={["dataMin - 10", "dataMax + 10"]} />
            <XAxis
              dataKey="timestamp"
              tickLine={false}
              axisLine={false}
              tickMargin={5}
              tickCount={2}
              interval="preserveStartEnd"
              tickFormatter={(value) => {
                return new Date(value).toLocaleTimeString();
              }}
            />
            <Line
              dataKey={metricName}
              type="natural"
              fill={`var(--color-${metricName})`}
              stroke={`var(--color-${metricName})`}
              strokeWidth={2}
              dot={false}
              activeDot={{
                fill: `var(--color-${metricName})`,
                stroke: `var(--color-${metricName})`,
                r: 4,
              }}
            />
            <ChartTooltip
              content={
                <ChartTooltipContent
                  indicator="line"
                  labelFormatter={(value, payload) => {
                    return new Date(
                      payload[0]["payload"]?.timestamp || 0,
                    ).toLocaleTimeString();
                  }}
                />
              }
              cursor={false}
            />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
