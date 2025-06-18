# cleanup-for-deployment.ps1
# Script to remove unnecessary files before deployment

Write-Host "Gnosis Wraith Cleanup Script" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host ""

# Dry run by default - set to $false to actually delete
$DryRun = $false

# Files to delete based on your git status
$FilesToDelete = @(
    # Core files that were deleted
    "core/LICENSE-CRAWL4AI.md",
    "core/content_filter.py",
    "core/enhanced_storage_service.py",
    "core/filename_utils.py",
    "core/html_cleaner.py",
    "core/javascript_executor.py",
    "core/lib/ndb_local.py",
    "core/markdown_extractor.py",
    "core/mcp.py",
    "core/pdf_generator.py",
    "core/reports_v2_example.py",
    "core/screenshot_capture.py",
    
    # Examples directory
    "examples/powershell/DumpsterHouse-Screenshot.ps1",
    "examples/powershell/README.md",
    "examples/powershell/Set-GnosisConfig.ps1",
    "examples/powershell/Test-BasicCrawl.ps1",
    "examples/powershell/Test-DataExtraction.ps1",
    "examples/powershell/Test-JavaScriptExecution.ps1",
    "examples/powershell/Test-SecurityValidation.ps1",
    
    # Terminal module
    "gnosis_wraith/terminal/__init__.py",
    "gnosis_wraith/terminal/parser.py",
    "gnosis_wraith/terminal/routes.py",
    
    # Lightning module
    "lightning/__init__.py",
    "lightning/client.py",
    "lightning/services.py",
    "lightning/wallet.py",
    
    # Search module
    "search/__init__.py",
    
    # Storage files
    "storage/gnosis-wraith.log",
    
    # Scripts
    "scripts/maintenance/migrate_to_ndb_storage.py",
    "scripts/maintenance/migrate_to_user_storage.py",
    "scripts/maintenance/safe_cleanup.py",
    
    # Web templates
    "web/templates/about.html",
    "web/templates/gnosis.html",
    "web/templates/min_logs.html",
    "web/templates/philosophy.html",
    "web/templates/upload.js",
    "web/templates/vault.html",
    "web/templates/wraith.html",
    
    # JS components
    "web/static/js/components/token-manager-modal-fixed.js",
    "web/static/js/components/token-status-icon-backup.js",
    
    # Test files in root
    "test_markdown_enhanced.py",
    "suspect_files.md"
)

# Directories to remove
$DirectoriesToDelete = @(
    "notes",
    "examples/powershell",
    "gnosis_wraith/terminal",
    "lightning",
    "search",
    ".mystic"
)

# Function to delete files
function Remove-Files {
    param($Files, $Type)
    
    $deleted = 0
    $notFound = 0
    
    foreach ($file in $Files) {
        if (Test-Path $file) {
            if ($DryRun) {
                Write-Host "[DRY RUN] Would delete $Type`: $file" -ForegroundColor Yellow
            } else {
                try {
                    if ($Type -eq "directory") {
                        Remove-Item -Path $file -Recurse -Force
                    } else {
                        Remove-Item -Path $file -Force
                    }
                    Write-Host "Deleted $Type`: $file" -ForegroundColor Green
                    $deleted++
                } catch {
                    Write-Host "ERROR deleting $file`: $_" -ForegroundColor Red
                }
            }
        } else {
            Write-Host "$Type not found: $file" -ForegroundColor Gray
            $notFound++
        }
    }
    
    return @{Deleted = $deleted; NotFound = $notFound}
}

# Clean up user storage (optional)
function Clean-UserStorage {
    $storageUsers = "storage/users"
    if (Test-Path $storageUsers) {
        $userDirs = Get-ChildItem -Path $storageUsers -Directory
        foreach ($dir in $userDirs) {
            if ($DryRun) {
                Write-Host "[DRY RUN] Would delete user storage: $($dir.FullName)" -ForegroundColor Yellow
            } else {
                Remove-Item -Path $dir.FullName -Recurse -Force
                Write-Host "Deleted user storage: $($dir.FullName)" -ForegroundColor Green
            }
        }
    }
}

# Main execution
Write-Host "Starting cleanup..." -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "*** DRY RUN MODE - No files will be deleted ***" -ForegroundColor Magenta
    Write-Host "Set `$DryRun = `$false at the top of the script to actually delete files" -ForegroundColor Magenta
    Write-Host ""
}

# Delete files
Write-Host "Cleaning up files..." -ForegroundColor Cyan
$fileResults = Remove-Files -Files $FilesToDelete -Type "file"

Write-Host ""
Write-Host "Cleaning up directories..." -ForegroundColor Cyan
$dirResults = Remove-Files -Files $DirectoriesToDelete -Type "directory"

Write-Host ""
Write-Host "Clean user storage? (y/n)" -ForegroundColor Yellow
$cleanStorage = Read-Host
if ($cleanStorage -eq 'y') {
    Clean-UserStorage
}

# Summary
Write-Host ""
Write-Host "Cleanup Summary" -ForegroundColor Green
Write-Host "===============" -ForegroundColor Green
if ($DryRun) {
    Write-Host "DRY RUN - No files were actually deleted" -ForegroundColor Magenta
    $totalFiles = $FilesToDelete.Count + $DirectoriesToDelete.Count
    Write-Host "Would delete $totalFiles items" -ForegroundColor Yellow
} else {
    Write-Host "Files deleted: $($fileResults.Deleted)" -ForegroundColor Green
    Write-Host "Directories deleted: $($dirResults.Deleted)" -ForegroundColor Green
    Write-Host "Items not found: $($fileResults.NotFound + $dirResults.NotFound)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review the changes with: git status" -ForegroundColor White
Write-Host "2. Stage remaining changes: git add -A" -ForegroundColor White
Write-Host "3. Commit: git commit -m 'feat: prepare for Cloud Run deployment'" -ForegroundColor White
Write-Host "4. Push to main: git push origin main" -ForegroundColor White
