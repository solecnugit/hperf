import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import NewCardDialog from "./dialog";
import { TimeSeriesData } from "@/api/metrics";
import { CpuInfo } from "os";

export default function HperfCard() {
  return (
    <Card className="flex flex-col items-center justify-center w-full h-full p-4">
      <CardHeader className="p-4 drag-handle">
        <CardTitle className="text-2xl uppercase tracking-tight">
          Hperf
        </CardTitle>
      </CardHeader>
    </Card>
  );
}
