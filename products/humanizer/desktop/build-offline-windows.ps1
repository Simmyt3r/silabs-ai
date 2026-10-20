# Build Silabs Humanizer as a self-contained offline Windows NSIS installer.
# Build-time internet may be needed for developer dependencies and packaging tools.
# The installer will include the model, bridge and WebView2 offline setup.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ModelPath,
    [Parameter(Mandatory=$true)]
    [ValidatePattern('^[0-9a-fA-F]{64}$')][string]$ModelSha256,
    [Parameter(Mandatory=$true)][switch]$LicenseReviewed,
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-Exit([string]$Step) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE."
    }
}

if ($PSVersionTable.PSEdition -eq "Core" -and -not $IsWindows) {
    throw "This packaging script must run on Windows."
}
if (-not $LicenseReviewed) {
    throw "Review all redistribution licences, then pass -LicenseReviewed."
}

$Root = (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
$Tauri = Join-Path $PSScriptRoot "src-tauri"
$Assets = Join-Path $Tauri "release-assets"
$PyInstallerWork = Join-Path $PSScriptRoot "build/pyinstaller"
$Entrypoint = Join-Path $Root "products/humanizer/service/bridge_executable.py"
$Config = Join-Path $Tauri "tauri.release.conf.json"

$Model = (Resolve-Path -LiteralPath $ModelPath).Path
if ([IO.Path]::GetExtension($Model).ToLowerInvariant() -ne ".gguf") {
    throw "A verified local .gguf model file is required."
}
$ModelInfo = Get-Item -LiteralPath $Model
if ($ModelInfo.Length -lt 500MB) {
    throw "GGUF is unexpectedly small; refusing an incomplete model file."
}

$Stream = [IO.File]::OpenRead($Model)
try {
    $Signature = New-Object byte[] 4
    if ($Stream.Read($Signature, 0, 4) -ne 4 -or
        [Text.Encoding]::ASCII.GetString($Signature) -ne "GGUF") {
        throw "Selected file does not have a GGUF header."
    }
} finally { $Stream.Dispose() }

$ActualHash = (Get-FileHash -LiteralPath $Model -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ActualHash -ne $ModelSha256.ToLowerInvariant()) {
    throw "Model SHA-256 mismatch. Check the original file and expected checksum."
}

Write-Host "Model verified: $($ModelInfo.Length) bytes, SHA-256 $ActualHash"
# PyInstaller's generic collect-all can miss wordfreq's gzip wordlists
# because locate.this_dir() resolves data relative to the frozen module.
# Explicitly bundle the required English wordlist files at the expected
# wordfreq/data resource path, independently of the other package assets.
$WordfreqData = (& $Python -c "from wordfreq.util import data_path; print(data_path())") -join ""
Assert-Exit "Offline wordfreq dictionary location"
$WordfreqData = $WordfreqData.Trim()
if (-not (Test-Path -LiteralPath $WordfreqData -PathType Container)) {
    throw "English dictionary source directory is missing: $WordfreqData"
}
$EnglishLists = @(Get-ChildItem -LiteralPath $WordfreqData -Filter "*_en.msgpack.gz" -File)
if ($EnglishLists.Count -lt 1) {
    throw "No English wordfreq data files were installed. Refusing incomplete packaging."
}
Write-Host "Bundling $($EnglishLists.Count) English offline dictionaries explicitly."

& $Python -m PyInstaller --version
Assert-Exit "PyInstaller prerequisite check"
& npm --version
Assert-Exit "Node/npm prerequisite check"
& rustc --version
Assert-Exit "Rust prerequisite check"

New-Item -ItemType Directory -Force -Path $Assets, $PyInstallerWork | Out-Null
$Bridge = Join-Path $Assets "silabs-humanizer-bridge.exe"

$PyArguments = @(
    "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--console", "--noupx",
    "--name", "silabs-humanizer-bridge",
    "--paths", $Root,
    "--collect-all", "llama_cpp",
    "--collect-submodules", "docx",
    "--hidden-import", "wordfreq",
    "--distpath", $Assets,
    "--workpath", $PyInstallerWork,
    "--specpath", (Join-Path $PSScriptRoot "build"),
    $Entrypoint
)

# Add before the Python entrypoint, preserving the PyInstaller command layout.
$Main = $PyArguments[-1]
$PyArguments = @($PyArguments[0..($PyArguments.Count - 2)])
foreach ($Lexicon in $EnglishLists) {
    $PyArguments += @("--add-data", "$($Lexicon.FullName);wordfreq/data")
}
$PyArguments += $Main

Push-Location $Root
try {
    & $Python @PyArguments
    Assert-Exit "Frozen local bridge build"
} finally { Pop-Location }

if (-not (Test-Path -LiteralPath $Bridge -PathType Leaf)) {
    throw "Packaged local bridge executable was not created."
}

$ProbeText = ('{"action":"no_such_action"}' | & $Bridge) -join ""
Assert-Exit "Frozen local bridge smoke test"
$Probe = $ProbeText | ConvertFrom-Json
if ($Probe.ok -ne $false -or $Probe.error -notmatch "Unknown action") {
    throw "Packaged bridge returned unexpected JSON. Check dependencies."
}
Write-Host "Frozen Python bridge: PASS"

# Hard release gate: spelling must work in the actual frozen EXE.
$GrammarProbe = ('{"action":"analyse_writing","text":"This sentences contains a sentnce."}' | & $Bridge) -join ""
Assert-Exit "Frozen bridge language dictionary smoke test"
$GrammarJson = $GrammarProbe | ConvertFrom-Json
if (-not $GrammarJson.ok -or @($GrammarJson.data.issues | Where-Object { $_.category -eq "grammar" }).Count -lt 1 -or
    @($GrammarJson.data.issues | Where-Object { $_.category -eq "spelling" }).Count -lt 1) {
    throw "Frozen English wordlist or grammar rules not operational. Do not release installer: $GrammarProbe"
}
Write-Host "Frozen offline English wordfreq, grammar and spelling: PASS"


$TargetModel = Join-Path $Assets "qwen3-1.7b.gguf"
Copy-Item -LiteralPath $Model -Destination $TargetModel -Force
if ((Get-FileHash -LiteralPath $TargetModel -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ActualHash) {
    throw "Copied GGUF resource failed SHA-256 verification."
}

$Manifest = @{
    product = "Silabs Humanizer"
    build_type = "offline"
    qwen_model_file = "qwen3-1.7b.gguf"
    model_sha256 = $ActualHash
    model_bytes = $ModelInfo.Length
    model_redistribution_reviewed = $true
    build_utc = (Get-Date).ToUniversalTime().ToString("o")
}
$Manifest | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $Assets "manifest.json") -Encoding UTF8

$ReleaseConfig = @{
    bundle = @{
        active = $true
        targets = @("nsis")
        resources = @{
            "release-assets/silabs-humanizer-bridge.exe" = "bridge/silabs-humanizer-bridge.exe"
            "release-assets/qwen3-1.7b.gguf" = "model/qwen3-1.7b.gguf"
            "release-assets/manifest.json" = "model/manifest.json"
        }
        windows = @{
            webviewInstallMode = @{ type = "offlineInstaller" }
            nsis = @{ installMode = "currentUser" }
        }
    }
}
$ReleaseConfig | ConvertTo-Json -Depth 10 |
    Set-Content -LiteralPath $Config -Encoding UTF8

Push-Location $PSScriptRoot
try {
    & npm install --no-audit --no-fund
    Assert-Exit "NPM dependency install"
    & npm run build
    Assert-Exit "React UI build"
    & npm run tauri -- build --config "./src-tauri/tauri.release.conf.json"
    Assert-Exit "Tauri offline NSIS build"
} finally { Pop-Location }

$Installers = @(Get-ChildItem (Join-Path $Tauri "target/release/bundle/nsis") -Filter "*-setup.exe" -File)
if ($Installers.Count -lt 1) {
    throw "Tauri succeeded but no NSIS setup executable was found."
}
Write-Host "Offline installer created:"
$Installers | ForEach-Object {
    Write-Host $_.FullName
    Write-Host "Installer SHA-256:" (Get-FileHash $_.FullName -Algorithm SHA256).Hash
}
Write-Warning "Release remains a candidate until offline install, inference and document QA pass on a clean Windows PC."
