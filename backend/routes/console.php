<?php

use App\Console\Commands\PurgeExpiredSimulations;
use App\Invoices\InvoiceDocumentReader;
use App\Invoices\Pdf\OrphanedInvoicePdfCleaner;
use App\Invoices\Readers\EnelInvoiceReader;
use App\Invoices\Validation\InvoiceUploadValidator;
use Illuminate\Foundation\Inspiring;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Schedule;
use Illuminate\Validation\ValidationException;
use Symfony\Component\HttpKernel\Exception\HttpExceptionInterface;

Artisan::command('inspire', function () {
    $this->comment(Inspiring::quote());
})->purpose('Display an inspiring quote');

Artisan::command('invoices:clean-temporary-files', function (OrphanedInvoicePdfCleaner $cleaner) {
    $this->info("Arquivos temporários órfãos removidos: {$cleaner->clean()}.");
})->purpose('Remove temporary invoice files older than one hour');

Schedule::command('invoices:clean-temporary-files')->daily();
Schedule::command(PurgeExpiredSimulations::class)->daily();
Schedule::command('tariffs:fetch-aneel')->dailyAt('04:00')->withoutOverlapping(10);

Artisan::command('invoices:inspect {file : Caminho de uma fatura ENEL em PDF, PNG ou JPEG}', function (
    InvoiceDocumentReader $reader,
    InvoiceUploadValidator $validator,
) {
    $path = realpath($this->argument('file'));
    if ($path === false || ! is_file($path)) {
        $this->error('Arquivo não encontrado.');

        return 1;
    }
    try {
        $file = new UploadedFile($path, basename($path), null, null, true);
        $validator->validate([$file]);
        $invoice = $reader->read(file_get_contents($path), app(EnelInvoiceReader::class));
        $sum = '0.00';
        foreach ($invoice->items as $item) {
            $sum = bcadd($sum, $item->amount, 2);
        }
        $this->line(json_encode(['invoice' => $invoice, 'item_sum' => $sum, 'difference' => bcsub($sum, $invoice->totalPaid, 2)], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR));

        return bccomp($sum, $invoice->totalPaid, 2) === 0 ? 0 : 2;
    } catch (ValidationException $exception) {
        $this->error(json_encode($exception->errors(), JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR));
    } catch (InvalidArgumentException|HttpExceptionInterface $exception) {
        $this->error($exception->getMessage());
    }

    return 1;
})->purpose('Conferir dados e fechamento de uma fatura ENEL sem salvar no banco');
