"use client";

import { Button } from "@/components/ui/button";
import {
    Drawer,
    DrawerClose,
    DrawerContent,
    DrawerDescription,
    DrawerFooter,
    DrawerHeader,
    DrawerTitle,
    DrawerTrigger,
} from "@/components/ui/drawer";
import { Minimize2, Plus } from "lucide-react";
import { useTranslations } from "next-intl";

import RGL, { WidthProvider } from "react-grid-layout";
import {
    availableCards,
    BarplotCardProps,
    CpuInfoCardProps,
    HperfCardProps,
    LineplotCardProps,
    RadialplotCardProps,
    RichLineplotCardsProps,
} from "./types";
import { numericFields, TimeSeriesData } from "@/api/metrics";
import { CpuInfo } from "os";
import { useEffect, useMemo, useState } from "react";
import BarplotCard from "./barplot";
import CpuInfoCard from "./cpuInfo";
import HperfCard from "./hperf";
import LinePlotCard from "./lineplot";
import RadialPlotCard from "./radialplot";
import { RichLineplotCard } from "./richLineplot";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
} from "@/components/ui/form";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogHeader,
    DialogOverlay,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";

const ReactGridLayout = WidthProvider(RGL);

const formSchema = z.object({
    type: z.string({ required_error: "Type is required" }),
    metricName: z.string({ required_error: "Metric name is required" }),
});

function CardForm({
    onSubmit,
}: {
    onSubmit: (data: z.infer<typeof formSchema>) => void;
}) {
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
    });

    const t = useTranslations("cards");
    const mt = useTranslations("metrics");
    const availableCardTypes = Object.keys(availableCards);

    const [selectedType, setSelectedType] = useState<string | null>(null);

    const metricNames = useMemo(() => {
        if (selectedType == null) {
            return [];
        }

        if (selectedType == "cpuInfo") {
            return ["model", "frequency", "cache"];
        }

        return numericFields;
    }, [selectedType]);

    return (
        <Form {...form}>
            <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="flex flex-col gap-4"
            >
                <FormField
                    control={form.control}
                    name="type"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>{t("type")}</FormLabel>
                            <Select
                                onValueChange={(value) => {
                                    field.onChange(value);
                                    setSelectedType(value);
                                }}
                                value={field.value}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {availableCardTypes.map((type) => (
                                        <SelectItem key={type} value={type}>
                                            {t(type)}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="metricName"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>{t("metricName")}</FormLabel>
                            <Select onValueChange={field.onChange} value={field.value}>
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {metricNames.map((metricName) => (
                                        <SelectItem key={metricName} value={metricName}>
                                            {mt(metricName)}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </FormItem>
                    )}
                />
                <Button type="submit">{t("create")}</Button>
            </form>
        </Form>
    );
}

export default function NewCardDialog({
    onSubmit,
    onCancel,
    isOpen,
}: {
    onSubmit: (data: z.infer<typeof formSchema>) => void;
    onCancel: () => void;
    isOpen: boolean;
}) {
    const t = useTranslations("cards");

    function onOpenChange(open: boolean) {
        if (!open) {
            onCancel();
        }
    }

    return (
        <Dialog open={isOpen} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader className="flex justify-between items-center">
                    <DialogTitle>{t("new")}</DialogTitle>
                    <DialogClose>
                        <Button variant="outline" size="icon">
                            <Minimize2 />
                        </Button>
                    </DialogClose>
                </DialogHeader>
                <DialogContent>
                    <CardForm onSubmit={onSubmit}></CardForm>
                </DialogContent>
            </DialogContent>
        </Dialog>
    );
}
