import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import CardDrawer from "./drawer";
import { TimeSeriesData } from "@/api/metrics";
import { CpuInfo } from "os";


export default function HperfCard({
  metrics,
  cpuInfo
}: {
  metrics: TimeSeriesData[] | null;
  cpuInfo: CpuInfo | null;
}) {
  return (
    <Card className="flex flex-col items-center justify-center w-full h-full p-4 select-none">
      <CardHeader className="p-4 drag-handle">
        <CardTitle className="text-2xl uppercase tracking-tight">
          Hperf
        </CardTitle>
      </CardHeader>
      <CardContent>
        <CardDrawer metrics={metrics} cpuInfo={cpuInfo}></CardDrawer>
      </CardContent>
    </Card>
  );
}
