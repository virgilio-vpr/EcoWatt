param([string]$TestFilter = 'windows_isolation')
$ErrorActionPreference = 'Stop'
$profileName = 'EcoWatt.Synthetic.' + [guid]::NewGuid().ToString('N')
$previousSid = $env:ECOWATT_SYNTHETIC_PROFILE_SID
$previousFlag = $env:ECOWATT_WINDOWS_ISOLATION_TESTS
$previousSource = $env:ECOWATT_TEST_SOURCE_PYTHON
$created = $false
try {
    $env:ECOWATT_SYNTHETIC_PROFILE_SID = & "$PSScriptRoot/windows_profile.ps1" -Action create -Name $profileName
    $created = $true
    $env:ECOWATT_WINDOWS_ISOLATION_TESTS = '1'
    # Executar também o controlador fora da identidade MSIX: um Python Store
    # pode acrescentar capacidade de seu pacote aos filhos, mesmo suspensos.
    $sourceRuntime = & .\.venv\Scripts\python.exe -c 'import sys; print(sys.base_prefix)'
    if ($LASTEXITCODE) { throw 'source_runtime' }
    $env:ECOWATT_TEST_SOURCE_PYTHON = $sourceRuntime
    $workspace = (Get-Location).Path
    $controller = Join-Path $workspace '.local-analysis/pytest/isolation-controller'
    [void](New-Item -ItemType Directory -Force -Path $controller)
    foreach ($filename in @('python.exe','python313.dll','python3.dll','vcruntime140.dll','vcruntime140_1.dll')) {
        $sourceFile = Join-Path $sourceRuntime $filename
        if (Test-Path -LiteralPath $sourceFile) {
            Copy-Item -LiteralPath $sourceFile -Destination (Join-Path $controller $filename) -Force
        }
    }
    foreach ($directory in @('Lib','DLLs')) {
        $sourceDirectory = Join-Path $sourceRuntime $directory
        $targetDirectory = Join-Path $controller $directory
        if (-not (Test-Path -LiteralPath $targetDirectory)) {
            Copy-Item -LiteralPath $sourceDirectory -Destination $targetDirectory -Recurse
        }
    }
    $env:ECOWATT_TEST_SOURCE_PYTHON = $controller
    $runtimePaths = @((Join-Path $controller 'Lib'), (Join-Path $controller 'DLLs'),
        $controller, (Join-Path $workspace '.venv/Lib/site-packages'),
        (Join-Path $workspace 'src'), $workspace)
    [IO.File]::WriteAllLines((Join-Path $controller 'python313._pth'), $runtimePaths, [Text.UTF8Encoding]::new($false))
    & (Join-Path $controller 'python.exe') -m pytest tests/test_windows_isolation.py -q --basetemp=.local-analysis/pytest/isolation -k $TestFilter
    $testExit = $LASTEXITCODE
} finally {
    $env:ECOWATT_SYNTHETIC_PROFILE_SID = $previousSid
    $env:ECOWATT_WINDOWS_ISOLATION_TESTS = $previousFlag
    $env:ECOWATT_TEST_SOURCE_PYTHON = $previousSource
    if ($created) { & "$PSScriptRoot/windows_profile.ps1" -Action delete -Name $profileName }
}
exit $testExit
