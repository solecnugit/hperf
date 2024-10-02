import { TimeSeriesData } from "@/api/metrics"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { ChartContainer } from "@/components/ui/chart"
import { useTranslations } from "next-intl";
import { useMemo } from "react";
import { RadialBarChart, PolarGrid, RadialBar, PolarRadiusAxis, Label } from "recharts"

export default function RadialPlotCard({ metricName, descriptionI18nKey, unit = "", metrics, maxValue = 5e9, radialColorStyle = "hsl(var(--chart-4))", valueFormatter }: { metrics: TimeSeriesData[], metricName: string, descriptionI18nKey: string, unit?: string, radialColorStyle?: string, maxValue?: number, valueFormatter?: (value: number) => string }) {
    const t = useTranslations("cards");

    const lastMetric = useMemo(() => {
        if (metrics.length === 0) {
            return 0.0;
        }

        const metric = metrics[metrics.length - 1];

        // @ts-ignore
        return metric[metricName] || 0.0;
    }, [metrics]);

    const lastMetricArray = useMemo(() => {
        if (metrics.length === 0) {
            return [];
        }

        return metrics.slice(-1);
    }, [metrics]);

    const angle = useMemo(() => {
        return (lastMetric / maxValue) * 360;
    }, [lastMetric, maxValue]);

    return (
        <Card
            className="max-w-xs col-span-4 row-span-1"
        >
            <CardHeader className="p-4 pb-0">
                <CardTitle>{t(metricName)}</CardTitle>
                <CardDescription>
                    {t(descriptionI18nKey)}
                </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-1 items-center">
                <ChartContainer
                    config={{
                        [metricName]: {
                            label: t(metricName),
                            color: radialColorStyle,
                        },
                    }}
                    className="w-full"
                >
                    <RadialBarChart
                        data={lastMetricArray}
                        startAngle={0}
                        endAngle={angle}
                        innerRadius={70}
                        outerRadius={90}
                    >
                        <PolarGrid
                            gridType="circle"
                            radialLines={false}
                            stroke="none"
                            className="first:fill-muted last:fill-background"
                            polarRadius={[74, 64]}
                        />
                        <RadialBar fill={radialColorStyle} dataKey={metricName} background cornerRadius={10} />
                        <PolarRadiusAxis tick={false} tickLine={false} axisLine={false}>
                            <Label
                                content={({ viewBox }) => {
                                    if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                                        return (
                                            <text
                                                x={viewBox.cx}
                                                y={viewBox.cy}
                                                textAnchor="middle"
                                                dominantBaseline="middle"
                                            >
                                                <tspan
                                                    x={viewBox.cx}
                                                    y={viewBox.cy}
                                                    className="fill-foreground text-3xl font-bold"
                                                >
                                                    {valueFormatter ? valueFormatter(lastMetric) : lastMetric}
                                                </tspan>
                                                <tspan
                                                    x={viewBox.cx}
                                                    y={(viewBox.cy || 0) + 24}
                                                    className="fill-muted-foreground"
                                                >
                                                    {t(metricName)}
                                                </tspan>
                                            </text>
                                        )
                                    }
                                }}
                            />
                        </PolarRadiusAxis>
                    </RadialBarChart>
                </ChartContainer>
            </CardContent>
        </Card>
    )
}