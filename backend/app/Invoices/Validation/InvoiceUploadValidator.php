<?php

namespace App\Invoices\Validation;

use App\Invoices\Pdf\PdfPageCounter;
use App\Services\PerformanceMetrics;
use App\Services\PerformanceStage;
use Illuminate\Http\UploadedFile;
use Illuminate\Validation\ValidationException;
use Symfony\Component\HttpKernel\Exception\HttpException;
use Symfony\Component\HttpKernel\Exception\UnsupportedMediaTypeHttpException;
use Throwable;

final class InvoiceUploadValidator
{
    public const int MIN_FILES = 1;

    public const int MAX_FILES = 12;

    public const int MAX_FILE_BYTES = 20 * 1024 * 1024;

    public const int MAX_TOTAL_BYTES = 120 * 1024 * 1024;

    public const int MAX_PAGES = 600;

    public function __construct(private readonly PdfPageCounter $pageCounter) {}

    /**
     * @param  list<UploadedFile>  $files
     */
    public function validate(array $files): void
    {
        app(PerformanceMetrics::class)->measure(PerformanceStage::UploadValidation, fn () => $this->validateFiles($files));
    }

    private function validateFiles(array $files): void
    {
        $fileCount = count($files);
        if ($fileCount < self::MIN_FILES || $fileCount > self::MAX_FILES) {
            throw ValidationException::withMessages([
                'invoices' => 'Envie de 1 a 12 faturas em PDF, PNG ou JPEG.',
            ]);
        }

        $totalBytes = 0;
        foreach ($files as $index => $file) {
            if (! $file instanceof UploadedFile) {
                throw ValidationException::withMessages([
                    "invoices.{$index}" => 'Não foi possível ler o arquivo enviado.',
                ]);
            }

            $size = $file->getSize();
            if (! is_int($size) || $size < 0) {
                throw ValidationException::withMessages([
                    "invoices.{$index}" => 'Não foi possível ler o arquivo enviado.',
                ]);
            }

            if ($size > self::MAX_FILE_BYTES) {
                throw new HttpException(413, 'Cada fatura deve ter no máximo 20 MB.');
            }

            $totalBytes += $size;
            if ($totalBytes > self::MAX_TOTAL_BYTES) {
                throw new HttpException(413, 'O conjunto de faturas deve ter no máximo 120 MB.');
            }
        }

        foreach ($files as $index => $file) {
            if (! $this->hasPdfSignature($file) && ! $this->hasImageSignature($file)) {
                throw new UnsupportedMediaTypeHttpException("O arquivo de índice {$index} não é um PDF, PNG ou JPEG válido.");
            }
        }

        $totalPages = 0;
        foreach ($files as $index => $file) {
            try {
                $totalPages += $this->pageCount($file);
            } catch (Throwable) {
                throw ValidationException::withMessages([
                    "invoices.{$index}" => 'Não foi possível ler as páginas do PDF enviado.',
                ]);
            }

            if ($totalPages > self::MAX_PAGES) {
                throw new HttpException(413, 'O conjunto de faturas deve ter no máximo 600 páginas.');
            }
        }
    }

    public function pageCount(UploadedFile $file): int
    {
        return app(PerformanceMetrics::class)->measure(PerformanceStage::PageCount, function () use ($file) {
            return $this->hasImageSignature($file) ? 1 : $this->pageCounter->count($file->getRealPath());
        });
    }

    private function hasImageSignature(UploadedFile $file): bool
    {
        $path = $file->getRealPath();
        if ($path === false) {
            return false;
        }
        $mime = (new \finfo(FILEINFO_MIME_TYPE))->file($path);
        if (! in_array($mime, ['image/png', 'image/jpeg'], true)) {
            return false;
        }
        $size = @getimagesize($path);
        if ($size === false || ! in_array($size[2], [IMAGETYPE_PNG, IMAGETYPE_JPEG], true)) {
            return false;
        }
        if (min($size[0], $size[1]) < 300 || max($size[0], $size[1]) > 10000 || $size[0] * $size[1] > 20000000) {
            throw new HttpException(413, 'Imagens devem ter ao menos 300 pixels por lado, até 10.000 por lado e até 20 megapixels.');
        }

        return true;
    }

    private function hasPdfSignature(UploadedFile $file): bool
    {
        $path = $file->getRealPath();
        if ($path === false) {
            return false;
        }

        $mimeType = (new \finfo(FILEINFO_MIME_TYPE))->file($path);
        $handle = fopen($path, 'rb');
        if ($handle === false) {
            return false;
        }

        try {
            $prefix = fread($handle, 1024);
        } finally {
            fclose($handle);
        }

        return $mimeType === 'application/pdf' && is_string($prefix) && preg_match('/%PDF-\d\.\d/', $prefix) === 1;
    }
}
