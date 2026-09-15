# MAPEOGEO v0.15.2 Confirmatory Real Analysis & Calculus Expansion Verification Script
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  MAPEOGEO v0.15.2 Local Confirmatory Verification" -ForegroundColor Cyan
Write-Host "  Clean-Room End-to-End Dependency Chain Replay & Provenance Audit" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Reconstruct Pipeline End-to-End
Write-Host "`n[1/5] Reconstructing mathematical dependency chain from scratch..." -ForegroundColor Yellow
python scripts/reconstruct_pipeline.py --target-stage v0.15.2
if ($LASTEXITCODE -ne 0) {
    Write-Host "Reconstruct pipeline failed." -ForegroundColor Red
    exit 1
}
Write-Host "  Clean-room pipeline reconstruction passed." -ForegroundColor Green

# Step 2: Syntax and Compilation Checks
Write-Host "`n[2/5] Compiling Python source files..." -ForegroundColor Yellow
python -m py_compile scripts/import_gallier_v0_12.py
python -m py_compile scripts/import_axler_v0_12.py
python -m py_compile scripts/import_vmls_v0_13.py
python -m py_compile scripts/import_cvx_v0_14.py
python -m py_compile scripts/import_analysis_v0_15.py
python -m py_compile scripts/analysis_intake_v0_15_2.py
python -m py_compile scripts/reconstruct_pipeline.py
python -m py_compile tests/test_analysis_expansion_v0_15_2.py
python -m py_compile tests/validate_analysis_expansion_v0_15_2.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python compilation failed." -ForegroundColor Red
    exit 1
}
Write-Host "  Python syntax checks passed." -ForegroundColor Green

# Step 3: Run Pytest Test Suite
Write-Host "`n[3/5] Running pytest test suite..." -ForegroundColor Yellow
pytest tests/test_analysis_expansion_v0_15_2.py -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "Pytest tests failed." -ForegroundColor Red
    exit 1
}
Write-Host "  Pytest suite passed." -ForegroundColor Green

# Step 4: Validate v0.15.2 Artifacts and Preregistered Bounds & Provenance Invariants
Write-Host "`n[4/5] Validating v0.15.2 artifacts and preregistered bounds..." -ForegroundColor Yellow
python tests/validate_analysis_expansion_v0_15_2.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "v0.15.2 artifact validation failed." -ForegroundColor Red
    exit 1
}
Write-Host "  v0.15.2 artifact validation passed." -ForegroundColor Green

# Step 5: Summary
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  MAPEOGEO v0.15.2 Confirmatory Replay: PASS" -ForegroundColor Green
Write-Host "  Clean-room reproducibility & provenance integrity verified." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
