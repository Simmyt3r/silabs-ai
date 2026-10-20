# Run in Windows PowerShell from the downloaded script, with Wi-Fi disconnected.
# No Python, elevated privileges, developer tools or user's documents are needed.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$InstallDir,
    [switch]$RunInference
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$started = Get-Date
$tests = New-Object 'System.Collections.Generic.List[string]'
$dir = (Resolve-Path -LiteralPath $InstallDir).Path
$bridge = Join-Path $dir "bridge\silabs-humanizer-bridge.exe"
$model = Join-Path $dir "model\qwen3-1.7b.gguf"
$manifest = Join-Path $dir "model\manifest.json"
$folder = Join-Path $env:TEMP ("SilabsHumanizerSelfTest-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $folder -Force | Out-Null

function Assert([bool]$good, [string]$name) {
    if (-not $good) { throw "FAIL: $name" }
    $tests.Add("PASS: $name")
    Write-Host "PASS: $name" -ForegroundColor Green
}

function Call-Bridge([hashtable]$payload) {
    $query = $payload | ConvertTo-Json -Compress -Depth 9
    $raw = ($query | & $bridge) -join ""
    if ($LASTEXITCODE -ne 0) { throw "Local bridge returned exit code $LASTEXITCODE" }
    $response = $raw | ConvertFrom-Json
    if (-not $response.ok) { throw ("Bridge error: " + $response.error) }
    return $response.data
}

try {
    Assert ((Test-Path $bridge -PathType Leaf) -and (Test-Path $model -PathType Leaf)) "Bundled local bridge and model are present"
    Assert (Test-Path $manifest -PathType Leaf) "Model integrity manifest is present"
    $metadata = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
    $digest = (Get-FileHash -LiteralPath $model -Algorithm SHA256).Hash
    Assert ($digest -ieq $metadata.model_sha256) "Bundled model matches installed SHA-256 manifest"

    $diagnostics = Call-Bridge @{action="diagnostics";model_path=$model}
    Assert ($diagnostics.components_present) "Local AI and Word dependencies are bundled"

    $text = "This sentences contains a sentnce. We should of checked the results."
    $language = Call-Bridge @{action="analyse_writing";text=$text}
    $issues = @($language.issues)
    Assert (@($issues | Where-Object { $_.category -eq "grammar" }).Count -gt 0) "Offline grammar detection works"
    Assert (@($issues | Where-Object { $_.category -eq "spelling" }).Count -gt 0) "Offline spelling suggestions work"

    $valid = "The NYSC programme in Makurdi covered georeferencing, SPSS and the harmattan."
    $legit = Call-Bridge @{action="analyse_writing";text=$valid}
    Assert (@($legit.issues | Where-Object { $_.category -eq "spelling" }).Count -eq 0) "Nigerian academic words are not falsely flagged"

    $original = Join-Path $folder "draft.txt"
    $reference = Join-Path $folder "reference.txt"
    $export = Join-Path $folder "exported.txt"
    $data = "Satellite observations require careful manual checking before final reporting."
    [IO.File]::WriteAllText($original, "Draft work is incomplete.", [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText($reference, $data, [Text.UTF8Encoding]::new($false))
    $originalSha = (Get-FileHash $original -Algorithm SHA256).Hash
    $opened = Call-Bridge @{action="open";path=$original}
    Assert ($opened.blocks.Count -eq 1) "TXT document import works"

    $similarity = Call-Bridge @{
        action="compare_local_sources";path=$original;
        fingerprint=$opened.fingerprint;
        sources=@($reference);
        revisions=@{"0"=$data}
    }
    Assert ($similarity.coverage_percent -eq 100) "Working-copy source similarity checks selected local references only"

    $null = Call-Bridge @{
        action="export";path=$original;fingerprint=$opened.fingerprint;
        revisions=@{"0"="Draft has been improved."};destination=$export
    }
    Assert ([IO.File]::ReadAllText($export) -eq "Draft has been improved.") "Edited TXT export succeeds"
    Assert ((Get-FileHash $original -Algorithm SHA256).Hash -eq $originalSha) "Original document remains unchanged"

    if ($RunInference) {
        Write-Host "Running real Qwen inference on this CPU. Older Windows laptops may be slow."
        $startInference = Get-Date
        $originalTwo = Join-Path $folder "inference.txt"
        [IO.File]::WriteAllText($originalTwo, "This sentences is difficult to understand.", [Text.UTF8Encoding]::new($false))
        $openedTwo = Call-Bridge @{action="open";path=$originalTwo}
        $result = Call-Bridge @{
            action="rewrite";path=$originalTwo;fingerprint=$openedTwo.fingerprint;
            index=0;mode="grammar";backend="gguf";model_path=$model
        }
        Assert ($result.passed -and -not [string]::IsNullOrWhiteSpace($result.proposal)) "Real local Qwen rewrite passed content checks"
        Write-Host ("Inference duration: " + [math]::Round(((Get-Date)-$startInference).TotalSeconds, 1) + " seconds")
    }
    Write-Host ("SUCCESS. Tests: " + $tests.Count + ". Total time " +
        [math]::Round(((Get-Date)-$started).TotalSeconds,1) + " seconds.") -ForegroundColor Green
    Write-Host "No user documents were opened. All fixture data stayed in the temporary folder."
} finally {
    Remove-Item -LiteralPath $folder -Recurse -Force -ErrorAction SilentlyContinue
}
