# Verify the installation contents and on-disk inference of a Tauri/NSIS
# release candidate on a fresh Windows runner.
# UI-click and disconnected-PC validation still require a human tester.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallerPath,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{64}$')]
    [string]$ExpectedModelSha256,

    [string]$InstallDir = "C:\SilabsHumanizerAcceptance"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$setup = (Resolve-Path -LiteralPath $InstallerPath).Path
if (Test-Path -LiteralPath $InstallDir) {
    throw "Test install path already exists: $InstallDir. Refusing to overwrite."
}

Write-Host "Installing NSIS candidate into $InstallDir..."
# NSIS /D must be the final argument. No quotes and no spaces in this test path.
$arguments = "/S /D=$InstallDir"
$process = Start-Process -FilePath $setup -ArgumentList $arguments -Wait -PassThru
if ($process.ExitCode -ne 0) {
    throw "Silent NSIS install failed with exit code $($process.ExitCode)"
}
if (-not (Test-Path -LiteralPath $InstallDir -PathType Container)) {
    throw "NSIS returned success but installation directory is missing."
}

$model = Join-Path $InstallDir "model\qwen3-1.7b.gguf"
$bridge = Join-Path $InstallDir "bridge\silabs-humanizer-bridge.exe"
$manifest = Join-Path $InstallDir "model\manifest.json"
foreach ($item in @($model, $bridge, $manifest)) {
    if (-not (Test-Path -LiteralPath $item -PathType Leaf)) {
        throw "Required bundled resource not installed: $item"
    }
}

$appExe = @(Get-ChildItem -LiteralPath $InstallDir -Filter "*humanizer*.exe" -File |
    Where-Object { $_.Name -notmatch '(?i)(uninstall|bridge|setup)' })
if ($appExe.Count -lt 1) {
    throw "Tauri desktop executable is missing from installed folder."
}

$hash = (Get-FileHash -LiteralPath $model -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne $ExpectedModelSha256.ToLowerInvariant()) {
    throw "Installed GGUF hash mismatch: $hash"
}
$metadata = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
if ($metadata.model_sha256.ToLowerInvariant() -ne $hash) {
    throw "Bundled model manifest does not match actual installed weights."
}
Write-Host "PASS: Tauri desktop and all local resources installed, model integrity verified."

$workspace = Join-Path $env:RUNNER_TEMP "humanizer-installed-check"
New-Item -ItemType Directory -Force -Path $workspace | Out-Null

# A system Python is used ONLY to produce/inspect fixtures in CI. All bridge
# operations below use the executable from the installed product, not Python.
$source = Join-Path $workspace "original.docx"
$target = Join-Path $workspace "humanized.docx"
$sourceTxt = Join-Path $workspace "original.txt"
$targetTxt = Join-Path $workspace "humanized.txt"
$env:HUMANIZER_FIXTURE_DOCX = $source
python -c "import os; from docx import Document; d=Document(); d.add_heading('Acceptance Test',1); d.add_paragraph('This sentences is not written clearly.'); d.add_paragraph('Smith (2024) reported 67.4% adoption.'); d.save(os.environ['HUMANIZER_FIXTURE_DOCX'])"
if ($LASTEXITCODE -ne 0) { throw "Failed to create independent DOCX fixture." }

$sourceSha = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()

function Invoke-InstalledBridge([hashtable] $request) {
    $json = $request | ConvertTo-Json -Compress -Depth 6
    $stdout = ($json | & $bridge) -join ""
    if ($LASTEXITCODE -ne 0) {
        throw "Bundled Python bridge crashed (exit $LASTEXITCODE)."
    }
    if ([string]::IsNullOrWhiteSpace($stdout)) {
        throw "Bundled Python bridge produced no response."
    }
    $reply = $stdout | ConvertFrom-Json
    if (-not $reply.ok) {
        throw "Bundled Python bridge rejected operation: $($reply.error)"
    }
    return $reply.data
}

$checks = Invoke-InstalledBridge @{
    action = "diagnostics"
    model_path = $model
}
if (-not $checks.components_present -or -not $checks.gguf_header_valid) {
    throw "Installed offline diagnostic probe failed: $($checks.issues -join '; ')"
}
Write-Host "PASS: Offline setup diagnostic reports bundled model and runtime."

$opened = Invoke-InstalledBridge @{
    action = "open"
    path = $source
}
if ($opened.blocks.Count -ne 3) {
    throw "Installed bridge parsed an unexpected DOCX structure."
}
if (-not $opened.fingerprint) {
    throw "Source integrity fingerprint was not returned."
}

$rewrite = Invoke-InstalledBridge @{
    action = "rewrite"
    path = $source
    fingerprint = $opened.fingerprint
    index = 1
    mode = "grammar"
    backend = "gguf"
    model_path = $model
}
if (-not $rewrite.passed -or [string]::IsNullOrWhiteSpace($rewrite.proposal)) {
    throw "Installed local Qwen inference did not return an acceptable suggestion."
}
Write-Host "PASS: Installed frozen GGUF runtime generated a grammar revision."
Write-Host "Proposal: $($rewrite.proposal)"

$export = Invoke-InstalledBridge @{
    action = "export"
    path = $source
    fingerprint = $opened.fingerprint
    destination = $target
    revisions = @{
        "1" = $rewrite.proposal
    }
}
if ($export.revised_count -ne 1 -or -not (Test-Path -LiteralPath $target)) {
    throw "Installed DOCX export did not produce a revised file."
}
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sourceSha) {
    throw "Original DOCX changed during rewrite/export."
}

$env:HUMANIZER_EXPORT_DOCX = $target
python -c "import os; from docx import Document; a=Document(os.environ['HUMANIZER_EXPORT_DOCX']); assert a.paragraphs[0].style.name=='Heading 1'; assert a.paragraphs[2].text=='Smith (2024) reported 67.4% adoption.'; assert len(a.paragraphs)==3; print('PASS: exported DOCX opens and preserves heading and citation paragraph')"
if ($LASTEXITCODE -ne 0) {
    throw "Exported Word document validation failed."
}

[IO.File]::WriteAllText($sourceTxt, "This original sentence needs work.", [Text.UTF8Encoding]::new($false))
$openedTxt = Invoke-InstalledBridge @{
    action = "open"
    path = $sourceTxt
}
$null = Invoke-InstalledBridge @{
    action = "export"
    path = $sourceTxt
    fingerprint = $openedTxt.fingerprint
    destination = $targetTxt
    revisions = @{ "0" = "This sentence is clearer." }
}
if ([IO.File]::ReadAllText($targetTxt) -ne "This sentence is clearer.") {
    throw "Installed TXT import/export failed."
}
if ([IO.File]::ReadAllText($sourceTxt) -ne "This original sentence needs work.") {
    throw "Original TXT was overwritten."
}

Write-Host "PASS: NSIS install + local Qwen rewrite + DOCX/TXT export + originals unchanged."
Write-Warning "Graphical UI, keyboard interactions and physically disconnected installation remain MANUAL acceptance checks."
