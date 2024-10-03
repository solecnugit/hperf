import { useTranslations } from "next-intl";

import { CpuInfo } from "api/cpuInfo";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CPUInfoType } from "./types";

function infoForType(cpuInfo: CpuInfo, type: CPUInfoType) {
  const t = useTranslations("cpuInfo");

  switch (type) {
    case "model":
      return (
        <ul className="leading-8">
          <li>
            {t("architecture")}:{cpuInfo.architecture}
          </li>
          <li>
            {t("modelName")}:{cpuInfo.modelName}
          </li>
          <li>
            {t("cpus")}:{cpuInfo.cpus}
          </li>
          <li>
            {t("cores")}:{cpuInfo.coresPerSocket}
          </li>
          <li>
            {t("threads")}:{cpuInfo.threadsPerCore}
          </li>
        </ul>
      );
    case "frequency":
      return (
        <ul className="leading-8">
          <li>
            {t("minMHz")}:{cpuInfo.minMHz}
          </li>
          <li>
            {t("maxMHz")}:{cpuInfo.maxMHz}
          </li>
        </ul>
      );
    case "cache":
      return (
        <ul className="leading-8">
          <li>
            {t("cache.l1i")}:{cpuInfo.cache.l1i}
          </li>
          <li>
            {t("cache.l1d")}:{cpuInfo.cache.l1d}
          </li>
          <li>
            {t("cache.l2")}:{cpuInfo.cache.l2}
          </li>
          <li>
            {t("cache.l3")}:{cpuInfo.cache.l3}
          </li>
        </ul>
      );
  }
}

export default function CpuInfoCard({
  cpuInfo,
  type,
}: {
  cpuInfo: CpuInfo;
  type: CPUInfoType;
}) {
  const t = useTranslations("cpuInfo");

  return (
    <Card className="w-full h-full px-2 pt-2 select-none">
      <div className="px-4 drag-handle w-full h-[6px] bg-primary rounded-md opacity-0 hover:opacity-5 transition-all "></div>
      <CardHeader className="pt-2 pb-2">
        <CardTitle>{t("cpuInfo")}</CardTitle>
      </CardHeader>
      <CardContent>
        <CardDescription className="text-md">
          {infoForType(cpuInfo, type)}
        </CardDescription>
      </CardContent>
    </Card>
  );
}
