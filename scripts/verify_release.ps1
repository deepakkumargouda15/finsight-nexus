$ErrorActionPreference = "Stop"

Write-Host "FinSight Nexus release verification" -ForegroundColor Cyan
Write-Host "Python executable:"
python --version

Write-Host "`n[1/4] Compiling application and tests..." -ForegroundColor Cyan
python -m compileall -q app.py src tests
if ($LASTEXITCODE -ne 0) { throw "Python compilation failed." }

Write-Host "`n[2/4] Verifying Streamlit AppTest is installed..." -ForegroundColor Cyan
python -c "from streamlit.testing.v1 import AppTest; print('Streamlit AppTest available')"
if ($LASTEXITCODE -ne 0) { throw "Streamlit AppTest is unavailable; install requirements-dev.txt before release." }

Write-Host "`n[3/4] Running automated tests..." -ForegroundColor Cyan
python -m pytest -q -ra
if ($LASTEXITCODE -ne 0) { throw "Tests failed. Resolve failures before deployment." }

Write-Host "`n[4/4] Checking required release files..." -ForegroundColor Cyan
$required = @("app.py", "requirements.txt", "requirements-dev.txt", "README.md", "DATA_PROVENANCE.md", "FEATURE_AUDIT.md", ".github/workflows/tests.yml")
foreach ($item in $required) {
    if (-not (Test-Path $item)) { throw "Missing required release file: $item" }
    Write-Host "OK  $item"
}

Write-Host "`nRelease checks passed. Next, run the UI manually with: python -m streamlit run app.py" -ForegroundColor Green
