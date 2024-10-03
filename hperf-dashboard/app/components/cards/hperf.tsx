import { Card, CardHeader, CardTitle } from "@/components/ui/card";

export default function HperfCard() {
    return (
        <Card
            className="flex flex-col items-center justify-center w-full h-full p-4 select-none"
        >
            <CardHeader className="p-4 drag-handle">
                <CardTitle className="text-2xl uppercase tracking-tight">Hperf</CardTitle>
            </CardHeader>
        </Card>
    )
}