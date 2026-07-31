<#
.SYNOPSIS
    Windows task runner. Mirrors the Makefile so both platforms run identical code paths.

.EXAMPLE
    .\tasks.ps1 check
    .\tasks.ps1 test
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet('help', 'install', 'check', 'lint', 'format', 'format-check', 'typecheck', 'test',
                 'audit', 'status', 'generate', 'freeze', 'verify', 'run',
                 'evaluate', 'report', 'clean')]
    [string]$Task = 'help'
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot

# Prefer the project venv so the task runner cannot accidentally use a different
# interpreter than the one the dependencies were pinned into.
$Py = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $Py)) { $Py = 'python' }

function Invoke-Step {
    param([string]$Name, [scriptblock]$Body)
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Body
    if ($LASTEXITCODE -ne 0) { throw "$Name failed (exit $LASTEXITCODE)" }
}

switch ($Task) {
    'help' {
        Write-Host "Tasks:" -ForegroundColor Cyan
        @(
            @{ n = 'install';   d = 'Install the package with dev extras' }
            @{ n = 'check';     d = 'Everything CI runs, in CI order' }
            @{ n = 'lint';      d = 'Static lint' }
            @{ n = 'format';    d = 'Auto-format (modifies files)' }
            @{ n = 'format-check'; d = 'Formatting check CI runs (no changes)' }
            @{ n = 'typecheck'; d = 'Strict type check' }
            @{ n = 'test';      d = 'Run the test suite' }
            @{ n = 'audit';     d = 'Run only publication-gating audit checks' }
            @{ n = 'status';    d = 'Show which pipeline steps are implemented' }
            @{ n = 'generate';  d = '[step 3-7] Generate corpus and instructions' }
            @{ n = 'freeze';    d = '[step 8] Freeze the corpus' }
            @{ n = 'verify';    d = '[step 8] Verify a frozen dataset' }
            @{ n = 'run';       d = '[step 10-13] Execute one experiment arm' }
            @{ n = 'evaluate';  d = '[step 9] Score stored responses' }
            @{ n = 'report';    d = '[step 14] Compute metrics and render report' }
            @{ n = 'clean';     d = 'Remove caches and the working area' }
        ) | ForEach-Object { "  {0,-12} {1}" -f $_.n, $_.d }
    }
    'install'   { Invoke-Step 'install'   { & $Py -m pip install -e ".[dev]" } }
    'lint'      { Invoke-Step 'lint'      { & $Py -m ruff check . } }
    'format'    { Invoke-Step 'format'    { & $Py -m ruff format .; & $Py -m ruff check --fix . } }
    'format-check' { Invoke-Step 'format-check' { & $Py -m ruff format --check . } }
    'typecheck' { Invoke-Step 'typecheck' { & $Py -m mypy } }
    'test'      { Invoke-Step 'test'      { & $Py -m pytest } }
    'audit'     { Invoke-Step 'audit'     { & $Py -m pytest -m audit } }
    'status'    { & $Py -m svgbench.cli status }
    'check' {
        # MUST stay identical to .github/workflows/ci.yml, in the same order. This
        # previously omitted the format check, so it passed while CI failed on every
        # push - a local signal that could not detect what CI tests.
        Invoke-Step 'lint'         { & $Py -m ruff check . }
        Invoke-Step 'format-check' { & $Py -m ruff format --check . }
        Invoke-Step 'typecheck'    { & $Py -m mypy }
        Invoke-Step 'test'         { & $Py -m pytest }
        Invoke-Step 'audit'        { & $Py -m pytest -m audit }
    }
    'clean' {
        foreach ($d in '.pytest_cache', '.ruff_cache', '.mypy_cache') {
            $p = Join-Path $Root $d
            if (Test-Path $p) { Remove-Item -Recurse -Force $p }
        }
        Get-ChildItem -Path $Root -Recurse -Directory -Filter '__pycache__' |
            Remove-Item -Recurse -Force
        $gen = Join-Path $Root 'data\generated'
        if (Test-Path $gen) { Get-ChildItem $gen | Remove-Item -Recurse -Force }
        Write-Host "cleaned" -ForegroundColor Green
    }
    default { & $Py -m svgbench.cli $Task }
}
