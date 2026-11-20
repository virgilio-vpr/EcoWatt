<?php

namespace App\Invoices\Ocr;

interface InvoiceOcr
{
    public function extract(string $path): string;
}
