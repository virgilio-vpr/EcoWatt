<?php

namespace Tests;

use Illuminate\Foundation\Testing\TestCase as BaseTestCase;

abstract class TestCase extends BaseTestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        config(['ocr.lock_path' => sys_get_temp_dir().'/ecowatt-ocr-tests-'.getmypid().'.lock']);
    }

    protected function tearDown(): void
    {
        $lock = config('ocr.lock_path');
        if (is_string($lock) && str_starts_with($lock, sys_get_temp_dir().'/ecowatt-ocr-tests-') && is_file($lock)) {
            unlink($lock);
        }
        parent::tearDown();
    }
}
