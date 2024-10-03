'use client'

import { Button } from "@/components/ui/button";
import { Drawer, DrawerClose, DrawerContent, DrawerDescription, DrawerFooter, DrawerHeader, DrawerTitle, DrawerTrigger } from "@/components/ui/drawer";
import { Minimize2, Plus } from "lucide-react";
import { useTranslations } from "next-intl";

import RGL, { WidthProvider } from "react-grid-layout";
import { availableCards, BarplotCardProps, CpuInfoCardProps, HperfCardProps, LineplotCardProps, RadialplotCardProps, RichLinePlotCardProps } from "./types";
import { TimeSeriesData } from "@/api/metrics";
import { CpuInfo } from "os";
import { useEffect, useMemo, useState } from "react";
import BarplotCard from "./barplot";
import CpuInfoCard from "./cpuInfo";
import HperfCard from "./hperf";
import LinePlotCard from "./lineplot";
import RadialPlotCard from "./radialplot";
import { RichLinePlotCard } from "./richLinePlot";

const ReactGridLayout = WidthProvider(RGL);

const deepCopy = (obj: any) => JSON.parse(JSON.stringify(obj));

export default function CardDrawer({ metrics, cpuInfo }: {
    metrics: TimeSeriesData[] | null;
    cpuInfo: CpuInfo | null;
}) {
    const t = useTranslations("drawer");

    // const [cardTemplates, setCardTemplates] = useState<any[]>([]);

    // useEffect(() => {
    //     const cardTemplates = Object.keys(availableCards).flatMap((key, index) => {
    //         const categoryCards = availableCards[key as keyof typeof availableCards]

    //         return categoryCards.map((card) => {
    //             const uuid = "card:" + index;

    //             return {
    //                 ...card,
    //                 id: uuid,
    //                 layout: {
    //                     ...card.layout,
    //                     i: uuid
    //                 }
    //             };
    //         });
    //     });

    //     setCardTemplates(cardTemplates);
    // }, [metrics, cpuInfo])

    // const cards = useMemo(() => {
    //     if (!metrics || !cpuInfo) {
    //         return null;
    //     }

    //     const factories = {
    //         "lineplot": (props: LineplotCardProps) => <LinePlotCard metrics={metrics} metricName={props.metricName} avgI18nKey={props.avgI18nKey} maxI18nKey={props.maxI18nKey} descriptionI18nKey={props.descriptionI18nKey} unit={props.unit} lineColorStyle={props.lineColorStyle} />,
    //         "barplot": (props: BarplotCardProps) => <BarplotCard metrics={metrics} metricName={props.metricName} descriptionI18nKey={props.descriptionI18nKey} barColorStyle={props.barColorStyle} />,
    //         "radialplot": (props: RadialplotCardProps) => <RadialPlotCard metrics={metrics} metricName={props.metricName} radialColorStyle={props.radialColorStyle} descriptionI18nKey={props.descriptionI18nKey} />,
    //         "cpuInfo": (props: CpuInfoCardProps) => <CpuInfoCard cpuInfo={cpuInfo} type={props.infoType} />,
    //         "richLinePlot": (props: RichLinePlotCardProps) => <RichLinePlotCard metrics={metrics} onMetricChange={(metricName) => {

    //         }} onTableStateChange={(state) => {
    //         }} metricName={props.metricName} tableExpanded={false} />,
    //     }

    //     return cardTemplates.map((card) => {
    //         // @ts-ignore
    //         let cardComponent = factories[card.type](card);

    //         console.log(card)

    //         return (
    //             <div key={card.id}>
    //                 {cardComponent}
    //             </div>
    //         )
    //     })
    // }, [metrics, cpuInfo]);

    // const layouts = useMemo(() => {
    //     return cardTemplates.map((card) => {
    //         return card.layout;
    //     })
    // }, [cardTemplates]);

    return (
        <Drawer>
            <DrawerTrigger>
                <Button variant="outline" size="icon">
                    <Plus />
                </Button>
            </DrawerTrigger>
            <DrawerContent>
                <DrawerHeader className="flex justify-between items-center">
                    <DrawerTitle>{t("new")}</DrawerTitle>
                    <DrawerClose>
                        <Button variant="outline" size="icon"><Minimize2 /></Button>
                    </DrawerClose>
                </DrawerHeader>
                {/* <div className="w-full">
                    <ReactGridLayout className="layout mx-auto gap-8"
                        cols={12}
                        layout={layouts}
                        rowHeight={60}
                        compactType="vertical"
                        preventCollision={false}
                        draggableHandle=".drag-handle"
                        width={1920}
                    >
                        {metrics && cpuInfo && cards}
                    </ReactGridLayout>
                </div> */}
            </DrawerContent>
        </Drawer>
    )
}