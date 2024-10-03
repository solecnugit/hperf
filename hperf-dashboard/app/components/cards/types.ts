import { NumericFields, numericFields } from "@/api/metrics";

export interface BaseCardLayout {
    i: string;
    x: number;
    y: number;
    w: number;
    h: number;
    resizable?: boolean;
}

export type CardType =
    | "lineplot"
    | "barplot"
    | "radialplot"
    | "hperf"
    | "cpuInfo"
    | "richLineplot";

export interface BaseCardProps {
    type: CardType;
    layout: BaseCardLayout;
    id: string;
}

export interface PlotCardProps extends BaseCardProps {
    metricName: NumericFields;
    unit: string;
}

export interface LineplotCardProps extends PlotCardProps {
    type: "lineplot";
    lineColorStyle: string;
}

export interface BarplotCardProps extends PlotCardProps {
    type: "barplot";
    barColorStyle: string;
}

export interface RadialplotCardProps extends PlotCardProps {
    type: "radialplot";
    radialColorStyle: string;
}

export interface HperfCardProps extends BaseCardProps {
    type: "hperf";
}

export type CPUInfoType = "model" | "cores" | "frequency" | "cache";

const cpuInfoTypes = ["model", "cores", "frequency", "cache"] as const;

export interface CpuInfoCardProps extends PlotCardProps {
    type: "cpuInfo";
    infoType: CPUInfoType;
}

export interface RichLineplotCardsProps extends PlotCardProps {
    type: "richLineplot";
    tableExpanded: boolean;
}

export type CardProps =
    | LineplotCardProps
    | BarplotCardProps
    | RadialplotCardProps
    | HperfCardProps
    | CpuInfoCardProps
    | RichLineplotCardsProps;

const randomBrightColor = (metricName: string) => {
    const seed = metricName
        .split("")
        .reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const hue = seed % 360;
    return `hsl(${hue}, 70%, 50%)`;
};

export const availableCards = {
    lineplot: numericFields.map((metricName) => ({
        type: "lineplot",
        metricName,
        unit: metricName == "cpuUtilization" ? "%" : "",
        lineColorStyle: randomBrightColor(metricName),
        layout: { i: metricName, x: 0, y: 0, w: 3, h: 5 },
    })),
    barplot: numericFields.map((metricName) => ({
        type: "barplot",
        metricName,
        barColorStyle: randomBrightColor(metricName),
        layout: { i: metricName, x: 0, y: 0, w: 3, h: 4 },
    })),
    radialplot: numericFields.map((metricName) => ({
        type: "radialplot",
        metricName,
        radialColorStyle: randomBrightColor(metricName),
        layout: { i: metricName, x: 0, y: 0, w: 1, h: 1 },
    })),
    cpuInfo: cpuInfoTypes.map((infoType) => ({
        type: "cpuInfo",
        infoType,
        layout: { i: infoType, x: 0, y: 0, w: 3, h: 4 },
    })),
    richLineplot: [
        {
            type: "richLineplot",
            metricName: "cpuUtilization",
            tableExpanded: false,
            onMetricChange: (metricName: string) => { },
            onTableStateChange: (expanded: boolean) => { },
            layout: { i: "richLinePlot", x: 0, y: 0, w: 12, h: 6 },
        },
    ],
};
