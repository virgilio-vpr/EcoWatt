<?php

namespace App\Http\Middleware;

use App\Services\PerformanceMetrics;
use App\Services\PerformanceStage;
use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;
use Throwable;

class MeasurePerformance
{
    public function __construct(private readonly PerformanceMetrics $metrics) {}

    /** @param Closure(Request): Response $next */
    public function handle(Request $request, Closure $next): Response
    {
        if (! $request->is('api/*')) {
            return $next($request);
        }
        $span = $this->metrics->start(PerformanceStage::Http);
        $error = null;
        $response = null;
        try {
            return $response = $next($request);
        } catch (Throwable $exception) {
            $error = $exception;
            throw $exception;
        } finally {
            $this->metrics->finish($span, $error, $response?->getStatusCode());
        }
    }
}
