<?php

namespace Tests\Unit;

use App\Calculation\Data\DemandMonthData;
use App\Calculation\Data\ExtractedInvoiceItemData;
use App\Invoices\Readers\EnelInvoiceReader;
use App\Invoices\Validation\InvoiceExtractionValidator;
use Tests\TestCase;

class EnelInvoiceReaderTest extends TestCase
{
    public function test_discounted_unique_demand_preserves_the_printed_quantity_rates_and_taxes(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/enel-unique-demand-green.txt');
        $text = str_replace("DEMANDA\tKW", "DEMANDA ÚNICA C/ DESCONTO\tKW", $text);
        $invoice = (new EnelInvoiceReader)->read($text);
        $demand = $this->item($invoice->items, 'measured_demand', 'unique');

        $this->assertSame('DEMANDA ÚNICA C/ DESCONTO', $demand->sourceLabel);
        $this->assertSame('51.072', $demand->quantity);
        $this->assertSame('21.85092', $demand->unitPriceTaxed);
        $this->assertSame('17.04000', $demand->tariffRate);
        $this->assertSame('1115.97', $demand->amount);
        $this->assertSame('200.87', $demand->icmsAmount);
        $this->assertSame([], $invoice->warnings);
        $this->assertNull((new InvoiceExtractionValidator)->validate([$invoice]));
    }

    public function test_enel_adjustments_keep_charges_and_negative_compensations_in_the_billing_total(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/enel-unique-demand-green.txt');
        $rows = <<<'ROWS'
DIF.FATUR.ENCA - HOMOLOG. CCEE 0,000 0,00000 12,34 0,01 0,00 0% 0,00 0,00000
TX.ENTR.FAT.OUTRA_LOCAL. 9,53 0,01 0,00 0% 0,00
PENAL.DIC/DMIC/FIC/DICRI ADIC. -100,00 0,01 0,00 0% 0,00
REV FATURA JUROS MORA ART. 323 -20,00 0,01 0,00 0% 0,00
ROWS;
        $text = str_replace('Subtotal Faturamento', $rows."\nSubtotal Faturamento", $text);
        $text = str_replace('15.737,88', '15.639,75', $text);
        $text = str_replace(["Subtotal Faturamento\t14.712,45", "Subtotal Outros\t1.025,43"], ["Subtotal Faturamento\t14.724,79", "Subtotal Outros\t914,96"], $text);
        $invoice = (new EnelInvoiceReader)->read($text);
        $adjustments = collect($invoice->items)->where('itemType', 'other_charge')->keyBy('sourceLabel');

        $this->assertSame('12.34', $adjustments['DIF.FATUR.ENCA - HOMOLOG. CCEE']->amount);
        $this->assertSame('9.53', $adjustments['TX.ENTR.FAT.OUTRA_LOCAL.']->amount);
        $this->assertSame('-100.00', $adjustments['PENAL.DIC/DMIC/FIC/DICRI ADIC.']->amount);
        $this->assertSame('-20.00', $adjustments['REV FATURA JUROS MORA ART. 323']->amount);
        $sum = collect($invoice->items)->reduce(fn ($sum, $item) => bcadd($sum, $item->amount, 2), '0.00');
        $this->assertSame('15639.75', $invoice->totalPaid);
        $this->assertSame($invoice->totalPaid, $sum);
        $this->assertNotContains('invoice_billing_total_mismatch', $invoice->warnings);
        $this->assertNull((new InvoiceExtractionValidator)->validate([$invoice]));
    }

    public function test_zero_payable_invoice_preserves_the_printed_credit_balance_instead_of_inventing_a_total(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/enel-unique-demand-green.txt');
        $rows = "REV FATURA JUROS MORA ART. 323 -16.000,00 0,01 0,00 0% 0,00\nVALOR A SER CREDITADO 262,12\n";
        $text = str_replace('Subtotal Faturamento', $rows.'Subtotal Faturamento', $text);
        $text = str_replace('15.737,88', '0,00', $text);
        $text = str_replace("Subtotal Outros\t1.025,43", "Subtotal Outros\t-14.712,45", $text);
        $invoice = (new EnelInvoiceReader)->read($text);
        $balance = collect($invoice->items)->firstWhere('sourceLabel', 'VALOR A SER CREDITADO');

        $this->assertSame('0.00', $invoice->totalPaid);
        $this->assertSame('262.12', $balance->amount);
        $this->assertNull($balance->quantity);
        $this->assertSame('0.00', collect($invoice->items)->reduce(fn ($sum, $item) => bcadd($sum, $item->amount, 2), '0.00'));
        $this->assertNotContains('invoice_billing_total_mismatch', $invoice->warnings);
        $this->assertNull((new InvoiceExtractionValidator)->validate([$invoice]));
    }

    public function test_it_reads_green_invoices_with_an_alphanumeric_consumer_unit_and_unique_demand(): void
    {
        $invoice = (new EnelInvoiceReader)->read(file_get_contents(__DIR__.'/../Fixtures/enel-unique-demand-green.txt'));

        $this->assertSame('MTE0012345', $invoice->consumerUnit);
        $this->assertSame('2026-01', $invoice->referenceMonth);
        $this->assertSame('green', $invoice->tariffModality);
        $this->assertSame('15737.88', $invoice->totalPaid);
        $this->assertSame('57.000', $this->item($invoice->items, 'contracted_demand', 'unique')->quantity);
        $this->assertSame('51.072', $this->item($invoice->items, 'measured_demand', 'unique')->quantity);
        $this->assertSame('1115.97', $this->item($invoice->items, 'measured_demand', 'unique')->amount);
        $this->assertSame('5.928', $this->item($invoice->items, 'idle_demand', 'unique')->quantity);
        $this->assertSame('106.19', $this->item($invoice->items, 'idle_demand', 'unique')->amount);
        $this->assertSame('40.488', $this->item($invoice->items, 'metered_demand', 'peak')->quantity);
        $this->assertSame('51.072', $this->item($invoice->items, 'metered_demand', 'off_peak')->quantity);
        $month = DemandMonthData::fromInvoice($invoice, $invoice->referenceMonth);
        $this->assertSame(['unique' => '51.072'], $month->measuredDemandByTimeSlot);
        $this->assertSame(['peak' => '40.488', 'off_peak' => '51.072'], $month->meteredDemandByTimeSlot);
        $this->assertSame([], $invoice->warnings);
        $sum = '0.00';
        foreach ($invoice->items as $item) {
            $sum = bcadd($sum, $item->amount, 2);
        }
        $this->assertSame($invoice->totalPaid, $sum);
        $this->assertNull((new InvoiceExtractionValidator)->validate([$invoice]));
    }

    public function test_ocr_reference_month_can_follow_text_from_adjacent_header_columns(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/ocr/expected.txt');
        $text = str_replace('Mês/Ano: 01/2026', "MÊS/ANO\nEmpresa Exemplo\nRua Exemplo, 10     01/2026 [QR] NOTA FISCAL emissão 03/01/2026\nVENCIMENTO 04/02/2026", $text);
        $this->assertSame('2026-01', (new EnelInvoiceReader)->read($text)->referenceMonth);
    }

    public function test_ocr_reference_does_not_use_due_or_issue_dates_when_the_month_is_missing(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/ocr/expected.txt');
        $text = str_replace('Mês/Ano: 01/2026', "MES/ANO\nEmpresa Exemplo emissão 03 / 01 / 2026\nVENCIMENTO 04/02/2026", $text);
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('mês de referência');
        (new EnelInvoiceReader)->read($text);
    }

    public function test_ocr_reference_requires_review_if_two_months_follow_the_label(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/ocr/expected.txt');
        $text = str_replace('Mês/Ano: 01/2026', "MES/ANO\nEmpresa Exemplo 01/2026 02/2026\nVENCIMENTO", $text);
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('referências diferentes');
        (new EnelInvoiceReader)->read($text);
    }

    public function test_ocr_decimal_dots_preserve_digits_precision_taxes_and_negative_credits(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/ocr/expected.txt');
        $expected = (new EnelInvoiceReader)->read($text);
        $invoice = (new EnelInvoiceReader)->readOcr(str_replace(',', '.', $text));
        $this->assertEquals($expected, $invoice);
        $this->assertNull((new InvoiceExtractionValidator)->validate([$invoice]));
    }

    public function test_native_decimal_parsing_remains_strict_when_commas_are_missing(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/ocr/expected.txt');
        $this->expectException(\InvalidArgumentException::class);
        (new EnelInvoiceReader)->read(str_replace(',', '.', $text));
    }

    public function test_ocr_preserves_an_mte_followed_by_the_account_in_the_header(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/enel-unique-demand-green.txt');
        $text = str_replace("Número UC\nMTE0012345", "UC           TOTAL A PAGAR\nMTE0012345", $text);
        $this->assertSame('MTE0012345', (new EnelInvoiceReader)->readOcr($text)->consumerUnit);
    }

    public function test_mte_and_consumer_unit_labels_preserve_the_same_identifier_and_leading_zeroes(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/enel-unique-demand-green.txt');

        foreach (['MTE', 'Unidade consumidora', 'UC', 'Instalação'] as $label) {
            foreach (['0012345', 'MTE0012345'] as $identifier) {
                foreach ([": {$identifier}", "\n{$identifier}"] as $value) {
                    $invoice = (new EnelInvoiceReader)->read(str_replace("Número UC\nMTE0012345", $label.$value, $text));

                    $this->assertSame($identifier, $invoice->consumerUnit, $label.$value);
                    $this->assertNotContains('invoice_billing_total_mismatch', $invoice->warnings);
                }
            }
        }
    }

    public function test_it_reads_a_standalone_mte_in_the_header_when_the_consumer_unit_label_is_not_selectable(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/enel-unique-demand-green.txt');
        $text = str_replace("Número UC\nMTE0012345 / 200001234567 R$15.737,88", "MTE0012345\nR$15.737,88\n10005547", $text);

        $invoice = (new EnelInvoiceReader)->read($text);

        $this->assertSame('MTE0012345', $invoice->consumerUnit);
        $this->assertSame('green', $invoice->tariffModality);
        $this->assertSame('15737.88', $invoice->totalPaid);
        $this->assertNotContains('invoice_billing_total_mismatch', $invoice->warnings);
    }

    public function test_blue_demands_use_active_metering_and_ignore_capacitive_and_dmcr_readings(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/enel-reference-blue.txt');
        $text .= "\n1234567 DEMANDA PONTA 100 200 0,16800 221,760\n"
            ."1234567 DEMANDA F PONTA INDU 100 200 0,16800 269,641\n"
            ."1234567 DEMANDA F PONTA CAP 100 200 0,16800 900,000\n"
            ."1234567 DEM RTV DMCR PONTA 100 200 0,16800 999,000\n";

        $invoice = (new EnelInvoiceReader)->read($text);
        $month = DemandMonthData::fromInvoice($invoice, $invoice->referenceMonth);

        $this->assertSame(['peak' => '221.760', 'off_peak' => '269.641'], $month->meteredDemandByTimeSlot);
        $this->assertSame($month->meteredDemandByTimeSlot, $month->measuredDemandByTimeSlot);
        $this->assertSame('8383.25', $this->item($invoice->items, 'measured_demand', 'peak')->amount);
    }

    public function test_it_reads_discounted_demand_credits_and_all_billing_rows_without_losing_signs_or_precision(): void
    {
        $invoice = (new EnelInvoiceReader)->read(file_get_contents(__DIR__.'/../Fixtures/enel-discounted-text-blue.txt'));
        $this->assertSame('2026-08', $invoice->referenceMonth);
        $this->assertSame('42446.32', $invoice->totalPaid);
        $this->assertSame(['free_market_invoice'], $invoice->warnings);
        $this->assertCount(17, $invoice->items);
        $this->assertSame('252.000', $this->item($invoice->items, 'measured_demand', 'peak')->quantity);
        $idle = $this->item($invoice->items, 'idle_demand', 'off_peak');
        $this->assertSame('67.920', $idle->quantity);
        $this->assertSame('10.05771', $idle->unitPriceTaxed);
        $this->assertSame('9.52000', $idle->tariffRate);
        $credits = array_values(array_filter($invoice->items, static fn ($item): bool => $item->sourceLabel === 'BENEFÍCIO TARIFÁRIO LÍQUIDO'));
        $this->assertSame('-9410.65', $credits[0]->amount);
        $this->assertSame('-503.46', $credits[0]->pisCofinsAmount);
        $sum = '0.00';
        foreach ($invoice->items as $item) {
            $sum = bcadd($sum, $item->amount, 2);
        }
        $this->assertSame($invoice->totalPaid, $sum);
        $this->assertNull((new InvoiceExtractionValidator)->validate([$invoice]));
    }

    public function test_it_matches_idle_tariffs_by_order_when_the_reference_column_has_rounding_differences(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/enel-discounted-text-blue.txt');
        $text = str_replace(['0,009,52000', '0,0015,87500'], ['0,009,51000', '0,0015,87000'], $text);

        $invoice = (new EnelInvoiceReader)->read($text);

        $this->assertSame('10.05771', $this->item($invoice->items, 'idle_demand', 'off_peak')->unitPriceTaxed);
        $this->assertSame('16.77221', $this->item($invoice->items, 'idle_demand', 'peak')->unitPriceTaxed);
        $this->assertNotContains('idle_demand_post_matching_unresolved', $invoice->warnings);
    }

    public function test_it_includes_flag_charges_in_full_or_short_format_when_reconciling_the_invoice_total(): void
    {
        foreach ([
            'ADIC. BANDEIRA TARIFÁRIA FP 0,000 0,00000 100,00 0,00 0,00 0% 0,00 0,00000',
            'ADICIONAL DE BANDEIRA TARIFÁRIA FORA DE PONTA KWH 100,000 1,00000 100,00 0,00 0,00 0% 0,00 1,00000',
            'ADICIONAL BANDEIRA VERMELHA PATAMAR 2 PONTA 100,00 0,00 0,00 0% 0,00',
            'ADICIONAL BANDEIRA AMARELA 100,00 0,00 0,00 0% 0,00',
        ] as $flagLine) {
            $text = file_get_contents(__DIR__.'/../Fixtures/enel-discounted-text-blue.txt');
            $text = str_replace('COSIP -', $flagLine."\nCOSIP -", $text);
            $text = str_replace(['42.446,32', '50.626,45'], ['42.546,32', '50.726,45'], $text);

            $invoice = (new EnelInvoiceReader)->read($text);
            $flags = array_values(array_filter($invoice->items, static fn ($item): bool => str_contains($item->sourceLabel ?? '', 'BANDEIRA')));

            $this->assertCount(1, $flags, $flagLine);
            $this->assertSame('100.00', $flags[0]->amount);
            $this->assertSame('other_charge', $flags[0]->itemType);
            $this->assertSame('42546.32', $invoice->totalPaid);
            $this->assertNotContains('invoice_billing_total_mismatch', $invoice->warnings);
            $this->assertNull((new InvoiceExtractionValidator)->validate([$invoice]));
        }
    }

    public function test_it_reads_the_tusd_billing_adjustment_that_otherwise_blocks_the_october_invoice(): void
    {
        foreach (['DIF.FATUR.TUSD - HOMOLOG. CCEE', 'DIF. FATUR. TUSD - HOMOLOG. CCEE'] as $label) {
            $text = file_get_contents(__DIR__.'/../Fixtures/enel-discounted-text-blue.txt');
            $text = str_replace('CONSUMO ATIVO PONTA TUSD', $label."\t0,000 0,00000 93,08 0,01 0,00 0% 0,000,00000\nCONSUMO ATIVO PONTA TUSD", $text);
            $text = str_replace(['42.446,32', '50.626,45'], ['42.539,40', '50.719,53'], $text);

            $invoice = (new EnelInvoiceReader)->read($text);
            $adjustments = array_values(array_filter($invoice->items, static fn ($item): bool => str_contains($item->sourceLabel ?? '', 'HOMOLOG. CCEE')));

            $this->assertCount(1, $adjustments);
            $this->assertSame('93.08', $adjustments[0]->amount);
            $this->assertSame('other_charge', $adjustments[0]->itemType);
            $this->assertNotContains('invoice_billing_total_mismatch', $invoice->warnings);
            $this->assertNull((new InvoiceExtractionValidator)->validate([$invoice]));
        }
    }

    public function test_it_warns_when_a_billing_row_is_missing_instead_of_silently_accepting_a_partial_table(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/enel-discounted-text-blue.txt');
        $text = preg_replace('/^ENCARGO ESCASSEZ.*\n/mu', '', $text);
        $invoice = (new EnelInvoiceReader)->read($text);
        $this->assertContains('invoice_billing_total_mismatch', $invoice->warnings);
    }

    public function test_dic_credit_is_subtracted_when_reconciling_the_invoice_shown_in_the_billing_table(): void
    {
        $text = <<<'INVOICE'
Referência: 07/2026
Unidade Consumidora: MTE0012345
Subgrupo: A4
Modalidade: Verde
Demanda - KW 57,000
DEMANDA KW 27,384 21,72702 594,98 0,00 0,00 0% 0,00 17,04000
CONSUMO ATIVO PONTA TUSD KWH 873,054 1,06733 931,84 0,00 0,00 0% 0,00 0,83707
CONSUMO ATIVO PONTA TE KWH 873,054 0,55992 488,84 0,00 0,00 0% 0,00 0,43913
CONSUMO ATIVO F. PONTA TUSD KWH 9.310,896 0,15945 1.484,62 0,00 0,00 0% 0,00 0,12505
CONSUMO ATIVO F. PONTA TE KWH 9.310,896 0,34879 3.247,56 0,00 0,00 0% 0,00 0,27354
DEMANDA LEI ESTADUAL 16.886/18 KW 29,616 17,81605 527,64 0,00 0,00 0% 0,00 17,04000
ADICIONAL BANDEIRA AMARELA FP 0,000 0,00000 223,79 0,00 0,00 0% 0,00 0,00000
ADICIONAL BANDEIRA AMARELA PT 0,000 0,00000 20,96 0,00 0,00 0% 0,00 0,00000
COSIP - SÃO PAULO - MUNICIPAL 712,11 0,00 0,00 0% 0,00
DIC MAIO/2026 -716,86
Subtotal Faturamento 7.520,23
Subtotal Outros -4,75
TOTAL 7.515,48
INVOICE;

        foreach (['-716,86', '-716,86 0,00 0,00 0% 0,00'] as $creditColumns) {
            $invoice = (new EnelInvoiceReader)->read(str_replace('DIC MAIO/2026 -716,86', 'DIC MAIO/2026 '.$creditColumns, $text));
            $credits = array_values(array_filter($invoice->items, static fn ($item): bool => $item->sourceLabel === 'DIC MAIO/2026'));

            $this->assertCount(1, $credits);
            $this->assertSame('other_charge', $credits[0]->itemType);
            $this->assertSame('-716.86', $credits[0]->amount);
            $this->assertNull($credits[0]->quantity);
            $this->assertSame('7515.48', $invoice->totalPaid);
            $sum = '0.00';
            foreach ($invoice->items as $item) {
                $sum = bcadd($sum, $item->amount, 2);
            }
            $this->assertSame('7515.48', $sum);
            $this->assertNotContains('invoice_billing_total_mismatch', $invoice->warnings);
            $this->assertNull((new InvoiceExtractionValidator)->validate([$invoice]));
        }

        $withoutCredit = (new EnelInvoiceReader)->read(str_replace("DIC MAIO/2026 -716,86\n", '', $text));
        $this->assertContains('invoice_billing_total_mismatch', $withoutCredit->warnings);
    }

    public function test_reading_date_takes_precedence_over_issue_month_due_date_and_dates_in_legal_notices(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/enel-reference-blue.txt');
        $invoice = (new EnelInvoiceReader)->read("LEITURA ATUAL 30/06/2026\nMês/Ano: 07/2026\n".$text);
        $this->assertSame('2026-06', $invoice->referenceMonth);

        $invoice = (new EnelInvoiceReader)->read("13/07/2026\n31/05/2026 30/06/2026 31/07/2026\n".$text);
        $this->assertSame('2026-06', $invoice->referenceMonth);
    }

    public function test_it_uses_the_standalone_header_month_without_taking_the_year_from_a_legal_notice(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/enel-discounted-text-blue.txt');
        $text = str_replace('31/07/2026 31/08/2026 30/09/2026', '', $text);
        $this->assertSame('2026-08', (new EnelInvoiceReader)->read($text)->referenceMonth);
    }

    public function test_it_matches_short_idle_demand_rows_using_net_tariffs_when_tax_rounding_exceeds_two_cents(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/enel-rounded-january-blue.txt');
        $invoice = (new EnelInvoiceReader)->read($text);
        $this->assertSame([], $invoice->warnings);
        $this->assertSame('571.06', $this->item($invoice->items, 'idle_demand', 'off_peak')->amount);
        $this->assertSame('1795.88', $this->item($invoice->items, 'idle_demand', 'peak')->amount);
    }

    public function test_it_preserves_values_from_january_and_february_invoices_with_rounding_differences(): void
    {
        $invoices = [];
        foreach (['january' => '48427.71', 'february' => '50934.67'] as $month => $billedAmount) {
            $invoice = (new EnelInvoiceReader)->read(file_get_contents(__DIR__.'/../Fixtures/enel-rounded-'.$month.'-blue.txt'));
            $consumption = array_values(array_filter($invoice->items, static fn ($item): bool => $item->itemType === 'active_consumption' && $item->timeSlot === 'off_peak' && $item->tariffComponent === 'energy_te'))[0];
            $this->assertSame($billedAmount, $consumption->amount);
            $this->assertSame($month === 'january' ? '0.32136' : '0.32129', $consumption->unitPriceTaxed);
            $invoices[] = $invoice;
        }
        $this->assertNull((new InvoiceExtractionValidator)->validate($invoices));
    }

    public function test_it_normalizes_the_reference_invoice_and_matches_reversed_idle_demand_rows(): void
    {
        $reader = new EnelInvoiceReader;
        $invoice = $reader->read(file_get_contents(__DIR__.'/../Fixtures/enel-reference-blue.txt'));

        $this->assertSame('2025-08', $invoice->referenceMonth);
        $this->assertSame('123456789', $invoice->consumerUnit);
        $this->assertSame('A4', $invoice->subgroup);
        $this->assertSame('blue', $invoice->tariffModality);
        $this->assertSame('98922.22', $invoice->totalPaid);

        $peakDemand = $this->item($invoice->items, 'measured_demand', 'peak');
        $this->assertSame('221.760', $peakDemand->quantity);
        $this->assertSame('37.80322', $peakDemand->unitPriceTaxed);
        $this->assertSame('29.30000', $peakDemand->tariffRate);
        $this->assertSame('8383.25', $peakDemand->amount);
        $this->assertSame('376.40', $peakDemand->pisCofinsAmount);
        $this->assertSame('0.1800', $peakDemand->icmsRate);
        $this->assertSame('1508.99', $peakDemand->icmsAmount);
        $overrun = $this->item($invoice->items, 'demand_overrun', 'peak');
        $this->assertSame('10.000', $overrun->quantity);
        $this->assertSame('756.06', $overrun->amount);

        $idleItems = array_values(array_filter($invoice->items, static fn ($item): bool => $item->itemType === 'idle_demand'));
        $this->assertCount(2, $idleItems);
        $this->assertSame('off_peak', $idleItems[0]->timeSlot);
        $this->assertSame('1845.32', $idleItems[0]->amount);
        $this->assertNull($idleItems[0]->quantity);
        $this->assertNull($idleItems[0]->unitPriceTaxed);
        $this->assertSame('peak', $idleItems[1]->timeSlot);
        $this->assertSame('3603.28', $idleItems[1]->amount);
        $this->assertSame([], $invoice->warnings);

        $this->assertNotContains('dmcr', array_map(static fn ($item): string => $item->itemType, $invoice->items));
        $this->assertSame('energy_tusd', $this->item($invoice->items, 'active_consumption', 'peak')->tariffComponent);
        $this->assertSame('reactive_demand_excess', $this->item($invoice->items, 'reactive_demand_excess', 'off_peak')->itemType);
        $this->assertSame('reactive_energy_excess', $this->item($invoice->items, 'reactive_energy_excess', 'late_night_weekend')->itemType);
        $this->assertNull((new InvoiceExtractionValidator)->validate([$invoice]));
    }

    public function test_it_returns_no_idle_demand_items_when_the_invoice_has_no_idle_demand_line(): void
    {
        $invoice = (new EnelInvoiceReader)->read(file_get_contents(__DIR__.'/../Fixtures/enel-no-idle-blue.txt'));

        $this->assertSame('2025-09', $invoice->referenceMonth);
        $this->assertSame([], array_values(array_filter($invoice->items, static fn ($item): bool => $item->itemType === 'idle_demand')));
        $this->assertSame([], $invoice->warnings);
    }

    public function test_it_keeps_idle_rows_unmatched_and_adds_a_warning_when_no_assignment_is_within_tolerance(): void
    {
        $text = file_get_contents(__DIR__.'/../Fixtures/enel-reference-blue.txt');
        $text = str_replace(['1.845,32', '3.603,28'], ['900,00', '800,00'], $text);

        $invoice = (new EnelInvoiceReader)->read($text);
        $idleItems = array_values(array_filter($invoice->items, static fn ($item): bool => $item->itemType === 'idle_demand'));

        $this->assertSame(['idle_demand_post_matching_unresolved'], $invoice->warnings);
        $this->assertSame(['unresolved_0', 'unresolved_1'], array_map(static fn ($item): string => $item->timeSlot, $idleItems));
    }

    /** @param list<ExtractedInvoiceItemData> $items */
    private function item(array $items, string $itemType, string $timeSlot): ExtractedInvoiceItemData
    {
        foreach ($items as $item) {
            if ($item->itemType === $itemType && $item->timeSlot === $timeSlot) {
                return $item;
            }
        }

        $this->fail("Missing invoice item {$itemType} / {$timeSlot}.");
    }
}
