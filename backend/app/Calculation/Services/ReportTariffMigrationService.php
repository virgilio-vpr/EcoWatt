<?php

namespace App\Calculation\Services;

use App\Calculation\Data\DemandMonthData;
use App\Calculation\Data\ExtractedInvoiceData;
use App\Calculation\Data\IdleDemandRatioResolution;
use App\Calculation\Data\TariffMigrationMonthData;
use App\Calculation\Data\TariffMigrationResult;
use App\Models\Simulation;

final class ReportTariffMigrationService
{
    public function __construct(
        private readonly RegulatoryParameterService $parameters,
        private readonly TariffCalibrationService $calibration,
        private readonly TariffMigrationService $migration,
    ) {}

    /** @param list<ExtractedInvoiceData> $invoices
     * @param  list<DemandMonthData>  $months
     */
    public function compare(Simulation $simulation, array $invoices, array $months, IdleDemandRatioResolution $ratios): TariffMigrationResult
    {
        $unavailable = new TariffMigrationResult(false, null, null, null, null, null, [TariffMigrationService::MIGRATION_UNAVAILABLE_WARNING]);
        if ($invoices === [] || count($invoices) !== count($months)) {
            return $unavailable;
        }
        $latest = $invoices[array_key_last($invoices)];
        $distributorId = $simulation->user?->profile?->distributor_id;
        $minimum = $this->parameters->resolve('minimum_contracted_demand', $latest->referenceMonth.'-01');
        if (! in_array($latest->tariffModality, ['blue', 'green'], true) || $distributorId === null || $minimum === null
            || bccomp($minimum->value, '0', 5) <= 0 || bccomp($minimum->value, '1000000', 5) > 0
            || bccomp($minimum->value, bcadd($minimum->value, '0', 0), 5) !== 0) {
            return $unavailable;
        }
        $min = (int) $minimum->value;
        $maximum = $min;
        $migrationMonths = [];
        $referenceFactor = $this->calibration->calculateFactor($latest)->factor;
        foreach ($invoices as $index => $invoice) {
            if ($invoice->tariffModality !== $latest->tariffModality || $invoice->subgroup !== $latest->subgroup) {
                return $unavailable;
            }
            $month = $months[$index];
            $measured = $month->measuredDemandByTimeSlot;
            $peak = $month->meteredDemandByTimeSlot['peak'] ?? $measured['peak'] ?? null;
            $offPeak = $month->meteredDemandByTimeSlot['off_peak'] ?? $measured['off_peak'] ?? $measured['unique'] ?? null;
            $peakRate = $month->normalDemandItemsByTimeSlot['peak']->unitPriceTaxed ?? null;
            $offPeakRate = $month->normalDemandItemsByTimeSlot['off_peak']->unitPriceTaxed ?? null;
            $peakRatio = $ratios->forMonthAndTimeSlot($invoice->referenceMonth, 'peak')?->ratio;
            $offPeakRatio = $ratios->forMonthAndTimeSlot($invoice->referenceMonth, 'off_peak')?->ratio;
            $uniqueRatio = $ratios->forMonthAndTimeSlot($invoice->referenceMonth, 'unique')?->ratio;
            if ($invoice->tariffModality === 'green') {
                $peakRatio = $uniqueRatio;
                $offPeakRatio = $uniqueRatio;
            }
            if ($peak === null || $offPeak === null
                || $peakRatio === null || $offPeakRatio === null
                || bccomp($peak, '0', 3) < 0 || bccomp($offPeak, '0', 3) < 0
                || bccomp($peak, '1000000', 3) > 0 || bccomp($offPeak, '1000000', 3) > 0) {
                return $unavailable;
            }
            $single = $offPeak;
            $maximum = max($maximum, (int) bcadd($peak, '0.999', 0), (int) bcadd($offPeak, '0.999', 0));
            $energy = [];
            $consumption = [];
            foreach ($invoice->items as $item) {
                if ($item->itemType !== 'active_consumption' || ! in_array($item->tariffComponent, ['energy_te', 'energy_tusd'], true)
                    || ! in_array($item->timeSlot, ['peak', 'off_peak'], true) || $item->quantity === null) {
                    continue;
                }
                if (isset($consumption[$item->timeSlot]) && bccomp($consumption[$item->timeSlot], $item->quantity, 3) !== 0) {
                    return $unavailable;
                }
                $consumption[$item->timeSlot] = $item->quantity;
                $energy[$item->tariffComponent][$item->timeSlot] = $item;
            }
            $migrationMonths[] = new TariffMigrationMonthData(
                $invoice->referenceMonth,
                ['blue' => ['peak' => $peak, 'off_peak' => $offPeak], 'green' => ['unique' => $single]],
                ['blue' => ['peak' => $peakRatio, 'off_peak' => $offPeakRatio], 'green' => ['unique' => $offPeakRatio]],
                $invoice->tariffModality === 'green'
                    ? ['unique' => $month->normalDemandItemsByTimeSlot['unique']->unitPriceTaxed ?? null]
                    : ['peak' => $peakRate, 'off_peak' => $offPeakRate],
                $consumption,
                $energy,
                $referenceFactor,
            );
        }

        return $this->migration->compare($distributorId, $latest->subgroup, $latest->tariffModality, $migrationMonths, $min, $maximum, true, today()->toDateString());
    }
}
