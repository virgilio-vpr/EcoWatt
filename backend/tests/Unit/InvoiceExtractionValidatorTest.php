<?php

namespace Tests\Unit;

use App\Calculation\Data\ExtractedInvoiceData;
use App\Invoices\Validation\InvoiceExtractionValidator;
use Illuminate\Validation\ValidationException;
use Tests\TestCase;

class InvoiceExtractionValidatorTest extends TestCase
{
    public function test_it_rejects_duplicate_reference_months_and_associates_the_error_with_the_second_file(): void
    {
        $validator = new InvoiceExtractionValidator;

        try {
            $validator->validate([$this->invoice('2025-08'), $this->invoice('2025-08')]);
            $this->fail('Duplicate reference months must be rejected.');
        } catch (ValidationException $exception) {
            $this->assertArrayHasKey('invoices.1.reference_month', $exception->errors());
        }
    }

    public function test_it_rejects_invoices_from_different_consumer_units(): void
    {
        $validator = new InvoiceExtractionValidator;

        try {
            $validator->validate([
                $this->invoice('2025-08', consumerUnit: 'UC-1'),
                $this->invoice('2025-09', consumerUnit: 'UC-2'),
            ]);
            $this->fail('Invoices from different consumer units must be rejected.');
        } catch (ValidationException $exception) {
            $this->assertArrayHasKey('invoices.1.consumer_unit', $exception->errors());
        }
    }

    public function test_it_accepts_quantity_price_difference_of_one_cent(): void
    {
        $item = $this->item(quantity: '1.000', price: '9.99000', amount: '10.00');

        $this->assertNull((new InvoiceExtractionValidator)->validate([$this->invoice('2025-08', items: [$item])]));
    }

    public function test_it_accepts_quantity_price_differences_up_to_five_reais_in_either_direction(): void
    {
        foreach (['95.00', '100.68', '105.00'] as $amount) {
            $invoice = $this->invoice('2025-01', items: [$this->item('1.000', '100.00000', $amount)]);
            $this->assertNull((new InvoiceExtractionValidator)->validate([$invoice]));
            $this->assertSame($amount, $invoice->items[0]->amount);
            $this->assertSame('100.00000', $invoice->items[0]->unitPriceTaxed);
        }
    }

    public function test_it_rejects_quantity_price_differences_above_five_reais_in_either_direction(): void
    {
        foreach (['94.99', '105.01'] as $amount) {
            try {
                (new InvoiceExtractionValidator)->validate([
                    $this->invoice('2025-01', items: [$this->item('1.000', '100.00000', $amount)]),
                ]);
                $this->fail('An amount mismatch above five reais must be rejected.');
            } catch (ValidationException $exception) {
                $this->assertArrayHasKey('invoices.0.items.0.amount', $exception->errors());
            }
        }
    }

    public function test_it_accepts_icms_difference_of_one_cent(): void
    {
        $item = $this->item(quantity: '1.000', price: '100.00000', amount: '100.00', icmsAmount: '17.99');

        $this->assertNull((new InvoiceExtractionValidator)->validate([$this->invoice('2025-08', items: [$item])]));
    }

    public function test_it_rejects_icms_difference_above_one_cent(): void
    {
        $item = $this->item(quantity: '1.000', price: '100.00000', amount: '100.00', icmsAmount: '17.98');

        try {
            (new InvoiceExtractionValidator)->validate([$this->invoice('2025-08', items: [$item])]);
            $this->fail('An ICMS mismatch above one cent must be rejected.');
        } catch (ValidationException $exception) {
            $this->assertArrayHasKey('invoices.0.items.0.icms_amount', $exception->errors());
        }
    }

    public function test_it_does_not_require_extracted_items_to_sum_to_the_total_paid(): void
    {
        $this->assertNull((new InvoiceExtractionValidator)->validate([
            $this->invoice('2025-08', items: [$this->item(quantity: '1.000', price: '1.00000', amount: '1.00')]),
        ]));
    }

    public function test_five_real_tolerance_preserves_printed_energy_quantities_prices_and_amounts(): void
    {
        foreach (['29995.00', '30005.00'] as $amount) {
            $item = array_replace($this->item('300000.000', '0.10000', $amount), ['icms_base' => '0.00', 'icms_rate' => '0.0000', 'icms_amount' => '0.00']);
            $invoice = $this->invoice('2025-08', items: [$item], total: $amount);
            $this->assertNull((new InvoiceExtractionValidator)->validate([$invoice]));
            $this->assertSame('0.10000', $invoice->items[0]->unitPriceTaxed);
            $this->assertSame($amount, $invoice->items[0]->amount);
        }
    }

    public function test_large_consumption_does_not_allow_differences_beyond_five_reais(): void
    {
        foreach ([['29994.99', '29994.99'], ['30005.01', '30005.01']] as [$amount, $total]) {
            $item = array_replace($this->item('300000.000', '0.10000', $amount), ['icms_base' => '0.00', 'icms_rate' => '0.0000', 'icms_amount' => '0.00']);
            try {
                (new InvoiceExtractionValidator)->validate([$this->invoice('2025-08', items: [$item], total: $total)]);
                $this->fail('Unexplained quantity/price differences must still be rejected.');
            } catch (ValidationException $exception) {
                $this->assertArrayHasKey('invoices.0.items.0.amount', $exception->errors());
            }
        }
    }

    public function test_informational_energy_prices_are_preserved_only_for_exactly_offsetting_pairs(): void
    {
        $charge = array_replace($this->item('100.000', '0.10000', '20.00'), ['item_type' => 'other_charge', 'tariff_component' => 'other', 'source_label' => 'ENERGIA ACL', 'icms_base' => '0.00', 'icms_rate' => '0.0000', 'icms_amount' => '0.00']);
        $deduction = array_replace($charge, ['source_label' => 'DEDUÇÃO ENERGIA ACL', 'amount' => '-20.00']);
        $invoice = $this->invoice('2025-08', items: [$charge, $deduction], total: '0.00');
        $this->assertNull((new InvoiceExtractionValidator)->validate([$invoice]));
        $this->assertSame('0.10000', $invoice->items[0]->unitPriceTaxed);
        $this->assertSame('20.00', $invoice->items[0]->amount);
        $this->assertSame('-20.00', $invoice->items[1]->amount);

        foreach ([[$charge], [$charge, $charge, $deduction], [$charge, array_replace($deduction, ['quantity' => '99.000'])], [$charge, array_replace($deduction, ['amount' => '-19.00'])]] as $items) {
            $sum = array_reduce($items, fn ($sum, $item) => bcadd($sum, $item['amount'], 2), '0.00');
            try {
                (new InvoiceExtractionValidator)->validate([$this->invoice('2025-08', items: $items, total: $sum)]);
                $this->fail('Unpaired energy entries must still be validated.');
            } catch (ValidationException $exception) {
                $this->assertNotEmpty(array_filter(array_keys($exception->errors()), static fn (string $field): bool => str_ends_with($field, '.amount')));
            }
        }
        try {
            (new InvoiceExtractionValidator)->validate([$this->invoice('2025-08', items: [$charge, $deduction], total: '5.01')]);
            $this->fail('Incomplete invoice totals must not enable the offset exception.');
        } catch (ValidationException $exception) {
            $this->assertArrayHasKey('invoices.0.items.0.amount', $exception->errors());
        }
    }

    public function test_amount_tolerance_does_not_relax_icms_validation(): void
    {
        $item = array_replace($this->item('300000.000', '0.10000', '30001.50'), ['icms_base' => '30001.50', 'icms_amount' => '5400.25']);
        try {
            (new InvoiceExtractionValidator)->validate([$this->invoice('2025-08', items: [$item], total: '30001.50')]);
            $this->fail('An ICMS difference above one cent must remain blocked.');
        } catch (ValidationException $exception) {
            $this->assertArrayHasKey('invoices.0.items.0.icms_amount', $exception->errors());
            $this->assertArrayNotHasKey('invoices.0.items.0.amount', $exception->errors());
        }
    }

    private function invoice(string $month, string $consumerUnit = 'UC-1', array $items = [], string $total = '98922.22'): ExtractedInvoiceData
    {
        return ExtractedInvoiceData::fromArray([
            'reference_month' => $month,
            'consumer_unit' => $consumerUnit,
            'subgroup' => 'A4',
            'tariff_modality' => 'blue',
            'total_paid' => $total,
            'items' => $items,
        ]);
    }

    private function item(string $quantity, string $price, string $amount, string $icmsAmount = '18.00'): array
    {
        return [
            'item_type' => 'active_consumption',
            'tariff_component' => 'energy_te',
            'time_slot' => 'peak',
            'reactive_nature' => 'not_applicable',
            'quantity' => $quantity,
            'unit' => 'kWh',
            'unit_price_taxed' => $price,
            'tariff_rate' => null,
            'amount' => $amount,
            'pis_cofins_amount' => '4.49',
            'icms_base' => '100.00',
            'icms_rate' => '0.1800',
            'icms_amount' => $icmsAmount,
        ];
    }
}
