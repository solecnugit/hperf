import { Card, CardHeader, CardTitle } from "@/components/ui/card";

export default function HperfCard() {
    return (
        <Card
            className="flex flex-col items-center justify-center max-w-xs col-span-2 row-span-1"
        >
            <CardHeader className="p-4">
                <CardTitle className="text-2xl uppercase tracking-tight">Hperf</CardTitle>
            </CardHeader>
        </Card>
    )
}