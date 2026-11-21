<?php

namespace Tests\Feature;

use App\Invoices\Ocr\LocalInvoiceOcr;
use App\Jobs\ProcessSimulation;
use App\Models\User;
use App\Services\PerformanceMetrics;
use App\Services\PerformanceStage;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Queue\Events\JobExceptionOccurred;
use Illuminate\Queue\Events\JobProcessed;
use Illuminate\Queue\Events\JobProcessing;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Event;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Queue;
use Illuminate\Support\Facades\Storage;
use PHPUnit\Framework\Attributes\DataProvider;
use RuntimeException;
use Tests\TestCase;

class PerformanceMetricsTest extends TestCase
{
    use RefreshDatabase;

    public function test_disabled_metrics_preserve_the_result_and_do_not_log(): void
    {
        config(['performance.enabled' => false]);
        Log::shouldReceive('info')->never();
        $result = app(PerformanceMetrics::class)->measure(PerformanceStage::DocumentRead, fn () => 'unchanged');
        $this->assertSame('unchanged', $result);
    }

    public function test_nested_metrics_count_queries_and_keep_invoice_and_sql_contents_private(): void
    {
        config(['performance.enabled' => true]);
        $records = $this->capture();
        $metrics = app(PerformanceMetrics::class);
        $result = $metrics->measure(PerformanceStage::DocumentRead, function () use ($metrics): string {
            $metrics->extractionMethod('native');

            return $metrics->measure(PerformanceStage::NativeExtraction, function (): string {
                DB::select('select ? as private_value', ['PRIVATE-CUSTOMER-00001234']);
                DB::select('select ? as private_value', ['another@example.test']);

                return 'PRIVATE INVOICE TEXT';
            });
        });
        $this->assertSame('PRIVATE INVOICE TEXT', $result);
        $this->assertCount(2, $records->getArrayCopy());
        [$child, $parent] = $records->getArrayCopy();
        $this->assertSame($parent['trace'], $child['trace']);
        $this->assertSame('native', $parent['method']);
        $this->assertSame(2, $parent['queries']);
        $this->assertSame(2, array_values($parent['query_groups'])[0]['count']);
        foreach (['duration_ms', 'cpu_ms', 'child_cpu_ms', 'php_peak_bytes'] as $key) {
            $this->assertGreaterThanOrEqual(0, $parent[$key]);
        }
        $serialized = json_encode($records->getArrayCopy());
        foreach (['PRIVATE', 'example.test', 'private_value', 'select ?', 'INVOICE TEXT'] as $secret) {
            $this->assertStringNotContainsString($secret, $serialized);
        }
    }

    public function test_failed_spans_preserve_the_exception_and_do_not_leak_into_the_next_operation(): void
    {
        config(['performance.enabled' => true]);
        $records = $this->capture();
        $error = new RuntimeException('PRIVATE STDOUT /private/customer.pdf');
        $metrics = app(PerformanceMetrics::class);
        try {
            $metrics->measure(PerformanceStage::Ocr, fn () => throw $error);
            $this->fail('The original exception must be preserved.');
        } catch (RuntimeException $caught) {
            $this->assertSame($error, $caught);
        }
        $metrics->measure(PerformanceStage::Pdf, fn () => null);
        [$failure, $next] = $records->getArrayCopy();
        $this->assertSame('error', $failure['outcome']);
        $this->assertSame('other', $failure['error_type']);
        $this->assertSame('ok', $next['outcome']);
        $this->assertNotSame($failure['trace'], $next['trace']);
        $this->assertStringNotContainsString('PRIVATE', json_encode($records->getArrayCopy()));
    }

    public function test_an_unavailable_log_sink_does_not_change_processing(): void
    {
        config(['performance.enabled' => true]);
        Log::shouldReceive('info')->andThrow(new RuntimeException('sink unavailable'));
        $this->assertSame('ok', app(PerformanceMetrics::class)->measure(PerformanceStage::Pdf, fn () => 'ok'));
    }

    public function test_http_metrics_cover_success_and_validation_authentication_and_authorization_errors(): void
    {
        config(['performance.enabled' => true]);
        $records = $this->capture();
        $this->getJson('/api/v1/status')->assertOk();
        $this->postJson('/api/v1/test-validation', ['email' => 'PRIVATE'])->assertUnprocessable();
        $this->getJson('/api/v1/simulations')->assertUnauthorized();
        $this->actingAs(User::factory()->create());
        $this->getJson('/api/v1/admin/customers')->assertForbidden();
        $http = array_values(array_filter($records->getArrayCopy(), fn ($record) => $record['stage'] === 'http'));
        $this->assertSame([200, 422, 401, 403], array_column($http, 'http_status'));
        $this->assertSame(['ok', 'error', 'error', 'error'], array_column($http, 'outcome'));
        $this->assertStringNotContainsString('PRIVATE', json_encode($http));
    }

    public function test_database_queue_metrics_measure_attempt_wait_and_reset_after_a_failure(): void
    {
        config(['performance.enabled' => true, 'queue.default' => 'database']);
        $records = $this->capture();
        $queue = Queue::connection('database');
        $id = $queue->push(new ProcessSimulation(999));
        DB::table('jobs')->where('id', $id)->update(['attempts' => 1, 'available_at' => time() - 2]);
        $job = $queue->pop();
        Event::dispatch(new JobProcessing('database', $job));
        Event::dispatch(new JobExceptionOccurred('database', $job, new RuntimeException('PRIVATE PAYLOAD')));
        $job->delete();
        $queue->push(new ProcessSimulation(999));
        $next = $queue->pop();
        Event::dispatch(new JobProcessing('database', $next));
        Event::dispatch(new JobProcessed('database', $next));
        $next->delete();
        [$failure, $success] = $records->getArrayCopy();
        $this->assertSame('job', $failure['stage']);
        $this->assertSame(2, $failure['attempt']);
        $this->assertGreaterThanOrEqual(2000, $failure['queue_wait_ms']);
        $this->assertSame('error', $failure['outcome']);
        $this->assertSame(1, $success['attempt']);
        $this->assertSame('ok', $success['outcome']);
        $this->assertNotSame($failure['trace'], $success['trace']);
        $this->assertStringNotContainsString('PRIVATE', json_encode($records->getArrayCopy()));
    }

    public static function processFailures(): array
    {
        return [['timeout', 'process_timeout', 'ocr_engine'], ['failure', 'process_failure', 'recognition']];
    }

    #[DataProvider('processFailures')]
    public function test_real_subprocess_failures_are_measured_without_output_and_clean_temporary_files(string $mode, string $type, string $stage): void
    {
        config(['performance.enabled' => true, 'ocr.timeout' => 1]);
        $records = $this->capture();
        Log::shouldReceive('warning')->andReturnNull();
        Storage::fake('invoice_temp');
        $script = tempnam(sys_get_temp_dir(), 'ecowatt-metric-process-');
        file_put_contents($script, $mode === 'timeout'
            ? "#!/bin/sh\nexec sleep 3\n"
            : "#!/bin/sh\nif [ \"\$1\" = \"--version\" ]; then echo 'synthetic engine'; exit 0; fi\necho 'PRIVATE PROCESS OUTPUT' >&2\nexit 23\n");
        chmod($script, 0700);
        config(['ocr.tesseract' => $script]);
        try {
            app(LocalInvoiceOcr::class)->extract(base_path('tests/Fixtures/ocr/invoice.png'));
            $this->fail('The subprocess must fail.');
        } catch (\InvalidArgumentException $exception) {
            $this->assertStringNotContainsString('PRIVATE', $exception->getMessage());
        } finally {
            unlink($script);
        }
        $process = collect($records->getArrayCopy())->firstWhere('stage', $stage);
        $this->assertSame('error', $process['outcome']);
        $this->assertSame($type, $process['error_type']);
        $this->assertStringNotContainsString('PRIVATE', json_encode($records->getArrayCopy()));
        $this->assertSame([], Storage::disk('invoice_temp')->allFiles());
    }

    /** @return \ArrayObject<int, array<string, mixed>> */
    private function capture(): \ArrayObject
    {
        $records = new \ArrayObject;
        Log::shouldReceive('info')->andReturnUsing(function (string $message, array $data = []) use ($records): void {
            if ($message === 'performance_stage') {
                $records->append($data);
            }
        });

        return $records;
    }
}
