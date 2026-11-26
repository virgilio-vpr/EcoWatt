<?php

namespace App\Services;

enum PerformanceStage: string
{
    case Http = 'http';
    case UploadValidation = 'upload_validation';
    case PageCount = 'page_count';
    case NativeExtraction = 'native_extraction';
    case DocumentRead = 'document_read';
    case Ocr = 'ocr';
    case OcrEngine = 'ocr_engine';
    case OcrMetadata = 'ocr_metadata';
    case Render = 'render';
    case Preparation = 'preparation';
    case Recognition = 'recognition';
    case Persistence = 'persistence';
    case Calculation = 'calculation';
    case Pdf = 'pdf';
    case Job = 'job';
}
