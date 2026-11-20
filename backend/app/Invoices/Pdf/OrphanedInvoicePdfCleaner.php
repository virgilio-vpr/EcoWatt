<?php

namespace App\Invoices\Pdf;

use Illuminate\Support\Facades\Storage;

final class OrphanedInvoicePdfCleaner
{
    public const ORPHAN_AGE_SECONDS = 3600;

    public function clean(): int
    {
        $disk = Storage::disk(TemporaryPdfTextExtractor::DISK);
        $cutoff = now()->subSeconds(self::ORPHAN_AGE_SECONDS)->timestamp;
        $deleted = 0;
        $orphanDirectories = array_filter($disk->directories(), fn (string $directory): bool => str_starts_with($directory, 'ocr-') && $disk->lastModified($directory) < $cutoff);

        foreach ($disk->allFiles() as $path) {
            if ($disk->lastModified($path) < $cutoff && $disk->delete($path)) {
                $deleted++;
            }
        }

        foreach ($orphanDirectories as $directory) {
            if ($disk->allFiles($directory) === []) {
                $disk->deleteDirectory($directory);
            }
        }

        return $deleted;
    }
}
