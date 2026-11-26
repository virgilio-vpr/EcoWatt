<?php

namespace App\Providers;

use App\Calculation\Contracts\ReportCalculationEngine;
use App\Calculation\Services\SimulationReportCalculationEngine;
use App\Invoices\Ocr\InvoiceOcr;
use App\Invoices\Ocr\LocalInvoiceOcr;
use App\Invoices\Pdf\PdfPageCounter;
use App\Invoices\Pdf\PdfTextParser;
use App\Invoices\Pdf\SmalotPdfPageCounter;
use App\Invoices\Pdf\SmalotPdfTextParser;
use App\Invoices\Readers\EnelInvoiceReader;
use App\Invoices\Readers\InvoiceReaderResolver;
use App\Services\PerformanceMetrics;
use App\Services\PerformanceStage;
use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Database\Events\QueryExecuted;
use Illuminate\Http\Request;
use Illuminate\Queue\Events\JobExceptionOccurred;
use Illuminate\Queue\Events\JobProcessed;
use Illuminate\Queue\Events\JobProcessing;
use Illuminate\Queue\Jobs\DatabaseJob;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Event;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        $this->app->singleton(PerformanceMetrics::class);
        $this->app->singleton(InvoiceReaderResolver::class, function (): InvoiceReaderResolver {
            return new InvoiceReaderResolver([new EnelInvoiceReader]);
        });
        $this->app->bind(ReportCalculationEngine::class, SimulationReportCalculationEngine::class);
        $this->app->bind(InvoiceOcr::class, LocalInvoiceOcr::class);
        $this->app->bind(PdfTextParser::class, SmalotPdfTextParser::class);
        $this->app->bind(PdfPageCounter::class, SmalotPdfPageCounter::class);
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        DB::listen(fn (QueryExecuted $query) => app(PerformanceMetrics::class)->query($query));
        $jobSpans = [];
        Event::listen(JobProcessing::class, function (JobProcessing $event) use (&$jobSpans): void {
            $wait = $event->job instanceof DatabaseJob
                ? max(0, microtime(true) - $event->job->getJobRecord()->available_at) * 1000
                : null;
            $jobSpans[spl_object_id($event->job)] = app(PerformanceMetrics::class)->start(
                PerformanceStage::Job, $event->job->attempts(), $wait,
            );
        });
        $finishJob = function (JobProcessed|JobExceptionOccurred $event) use (&$jobSpans): void {
            $key = spl_object_id($event->job);
            app(PerformanceMetrics::class)->finish($jobSpans[$key] ?? null, $event instanceof JobExceptionOccurred ? $event->exception : null);
            unset($jobSpans[$key]);
        };
        Event::listen(JobProcessed::class, $finishJob);
        Event::listen(JobExceptionOccurred::class, $finishJob);

        RateLimiter::for('api', function (Request $request) {
            return Limit::perMinute(60)->by($request->user()?->id ?: $request->ip());
        });

        RateLimiter::for('auth', function (Request $request) {
            return Limit::perMinute(5)->by($request->ip());
        });

        RateLimiter::for('verification_codes', function (Request $request) {
            return Limit::perMinute(3)->by($request->user()?->id ?: $request->ip());
        });

        RateLimiter::for('uploads', function (Request $request) {
            return Limit::perMinute(10)->by($request->user()?->id ?: $request->ip());
        });

        RateLimiter::for('invoice_imports', function (Request $request) {
            return Limit::perMinute(30)->by($request->user()?->id ?: $request->ip());
        });

        RateLimiter::for('leads', function (Request $request) {
            return Limit::perMinute(5)->by($request->ip());
        });
    }
}
