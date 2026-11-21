<?php

namespace App\Invoices\Pdf;

use App\Services\PerformanceMetrics;
use App\Services\PerformanceStage;
use Smalot\PdfParser\Config;
use Smalot\PdfParser\Parser;

final class SmalotPdfTextParser implements PdfTextParser
{
    private const DECODE_MEMORY_LIMIT = 104_857_600;

    public function extract(string $path): string
    {
        return app(PerformanceMetrics::class)->measure(PerformanceStage::NativeExtraction, function () use ($path) {
            $config = new Config;
            $config->setDecodeMemoryLimit(self::DECODE_MEMORY_LIMIT);

            return (new Parser([], $config))->parseFile($path)->getText();
        });
    }
}
