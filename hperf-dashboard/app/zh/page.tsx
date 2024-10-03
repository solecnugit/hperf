"use client";

export const dynamic = "force-dynamic"

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

import { NumericFields, streamingMetricsJSON, TimeSeriesData } from "@/api/metrics";
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
import { RichLineplotCard } from "../components/cards/richLineplot";
import useLocalStorage from "./storage";
import {
  BarplotCardProps,
  BaseCardLayout,
  BaseCardProps,
  CardProps,
  CardType,
  CpuInfoCardProps,
  HperfCardProps,
  LineplotCardProps,
  PlotCardProps,
  RadialplotCardProps,
  RichLineplotCardsProps,
} from "../components/cards/types";
import { ContextMenu, ContextMenuItem } from "@/components/ui/context-menu";
import {
  ContextMenuContent,
  ContextMenuTrigger,
} from "@radix-ui/react-context-menu";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import NewCardDialog from "../components/cards/dialog";
import { unstable_setRequestLocale } from 'next-intl/server';

const ReactGridLayout = WidthProvider(RGL);

export default function Home() {
  const t = useTranslations("cards");

  const [metrics, setMetrics] = useState<TimeSeriesData[] | null>(null);
  const [cpuInfo, setCpuInfo] = useState<CpuInfo | null>(null);
  const [isNewCardDialogOpen, setNewCardDialogOpen] = useState(false);

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

  const [cardStorages, setCardStorages] = useLocalStorage<CardProps[]>(
    "cardStorages",
    [
      {
        type: "hperf",
        id: "hperf",
        layout: { i: "hperf", x: 0, y: Infinity, w: 2, h: 2 },
      },
    ],
  );

  const layouts = useMemo(() => {
    return cardStorages.map((card) => {
      return card.layout;
    });
  }, [cardStorages]);

  const onLayoutChange = (props: BaseCardLayout[]) => {
    if (props.length == 0) return

    setCardStorages((prev) => {
      return prev.map((card) => {
        const layout = props.find((prop) => prop.i === card.layout.i);

        if (layout) {
          return {
            ...card,
            layout: {
              ...card.layout,
              ...layout,
            }
          }
        }

        return card;
      });
    });
  };

  const removeCard = (id: string) => {
    if (id === "hperf") {
      return;
    }

    return () => {
      setCardStorages((prev) => {
        return prev.filter((card) => card.layout.i !== id);
      });
    }
  }

  const cards = useMemo(() => {
    if (!metrics || !cpuInfo) {
      return null;
    }

    const factories = {
      hperf: (props: HperfCardProps) => <HperfCard />,
      lineplot: (props: LineplotCardProps) => (
        <LinePlotCard metrics={metrics} {...props} />
      ),
      barplot: (props: BarplotCardProps) => (
        <BarplotCard metrics={metrics} {...props} />
      ),
      radialplot: (props: RadialplotCardProps) => (
        <RadialPlotCard metrics={metrics} {...props} />
      ),
      cpuInfo: (props: CpuInfoCardProps) => (
        <CpuInfoCard cpuInfo={cpuInfo} type={props.infoType} />
      ),
      richLineplot: (props: RichLineplotCardsProps) => (
        <RichLineplotCard
          metrics={metrics}
          onMetricChange={(metricName) => {
            // @ts-ignore
            setCardStorages((prev) => {
              return prev.map((card) => {
                if (card.type === "richLineplot" && card.layout.i == props.layout.i) {
                  return {
                    ...card,
                    metricName,
                  };
                }

                return card;
              });
            });
          }}
          onTableStateChange={(state) => {
            setCardStorages((prev) => {
              return prev.map((card) => {
                if (card.type === "richLineplot" && card.layout.i == props.layout.i) {
                  return {
                    ...card,
                    tableExpanded: state,
                  };
                }

                return card;
              });
            });
          }}
          {...props}
        />
      ),
    };

    return cardStorages.map((card) => {
      // @ts-ignore
      const cardComponent = factories[card.type](card);

      debugger

      return <div key={card.layout.i} onDoubleClick={
        removeCard(card.layout.i)
      }>{cardComponent}</div>;
    });
  }, [cardStorages, metrics, cpuInfo]);

  const createCard = ({ type, metricName }: { type: string; metricName: string }) => {
    const randomId = ((new Date()).getTime() * Math.random()).toString(16);
    const cardType = type as CardType;

    const randomBrightColor = () => {
      const seed = metricName.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
      const hue = seed % 360;
      return `hsl(${hue}, 70%, 50%)`;
    }

    const newCard: PlotCardProps = {
      type: cardType,
      metricName: metricName as NumericFields,
      id: randomId,
      unit: "",
      layout: {
        i: randomId,
        x: 0,
        y: Infinity,
        w: 2,
        h: 2,
        resizable: true,
      },
    };

    if (cardType == "lineplot") {
      // @ts-ignore
      newCard["lineColorStyle"] = randomBrightColor();
      newCard["layout"].h = 3;
      newCard["layout"].w = 4;
      newCard["unit"] = metricName == "cpuUtilization" ? "%" : "";
    }

    if (cardType == "barplot") {
      // @ts-ignore
      newCard["barColorStyle"] = randomBrightColor();
      newCard["layout"].h = 2;
      newCard["layout"].w = 3;
    }

    if (cardType == "radialplot") {
      // @ts-ignore
      newCard["radialColorStyle"] = randomBrightColor();
      newCard["layout"].h = 4;
      newCard["layout"].w = 3;
    }

    if (cardType == "radialplot" && metricName == "frequency") {
      // @ts-ignore
      newCard["valueFormatter"] = formatFrequency;
    }

    if (cardType == "cpuInfo") {
      newCard["layout"].h = 4;
      newCard["layout"].w = 3;
      // @ts-ignore
      newCard["infoType"] = metricName;
    }

    if (type === "richLineplot") {
      newCard["layout"].w = 12;
      newCard["layout"].h = 6;
      // @ts-ignore
      newCard["tableExpanded"] = false;
    }

    // @ts-ignore
    setCardStorages((prev) => {
      if (prev) {
        return [...prev, newCard];
      }
    });
  }

  return (
    <ContextMenu>
      <ContextMenuTrigger>
        <div className="p-8 w-full h-screen">
          <NewCardDialog
            onSubmit={(data) => {
              createCard(data)
              setNewCardDialogOpen(false);
            }}
            onCancel={() => {
              setNewCardDialogOpen(false);
            }}
            isOpen={isNewCardDialogOpen}
          ></NewCardDialog>
          <ReactGridLayout
            className="layout mx-auto gap-8"
            cols={12}
            layout={layouts}
            rowHeight={60}
            compactType="vertical"
            preventCollision={false}
            draggableHandle=".drag-handle"
            width={1920}
            onLayoutChange={onLayoutChange}
          >
            {cards}
          </ReactGridLayout>
        </div>
      </ContextMenuTrigger>
      <ContextMenuContent>
        <ContextMenuItem>
          <Button variant="outline" className="flex items-center" onClick={
            () => {
              setNewCardDialogOpen(true);
            }
          }>
            <Plus /> <span className="pl-1 text-sm">{t("new")}</span>
          </Button>
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
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
