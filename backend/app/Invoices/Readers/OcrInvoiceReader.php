<?php

namespace App\Invoices\Readers;

use App\Calculation\Data\ExtractedInvoiceData;

interface OcrInvoiceReader
{
    public function readOcr(string $text): ExtractedInvoiceData;
}
