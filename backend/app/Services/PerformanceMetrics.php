<?php

namespace App\Services;

use Illuminate\Database\Events\QueryExecuted;
use Illuminate\Support\Facades\Log;
use Illuminate\Validation\ValidationException;
use Symfony\Component\Process\Exception\ProcessFailedException;
use Symfony\Component\Process\Exception\ProcessTimedOutException;
use Throwable;

final class PerformanceMetrics
{
    /** @var array<string, array<string, mixed>> */
    private array $spans = [];

    /** @template T
     * @param  callable(): T  $operation
     * @return T
     */
    public function measure(PerformanceStage $stage, callable $operation): mixed
    {
        $span = $this->start($stage);
        $error = null;
        try {
            return $operation();
        } catch (Throwable $exception) {
            $error = $exception;
            throw $exception;
        } finally {
            $this->finish($span, $error);
        }
    }

    public function start(PerformanceStage $stage, ?int $attempt = null, ?float $queueWaitMs = null): ?string
    {
        if (! config('performance.enabled')) {
            return null;
        }
        $id = bin2hex(random_bytes(8));
        $root = $this->spans === [] ? null : reset($this->spans);
        $this->spans[$id] = [
            'stage' => $stage->value,
            'trace' => $root['trace'] ?? $id,
            'started' => hrtime(true),
            'cpu' => $this->cpu(),
            'child_cpu' => $this->cpu(1),
            'attempt' => max(1, $attempt ?? $root['attempt'] ?? 1),
            'queue_wait_ms' => $queueWaitMs,
            'queries' => 0,
            'query_ms' => 0.0,
            'query_groups' => [],
        ];

        return $id;
    }

    public function finish(?string $id, ?Throwable $error = null, ?int $httpStatus = null): void
    {
        if ($id === null || ! isset($this->spans[$id])) {
            return;
        }
        $span = $this->spans[$id];
        unset($this->spans[$id]);
        $data = [
            'stage' => $span['stage'], 'trace' => $span['trace'],
            'duration_ms' => round((hrtime(true) - $span['started']) / 1e6, 3),
            'cpu_ms' => $this->difference($this->cpu(), $span['cpu']),
            'child_cpu_ms' => $this->difference($this->cpu(1), $span['child_cpu']),
            'php_peak_bytes' => memory_get_peak_usage(true),
            'child_peak_rss_kib' => function_exists('getrusage') ? (getrusage(1)['ru_maxrss'] ?? null) : null,
            'attempt' => $span['attempt'], 'queue_wait_ms' => $span['queue_wait_ms'],
            'outcome' => $error !== null || ($httpStatus !== null && $httpStatus >= 400) ? 'error' : 'ok',
            'error_type' => match (true) {
                $error instanceof ValidationException => 'validation',
                $error instanceof ProcessTimedOutException => 'process_timeout',
                $error instanceof ProcessFailedException => 'process_failure',
                $error !== null => 'other',
                default => null,
            },
            'http_status' => $httpStatus, 'method' => $span['method'] ?? null,
            'queries' => $span['queries'], 'query_ms' => round($span['query_ms'], 3),
            'query_groups' => $span['query_groups'],
        ];
        try {
            Log::info('performance_stage', $data);
        } catch (Throwable) {
            // A metrics sink must not interrupt invoice processing or temporary file cleanup.
        }
    }

    public function extractionMethod(string $method): void
    {
        if (! in_array($method, ['native', 'ocr', 'hybrid'], true)) {
            return;
        }
        foreach ($this->spans as &$span) {
            if ($span['stage'] === PerformanceStage::DocumentRead->value) {
                $span['method'] = $method;
            }
        }
    }

    public function query(QueryExecuted $query): void
    {
        if ($this->spans === []) {
            return;
        }
        $fingerprint = hash('sha256', $query->sql);
        $table = 'other';
        foreach (['regulatory_parameters', 'tariffs', 'invoice_items', 'invoices', 'reports', 'simulations', 'jobs'] as $candidate) {
            if (preg_match('/\b'.$candidate.'\b/i', $query->sql) === 1) {
                $table = $candidate;
                break;
            }
        }
        foreach ($this->spans as &$span) {
            $span['queries']++;
            $span['query_ms'] += $query->time;
            if (isset($span['query_groups'][$fingerprint]) || count($span['query_groups']) < 64) {
                $group = $span['query_groups'][$fingerprint] ?? ['table' => $table, 'count' => 0, 'time_ms' => 0.0];
                $group['count']++;
                $group['time_ms'] = round($group['time_ms'] + $query->time, 3);
                $span['query_groups'][$fingerprint] = $group;
            }
        }
    }

    private function cpu(int $children = 0): ?float
    {
        $usage = function_exists('getrusage') ? getrusage($children) : false;

        return $usage === false ? null : ($usage['ru_utime.tv_sec'] + $usage['ru_stime.tv_sec']) * 1000
            + ($usage['ru_utime.tv_usec'] + $usage['ru_stime.tv_usec']) / 1000;
    }

    private function difference(?float $end, ?float $start): ?float
    {
        return $end === null || $start === null ? null : round(max(0, $end - $start), 3);
    }
}
