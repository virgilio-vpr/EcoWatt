<?php

return [
    'python' => env('OCR_PYTHON', '/usr/bin/python3'),
    'tesseract' => env('OCR_TESSERACT', 'tesseract'),
    'pdftoppm' => env('OCR_PDFTOPPM', 'pdftoppm'),
    'pdfinfo' => env('OCR_PDFINFO', 'pdfinfo'),
    'lock_path' => env('OCR_LOCK_PATH', storage_path('app/private/invoice-ocr.lock')),
    'languages' => 'por+eng',
    'timeout' => 40,
    'max_pages' => 4,
    'max_dimension' => 4096,
    'max_pixels' => 20000000,
];
