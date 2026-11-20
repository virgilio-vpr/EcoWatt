<?php

namespace App\Calculation\Data;

final readonly class DemandMonthData
{
    /**
     * @param  array<string, string>  $contractedDemandByTimeSlot
     * @param  array<string, string>  $measuredDemandByTimeSlot
     * @param  array<string, ExtractedInvoiceItemData>  $normalDemandItemsByTimeSlot
     * @param  list<ExtractedInvoiceItemData>  $idleDemandItems
     * @param  array<string, string>  $meteredDemandByTimeSlot
     */
    public function __construct(
        public string $referenceMonth,
        public string $tariffPeriod,
        public array $contractedDemandByTimeSlot,
        public array $measuredDemandByTimeSlot,
        public array $normalDemandItemsByTimeSlot,
        public array $idleDemandItems,
        public array $meteredDemandByTimeSlot = [],
    ) {}

    public static function fromInvoice(ExtractedInvoiceData $invoice, string $tariffPeriod): self
    {
        $contracted = [];
        $measured = [];
        $normalItems = [];
        $idleItems = [];
        $metered = [];

        foreach ($invoice->items as $item) {
            if ($item->itemType === 'contracted_demand' && $item->quantity !== null) {
                $contracted[$item->timeSlot] = $item->quantity;
            }

            if ($item->itemType === 'measured_demand' && $item->quantity !== null) {
                $measured[$item->timeSlot] = $item->quantity;
                $normalItems[$item->timeSlot] = $item;
            }

            if ($item->itemType === 'idle_demand') {
                $idleItems[] = $item;
            }
            if ($item->itemType === 'metered_demand' && $item->quantity !== null) {
                $metered[$item->timeSlot] = $item->quantity;
            }
        }

        foreach (array_keys($contracted) as $slot) {
            $meterSlot = $slot === 'unique' ? 'off_peak' : $slot;
            if (isset($metered[$meterSlot])) {
                $measured[$slot] = $metered[$meterSlot];
            }
        }

        return new self(
            referenceMonth: $invoice->referenceMonth,
            tariffPeriod: $tariffPeriod,
            contractedDemandByTimeSlot: $contracted,
            measuredDemandByTimeSlot: $measured,
            normalDemandItemsByTimeSlot: $normalItems,
            idleDemandItems: $idleItems,
            meteredDemandByTimeSlot: $metered,
        );
    }
}
