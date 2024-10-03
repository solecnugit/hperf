import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Layers3 } from "lucide-react"

import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart"
import { TimeSeriesData } from "@/api/metrics"
import { useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { SelectGroup, SelectLabel } from "@radix-ui/react-select"
import { Button } from "@/components/ui/button"
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"

export function RichLinePlotCard({ metrics }: { metrics: TimeSeriesData[] }) {
    const mt = useTranslations("metrics")
    const t = useTranslations("cards")

    const [metricName, setMetricName] = useState("cpuUtilization")
    const [tableExpanded, setTableExpanded] = useState(false)

    const toggleTable = () => {
        setTableExpanded(!tableExpanded)
    }

    const lineColor = useMemo(() => {
        const seed = metricName.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0)
        const hue = seed % 360
        return `hsl(${hue}, 70%, 50%)`
    }, [metricName])

    const groupedMetricNames = {
        "software": [
            "cpuUtilization",
            "cpuTime",
            "wallClockTime",
            "contextSwitches",
            "user",
            "nice",
            "system",
            "iowait",
            "steal",
            "idle",
        ],
        "cycles": [
            "tsc",
            "cycles",
            "instructions",
            "referenceCycles",
            "memAccessesRd",
            "memAccessesWr",
            "branchMisses",
            "branches",
            "frequency",
            "cpi",
            "memBandwidthRd",
            "memBandwidthWr",
            "memBandwidth",
        ],
        "cache": [
            "l1CacheMisses",
            "l1CacheHits",
            "l2CacheMisses",
            "l2CacheHits",
            "llCacheMisses",
            "llCacheAccesses",
            "l1CacheMpki",
            "l1CacheMissRate",
            "l2CacheMpki",
            "l2CacheMissRate",
            "llCacheMpki",
            "llCacheMissRate",
            "itlbWalks",
            "dtlbLoadWalks",
            "dtlbStoreWalks",
            "dtlbAccesses",
            "branchMpki",
            "branchMissRate",
            "itlbMpki",
            "dtlbMpki",
            "dtlbWalkRate",
        ]
    }

    return (
        <Card className="w-full h-full px-4 pt-2 pb-0 select-none">
            <div className="drag-handle w-full h-[6px] bg-primary rounded-md opacity-0 hover:opacity-5 transition-all"></div>
            <CardHeader className="flex flex-row items-center justify-between">
                <div>
                    <CardTitle>{mt(metricName)}</CardTitle>
                    <CardDescription></CardDescription>
                </div>
                <div className="flex items-center gap-2">
                    <Select onValueChange={setMetricName}>
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder={mt(metricName)} />
                        </SelectTrigger>
                        <SelectContent>
                            {
                                Object.entries(groupedMetricNames).map(([groupName, metricNames]) => (
                                    <SelectGroup>
                                        <SelectLabel className="font-semibold leading-8">{mt(`group.${groupName}`)}</SelectLabel>
                                        {
                                            metricNames.map((metricName) => (
                                                <SelectItem value={metricName}>
                                                    {mt(metricName)}({metricName})
                                                </SelectItem>
                                            ))
                                        }
                                    </SelectGroup>
                                ))
                            }
                        </SelectContent>
                    </Select>
                    <Checkbox id="tableExpand" onCheckedChange={(state) => {
                        if (state === "indeterminate") {
                            return
                        }

                        setTableExpanded(state)
                    }} className="z-100"></Checkbox>
                    <label htmlFor="tableExpand">{mt("expandTable")}</label>
                </div>
            </CardHeader>
            <CardContent>
                <ResizablePanelGroup direction="horizontal">
                    <ResizablePanel className="px-2">
                        <ChartContainer config={{
                            [metricName]: {
                                label: mt(metricName),
                                color: lineColor,
                            }
                        }} className="w-full min-h-[60px] max-h-[220px]">
                            <LineChart
                                accessibilityLayer
                                data={metrics}
                                margin={{
                                    left: 12,
                                    right: 12,
                                }}
                            >
                                <CartesianGrid vertical={false} />
                                <YAxis
                                    tickLine={false}
                                    axisLine={false}
                                    tickMargin={8}
                                    interval="preserveStartEnd"
                                />
                                <XAxis
                                    dataKey="timestamp"
                                    tickLine={false}
                                    axisLine={false}
                                    tickMargin={8}
                                    interval="preserveStartEnd"
                                    tickFormatter={(value) => {
                                        return new Date(value).toLocaleTimeString()
                                    }}
                                />
                                <ChartTooltip
                                    cursor={false}
                                    content={<ChartTooltipContent hideLabel />}
                                />
                                <Line
                                    dataKey={metricName}
                                    type="natural"
                                    stroke={`var(--color-${metricName})`}
                                    strokeWidth={2}
                                    dot={{
                                        fill: `var(--color-${metricName})`,
                                    }}
                                    activeDot={{
                                        r: 6,
                                    }}
                                />
                            </LineChart>
                        </ChartContainer>
                    </ResizablePanel>
                    {
                        tableExpanded && (
                            <ResizableHandle />
                        )
                    }
                    {
                        tableExpanded && (
                            <ResizablePanel className="px-2 h-[220px] max-h-[220px] overflow-y-scroll first:h-[220px] first:overflow-y-scroll">
                                <Table className="table-fixed">
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead className="text-right sticky top-0">{mt("timestamp")}</TableHead>
                                            <TableHead className="text-right sticky top-0">{mt(metricName)}</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {
                                            metrics.toReversed().map((metric) => (
                                                <TableRow className="text-right leading-8">
                                                    <td>{new Date(metric.timestamp).toLocaleTimeString()}</td>
                                                    <td>{metric[metricName].toFixed(2)}</td>
                                                </TableRow>
                                            ))
                                        }
                                    </TableBody>
                                </Table>
                            </ResizablePanel>
                        )
                    }
                </ResizablePanelGroup>
            </CardContent>
        </Card>
    )
}
