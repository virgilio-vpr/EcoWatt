<?php

namespace Tests\Feature;

use App\Calculation\Contracts\ReportCalculationEngine;
use App\Calculation\Data\ExtractedInvoiceData;
use App\Invoices\InvoiceDocumentReader;
use App\Invoices\Ocr\InvoiceOcr;
use App\Invoices\Pdf\PdfTextParser;
use App\Invoices\Readers\EnelInvoiceReader;
use App\Invoices\Readers\InvoiceReader;
use App\Invoices\Readers\InvoiceReaderResolver;
use App\Invoices\Validation\InvoiceExtractionValidator;
use App\Invoices\Validation\InvoiceProcessingFailureRecorder;
use App\Jobs\ProcessSimulation;
use App\Mail\SimulationCompleted;
use App\Models\CustomerProfile;
use App\Models\Distributor;
use App\Models\Invoice;
use App\Models\InvoiceItem;
use App\Models\Report;
use App\Models\Simulation;
use App\Models\Tariff;
use App\Models\User;
use App\Reports\PdfReportGenerator;
use Database\Seeders\RegulatoryParameterSeeder;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Mail;
use Illuminate\Support\Facades\Storage;
use RuntimeException;
use Smalot\PdfParser\Parser;
use Tests\TestCase;

class ProcessSimulationTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        $this->seed(RegulatoryParameterSeeder::class);
        Storage::fake('invoice_temp');
    }

    public function test_job_completes_two_invoices_with_amount_differences_within_one_real(): void
    {
        Mail::fake();
        [$simulation] = $this->simulationWithFiles();
        Storage::disk('invoice_temp')->put('simulation-'.$simulation->id.'/invoice-2.pdf', '%PDF-1.4 fixture');
        $this->app->instance(InvoiceReaderResolver::class, new InvoiceReaderResolver([new EnelInvoiceReader]));
        $this->mock(PdfTextParser::class)->shouldReceive('extract')->twice()->andReturn(
            file_get_contents(base_path('tests/Fixtures/enel-rounded-january-blue.txt')),
            file_get_contents(base_path('tests/Fixtures/enel-rounded-february-blue.txt')),
        );

        (new ProcessSimulation($simulation->id))->handle(
            app(InvoiceReaderResolver::class),
            app(InvoiceDocumentReader::class),
            app(InvoiceExtractionValidator::class),
            app(InvoiceProcessingFailureRecorder::class),
            app(ReportCalculationEngine::class),
        );

        $this->assertDatabaseHas('simulations', ['id' => $simulation->id, 'status' => 'completed', 'months_count' => 2]);
        $this->assertSame(2, $simulation->invoices()->count());
        $this->assertSame(1, $simulation->report()->count());
        $report = $simulation->report()->firstOrFail();
        $this->assertNull($report->optimal_demand_peak);
        $this->assertNull($report->optimal_demand_off_peak);
        $this->assertSame('0.00', $report->demand_savings_monthly);
        $this->assertContains('demand_optimization_unavailable', $report->warnings);
        $this->assertSame([], $report->recommendations);
        foreach ($report->chart_series['demand'] as $point) {
            $this->assertSame($point['time_slot'] === 'peak' ? $report->optimal_demand_peak : $report->optimal_demand_off_peak, $point['optimal']);
            $this->assertSame('0.05000', $point['overrun_tolerance']);
            $this->assertArrayNotHasKey('reference_tariff', $point);
        }
        $this->assertDatabaseHas('invoice_items', ['amount' => '48427.71', 'unit_price_taxed' => '0.32136']);
        $this->assertDatabaseHas('invoice_items', ['amount' => '50934.67', 'unit_price_taxed' => '0.32129']);
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles('simulation-'.$simulation->id));
        Mail::assertSent(SimulationCompleted::class);
    }

    public function test_job_persists_invoices_creates_report_and_is_idempotent(): void
    {
        Mail::fake();
        [$simulation] = $this->simulationWithFiles();
        $fixture = file_get_contents(base_path('tests/Fixtures/enel-reference-blue.txt'));
        $this->app->instance(InvoiceReaderResolver::class, new InvoiceReaderResolver([new EnelInvoiceReader]));
        $this->mock(PdfTextParser::class)->shouldReceive('extract')->andReturn($fixture);

        $job = new ProcessSimulation($simulation->id);
        $job->handle(
            app(InvoiceReaderResolver::class),
            app(InvoiceDocumentReader::class),
            app(InvoiceExtractionValidator::class),
            app(InvoiceProcessingFailureRecorder::class),
            app(ReportCalculationEngine::class),
        );
        $job->handle(
            app(InvoiceReaderResolver::class),
            app(InvoiceDocumentReader::class),
            app(InvoiceExtractionValidator::class),
            app(InvoiceProcessingFailureRecorder::class),
            app(ReportCalculationEngine::class),
        );

        $this->assertDatabaseHas('simulations', ['id' => $simulation->id, 'status' => 'completed', 'months_count' => 1]);
        $this->assertSame(1, Invoice::query()->where('simulation_id', $simulation->id)->count());
        $this->assertGreaterThan(0, InvoiceItem::query()->whereHas('invoice', fn ($query) => $query->where('simulation_id', $simulation->id))->count());
        $report = Report::query()->where('simulation_id', $simulation->id)->firstOrFail();
        $this->assertSame('1.5', $report->algorithm_version);
        $this->assertContains('incomplete_invoice_series', $report->warnings);
        $pdfText = (new Parser)->parseContent(app(PdfReportGenerator::class)->generate($report))->getText();
        $this->assertStringContainsString('menos de 12 faturas', preg_replace('/\s+/u', ' ', $pdfText));
        $this->assertContains('demand_invoice_reconciliation_mismatch', $report->warnings);
        $this->assertSame('0.820000', $report->r_values[0]['ratio']);
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles('simulation-'.$simulation->id));
        Mail::assertSent(SimulationCompleted::class, fn (SimulationCompleted $mail): bool => $mail->report->simulation_id === $simulation->id);
    }

    public function test_report_compares_modalities_when_approved_green_tariffs_are_available(): void
    {
        Mail::fake();
        [$simulation] = $this->simulationWithFiles();
        $distributorId = $simulation->user->profile->distributor_id;
        foreach ([['single', 'demand', '10.00000'], ['peak', 'energy_tusd', '0.10000'], ['off_peak', 'energy_tusd', '0.05000']] as [$slot, $component, $rate]) {
            Tariff::query()->create([
                'distributor_id' => $distributorId, 'subgroup' => 'A4', 'tariff_modality' => 'green',
                'time_slot' => $slot, 'component' => $component, 'rate' => $rate,
                'includes_taxes' => false, 'source' => 'aneel_import', 'valid_from' => today()->startOfYear()->toDateString(), 'valid_to' => today()->endOfYear()->toDateString(),
            ]);
        }
        foreach ([
            ['blue', 'peak', 'demand', '28.84000'], ['blue', 'off_peak', 'demand', '17.05000'],
            ['blue', 'peak', 'energy_tusd', '0.09184'], ['blue', 'off_peak', 'energy_tusd', '0.09184'],
            ['blue', 'peak', 'energy_te', '0.38642'], ['blue', 'off_peak', 'energy_te', '0.25018'],
            ['green', 'peak', 'energy_te', '0.38642'], ['green', 'off_peak', 'energy_te', '0.25018'],
        ] as [$modality, $slot, $component, $rate]) {
            Tariff::query()->create([
                'distributor_id' => $distributorId, 'subgroup' => 'A4', 'tariff_modality' => $modality,
                'time_slot' => $slot, 'component' => $component, 'rate' => $rate,
                'includes_taxes' => false, 'source' => 'aneel_import',
                'valid_from' => today()->startOfYear()->toDateString(), 'valid_to' => today()->endOfYear()->toDateString(),
            ]);
        }
        $this->app->instance(InvoiceReaderResolver::class, new InvoiceReaderResolver([new EnelInvoiceReader]));
        $this->mock(PdfTextParser::class)->shouldReceive('extract')->andReturn(file_get_contents(base_path('tests/Fixtures/enel-rounded-january-blue.txt')));

        (new ProcessSimulation($simulation->id))->handle(
            app(InvoiceReaderResolver::class), app(InvoiceDocumentReader::class),
            app(InvoiceExtractionValidator::class), app(InvoiceProcessingFailureRecorder::class), app(ReportCalculationEngine::class),
        );

        $report = $simulation->report()->firstOrFail();
        $this->assertSame('green', $report->recommended_modality);
        $this->assertGreaterThan(0, bccomp($report->migration_savings_monthly, '0', 2));
        $this->assertNotContains('migration_unavailable', $report->warnings);
        $this->assertCount(11, $report->tariff_version_ids);
        $this->assertArrayHasKey('modality', $report->chart_series);
    }

    public function test_green_report_uses_metered_peak_for_blue_and_current_aneel_tariffs_with_invoice_taxes(): void
    {
        Mail::fake();
        [$simulation] = $this->simulationWithFiles();
        $distributorId = $simulation->user->profile->distributor_id;
        foreach ([
            ['blue', 'peak', 'demand', '29.30000'], ['blue', 'off_peak', 'demand', '17.04000'],
            ['green', 'single', 'demand', '17.04000'],
            ['blue', 'peak', 'energy_tusd', '0.12505'], ['blue', 'off_peak', 'energy_tusd', '0.12505'],
            ['green', 'peak', 'energy_tusd', '0.83707'], ['green', 'off_peak', 'energy_tusd', '0.12505'],
            ['blue', 'peak', 'energy_te', '0.43913'], ['blue', 'off_peak', 'energy_te', '0.27354'],
            ['green', 'peak', 'energy_te', '0.43913'], ['green', 'off_peak', 'energy_te', '0.27354'],
        ] as [$modality, $slot, $component, $rate]) {
            Tariff::query()->create([
                'distributor_id' => $distributorId, 'subgroup' => 'A4', 'tariff_modality' => $modality,
                'time_slot' => $slot, 'component' => $component, 'rate' => $rate,
                'includes_taxes' => false, 'source' => 'aneel_import',
                'valid_from' => today()->startOfYear()->toDateString(), 'valid_to' => today()->endOfYear()->toDateString(),
            ]);
        }
        $this->mock(PdfTextParser::class)->shouldReceive('extract')->andReturn(file_get_contents(base_path('tests/Fixtures/enel-unique-demand-green.txt')));

        (new ProcessSimulation($simulation->id))->handle(
            app(InvoiceReaderResolver::class), app(InvoiceDocumentReader::class),
            app(InvoiceExtractionValidator::class), app(InvoiceProcessingFailureRecorder::class), app(ReportCalculationEngine::class),
        );

        $report = $simulation->report()->firstOrFail();
        $this->assertNotContains('migration_unavailable', $report->warnings);
        $this->assertCount(11, $report->tariff_version_ids);
        $this->assertSame('0.820000', $report->r_values[0]['ratio']);
        $this->assertSame('51.072', $report->chart_series['demand'][0]['measured']);
        $this->assertSame('registered_tariff', $report->chart_series['demand'][0]['tariff_reference_source']);
        $this->assertSame('21.85092', $report->chart_series['demand'][0]['reference_tariff']);
        $this->assertSame([
            ['reference_month' => '2026-01', 'time_slot' => 'peak', 'measured' => '40.488'],
            ['reference_month' => '2026-01', 'time_slot' => 'off_peak', 'measured' => '51.072'],
        ], $report->chart_series['demand_measurements']);
        $this->assertSame(2, $simulation->invoices()->firstOrFail()->items()->where('item_type', 'metered_demand')->count());
        $pdfText = (new Parser)->parseContent(app(PdfReportGenerator::class)->generate($report))->getText();
        $this->assertStringContainsString('Demandas do quadro de medição', $pdfText);
        $this->assertStringContainsString('40,488', $pdfText);
        $this->assertStringContainsString('51,072', $pdfText);

        $simulation->invoices()->firstOrFail()->items()->where('item_type', 'metered_demand')->where('time_slot', 'peak')->delete();
        $incomplete = app(ReportCalculationEngine::class)->calculate($simulation->fresh()->load('invoices.items', 'user.profile'));
        $this->assertContains('migration_unavailable', $incomplete->calculatedAttributes['warnings']);
    }

    public function test_batch_reads_an_image_with_ocr_without_duplicate_rows_on_retry(): void
    {
        Mail::fake();
        [$simulation] = $this->simulationWithFiles();
        $disk = Storage::disk('invoice_temp');
        $disk->deleteDirectory('simulation-'.$simulation->id);
        $disk->put('simulation-'.$simulation->id.'/invoice.png', file_get_contents(base_path('tests/Fixtures/ocr/invoice.png')));
        $this->app->instance(InvoiceReaderResolver::class, new InvoiceReaderResolver([new EnelInvoiceReader]));
        $this->mock(InvoiceOcr::class)->shouldReceive('extract')->once()
            ->andReturn(file_get_contents(base_path('tests/Fixtures/ocr/expected.txt')));
        $job = new ProcessSimulation($simulation->id);
        for ($attempt = 0; $attempt < 2; $attempt++) {
            $job->handle(app(InvoiceReaderResolver::class), app(InvoiceDocumentReader::class),
                app(InvoiceExtractionValidator::class), app(InvoiceProcessingFailureRecorder::class), app(ReportCalculationEngine::class));
        }
        $this->assertSame('completed', $simulation->fresh()->status);
        $this->assertSame(1, $simulation->invoices()->count());
        $this->assertSame(11, $simulation->invoices()->first()->items()->count());
        $this->assertSame([], $disk->allFiles());
    }

    public function test_final_read_failure_records_file_error_and_removes_temporary_pdf(): void
    {
        [$simulation] = $this->simulationWithFiles();
        $this->bindReader(ExtractedInvoiceData::fromArray($this->invoiceArray()));
        $this->mock(PdfTextParser::class)->shouldReceive('extract')->andThrow(new RuntimeException('parser details must not leak'));
        $this->mock(InvoiceOcr::class)->shouldReceive('extract')->andThrow(new \InvalidArgumentException('OCR indisponível'));

        $job = new ProcessSimulation($simulation->id);
        try {
            $job->handle(
                app(InvoiceReaderResolver::class),
                app(InvoiceDocumentReader::class),
                app(InvoiceExtractionValidator::class),
                app(InvoiceProcessingFailureRecorder::class),
                app(ReportCalculationEngine::class),
            );
            $this->fail('The parser failure should be retried by the queue.');
        } catch (\InvalidArgumentException $exception) {
            $this->assertSame('OCR indisponível', $exception->getMessage());
        }

        $job->failed(new RuntimeException('parser details must not leak'));
        $simulation->refresh();
        $this->assertSame('failed', $simulation->status);
        $this->assertSame('INVOICE_READ_FAILED', $simulation->processing_errors[0]['code']);
        $this->assertStringContainsString('invoice-1.pdf', $simulation->processing_errors[0]['file']);
        $this->assertStringNotContainsString('parser details', json_encode($simulation->processing_errors));
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles('simulation-'.$simulation->id));

        $token = $simulation->user->createToken('status-check')->plainTextToken;
        $this->getJson('/api/v1/simulations/'.$simulation->id.'/status')->assertUnauthorized();
        $this->withToken($token)->getJson('/api/v1/simulations/'.$simulation->id.'/status')
            ->assertOk()
            ->assertJsonPath('data.status', 'failed')
            ->assertJsonPath('data.processing_errors.0.code', 'INVOICE_READ_FAILED')
            ->assertJsonPath('data.processing_errors.0.file', $simulation->processing_errors[0]['file']);

        $other = User::factory()->create();
        $otherToken = $other->createToken('status-check')->plainTextToken;
        $this->app['auth']->forgetGuards();
        $otherResponse = $this->getJson('/api/v1/simulations/'.$simulation->id.'/status', ['Authorization' => 'Bearer '.$otherToken]);
        $this->assertSame(404, $otherResponse->status(), $otherResponse->getContent());
    }

    public function test_extraction_validation_failure_is_associated_with_the_offending_file(): void
    {
        [$simulation] = $this->simulationWithFiles();
        Storage::disk('invoice_temp')->put('simulation-'.$simulation->id.'/invoice-2.pdf', '%PDF-1.4 fixture');
        $this->bindReader(ExtractedInvoiceData::fromArray($this->invoiceArray()));
        $this->mock(PdfTextParser::class)->shouldReceive('extract')->twice()->andReturn('fixture invoice');

        $job = new ProcessSimulation($simulation->id);
        $job->handle(
            app(InvoiceReaderResolver::class),
            app(InvoiceDocumentReader::class),
            app(InvoiceExtractionValidator::class),
            app(InvoiceProcessingFailureRecorder::class),
            app(ReportCalculationEngine::class),
        );

        $simulation->refresh();
        $this->assertSame('failed', $simulation->status);
        $this->assertStringContainsString('invoice-2.pdf', $simulation->processing_errors[0]['file']);
        $this->assertSame('INVOICE_EXTRACTION_INVALID', $simulation->processing_errors[0]['code']);
        $this->assertArrayHasKey('reference_month', $simulation->processing_errors[0]['errors']);
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles('simulation-'.$simulation->id));
        $this->assertDatabaseCount('invoices', 0);
    }

    public function test_terminal_timeout_failure_records_failure_and_cleans_temporary_files(): void
    {
        [$simulation] = $this->simulationWithFiles();
        $simulation->forceFill(['status' => 'processing'])->save();

        (new ProcessSimulation($simulation->id))->failed(new RuntimeException('timeout'));

        $this->assertDatabaseHas('simulations', ['id' => $simulation->id, 'status' => 'failed']);
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles('simulation-'.$simulation->id));
    }

    private function simulationWithFiles(): array
    {
        $user = User::factory()->create();
        $distributor = Distributor::query()->create(['name' => 'ENEL SP', 'state' => 'SP', 'parser_key' => 'enel', 'active' => true]);
        CustomerProfile::query()->create([
            'user_id' => $user->id,
            'company_name' => 'Empresa Exemplo Ltda.',
            'distributor_id' => $distributor->id,
            'address_details' => 'Rua Exemplo, 100',
            'substation_same_address' => true,
        ]);
        $simulation = Simulation::query()->create(['user_id' => $user->id, 'status' => 'queued', 'months_count' => 0]);
        Storage::disk('invoice_temp')->put('simulation-'.$simulation->id.'/invoice-1.pdf', '%PDF-1.4 fixture');

        return [$simulation];
    }

    private function bindReader(ExtractedInvoiceData $invoiceData): void
    {
        $reader = new class($invoiceData) implements InvoiceReader
        {
            public function __construct(private ExtractedInvoiceData $invoiceData) {}

            public function parserKey(): string
            {
                return 'enel';
            }

            public function recognizesIdleDemandLine(): bool
            {
                return true;
            }

            public function read(string $text): ExtractedInvoiceData
            {
                return $this->invoiceData;
            }
        };

        $this->app->instance(InvoiceReaderResolver::class, new InvoiceReaderResolver([$reader]));
    }

    private function invoiceArray(): array
    {
        return [
            'reference_month' => '2025-01',
            'consumer_unit' => '12345678',
            'subgroup' => 'A4',
            'tariff_modality' => 'blue',
            'total_paid' => '100.00',
            'items' => [[
                'item_type' => 'measured_demand', 'tariff_component' => 'demand',
                'time_slot' => 'peak', 'reactive_nature' => 'not_applicable',
                'quantity' => '100.000', 'unit' => 'kW', 'unit_price_taxed' => '1.00000',
                'tariff_rate' => '1.00000', 'amount' => '100.00',
                'pis_cofins_amount' => '0.00', 'icms_base' => '0.00',
                'icms_rate' => '0.0000', 'icms_amount' => '0.00', 'source_label' => 'DEMANDA PONTA',
            ]],
        ];
    }
}
