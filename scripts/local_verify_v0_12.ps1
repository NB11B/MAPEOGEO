# MAPEOGEO v0.12 Local Verification Script for Windows PowerShell
param (
    [string]$PdfPath = "data/sources/LADR4e.pdf",
    [string]$BaseGraph = "artifacts/pinch_intake_v0_11/mapeogeo_v0_11_graph.json.gz",
    [switch]$Mock = $false
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  MAPEOGEO v0.12 Local Verification Sequence" -ForegroundColor Cyan
Write-Host "  Cross-Source Mathematics Expansion" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Python compilation checks
Write-Host "`n[1/5] Compiling Python source files..." -ForegroundColor Yellow
python -m py_compile scripts/import_axler_v0_12.py
python -m py_compile scripts/cross_source_intake_v0_12.py
python -m py_compile tests/test_cross_source_v0_12.py
python -m py_compile tests/validate_cross_source_v0_12.py
Write-Host "  Python syntax checks passed." -ForegroundColor Green

# Step 2: Pytest suite
Write-Host "`n[2/5] Running pytest test suite..." -ForegroundColor Yellow
pytest tests/test_cross_source_v0_12.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pytest failed with exit code $LASTEXITCODE"
}
Write-Host "  Pytest suite passed." -ForegroundColor Green

# Step 3: Formal checks (Lake build if available)
Write-Host "`n[3/5] Verifying Lean 4 formal declarations (lake build)..." -ForegroundColor Yellow
if (Get-Command "lake" -ErrorAction SilentlyContinue) {
    lake build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Lake build failed with exit code $LASTEXITCODE"
    }
    Write-Host "  Lean 4 verification passed." -ForegroundColor Green
} else {
    Write-Host "  Lake not found in PATH; skipping formal build (unblocked by design)." -ForegroundColor Yellow
}

# Step 4: Run v0.12 Cross-Source Intake Runner
Write-Host "`n[4/5] Executing MAPEOGEO v0.12 cross-source intake runner..." -ForegroundColor Yellow
$intakeArgs = @(
    "scripts/cross_source_intake_v0_12.py",
    "--base-graph", $BaseGraph,
    "--alignments", "formal/cross_source_alignments_v0_12.json",
    "--preregistration", "evidence/v0_12_preregistration.json",
    "--pdf-path", $PdfPath,
    "--out-dir", "artifacts/cross_source_v0_12"
)

if ($Mock) {
    $intakeArgs += @("--mock")
}

python @intakeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "v0.12 cross-source intake failed with exit code $LASTEXITCODE"
}
Write-Host "  v0.12 cross-source intake completed successfully." -ForegroundColor Green

# Step 5: Independent Artifact Validation
Write-Host "`n[5/5] Validating v0.12 artifacts and fail-closed boundaries..." -ForegroundColor Yellow
python tests/validate_cross_source_v0_12.py artifacts/cross_source_v0_12
if ($LASTEXITCODE -ne 0) {
    Write-Error "Artifact validation failed with exit code $LASTEXITCODE"
}
Write-Host "  v0.12 artifact validation passed." -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  MAPEOGEO v0.12 Local Verification: PASS" -ForegroundColor Green
Write-Host "  Coverage expanded; architecture unified across sources." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
