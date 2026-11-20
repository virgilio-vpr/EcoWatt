<?php

namespace Tests\Unit;

use App\Invoices\Pdf\PdfPageCounter;
use App\Invoices\Validation\InvoiceUploadValidator;
use Illuminate\Http\UploadedFile;
use Symfony\Component\HttpKernel\Exception\HttpExceptionInterface;
use Tests\TestCase;

class InvoiceImageUploadTest extends TestCase
{
    public function test_real_png_and_jpeg_are_accepted_regardless_of_client_mime_and_count_as_one_page(): void
    {
        $counter = $this->createMock(PdfPageCounter::class);
        $counter->expects($this->never())->method('count');
        $validator = new InvoiceUploadValidator($counter);
        foreach (['invoice.png', 'invoice.jpg'] as $name) {
            $file = new UploadedFile(base_path('tests/Fixtures/ocr/'.$name), 'renamed.pdf', 'application/octet-stream', null, true);
            $validator->validate([$file]);
            $this->assertSame(1, $validator->pageCount($file));
        }
    }

    public function test_an_executable_disguised_as_a_png_is_rejected(): void
    {
        $file = UploadedFile::fake()->createWithContent('invoice.png', 'MZ executable');
        $this->assertRejected($file, 415);
    }

    public function test_oversized_image_dimensions_are_rejected_before_decoding_pixels(): void
    {
        $contents = file_get_contents(base_path('tests/Fixtures/ocr/invoice.png'));
        $contents = substr_replace($contents, pack('N', 20000), 16, 4);
        $this->assertRejected(UploadedFile::fake()->createWithContent('invoice.png', $contents), 413);
    }

    private function assertRejected(UploadedFile $file, int $status): void
    {
        try {
            (new InvoiceUploadValidator($this->createMock(PdfPageCounter::class)))->validate([$file]);
            $this->fail('Invalid image must be rejected.');
        } catch (HttpExceptionInterface $exception) {
            $this->assertSame($status, $exception->getStatusCode());
        }
    }
}
