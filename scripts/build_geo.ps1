param(
    [string]$SourceRoot = 'C:\Users\nateb\Documents\GeometricElementaryOperators',
    [string]$OutputDirectory = '',
    [string]$ExpectedCommit = 'c590bd7a01f316971722053faf8626458958f820'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $repoRoot 'experiments\mapeogeo_llm\artifacts\geo'
}
$header = Join-Path $SourceRoot 'include\geo\operator_kernel.h'
$source = Join-Path $SourceRoot 'src\operator_kernel.c'
if (-not (Test-Path -LiteralPath $header) -or -not (Test-Path -LiteralPath $source)) {
    throw "GeometricElementaryOperators source checkout is incomplete: $SourceRoot"
}
$actualCommit = (& git -C $SourceRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actualCommit -ne $ExpectedCommit) {
    throw "GEO source commit mismatch: expected $ExpectedCommit, got $actualCommit"
}
& git -C $SourceRoot diff --quiet $ExpectedCommit -- 'include/geo/operator_kernel.h' 'src/operator_kernel.c'
if ($LASTEXITCODE -ne 0) {
    throw 'GEO compiled source inputs differ from pinned commit'
}
$abiLine = Select-String -LiteralPath $header -Pattern '^#define GEO_OPERATOR_ABI_VERSION 0x00050100u$'
if ($null -eq $abiLine) {
    throw 'GEO ABI 0x00050100 was not found in operator_kernel.h'
}
$gcc = (Get-Command gcc -ErrorAction Stop).Source
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$output = Join-Path $OutputDirectory 'geo_operator_kernel.dll'
& $gcc -std=c11 -O2 -Wall -Wextra -Wpedantic -shared '-Wl,--no-insert-timestamp,--image-base,0x180000000' -I (Join-Path $SourceRoot 'include') $source -o $output
if ($LASTEXITCODE -ne 0) {
    throw "GEO native library build failed with exit code $LASTEXITCODE"
}
function Get-Sha256([string]$Path) {
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        return ([System.BitConverter]::ToString($sha256.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $stream.Dispose()
        $sha256.Dispose()
    }
}
$digest = Get-Sha256 $output
$compiler = (& $gcc --version | Select-Object -First 1)
$receipt = [ordered]@{
    schema = 'mapeogeo.geo.native-build.v1'
    schema_version = 1
    source_repository = 'NB11B/GeometricElementaryOperators'
    source_commit = $actualCommit
    source_inputs_sha256 = [ordered]@{
        'include/geo/operator_kernel.h' = Get-Sha256 $header
        'src/operator_kernel.c' = Get-Sha256 $source
    }
    abi_version = '0x00050100'
    library_sha256 = $digest
    compiler = $compiler
}
$receiptPath = Join-Path $OutputDirectory 'geo_operator_kernel.receipt.json'
$receiptJson = $receipt | ConvertTo-Json -Depth 4
[System.IO.File]::WriteAllText(
    $receiptPath,
    $receiptJson + [Environment]::NewLine,
    [System.Text.UTF8Encoding]::new($false)
)
[ordered]@{
    output = $output
    receipt = $receiptPath
    sha256 = $digest
    source_commit = $actualCommit
    abi_version = '0x00050100'
    compiler = $compiler
} | ConvertTo-Json
