# MAPEOGEO v0.13 Local Verification Script for Windows PowerShell
param (
    [string]$VmlsPdf = "data/sources/vmls.pdf",
    [string]$BaseGraph = "artifacts/cross_source_v0_12/mapeogeo_v0_12_graph.json.gz",
    [switch]$Mock = $false
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  MAPEOGEO v0.13 Local Verification Sequence" -ForegroundColor Cyan
Write-Host "  Tri-Source Mathematics Expansion (VMLS)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Python compilation checks
Write-Host "`n[1/6] Compiling Python source files..." -ForegroundColor Yellow
python -m py_compile scripts/import_vmls_v0_13.py
python -m py_compile scripts/blinded_alignment_benchmark_v0_13.py
python -m py_compile scripts/tri_source_intake_v0_13.py
python -m py_compile tests/test_tri_source_v0_13.py
python -m py_compile tests/validate_tri_source_v0_13.py
Write-Host "  Python syntax checks passed." -ForegroundColor Green

# Step 2: Pytest suite
Write-Host "`n[2/6] Running pytest test suite..." -ForegroundColor Yellow
pytest tests/test_tri_source_v0_13.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pytest failed with exit code $LASTEXITCODE"
}
Write-Host "  Pytest suite passed." -ForegroundColor Green

# Step 3: Blinded Alignment Benchmark
Write-Host "`n[3/6] Executing blinded alignment benchmark (20% holdout)..." -ForegroundColor Yellow
python scripts/blinded_alignment_benchmark_v0_13.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Blinded alignment benchmark failed with exit code $LASTEXITCODE"
}
Write-Host "  Blinded alignment benchmark completed." -ForegroundColor Green

# Step 4: Run v0.13 Tri-Source Intake Runner
Write-Host "`n[4/6] Executing MAPEOGEO v0.13 tri-source intake runner..." -ForegroundColor Yellow
$intakeArgs = @(
    "scripts/tri_source_intake_v0_13.py",
    "--base-graph", $BaseGraph,
    "--alignments", "formal/tri_source_alignments_v0_13.json",
    "--preregistration", "evidence/v0_13_preregistration.json",
    "--vmls-pdf", $VmlsPdf,
    "--out-dir", "artifacts/tri_source_v0_13"
)

if ($Mock) {
    $intakeArgs += @("--mock")
}

python @intakeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "v0.13 tri-source intake failed with exit code $LASTEXITCODE"
}
Write-Host "  v0.13 tri-source intake completed successfully." -ForegroundColor Green

# Step 5: Independent Artifact Validation
Write-Host "`n[5/6] Validating v0.13 artifacts and fail-closed boundaries..." -ForegroundColor Yellow
python tests/validate_tri_source_v0_13.py artifacts/tri_source_v0_13
if ($LASTEXITCODE -ne 0) {
    Write-Error "Artifact validation failed with exit code $LASTEXITCODE"
}
Write-Host "  v0.13 artifact validation passed." -ForegroundColor Green

# Step 6: Summary
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  MAPEOGEO v0.13 Local Verification: PASS" -ForegroundColor Green
Write-Host "  Tri-source convergence demonstrated across S_A, S_B, and S_C." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
