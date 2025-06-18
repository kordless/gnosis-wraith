# Replace White House with Dumpster House and take screenshot
# This script modifies the page content and captures the result

# Load helper functions
. "$env:USERPROFILE\.gnosis-wraith\GnosisHelper.ps1"

Write-Host "`nWhite House → Dumpster House Screenshot Generator" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# First, let's execute JavaScript to replace all instances of "White" with "Dumpster"
Write-Host "`nModifying page content..." -ForegroundColor Yellow

$result = Invoke-GnosisApi -Endpoint "/api/v2/execute" -Body @{
    url = "https://www.whitehouse.gov"
    javascript = @"
// Function to replace text in all text nodes
function replaceInText(element, pattern, replacement) {
    for (let node of element.childNodes) {
        switch (node.nodeType) {
            case Node.ELEMENT_NODE:
                replaceInText(node, pattern, replacement);
                break;
            case Node.TEXT_NODE:
                node.textContent = node.textContent.replace(pattern, replacement);
                break;
        }
    }
}

// Replace in the main content
replaceInText(document.body, /White/g, 'Dumpster');
replaceInText(document.body, /WHITE/g, 'DUMPSTER');
replaceInText(document.body, /white/g, 'dumpster');

// Also replace in the title
document.title = document.title.replace(/White/g, 'Dumpster');
document.title = document.title.replace(/WHITE/g, 'DUMPSTER');
document.title = document.title.replace(/white/g, 'dumpster');

// Update any alt text in images
document.querySelectorAll('img').forEach(img => {
    if (img.alt) {
        img.alt = img.alt.replace(/White/g, 'Dumpster');
        img.alt = img.alt.replace(/WHITE/g, 'DUMPSTER');
        img.alt = img.alt.replace(/white/g, 'dumpster');
    }
});

// Update meta tags
document.querySelectorAll('meta').forEach(meta => {
    if (meta.content) {
        meta.content = meta.content.replace(/White/g, 'Dumpster');
        meta.content = meta.content.replace(/WHITE/g, 'DUMPSTER');
        meta.content = meta.content.replace(/white/g, 'dumpster');
    }
});

// Count replacements for fun
const bodyText = document.body.innerText;
const matches = bodyText.match(/Dumpster/gi) || [];

return {
    success: true,
    replacements: matches.length,
    newTitle: document.title,
    message: `Replaced ${matches.length} instances of White with Dumpster`
};
"@
    javascript_enabled = $true
    javascript_settle_time = 2000
}

if ($result.success) {
    Write-Host "✓ Page modified successfully!" -ForegroundColor Green
    Write-Host "  $($result.result.message)" -ForegroundColor Gray
    Write-Host "  New title: $($result.result.newTitle)" -ForegroundColor Gray
} else {
    Write-Host "✗ Failed to modify page: $($result.error)" -ForegroundColor Red
    return
}

# Now take a screenshot of the modified page
Write-Host "`nTaking screenshot of modified page..." -ForegroundColor Yellow

$screenshotResult = Invoke-GnosisApi -Endpoint "/api/crawl" -Body @{
    url = "https://www.whitehouse.gov"
    javascript_enabled = $true
    javascript_settle_time = 2000
    take_screenshot = $true
    screenshot_mode = "full"
    markdown_extraction = "none"  # We only want the screenshot
    title = "Dumpster House Homepage"
    # Execute the same replacement code before screenshot
    javascript_code = @"
// Same replacement logic
function replaceInText(element, pattern, replacement) {
    for (let node of element.childNodes) {
        switch (node.nodeType) {
            case Node.ELEMENT_NODE:
                replaceInText(node, pattern, replacement);
                break;
            case Node.TEXT_NODE:
                node.textContent = node.textContent.replace(pattern, replacement);
                break;
        }
    }
}

replaceInText(document.body, /White/g, 'Dumpster');
replaceInText(document.body, /WHITE/g, 'DUMPSTER');
replaceInText(document.body, /white/g, 'dumpster');

document.title = document.title.replace(/White/g, 'Dumpster').replace(/WHITE/g, 'DUMPSTER').replace(/white/g, 'dumpster');

document.querySelectorAll('img').forEach(img => {
    if (img.alt) {
        img.alt = img.alt.replace(/White/g, 'Dumpster').replace(/WHITE/g, 'DUMPSTER').replace(/white/g, 'dumpster');
    }
});
"@
}

if ($screenshotResult.success) {
    Write-Host "✓ Screenshot captured!" -ForegroundColor Green
    
    # Extract screenshot path
    $screenshotPath = $null
    if ($screenshotResult.results -and $screenshotResult.results[0].screenshot) {
        $screenshotPath = $screenshotResult.results[0].screenshot
    } elseif ($screenshotResult.screenshot) {
        $screenshotPath = $screenshotResult.screenshot
    }
    
    if ($screenshotPath) {
        $fullUrl = "$($config.ServerUrl)$screenshotPath"
        Write-Host "  Screenshot URL: $fullUrl" -ForegroundColor Green
        Write-Host "`nOpening screenshot in browser..." -ForegroundColor Yellow
        Start-Process $fullUrl
        
        # Also save locally if desired
        $saveLocal = Read-Host "`nSave screenshot locally? (y/n)"
        if ($saveLocal -eq 'y') {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $filename = "DumpsterHouse_$timestamp.png"
            $localPath = Join-Path $env:USERPROFILE\Pictures $filename
            
            try {
                # Download the screenshot
                $headers = Get-GnosisHeaders
                Invoke-WebRequest -Uri $fullUrl -Headers $headers -OutFile $localPath
                Write-Host "✓ Screenshot saved to: $localPath" -ForegroundColor Green
            } catch {
                Write-Host "✗ Failed to save locally: $_" -ForegroundColor Red
            }
        }
    }
} else {
    Write-Host "✗ Screenshot failed: $($screenshotResult.error)" -ForegroundColor Red
}

Write-Host "`nDumpster House mission complete! 🗑️" -ForegroundColor Cyan