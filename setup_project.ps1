# ============================================
# Performance Test AI - Project Setup Script
# ============================================

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Performance Test AI - Project Setup"
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Change this path if you want another location
$ProjectPath = "$PWD\Performance_Test_AI"

# Create Root Folder
New-Item -ItemType Directory -Force -Path $ProjectPath | Out-Null

# Create Folder Structure
$Folders = @(
    "uploads",
    "uploads\Legacy",
    "uploads\Current",
    "converted",
    "output",
    "temp"
)

foreach ($folder in $Folders) {
    New-Item -ItemType Directory -Force -Path (Join-Path $ProjectPath $folder) | Out-Null
}

# Create Files
$Files = @(
    "main.py",
    "convert_csv_to_json.py",
    "PerfResultsAnalysis_Instructions.md",
    "README.md",
    ".gitignore"
)

foreach ($file in $Files) {
    $FilePath = Join-Path $ProjectPath $file
    if (!(Test-Path $FilePath)) {
        New-Item -ItemType File -Path $FilePath | Out-Null
    }
}

Write-Host ""
Write-Host "Project structure created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host $ProjectPath -ForegroundColor Yellow
Write-Host ""

tree $ProjectPath /F