<?php

namespace Tests\Feature;

use App\Calculation\Data\ExtractedInvoiceData;
use App\Invoices\Readers\EnelInvoiceReader;
use App\Models\Distributor;
use App\Models\Simulation;
use App\Models\User;
use Database\Seeders\RegulatoryParameterSeeder;
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Illuminate\Queue\WorkerOptions;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Mail;
use Illuminate\Support\Facades\Storage;
use Tests\TestCase;

class PerformanceBaselineTest extends TestCase
{
    use RefreshDatabase;

    private float $applicationBootMs = 0;

    private ?string $temporaryRoot = null;

    protected function tearDown(): void
    {
        if ($this->temporaryRoot !== null) {
            File::deleteDirectory($this->temporaryRoot);
        }
        parent::tearDown();
    }

    public function createApplication(): Application
    {
        $started = hrtime(true);
        $app = parent::createApplication();
        $this->applicationBootMs = (hrtime(true) - $started) / 1e6;
        if ($app['config']->get('database.default') !== 'sqlite'
            || $app['config']->get('database.connections.sqlite.database') !== ':memory:') {
            throw new \RuntimeException('A linha de base exige SQLite em memória antes de preparar o banco de teste.');
        }

        return $app;
    }

    public function test_synthetic_baseline_records_real_stages_and_preserves_results(): void
    {
        if (getenv('ECOWATT_RUN_BASELINE') !== '1') {
            $this->markTestSkipped('Execute com ECOWATT_RUN_BASELINE=1 para medir a amostra sintética.');
        }
        $this->assertSame('sqlite', config('database.default'));
        $this->assertSame(':memory:', config('database.connections.sqlite.database'));
        config(['performance.enabled' => true, 'queue.default' => 'database']);
        $this->temporaryRoot = storage_path('framework/testing/disks/invoice_temp_baseline-'.getmypid().'-'.bin2hex(random_bytes(4)));
        Storage::set('invoice_temp', Storage::build([
            'driver' => 'local', 'root' => $this->temporaryRoot, 'throw' => true,
            'visibility' => 'private', 'directory_visibility' => 'private',
        ]));
        Mail::fake();
        $this->seed(RegulatoryParameterSeeder::class);
        $distributor = Distributor::query()->create(['name' => 'Synthetic ENEL', 'state' => 'SP', 'parser_key' => 'enel', 'active' => true]);
        $records = [];
        Log::shouldReceive('info')->andReturnUsing(function (string $message, array $data = []) use (&$records): void {
            if ($message === 'performance_stage') {
                $records[] = $data;
            }
        });
        $samples = [];
        $expected = (new EnelInvoiceReader)->read(file_get_contents(base_path('tests/Fixtures/ocr/expected.txt')));
        $formats = ['native.pdf', 'invoice.png', 'scanned.pdf', 'hybrid.pdf'];
        $selected = getenv('ECOWATT_BASELINE_SCENARIO');
        if (is_string($selected) && $selected !== '') {
            $this->assertContains($selected, $formats);
            $formats = [$selected];
        }
        foreach ($formats as $file) {
            for ($iteration = 0; $iteration < 3; $iteration++) {
                $records = [];
                $this->actingAs(User::factory()->create());
                $id = $this->postJson('/api/v1/invoice-imports', [
                    'company_name' => 'Synthetic company', 'distributor_id' => $distributor->id,
                    'address_details' => 'Synthetic address', 'substation_same_address' => true,
                ])->assertCreated()->json('data.id');
                $image = new UploadedFile(base_path('tests/Fixtures/ocr/'.$file), $file, null, null, true);
                $response = $this->postJson("/api/v1/invoice-imports/{$id}/invoices", ['invoice' => $image])->assertCreated();
                $response->assertJsonPath('data.invoices.0.total_paid', '1189.75')->assertJsonCount(11, 'data.invoices.0.items');
                $this->assertSame('-10.25', collect($response->json('data.invoices.0.items'))->firstWhere('item_type', 'other_charge')['amount']);
                $this->postJson("/api/v1/invoice-imports/{$id}/complete")->assertOk()->assertJsonPath('data.status', 'completed');
                $this->getJson("/api/v1/simulations/{$id}/pdf")->assertOk()->assertHeader('content-type', 'application/pdf');
                $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
                $this->assertSame(match ($file) {
                    'native.pdf' => 'native', 'hybrid.pdf' => 'hybrid', default => 'ocr',
                }, collect($records)->firstWhere('stage', 'document_read')['method']);
                foreach (['http', 'upload_validation', 'page_count', 'persistence', 'calculation', 'pdf'] as $stage) {
                    $this->assertNotNull(collect($records)->firstWhere('stage', $stage));
                }
                if ($file !== 'native.pdf') {
                    foreach (['ocr', 'ocr_engine', 'recognition'] as $stage) {
                        $this->assertNotNull(collect($records)->firstWhere('stage', $stage));
                    }
                }
                $samples[] = [
                    'scenario' => $file,
                    'state' => $iteration === 0 ? 'first_use' : 'warm',
                    'iteration' => $iteration,
                    'stages' => $records,
                ];
                $saved = Simulation::findOrFail($id)->invoices()->with('items')->firstOrFail();
                $actual = ExtractedInvoiceData::fromArray($saved->attributesToArray() + [
                    'items' => $saved->items->map(fn ($item) => $item->attributesToArray())->all(),
                    'warnings' => $saved->extraction_warnings ?? [],
                ]);
                $this->assertEquals($expected, $actual);
            }
        }
        // Exercise the existing batch journey through an actual database reservation and worker.
        $records = [];
        $queuedId = $this->postJson('/api/v1/simulations', [
            'company_name' => 'Synthetic company', 'distributor_id' => $distributor->id,
            'address_details' => 'Synthetic address', 'substation_same_address' => true,
            'invoices' => [new UploadedFile(base_path('tests/Fixtures/ocr/native.pdf'), 'native.pdf', null, null, true)],
        ])->assertAccepted()->json('data.id');
        app('queue.worker')->runNextJob('database', 'default', new WorkerOptions(sleep: 0, maxTries: 3, timeout: 300));
        $this->assertDatabaseHas('simulations', ['id' => $queuedId, 'status' => 'completed']);
        $job = collect($records)->firstWhere('stage', 'job');
        $this->assertNotNull($job);
        $this->assertSame('ok', $job['outcome']);
        $this->assertNotNull($job['queue_wait_ms']);
        $this->assertDatabaseCount('jobs', 0);
        $samples[] = ['scenario' => 'batch_native', 'state' => 'warm', 'iteration' => 0, 'stages' => $records];
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
        fwrite(STDOUT, "\nECOWATT_BASELINE=".json_encode([
            'environment' => [
                'application_boot_ms' => round($this->applicationBootMs, 3), 'php' => PHP_VERSION, 'laravel' => app()->version(), 'os' => PHP_OS_FAMILY,
                'filesystem' => str_starts_with(base_path(), '/mnt/c/') ? 'wsl_windows_mount' : 'other',
                'opcache_cli' => ini_get('opcache.enable_cli'), 'memory_limit' => ini_get('memory_limit'),
                'database' => 'sqlite_memory', 'mail' => 'fake', 'workers' => 1,
            ],
            'samples' => $samples,
        ], JSON_THROW_ON_ERROR)."\n");
    }
}
