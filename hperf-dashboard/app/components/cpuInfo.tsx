import { useTranslations } from 'next-intl';

import { CpuInfo } from 'api/cpuInfo';
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function CpuInfoCard({ cpuInfo }: { cpuInfo: CpuInfo }) {
    const t = useTranslations("cpuInfo");

    return (
        <Card>
            <CardHeader>
                <CardTitle>{t('cpuInfo')}</CardTitle>
            </CardHeader>
            <CardContent>
                <CardDescription>
                    <ul className='*:py-1'>
                        <li>{t('architecture')}: {cpuInfo.architecture}</li>
                        <li>{t('vendorId')}: {cpuInfo.vendorId}</li>
                        <li>{t('modelName')}: {cpuInfo.modelName}</li>
                        <li>{t('cores')}: {cpuInfo.coresPerSocket}</li>
                        <li>{t('threads')}: {cpuInfo.threadsPerCore}</li>
                        <li>{t('maxMHz')}: {cpuInfo.maxMHz}</li>
                        <li>{t('minMHz')}: {cpuInfo.minMHz}</li>
                        <li>{t("cache.l1i")}: {cpuInfo.cache.l1i}</li>
                        <li>{t("cache.l1d")}: {cpuInfo.cache.l1d}</li>
                        <li>{t("cache.l2")}: {cpuInfo.cache.l2}</li>
                        <li>{t("cache.l3")}: {cpuInfo.cache.l3}</li>
                    </ul>
                </CardDescription>
            </CardContent>
            <CardFooter>
                <Button>{t('viewMore')}</Button>
            </CardFooter>
        </Card>
    );
}