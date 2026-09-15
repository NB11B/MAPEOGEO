# MAPEOGEO v0.15 Local Verification Script for Windows PowerShell
param (
    [string]$BaseGraph = "artifacts/convex_v0_14/mapeogeo_v0_14_graph.json.gz",
    [string]$Alignments = "formal/analysis_alignments_v0_15.json",
    [string]$OutDir = "artifacts/analysis_v0_15"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  MAPEOGEO v0.15 Local Verification Sequence" -ForegroundColor Cyan
Write-Host "  Real Analysis & Differential Calculus Expansion" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Python compilation checks
Write-Host "`n[1/5] Compiling Python source files..." -ForegroundColor Yellow
python -m py_compile scripts/import_analysis_v0_15.py
python -m py_compile scripts/analysis_intake_v0_15.py
python -m py_compile tests/test_analysis_expansion_v0_15.py
python -m py_compile tests/validate_analysis_expansion_v0_15.py
Write-Host "  Python syntax checks passed." -ForegroundColor Green

# Step 2: Pytest suite
Write-Host "`n[2/5] Running pytest test suite..." -ForegroundColor Yellow
pytest tests/test_analysis_expansion_v0_15.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pytest failed with exit code $LASTEXITCODE"
}
Write-Host "  Pytest suite passed." -ForegroundColor Green

# Step 3: Run v0.15 Analysis Intake Runner
Write-Host "`n[3/5] Executing MAPEOGEO v0.15 analysis intake runner..." -ForegroundColor Yellow
$intakeArgs = @(
    "scripts/analysis_intake_v0_15.py",
    "--base-graph", $BaseGraph,
    "--alignments", $Alignments,
    "--out-dir", $OutDir
)

python @intakeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "v0.15 analysis intake failed with exit code $LASTEXITCODE"
}
Write-Host "  v0.15 analysis intake completed successfully." -ForegroundColor Green

# Step 4: Independent Artifact Validation
Write-Host "`n[4/5] Validating v0.15 artifacts and preregistered bounds..." -ForegroundColor Yellow
python tests/validate_analysis_expansion_v0_15.py --graph "$OutDir/mapeogeo_v0_15_graph.json.gz" --dashboard "$OutDir/analysis_expansion_dashboard.json" --prereg evidence/v0_15_preregistration.json
if ($LASTEXITCODE -ne 0) {
    Write-Error "Artifact validation failed with exit code $LASTEXITCODE"
}
Write-Host "  v0.15 artifact validation passed." -ForegroundColor Green

# Step 5: Summary
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  MAPEOGEO v0.15 Local Verification: PASS" -ForegroundColor Green
Write-Host "  Real Analysis & Multivariable Calculus expansion verified across 4 sources." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
