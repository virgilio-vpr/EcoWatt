<?php

namespace App\Invoices;

use App\Calculation\Data\ExtractedInvoiceData;
use App\Calculation\Data\ExtractedInvoiceItemData;
use App\Invoices\Ocr\InvoiceOcr;
use App\Invoices\Pdf\TemporaryPdfTextExtractor;
use App\Invoices\Readers\InvoiceReader;
use App\Invoices\Readers\OcrInvoiceReader;
use App\Invoices\Validation\InvoiceExtractionValidator;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use Illuminate\Validation\ValidationException;
use InvalidArgumentException;
use Throwable;

final class InvoiceDocumentReader
{
    public function __construct(
        private readonly TemporaryPdfTextExtractor $native,
        private readonly InvoiceOcr $ocr,
        private readonly InvoiceExtractionValidator $validator,
    ) {}

    public function read(string $contents, InvoiceReader $reader): ExtractedInvoiceData
    {
        $native = null;
        $pdf = (new \finfo(FILEINFO_MIME_TYPE))->buffer($contents) === 'application/pdf';
        if ($pdf) {
            try {
                $native = $reader->read($this->native->extract($contents));
                $this->validator->validate([$native]);
                if ($this->sufficient($native)) {
                    Log::info('invoice_extraction', ['method' => 'native']);

                    return $native;
                }
            } catch (InvalidArgumentException|ValidationException) {
                // Keep a parsed native candidate for comparison, even if a table is invalid.
            } catch (Throwable) {
                // A scanned PDF may have no extractable text layer.
            }
        }
        $disk = Storage::disk(TemporaryPdfTextExtractor::DISK);
        $path = Str::uuid().($pdf ? '.pdf' : '.image');
        try {
            $disk->put($path, $contents);
            try {
                $ocrText = $this->ocr->extract($disk->path($path));
                $ocr = $reader instanceof OcrInvoiceReader ? $reader->readOcr($ocrText) : $reader->read($ocrText);
            } catch (InvalidArgumentException|ValidationException $exception) {
                if ($native === null || ! collect($native->items)->contains(fn ($item) => $item->itemType === 'measured_demand')) {
                    throw $exception;
                }
                Log::info('invoice_extraction', ['method' => 'native', 'ocr' => 'unavailable_or_unreadable']);

                return $this->copy($native, $native->items, array_values(array_unique([...$native->warnings, 'ocr_support_unavailable'])));
            }
            $result = $native === null ? $ocr : $this->merge($native, $ocr);
            $sum = '0.00';
            foreach ($result->items as $item) {
                $sum = bcadd($sum, $item->amount, 2);
            }
            if (! $this->totalMatches($sum, $result->totalPaid)) {
                $result = $this->copy($result, $result->items, array_values(array_unique([...$result->warnings, 'invoice_billing_total_mismatch'])));
            }
            $this->validator->validate([$result]);
            if ($result->items === [] || ! collect($result->items)->contains(fn ($item) => $item->itemType === 'measured_demand')) {
                throw new InvalidArgumentException('O quadro de faturamento está incompleto. Envie uma cópia mais nítida para revisão.');
            }
            Log::info('invoice_extraction', ['method' => $native === null ? 'ocr' : 'hybrid']);

            return $result;
        } finally {
            $disk->delete($path);
        }
    }

    private function sufficient(ExtractedInvoiceData $data): bool
    {
        $slots = collect($data->items)->where('itemType', 'metered_demand')->pluck('timeSlot')->all();

        return ! in_array('invoice_billing_total_mismatch', $data->warnings, true)
            && collect($data->items)->contains(fn ($item) => $item->itemType === 'measured_demand')
            && array_diff(['peak', 'off_peak'], $slots) === [];
    }

    private function merge(ExtractedInvoiceData $native, ExtractedInvoiceData $ocr): ExtractedInvoiceData
    {
        foreach (['referenceMonth', 'consumerUnit', 'subgroup', 'tariffModality', 'totalPaid'] as $field) {
            if ($native->$field !== $ocr->$field) {
                throw new InvalidArgumentException('Texto nativo e OCR divergem nos campos da fatura. Revise o documento e envie outra cópia.');
            }
        }
        $items = $native->items;
        $groups = [];
        foreach ($items as $item) {
            $groups[$this->key($item)][] = $item;
        }
        $seen = [];
        foreach ($ocr->items as $item) {
            $key = $this->key($item);
            $index = $seen[$key] ?? 0;
            $seen[$key] = $index + 1;
            if (isset($groups[$key][$index])) {
                if ((array) $groups[$key][$index] !== (array) $item) {
                    throw new InvalidArgumentException('Texto nativo e OCR divergem em um lançamento. Revise a fatura; nenhum valor foi ajustado.');
                }
            } else {
                $items[] = $item;
            }
        }
        $warnings = array_values(array_unique([...$native->warnings, ...$ocr->warnings]));
        $sum = '0.00';
        foreach ($items as $item) {
            $sum = bcadd($sum, $item->amount, 2);
        }
        if ($this->totalMatches($sum, $native->totalPaid)) {
            $warnings = array_values(array_diff($warnings, ['invoice_billing_total_mismatch']));
        }

        return $this->copy($native, $items, $warnings);
    }

    private function totalMatches(string $sum, string $total): bool
    {
        $difference = bcsub($sum, $total, 2);
        $absolute = bccomp($difference, '0', 2) < 0 ? bcsub('0', $difference, 2) : $difference;

        return bccomp($absolute, InvoiceExtractionValidator::TOTAL_TOLERANCE, 2) <= 0;
    }

    private function key(ExtractedInvoiceItemData $item): string
    {
        return implode('|', [$item->itemType, $item->tariffComponent, $item->timeSlot, $item->reactiveNature, $item->sourceLabel]);
    }

    /** @param list<ExtractedInvoiceItemData> $items
     * @param  list<string>  $warnings
     */
    private function copy(ExtractedInvoiceData $data, array $items, array $warnings): ExtractedInvoiceData
    {
        return ExtractedInvoiceData::fromArray([
            'reference_month' => $data->referenceMonth,
            'consumer_unit' => $data->consumerUnit,
            'subgroup' => $data->subgroup,
            'tariff_modality' => $data->tariffModality,
            'total_paid' => $data->totalPaid,
            'items' => array_map(fn ($item) => [
                'item_type' => $item->itemType, 'tariff_component' => $item->tariffComponent,
                'time_slot' => $item->timeSlot, 'reactive_nature' => $item->reactiveNature,
                'quantity' => $item->quantity, 'unit' => $item->unit, 'unit_price_taxed' => $item->unitPriceTaxed,
                'tariff_rate' => $item->tariffRate, 'amount' => $item->amount,
                'pis_cofins_amount' => $item->pisCofinsAmount, 'icms_base' => $item->icmsBase,
                'icms_rate' => $item->icmsRate, 'icms_amount' => $item->icmsAmount, 'source_label' => $item->sourceLabel,
            ], $items),
            'warnings' => $warnings,
        ]);
    }
}
