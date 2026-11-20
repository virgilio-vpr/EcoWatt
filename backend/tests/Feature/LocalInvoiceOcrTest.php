<?php

namespace Tests\Feature;

use App\Invoices\InvoiceDocumentReader;
use App\Invoices\Ocr\LocalInvoiceOcr;
use App\Invoices\Readers\EnelInvoiceReader;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use InvalidArgumentException;
use PHPUnit\Framework\Attributes\DataProvider;
use Symfony\Component\Process\ExecutableFinder;
use Tests\TestCase;

class LocalInvoiceOcrTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        config(['ocr.lock_path' => sys_get_temp_dir().'/ecowatt-ocr-test-'.getmypid().'.lock']);
    }

    protected function tearDown(): void
    {
        @unlink(config('ocr.lock_path'));
        parent::tearDown();
    }

    public static function formats(): array
    {
        return [['invoice.png'], ['invoice.jpg'], ['scanned.pdf'], ['native.pdf'], ['hybrid.pdf'], ['enel-panels.png']];
    }

    #[DataProvider('formats')]
    public function test_real_engine_preserves_fields_and_closes_totals(string $file): void
    {
        if (! is_executable(config('ocr.tesseract')) && ! (new ExecutableFinder)->find(config('ocr.tesseract'))) {
            $this->markTestSkipped('Instale o Tesseract para executar a integração OCR real.');
        }
        Storage::fake('invoice_temp');
        $invoice = app(InvoiceDocumentReader::class)->read(file_get_contents(base_path('tests/Fixtures/ocr/'.$file)), new EnelInvoiceReader);
        $expected = (new EnelInvoiceReader)->read(file_get_contents(base_path('tests/Fixtures/ocr/expected.txt')));
        $this->assertEquals($expected, $invoice, $file);
        $this->assertCount(11, $invoice->items);
        $this->assertSame('1189.75', collect($invoice->items)->reduce(fn ($sum, $item) => bcadd($sum, $item->amount, 2), '0.00'));
        $this->assertSame('-10.25', collect($invoice->items)->firstWhere('itemType', 'other_charge')->amount);
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
    }

    public function test_page_limit_is_enforced_before_rendering(): void
    {
        if (! is_executable(config('ocr.tesseract')) && ! (new ExecutableFinder)->find(config('ocr.tesseract'))) {
            $this->markTestSkipped('Instale o motor OCR local.');
        }
        Storage::fake('invoice_temp');
        try {
            app(LocalInvoiceOcr::class)->extract(base_path('tests/Fixtures/ocr/five-pages.pdf'));
            $this->fail('Five pages must exceed the OCR budget.');
        } catch (InvalidArgumentException $exception) {
            $this->assertStringContainsString('até 4 páginas', $exception->getMessage());
        }
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
    }

    public function test_concurrent_read_returns_a_retryable_message_without_creating_intermediates(): void
    {
        Storage::fake('invoice_temp');
        $lock = fopen(config('ocr.lock_path'), 'c');
        flock($lock, LOCK_EX);
        try {
            app(LocalInvoiceOcr::class)->extract(base_path('tests/Fixtures/ocr/invoice.png'));
            $this->fail('Only one OCR process may run per shared volume.');
        } catch (InvalidArgumentException $exception) {
            $this->assertStringContainsString('ocupado', $exception->getMessage());
        } finally {
            fclose($lock);
        }
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
    }

    public function test_missing_engine_cleans_intermediates(): void
    {
        Storage::fake('invoice_temp');
        config(['ocr.tesseract' => '/nonexistent/tesseract']);
        try {
            app(LocalInvoiceOcr::class)->extract(base_path('tests/Fixtures/ocr/invoice.png'));
            $this->fail('Missing OCR engine must fail.');
        } catch (InvalidArgumentException $exception) {
            $this->assertStringContainsString('indisponível', $exception->getMessage());
        }
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
    }

    public function test_timeout_terminates_process_and_cleans_intermediates(): void
    {
        Storage::fake('invoice_temp');
        Log::spy();
        $script = tempnam(sys_get_temp_dir(), 'slow-ocr-');
        file_put_contents($script, "#!/bin/sh\nexec sleep 5\n");
        chmod($script, 0700);
        config(['ocr.tesseract' => $script, 'ocr.timeout' => 1]);
        try {
            app(LocalInvoiceOcr::class)->extract(base_path('tests/Fixtures/ocr/invoice.png'));
            $this->fail('OCR must time out.');
        } catch (InvalidArgumentException $exception) {
            $this->assertStringContainsString('40 segundos', $exception->getMessage());
        } finally {
            unlink($script);
        }
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
        Log::shouldHaveReceived('warning')->with('invoice_ocr_failure', ['stage' => 'engine', 'reason' => 'timeout'])->once();
    }

    public function test_recognition_failure_is_distinct_from_timeout_and_does_not_expose_process_output(): void
    {
        Storage::fake('invoice_temp');
        Log::spy();
        $script = tempnam(sys_get_temp_dir(), 'failed-ocr-');
        file_put_contents($script, "#!/bin/sh\nif [ \"\$1\" = \"--version\" ]; then echo 'test engine'; exit 0; fi\necho 'PRIVATE INVOICE CONTENT' >&2\nexit 1\n");
        chmod($script, 0700);
        config(['ocr.tesseract' => $script]);
        try {
            app(LocalInvoiceOcr::class)->extract(base_path('tests/Fixtures/ocr/invoice.png'));
            $this->fail('A failed recognizer must be reported.');
        } catch (InvalidArgumentException $exception) {
            $this->assertStringContainsString('etapa de reconhecimento', $exception->getMessage());
            $this->assertStringNotContainsString('PRIVATE INVOICE CONTENT', $exception->getMessage());
            $this->assertStringNotContainsString('40 segundos', $exception->getMessage());
        } finally {
            unlink($script);
        }
        Log::shouldHaveReceived('warning')->with('invoice_ocr_failure', ['stage' => 'recognition', 'reason' => 'process_failed', 'exit_code' => 1])->once();
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
    }
}
