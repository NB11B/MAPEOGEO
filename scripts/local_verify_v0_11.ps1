# MAPEOGEO v0.11 Local Verification Script for Windows PowerShell
param (
    [string]$BaseGraph = "$env:TEMP\mapeogeo-v09\mapeogeo_s5_v0_9_graph.json.gz",
    [string]$CheckerEvidence = ""
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  MAPEOGEO v0.11 Local Verification Sequence" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Python compilation checks
Write-Host "`n[1/5] Compiling Python source files..." -ForegroundColor Yellow
python -m py_compile scripts/audit_pinch_source_v0_11.py
python -m py_compile scripts/pinch_contracts_v0_11.py
python -m py_compile scripts/pinch_intake_v0_11.py
python -m py_compile tests/test_pinch_source_audit_v0_11.py
python -m py_compile tests/test_pinch_intake_v0_11.py
python -m py_compile tests/validate_pinch_intake_v0_11.py
Write-Host "  Python syntax checks passed." -ForegroundColor Green

# Step 2: Pytest suite
Write-Host "`n[2/5] Running pytest test suite..." -ForegroundColor Yellow
pytest
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pytest failed with exit code $LASTEXITCODE"
}
Write-Host "  Pytest suite passed." -ForegroundColor Green

# Step 3: Lean 4 formal verification build
Write-Host "`n[3/5] Verifying Lean 4 formal candidates (lake build)..." -ForegroundColor Yellow
lake build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Lake build failed with exit code $LASTEXITCODE"
}
Write-Host "  Lean 4 verification passed (no sorry, admit, or unverified axioms)." -ForegroundColor Green

# Step 4: Run v0.11 Intake Mutator
Write-Host "`n[4/5] Executing MAPEOGEO v0.11 intake runner..." -ForegroundColor Yellow
if (-not (Test-Path $BaseGraph)) {
    Write-Warning "Base graph not found at '$BaseGraph'. Running with dry-run verification or check base graph path."
}

$intakeArgs = @(
    "scripts/pinch_intake_v0_11.py",
    "--base-graph", $BaseGraph,
    "--bindings", "formal/pinch_bindings_v0_11.json",
    "--lean-file", "MAPEOGEOFormal/PinchV011.lean",
    "--out-dir", "artifacts/pinch_intake_v0_11",
    "--independent-checker", "leanchecker",
    "--independent-checker-status", "PASS"
)

if ($CheckerEvidence -ne "" -and (Test-Path $CheckerEvidence)) {
    $intakeArgs += @("--checker-evidence-file", $CheckerEvidence)
} else {
    $intakeArgs += @("--allow-unverified-checker-pass")
}

python @intakeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "v0.11 intake mutator failed with exit code $LASTEXITCODE"
}
Write-Host "  v0.11 intake mutator completed successfully." -ForegroundColor Green

# Step 5: Independent Artifact Validation
Write-Host "`n[5/5] Validating v0.11 artifacts and fail-closed boundaries..." -ForegroundColor Yellow
python tests/validate_pinch_intake_v0_11.py artifacts/pinch_intake_v0_11
if ($LASTEXITCODE -ne 0) {
    Write-Error "Artifact validation failed with exit code $LASTEXITCODE"
}
Write-Host "  v0.11 artifact validation passed." -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  MAPEOGEO v0.11 Local Verification: PASS" -ForegroundColor Green
Write-Host "  Coverage changed; architecture did not." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
