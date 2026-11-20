<?php

namespace App\Invoices\Ocr;

use App\Invoices\Pdf\TemporaryPdfTextExtractor;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use InvalidArgumentException;
use Symfony\Component\Process\Exception\ProcessFailedException;
use Symfony\Component\Process\Exception\ProcessTimedOutException;
use Symfony\Component\Process\Process;
use Throwable;

final class LocalInvoiceOcr implements InvoiceOcr
{
    public function extract(string $path): string
    {
        $disk = Storage::disk(TemporaryPdfTextExtractor::DISK);
        $directory = 'ocr-'.Str::uuid();
        $disk->makeDirectory($directory);
        $work = $disk->path($directory);
        chmod($work, 0700);
        $lock = fopen((string) config('ocr.lock_path'), 'c');
        $deadline = microtime(true) + (int) config('ocr.timeout');
        try {
            if ($lock === false || ! flock($lock, LOCK_EX | LOCK_NB)) {
                throw new InvalidArgumentException('O leitor OCR está ocupado. Tente enviar novamente em instantes.');
            }
            $version = $this->run([(string) config('ocr.tesseract'), '--version'], $deadline, 'engine');
            $pages = 1;
            $pdf = (new \finfo(FILEINFO_MIME_TYPE))->file($path) === 'application/pdf';
            if ($pdf) {
                $info = $this->run([(string) config('ocr.pdfinfo'), $path], $deadline, 'metadata');
                if (preg_match('/^Pages:\s+(\d+)/m', $info, $match) !== 1) {
                    throw new InvalidArgumentException('Não foi possível contar as páginas para OCR.');
                }
                $pages = (int) $match[1];
                if ($pages > (int) config('ocr.max_pages')) {
                    throw new InvalidArgumentException('OCR aceita até 4 páginas por arquivo. Separe as páginas da fatura e envie novamente.');
                }
            }
            $texts = [];
            for ($page = 1; $page <= $pages; $page++) {
                $image = $path;
                if ($pdf) {
                    $base = $work.'/page';
                    $this->run([(string) config('ocr.pdftoppm'), '-f', (string) $page, '-l', (string) $page, '-singlefile', '-r', '300', '-scale-to', (string) config('ocr.max_dimension'), '-png', $path, $base], $deadline, 'render');
                    $image = $base.'.png';
                }
                $size = @getimagesize($image);
                if ($size === false || (int) config('ocr.max_pixels') < $size[0] * $size[1] || max($size[0], $size[1]) > 10000) {
                    throw new InvalidArgumentException('Imagem inválida ou resolução acima do limite de OCR.');
                }
                $texts[] = $this->recognize($image, $work, $deadline);
                if ($pdf) {
                    unlink($image);
                }
            }
            Log::info('invoice_ocr', ['engine' => strtok($version, "\n"), 'pages' => $pages]);

            return implode("\n\f\n", $texts);
        } catch (InvalidArgumentException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            Log::warning('invoice_ocr_failure', ['reason' => 'unexpected_failure', 'exception_class' => $exception::class]);
            throw new InvalidArgumentException('Não foi possível concluir o OCR local. A falha foi registrada para diagnóstico. Tente enviar outra cópia da fatura.');
        } finally {
            $disk->deleteDirectory($directory);
            if (is_resource($lock)) {
                fclose($lock);
            }
        }
    }

    private function recognize(string $image, string $work, float $deadline): string
    {
        $arguments = [(string) config('ocr.tesseract'), $image, 'stdout', '-l', (string) config('ocr.languages'), '--psm', '6', '-c', 'preserve_interword_spaces=1'];
        $text = $this->run($arguments, $deadline, 'recognition');
        if (preg_match('~DADOS\s+DE\s+MEDI[CÇ][AÃ]O~iu', $text, $heading, PREG_OFFSET_CAPTURE) !== 1
            || preg_match('~DESCRI[CÇ][AÃ]O\s+DO\s+FATURAMENTO~iu', $text) !== 1) {
            return $text;
        }

        $manifest = $this->run([(string) config('ocr.python'), __DIR__.'/prepare_enel_tables.py', $image, $work, (string) config('ocr.max_pixels')], $deadline, 'preparation');
        $panels = json_decode($manifest, true, flags: JSON_THROW_ON_ERROR);
        if (! is_array($panels) || $panels === []) {
            return $text;
        }
        if (count($panels) > 6) {
            throw new InvalidArgumentException('O quadro da fatura excedeu o limite de processamento OCR.');
        }
        $blocks = [substr($text, 0, $heading[0][1])];
        foreach ($panels as $panel) {
            if (! is_string($panel) || basename($panel) !== $panel) {
                throw new InvalidArgumentException('Não foi possível preparar os quadros da fatura.');
            }
            $arguments[1] = $work.'/'.$panel;
            $blocks[] = $this->run($arguments, $deadline, 'recognition');
            unlink($work.'/'.$panel);
        }
        Log::info('invoice_ocr_layout', ['layout' => 'enel_panels', 'blocks' => count($panels)]);

        return implode("\n", $blocks);
    }

    /** @param list<string> $arguments */
    private function run(array $arguments, float $deadline, string $stage): string
    {
        $remaining = $deadline - microtime(true);
        if ($remaining <= 0) {
            throw new InvalidArgumentException('A leitura OCR excedeu 40 segundos.');
        }
        $process = new Process(array_merge(['/usr/bin/prlimit', '--as=805306368', '--cpu=40', '--fsize=104857600', '--'], $arguments), null, ['OMP_THREAD_LIMIT' => '1'], null, $remaining);
        try {
            $process->mustRun();
        } catch (ProcessTimedOutException) {
            Log::warning('invoice_ocr_failure', ['stage' => $stage, 'reason' => 'timeout']);

            throw new InvalidArgumentException('A leitura OCR excedeu 40 segundos. Envie apenas as páginas da fatura ou uma imagem mais nítida.');
        } catch (ProcessFailedException) {
            Log::warning('invoice_ocr_failure', ['stage' => $stage, 'reason' => 'process_failed', 'exit_code' => $process->getExitCode()]);

            throw new InvalidArgumentException($stage === 'engine'
                ? 'O motor OCR está indisponível. Confira a instalação do Tesseract e dos idiomas português e inglês.'
                : 'O processamento OCR falhou na etapa de '.match ($stage) {
                    'recognition' => 'reconhecimento',
                    'preparation' => 'preparação da imagem',
                    default => 'leitura do PDF',
                }.'. Tente enviar outra cópia do documento.');
        }

        return $process->getOutput();
    }
}
