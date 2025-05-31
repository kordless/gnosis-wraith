@echo off
echo 🚀 Gnosis Wraith Performance Benchmark Runner
echo =============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python or add it to PATH.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Default options
set COMPANIES=50
set DELAY=1.0
set SERVER=http://localhost:5678

echo Available benchmark options:
echo.
echo 1. Full Benchmark (50 companies, all configs) - ~30 minutes
echo 2. Quick Test (10 companies, all configs) - ~5 minutes  
echo 3. Lightning Test (5 companies, all configs) - ~2 minutes
echo 4. Custom configuration
echo 5. Exit
echo.

set /p CHOICE="Choose option (1-5): "

if "%CHOICE%"=="1" (
    echo 🔥 Running FULL benchmark...
    set COMPANIES=50
    set DELAY=1.0
    goto :run_benchmark
)

if "%CHOICE%"=="2" (
    echo ⚡ Running QUICK test...
    set COMPANIES=10
    set DELAY=0.5
    goto :run_benchmark
)

if "%CHOICE%"=="3" (
    echo ⚡ Running LIGHTNING test...
    set COMPANIES=5
    set DELAY=0.2
    goto :run_benchmark
)

if "%CHOICE%"=="4" (
    echo.
    set /p COMPANIES="Number of companies to test (1-50): "
    set /p DELAY="Delay between requests in seconds (0.1-5.0): "
    set /p SERVER="Server URL (default: http://localhost:5678): "
    if "%SERVER%"=="" set SERVER=http://localhost:5678
    goto :run_benchmark
)

if "%CHOICE%"=="5" (
    echo 👋 Goodbye!
    exit /b 0
)

echo ❌ Invalid choice. Please select 1-5.
pause
exit /b 1

:run_benchmark
echo.
echo 📊 Benchmark Configuration:
echo    Companies: %COMPANIES%
echo    Delay: %DELAY%s
echo    Server: %SERVER%
echo.
echo 🔧 Test Configurations:
echo    1. baseline_no_extras (basic markdown, no screenshot, no OCR)
echo    2. enhanced_markdown_only (enhanced markdown, no screenshot, no OCR)  
echo    3. basic_with_screenshot (basic markdown, top screenshot, no OCR)
echo    4. enhanced_with_screenshot (enhanced markdown, top screenshot, no OCR)
echo.

set /p CONFIRM="Start benchmark? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo 🚫 Benchmark cancelled.
    pause
    exit /b 0
)

echo.
echo 🚀 Starting benchmark...
echo ⏱️  This will take approximately %COMPANIES% minutes
echo 📁 Results will be saved to benchmark_results/ directory
echo.

REM Run the benchmark
python benchmark_crawl_performance.py --companies %COMPANIES% --delay %DELAY% --url "%SERVER%"

echo.
echo 🎯 Benchmark completed!
echo 📁 Check the benchmark_results/ directory for detailed reports.
echo.
pause
