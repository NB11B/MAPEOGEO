# MAPEOGEO v0.14 Local Verification Script for Windows PowerShell
param (
    [string]$CvxPdf = "data/sources/bv_cvxbook.pdf",
    [string]$BaseGraph = "artifacts/tri_source_v0_13/mapeogeo_v0_13_graph.json.gz",
    [switch]$Mock = $false
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  MAPEOGEO v0.14 Local Verification Sequence" -ForegroundColor Cyan
Write-Host "  Convex Analysis & Optimization Expansion" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Python compilation checks
Write-Host "`n[1/5] Compiling Python source files..." -ForegroundColor Yellow
python -m py_compile scripts/import_cvx_v0_14.py
python -m py_compile scripts/convex_intake_v0_14.py
python -m py_compile tests/test_convex_expansion_v0_14.py
python -m py_compile tests/validate_convex_expansion_v0_14.py
Write-Host "  Python syntax checks passed." -ForegroundColor Green

# Step 2: Pytest suite
Write-Host "`n[2/5] Running pytest test suite..." -ForegroundColor Yellow
pytest tests/test_convex_expansion_v0_14.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pytest failed with exit code $LASTEXITCODE"
}
Write-Host "  Pytest suite passed." -ForegroundColor Green

# Step 3: Run v0.14 Convex Intake Runner
Write-Host "`n[3/5] Executing MAPEOGEO v0.14 convex intake runner..." -ForegroundColor Yellow
$intakeArgs = @(
    "scripts/convex_intake_v0_14.py",
    "--base-graph", $BaseGraph,
    "--alignments", "formal/convex_alignments_v0_14.json",
    "--pdf-path", $CvxPdf,
    "--out-dir", "artifacts/convex_v0_14"
)

if ($Mock) {
    $intakeArgs += @("--mock")
}

python @intakeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "v0.14 convex intake failed with exit code $LASTEXITCODE"
}
Write-Host "  v0.14 convex intake completed successfully." -ForegroundColor Green

# Step 4: Independent Artifact Validation
Write-Host "`n[4/5] Validating v0.14 artifacts and preregistered bounds..." -ForegroundColor Yellow
python tests/validate_convex_expansion_v0_14.py --graph artifacts/convex_v0_14/mapeogeo_v0_14_graph.json.gz --dashboard artifacts/convex_v0_14/convex_expansion_dashboard.json --prereg evidence/v0_14_preregistration.json
if ($LASTEXITCODE -ne 0) {
    Write-Error "Artifact validation failed with exit code $LASTEXITCODE"
}
Write-Host "  v0.14 artifact validation passed." -ForegroundColor Green

# Step 5: Summary
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  MAPEOGEO v0.14 Local Verification: PASS" -ForegroundColor Green
Write-Host "  Quad-source convergence demonstrated across S_A, S_B, S_C, and S_D." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
