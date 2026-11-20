<?php

namespace Tests\Feature;

use App\Invoices\InvoiceDocumentReader;
use App\Invoices\Readers\EnelInvoiceReader;
use Illuminate\Support\Facades\Storage;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\TestCase;

class ProvidedInvoiceDocumentsTest extends TestCase
{
    public static function documents(): array
    {
        return [
            ['1_Fatura - Janeiro_26.pdf', '2026-01', '15737.88', '40.488', '51.072', '21.85092', '200.87', '44.83'],
            ['Code_Generated_Image.png', '2026-01', '15737.88', '40.488', '51.072', '21.85092', '200.87', '44.83'],
            ['fatura-Dezembro_25-MTE0015497.pdf', '2025-12', '13174.31', '31.752', '41.496', '22.07345', '164.87', '44.00'],
        ];
    }

    #[DataProvider('documents')]
    public function test_provided_native_documents_match_the_bill(string $name, string $month, string $total, string $peak, string $offPeak, string $price, string $icms, string $pis): void
    {
        $path = base_path('../docs/'.$name);
        if (! is_file($path)) {
            $this->markTestSkipped('Documento local privado não versionado.');
        }
        Storage::fake('invoice_temp');
        $invoice = app(InvoiceDocumentReader::class)->read(file_get_contents($path), new EnelInvoiceReader);
        $this->assertSame($month, $invoice->referenceMonth);
        $this->assertSame('MTE0015497', $invoice->consumerUnit);
        $this->assertSame($total, $invoice->totalPaid);
        $this->assertSame('A4', $invoice->subgroup);
        $this->assertSame('green', $invoice->tariffModality);
        $items = collect($invoice->items);
        $this->assertSame('57.000', $items->firstWhere('itemType', 'contracted_demand')->quantity);
        $this->assertSame($peak, $items->first(fn ($item) => $item->itemType === 'metered_demand' && $item->timeSlot === 'peak')->quantity);
        $this->assertSame($offPeak, $items->first(fn ($item) => $item->itemType === 'metered_demand' && $item->timeSlot === 'off_peak')->quantity);
        $demand = $items->firstWhere('itemType', 'measured_demand');
        $this->assertSame($offPeak, $demand->quantity);
        $this->assertSame($price, $demand->unitPriceTaxed);
        $this->assertSame('17.04000', $demand->tariffRate);
        $this->assertSame($icms, $demand->icmsAmount);
        $this->assertSame($pis, $demand->pisCofinsAmount);

        $this->assertSame($total, collect($invoice->items)->reduce(fn ($sum, $item) => bcadd($sum, $item->amount, 2), '0.00'));
        $this->assertNotContains('invoice_billing_total_mismatch', $invoice->warnings);
        if ($name === 'Code_Generated_Image.png' && is_file(base_path('../docs/1_Fatura - Janeiro_26.pdf'))) {
            $native = app(InvoiceDocumentReader::class)->read(file_get_contents(base_path('../docs/1_Fatura - Janeiro_26.pdf')), new EnelInvoiceReader);
            $values = static function ($item): array {
                $data = (array) $item;
                unset($data['sourceLabel']);

                return $data;
            };
            $this->assertEquals(array_map($values, $native->items), array_map($values, $invoice->items));
        }

        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
    }
}
