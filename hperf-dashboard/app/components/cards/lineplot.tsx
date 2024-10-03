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

export default function LinePlotCard({
  metricName,
  avgI18nKey,
  maxI18nKey,
  descriptionI18nKey,
  unit = "",
  metrics,
  lineColorStyle = "hsl(var(--chart-1))",
}: {
  metrics: TimeSeriesData[];
  metricName: NumericFields;
  avgI18nKey: string;
  maxI18nKey: string;
  descriptionI18nKey: string;
  unit?: string;
  lineColorStyle?: string;
}) {
  const t = useTranslations("cards");

  const avgValue = useMemo(() => {
    if (metrics.length === 0) {
      return 0.0;
    }

    return computeOne(metrics, "average", metricName);
  }, [metrics]);

  const maxValue = useMemo(() => {
    if (metrics.length === 0) {
      return 0.0;
    }

    return computeOne(metrics, "max", metricName);
  }, [metrics]);

  return (
    <Card className="flex flex-col w-full h-full px-2 pt-2 select-none">
      <div className="px-4 drag-handle w-full h-[6px] bg-primary rounded-md opacity-0 hover:opacity-5 transition-all "></div>
      <CardHeader className="drag-handle flex flex-row items-center gap-4 space-y-0 py-2 [&>div]:flex-1">
        <div>
          <CardDescription>{t(avgI18nKey)}</CardDescription>
          <CardTitle className="flex items-baseline gap-1 text-4xl tabular-nums">
            {avgValue.toFixed(2)}
            <span className="text-sm font-normal tracking-normal text-muted-foreground">
              {unit}
            </span>
          </CardTitle>
        </div>
        <div>
          <CardDescription>{t(maxI18nKey)}</CardDescription>
          <CardTitle className="flex items-baseline gap-1 text-4xl tabular-nums">
            {maxValue.toFixed(2)}
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
          className="w-full"
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
