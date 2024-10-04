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

// import RGL, { WidthProvider } from "react-grid-layout";

// const ReactGridLayout = WidthProvider(RGL);

import dynamic from "next/dynamic";

const ReactGridLayout = dynamic(async () => {
  const module = await import("react-grid-layout")
  const m = module.default;

  return m.WidthProvider(m);
}, { ssr: false });

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
      },
    ],
  );

  const [cardLayouts, setCardLayouts] = useLocalStorage<BaseCardLayout[]>(
    "cardLayouts",
    [
      {
        i: "hperf",
        x: 0,
        y: 0,
        w: 2,
        h: 2,
        resizable: true,
      },
    ],
  );

  const onLayoutChange = (props: BaseCardLayout[]) => {
    if (props.length == 0) return

    setCardLayouts(props);
  };

  const removeCard = (id: string) => {
    if (id === "hperf") {
      return;
    }

    return () => {
      setCardLayouts((prev) => {
        return prev?.filter((layout) => layout.i !== id);
      });

      setCardStorages((prev) => {
        return prev?.filter((card) => card.id !== id);
      });
    }
  }

  const cards = useMemo(() => {
    const factories = {
      hperf: (props: HperfCardProps) => <HperfCard />,
      lineplot: (props: LineplotCardProps) => (
        <LinePlotCard metrics={metrics || []} {...props} />
      ),
      barplot: (props: BarplotCardProps) => (
        <BarplotCard metrics={metrics || []} {...props} />
      ),
      radialplot: (props: RadialplotCardProps) => (
        <RadialPlotCard metrics={metrics || []} {...props} />
      ),
      cpuInfo: (props: CpuInfoCardProps) => (
        <CpuInfoCard cpuInfo={cpuInfo} type={props.infoType} />
      ),
      richLineplot: (props: RichLineplotCardsProps) => (
        <RichLineplotCard
          metrics={metrics || []}
          onMetricChange={(metricName) => {
            // @ts-ignore
            setCardStorages((prev) => {
              return prev?.map((card) => {
                if (card.type === "richLineplot" && card.id == props.id) {
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
              return prev?.map((card) => {
                if (card.type === "richLineplot" && card.id == props.id) {
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

      return <div key={card.id} onDoubleClick={
        removeCard(card.id)
      }>{cardComponent}</div>;
    });
  }, [cardStorages, cardLayouts, metrics, cpuInfo]);

  const createCard = ({ type, metricName }: { type: string; metricName: string }) => {
    const randomId = ((new Date()).getTime() * Math.random() * 100000).toFixed(0);
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
    };

    const newCardLayout = {
      x: 0, y: Infinity, i: randomId, h: 2, w: 2
    } as BaseCardLayout;

    if (cardType == "lineplot") {
      // @ts-ignore
      newCard["lineColorStyle"] = randomBrightColor();
      newCardLayout.h = 3;
      newCardLayout.w = 4;
      newCardLayout.minH = 3;
      newCardLayout.minW = 4;
      newCard["unit"] = metricName == "cpuUtilization" ? "%" : "";
    }

    if (cardType == "barplot") {
      // @ts-ignore
      newCard["barColorStyle"] = randomBrightColor();
      newCardLayout.h = 2;
      newCardLayout.w = 3;
      newCardLayout.minH = 2;
      newCardLayout.minW = 3;
    }

    if (cardType == "radialplot") {
      // @ts-ignore
      newCard["radialColorStyle"] = randomBrightColor();
      newCardLayout.h = 4;
      newCardLayout.w = 3;
      newCardLayout.minH = 4;
      newCardLayout.minW = 3;
    }

    if (cardType == "radialplot" && metricName == "frequency") {
      // @ts-ignore
      newCard["valueFormatter"] = formatFrequency;
    }

    if (cardType == "cpuInfo") {
      newCardLayout.h = 4;
      newCardLayout.w = 3;
      newCardLayout.minH = 2;
      newCardLayout.minW = 3;
      // @ts-ignore
      newCard["infoType"] = metricName;
    }

    if (type === "richLineplot") {
      newCardLayout.w = 12;
      newCardLayout.h = 6;
      newCardLayout.minH = 6;
      newCardLayout.minW = 12;
      // @ts-ignore
      newCard["tableExpanded"] = false;
    }

    setCardLayouts((prev) => {
      if (prev) {
        return prev.concat(newCardLayout);
      } else {
        return [newCardLayout];
      }
    });

    // @ts-ignore
    setCardStorages((prev) => {
      if (prev) {
        return [...prev, newCard];
      } else {
        return [newCard];
      }
    });
  }

  return (
    <ContextMenu>
      <ContextMenuTrigger>
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
        <div className="p-8 w-full h-screen flex-1">
          <ReactGridLayout
            className="layout mx-auto gap-8"
            cols={12}
            layout={cardLayouts}
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