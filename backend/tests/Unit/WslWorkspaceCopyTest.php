<?php

namespace Tests\Unit;

use Illuminate\Filesystem\Filesystem;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Process\Process;

class WslWorkspaceCopyTest extends TestCase
{
    private string $directory;

    private string $source;

    private string $destination;

    protected function setUp(): void
    {
        parent::setUp();
        $this->directory = sys_get_temp_dir().'/ecowatt-wsl-copy-'.bin2hex(random_bytes(8));
        $this->source = $this->directory.'/original';
        $this->destination = $this->directory.'/linux-copy';
        foreach ([
            '.git/HEAD' => "ref: refs/heads/local\n",
            'docs/PROJECT_SPEC.md' => 'synthetic spec',
            'backend/artisan' => 'synthetic artisan',
            'frontend/package.json' => '{}',
            'docker-compose.yml' => "name: ecowatt\nvolumes: {postgres_data: {}}\n",
            '.env' => "DB_PASSWORD=PRIVATE-ROOT-SECRET\n",
            'backend/.env' => 'APP_KEY=PRIVATE-KEY'."\r\n".'DB_PASSWORD=PRIVATE-PASSWORD'."\r\n"
                .'OCR_TESSERACT="'.$this->source.'/backend/storage/ocr-local/bin/tesseract" # local'."\r\n"
                .'OCR_PYTHON=/usr/bin/python3'."\r\n".'CUSTOM_PATH='.$this->source.'/custom'."\r\n",
            'backend/storage/ocr-local/bin/tesseract' => "#!/bin/sh\nexit 0\n",
            'backend/storage/app/private/backups/restore.sql' => 'PRIVATE SYNTHETIC BACKUP',
            'dirty.txt' => 'uncommitted change',
            'untracked.txt' => 'untracked work',
            'backend/bootstrap/cache/config.php' => 'stale absolute paths',
            'backend/storage/framework/testing/synthetic.txt' => 'old test data',
        ] as $relative => $contents) {
            $path = $this->source.'/'.$relative;
            (new Filesystem)->ensureDirectoryExists(dirname($path));
            file_put_contents($path, $contents);
        }
        chmod($this->source.'/backend/storage/ocr-local/bin/tesseract', 0755);
    }

    protected function tearDown(): void
    {
        (new Filesystem)->deleteDirectory($this->directory);
        parent::tearDown();
    }

    public function test_default_is_a_read_only_plan_and_does_not_disclose_secrets(): void
    {
        $process = $this->runTool();
        $this->assertTrue($process->isSuccessful(), $process->getErrorOutput());
        $result = json_decode($process->getOutput(), true, flags: JSON_THROW_ON_ERROR);
        $this->assertSame('plan', $result['mode']);
        $this->assertSame('none', $result['database_action']);
        $this->assertSame(['OCR_TESSERACT'], $result['ocr_keys_to_remap']);
        $this->assertFileDoesNotExist($this->destination);
        $this->assertStringNotContainsString('PRIVATE', $process->getOutput().$process->getErrorOutput());
    }

    public function test_copy_preserves_local_work_secrets_backup_and_git_and_only_remaps_internal_ocr_paths(): void
    {
        $before = file_get_contents($this->source.'/backend/.env');
        symlink('dirty.txt', $this->source.'/relative-link');
        symlink($this->source.'/untracked.txt', $this->source.'/absolute-link');
        $process = $this->runTool(['--copy', '--source-paused']);
        $this->assertTrue($process->isSuccessful(), $process->getErrorOutput());
        $result = json_decode($process->getOutput(), true);
        $this->assertTrue($result['verified']);
        $this->assertTrue($result['runtime_directories_prepared']);
        $this->assertSame(8, $result['copy_workers']);
        $this->assertDirectoryExists($this->destination.'/backend/storage/framework/views');
        $this->assertSame($before, file_get_contents($this->source.'/backend/.env'));
        $expected = str_replace('OCR_TESSERACT="'.$this->source, 'OCR_TESSERACT="'.$this->destination, $before);
        $this->assertSame($expected, file_get_contents($this->destination.'/backend/.env'));
        foreach (['.git/HEAD', '.env', 'dirty.txt', 'untracked.txt', 'docker-compose.yml', 'backend/storage/app/private/backups/restore.sql'] as $file) {
            $this->assertFileEquals($this->source.'/'.$file, $this->destination.'/'.$file);
        }
        $this->assertSame('uncommitted change', file_get_contents($this->destination.'/relative-link'));
        $this->assertSame($this->destination.'/untracked.txt', readlink($this->destination.'/absolute-link'));
        $this->assertTrue(is_executable($this->destination.'/backend/storage/ocr-local/bin/tesseract'));
        $this->assertSame(0600, fileperms($this->destination.'/backend/.env') & 0777);
        $this->assertSame(0700, fileperms($this->destination) & 0777);
        $this->assertFileDoesNotExist($this->destination.'/backend/bootstrap/cache/config.php');
        $this->assertFileDoesNotExist($this->destination.'/backend/storage/framework/testing/synthetic.txt');
        $this->assertStringNotContainsString('PRIVATE', $process->getOutput().$process->getErrorOutput());
    }

    public function test_copy_requires_explicit_confirmation_that_source_writes_are_paused(): void
    {
        $this->assertFalse($this->runTool(['--copy'])->isSuccessful());
        $this->assertFileDoesNotExist($this->destination);
    }

    public function test_an_existing_destination_is_never_overwritten(): void
    {
        mkdir($this->destination);
        file_put_contents($this->destination.'/keep.txt', 'keep');
        $this->assertFalse($this->runTool(['--copy', '--source-paused'])->isSuccessful());
        $this->assertSame('keep', file_get_contents($this->destination.'/keep.txt'));
        $this->assertFileDoesNotExist($this->destination.'/.env');
    }

    public function test_copy_rejects_pending_originals_git_locks_and_external_links(): void
    {
        foreach (['backend/storage/app/private/invoice-temp/invoice.pdf', '.git/index.lock', 'external-link'] as $blocker) {
            $path = $this->source.'/'.$blocker;
            (new Filesystem)->ensureDirectoryExists(dirname($path));
            if ($blocker === 'external-link') {
                symlink('/usr/bin/python3', $path);
            } else {
                file_put_contents($path, 'synthetic blocker');
            }
            $this->assertFalse($this->runTool(['--copy', '--source-paused'])->isSuccessful());
            $this->assertFileDoesNotExist($this->destination);
            unlink($path);
        }
    }

    public function test_a_destination_inside_the_source_is_rejected(): void
    {
        $this->destination = $this->source.'/nested';
        $this->assertFalse($this->runTool(['--copy', '--source-paused'])->isSuccessful());
        $this->assertDirectoryDoesNotExist($this->destination);
    }

    public function test_a_destination_link_cannot_redirect_the_copy(): void
    {
        symlink($this->directory.'/redirected', $this->destination);
        $this->assertFalse($this->runTool(['--copy', '--source-paused'])->isSuccessful());
        $this->assertDirectoryDoesNotExist($this->directory.'/redirected');
        $this->assertTrue(is_link($this->destination));
    }

    public function test_linked_environment_files_require_manual_review(): void
    {
        rename($this->source.'/backend/.env', $this->source.'/backend/environment-local');
        symlink('environment-local', $this->source.'/backend/.env');
        $this->assertFalse($this->runTool(['--copy', '--source-paused'])->isSuccessful());
        $this->assertDirectoryDoesNotExist($this->destination);
    }

    public function test_an_ocr_root_alias_with_different_case_is_remapped_only_if_it_is_the_same_directory(): void
    {
        $alias = $this->directory.'/ORIGINAL';
        symlink($this->source, $alias);
        $environment = file_get_contents($this->source.'/backend/.env');
        file_put_contents($this->source.'/backend/.env', str_replace('OCR_TESSERACT="'.$this->source, 'OCR_TESSERACT="'.$alias, $environment));
        $process = $this->runTool(['--copy', '--source-paused']);
        $this->assertTrue($process->isSuccessful(), $process->getErrorOutput());
        $copied = file_get_contents($this->destination.'/backend/.env');
        $this->assertStringContainsString('OCR_TESSERACT="'.$this->destination, $copied);
        $this->assertStringContainsString('CUSTOM_PATH='.$this->source, $copied);
    }

    public function test_a_distinct_linux_directory_with_different_case_keeps_its_custom_ocr_path(): void
    {
        $external = $this->directory.'/ORIGINAL';
        mkdir($external);
        $environment = str_replace('OCR_TESSERACT="'.$this->source, 'OCR_TESSERACT="'.$external, file_get_contents($this->source.'/backend/.env'));
        file_put_contents($this->source.'/backend/.env', $environment);
        $process = $this->runTool(['--copy', '--source-paused']);
        $this->assertTrue($process->isSuccessful(), $process->getErrorOutput());
        $this->assertSame($environment, file_get_contents($this->destination.'/backend/.env'));
    }

    public function test_a_source_change_during_copy_invalidates_the_destination(): void
    {
        $script = <<<'PYTHON'
import runpy, sys
from pathlib import Path
module = runpy.run_path(sys.argv[1])
source, destination = Path(sys.argv[2]), Path(sys.argv[3])
copy = module['shutil'].copy2

def copy_and_change(original, copied):
    result = copy(original, copied)
    if Path(original).name == 'dirty.txt':
        Path(original).write_text('changed during copy')
    return result

module['shutil'].copy2 = copy_and_change
plan, files, directories = module['prepare'](source, destination)
try:
    module['copy_workspace'](source, destination, plan, files, directories)
except module['CopyError']:
    print('copy_rejected')
else:
    sys.exit(1)
PYTHON;
        $process = new Process(['python3', '-B', '-c', $script, dirname(__DIR__, 3).'/docs/wsl_workspace.py', $this->source, $this->destination]);
        $process->setTimeout(30);
        $process->mustRun();
        $this->assertStringContainsString('copy_rejected', $process->getOutput());
        $this->assertSame('changed during copy', file_get_contents($this->source.'/dirty.txt'));
        $this->assertSame('uncommitted change', file_get_contents($this->destination.'/dirty.txt'));
    }

    /** @param list<string> $options */
    private function runTool(array $options = []): Process
    {
        $process = new Process(array_merge([
            'python3', dirname(__DIR__, 3).'/docs/wsl_workspace.py',
            '--source', $this->source, '--destination', $this->destination,
        ], $options));
        $process->setTimeout(30);
        $process->run();

        return $process;
    }
}
