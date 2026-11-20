<?php

namespace Tests\Feature;

use App\Invoices\InvoiceDocumentReader;
use App\Invoices\Ocr\InvoiceOcr;
use App\Invoices\Pdf\PdfTextParser;
use App\Invoices\Readers\EnelInvoiceReader;
use Illuminate\Support\Facades\Storage;
use InvalidArgumentException;
use Tests\TestCase;

class InvoiceDocumentReaderTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        Storage::fake('invoice_temp');
    }

    private function text(): string
    {
        return file_get_contents(base_path('tests/Fixtures/ocr/expected.txt'));
    }

    public function test_sufficient_native_text_does_not_call_ocr(): void
    {
        $this->mock(PdfTextParser::class)->shouldReceive('extract')->once()->andReturn($this->text());
        $this->mock(InvoiceOcr::class)->shouldNotReceive('extract');
        $invoice = app(InvoiceDocumentReader::class)->read('%PDF-1.4 fixture', new EnelInvoiceReader);
        $this->assertSame('MTE0015497', $invoice->consumerUnit);
        $this->assertSame('1189.75', $invoice->totalPaid);
        $this->assertSame([], $invoice->warnings);
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
    }

    public function test_hybrid_fills_missing_metered_demands_without_duplicating_billing_rows(): void
    {
        $native = preg_replace('/^1234567.*\n/m', '', $this->text());
        $this->mock(PdfTextParser::class)->shouldReceive('extract')->once()->andReturn($native);
        $this->mock(InvoiceOcr::class)->shouldReceive('extract')->once()->andReturn($this->text());
        $invoice = app(InvoiceDocumentReader::class)->read('%PDF-1.4 fixture', new EnelInvoiceReader);
        $this->assertCount(11, $invoice->items);
        $this->assertSame('1189.75', collect($invoice->items)->reduce(fn ($sum, $item) => bcadd($sum, $item->amount, 2), '0.00'));
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
    }

    public function test_conflicting_sources_are_rejected_without_selecting_the_value_that_closes_the_total(): void
    {
        $native = preg_replace('/^1234567.*\n/m', '', $this->text());
        $this->mock(PdfTextParser::class)->shouldReceive('extract')->andReturn($native);
        $this->mock(InvoiceOcr::class)->shouldReceive('extract')->andReturn(str_replace('MTE0015497', 'MTE0015498', $this->text()));
        try {
            app(InvoiceDocumentReader::class)->read('%PDF-1.4 fixture', new EnelInvoiceReader);
            $this->fail('Conflicting identifiers must require review.');
        } catch (InvalidArgumentException $exception) {
            $this->assertStringContainsString('divergem', $exception->getMessage());
        }
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
    }

    public function test_ocr_total_mismatch_is_preserved_for_review_without_adjusting_items(): void
    {
        $this->mock(InvoiceOcr::class)->shouldReceive('extract')->andReturn(str_replace('TOTAL A PAGAR 1.189,75', 'TOTAL A PAGAR 1.190,75', $this->text()));
        $invoice = app(InvoiceDocumentReader::class)->read('image', new EnelInvoiceReader);
        $this->assertSame('1190.75', $invoice->totalPaid);
        $this->assertContains('invoice_billing_total_mismatch', $invoice->warnings);
        $this->assertSame('-10.25', collect($invoice->items)->firstWhere('itemType', 'other_charge')->amount);
    }

    public function test_inspect_command_checks_a_native_document_without_persisting(): void
    {
        $this->artisan('invoices:inspect', ['file' => base_path('tests/Fixtures/ocr/native.pdf')])->assertExitCode(0);
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
    }

    public function test_native_headers_without_a_billing_table_cannot_be_saved_when_ocr_fails(): void
    {
        $text = implode("\n", array_slice(explode("\n", $this->text()), 0, 6));
        $this->mock(PdfTextParser::class)->shouldReceive('extract')->andReturn($text);
        $this->mock(InvoiceOcr::class)->shouldReceive('extract')->andThrow(new InvalidArgumentException('OCR ilegível'));
        try {
            app(InvoiceDocumentReader::class)->read('%PDF-1.4 fixture', new EnelInvoiceReader);
            $this->fail('Headers alone must not produce a partial invoice.');
        } catch (InvalidArgumentException $exception) {
            $this->assertSame('OCR ilegível', $exception->getMessage());
        }
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
    }

    public function test_unreadable_ocr_leaves_no_temporary_files(): void
    {
        $this->mock(InvoiceOcr::class)->shouldReceive('extract')->andThrow(new InvalidArgumentException('OCR ilegível'));
        try {
            app(InvoiceDocumentReader::class)->read('image', new EnelInvoiceReader);
            $this->fail('Unreadable OCR must fail.');
        } catch (InvalidArgumentException $exception) {
            $this->assertSame('OCR ilegível', $exception->getMessage());
        }
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
    }
}
