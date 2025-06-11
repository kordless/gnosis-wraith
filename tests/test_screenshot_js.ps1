# Test JavaScript Execution with Screenshot Capture
# This script demonstrates executing JavaScript and capturing screenshots

param(
    [Parameter(Mandatory=$false)]
    [string]$Token = $env:GNOSIS_API_TOKEN,
    
    [Parameter(Mandatory=$false)]
    [string]$BaseUrl = "http://localhost:5678"
)

if (-not $Token) {
    Write-Host "Error: No API token provided!" -ForegroundColor Red
    exit 1
}

Write-Host "📸 Testing JavaScript Execution with Screenshots" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Cyan

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

# Test 1: Execute JavaScript and capture screenshot
Write-Host "`n📋 Test 1: Modify page and capture screenshot" -ForegroundColor Yellow
$body = @{
    url = "https://example.com"
    javascript = @'
// Change the page title
document.title = "Modified by Gnosis Wraith!";

// Add a custom element
const banner = document.createElement('div');
banner.style.cssText = 'background: #4CAF50; color: white; padding: 20px; text-align: center; font-size: 24px; position: fixed; top: 0; width: 100%; z-index: 9999;';
banner.textContent = 'This page was modified by JavaScript!';
document.body.insertBefore(banner, document.body.firstChild);

// Change background color
document.body.style.backgroundColor = '#f0f0f0';

// Return what we did
return {
    newTitle: document.title,
    elementsAdded: 1,
    backgroundColor: document.body.style.backgroundColor
};
'@
    take_screenshot = $true
    screenshot_options = @{
        full_page = $true
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ JavaScript executed successfully!" -ForegroundColor Green
        Write-Host "   Result: $($response.result | ConvertTo-Json -Compress)" -ForegroundColor Gray
        
        if ($response.screenshot) {
            Write-Host "📸 Screenshot captured!" -ForegroundColor Green
            Write-Host "   Format: $($response.screenshot.format)" -ForegroundColor Gray
            Write-Host "   Size: $($response.screenshot.size) bytes" -ForegroundColor Gray
            Write-Host "   Full page: $($response.screenshot.full_page)" -ForegroundColor Gray
            
            # Save screenshot to file
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $filename = "screenshot_js_$timestamp.png"
            $bytes = [Convert]::FromBase64String($response.screenshot.data)
            [IO.File]::WriteAllBytes($filename, $bytes)
            Write-Host "   Saved to: $filename" -ForegroundColor Green
        }
    } else {
        Write-Host "❌ Execution failed: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

# Test 2: Highlight elements and capture
Write-Host "`n📋 Test 2: Highlight search results on Google" -ForegroundColor Yellow
$body = @{
    url = "https://www.google.com/search?q=gnosis+wraith"
    javascript = @'
// Highlight all search result titles
const results = document.querySelectorAll('h3');
results.forEach((result, index) => {
    result.style.backgroundColor = index % 2 === 0 ? '#ffeb3b' : '#ff9800';
    result.style.padding = '10px';
    result.style.borderRadius = '5px';
});

// Add a summary at the top
const summary = document.createElement('div');
summary.style.cssText = 'background: #2196F3; color: white; padding: 20px; margin: 20px; border-radius: 10px; font-size: 18px;';
summary.textContent = `Found ${results.length} search results - highlighted by Gnosis Wraith`;
document.body.insertBefore(summary, document.body.firstChild);

return {
    resultsHighlighted: results.length,
    message: "Search results highlighted"
};
'@
    take_screenshot = $true
    screenshot_options = @{
        full_page = $false  # Just viewport
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ JavaScript executed successfully!" -ForegroundColor Green
        Write-Host "   Result: $($response.result | ConvertTo-Json -Compress)" -ForegroundColor Gray
        
        if ($response.screenshot) {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $filename = "google_highlighted_$timestamp.png"
            $bytes = [Convert]::FromBase64String($response.screenshot.data)
            [IO.File]::WriteAllBytes($filename, $bytes)
            Write-Host "📸 Screenshot saved to: $filename" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

# Test 3: Extract data AND capture screenshot
Write-Host "`n📋 Test 3: Extract HN data and visualize on page" -ForegroundColor Yellow
$body = @{
    url = "https://news.ycombinator.com"
    javascript = @'
// Extract top stories
const stories = Array.from(document.querySelectorAll('.titleline > a')).slice(0, 5);

// Create visualization on the page
const viz = document.createElement('div');
viz.style.cssText = 'position: fixed; top: 10px; right: 10px; background: white; border: 2px solid #ff6600; padding: 20px; max-width: 400px; z-index: 9999; box-shadow: 0 4px 6px rgba(0,0,0,0.1);';
viz.innerHTML = '<h3 style="color: #ff6600; margin-top: 0;">Top 5 Stories</h3>';

const list = document.createElement('ol');
stories.forEach(story => {
    const li = document.createElement('li');
    li.style.marginBottom = '10px';
    li.textContent = story.textContent;
    list.appendChild(li);
});
viz.appendChild(list);
document.body.appendChild(viz);

// Return the data
return {
    stories: stories.map(s => s.textContent),
    visualizationAdded: true
};
'@
    take_screenshot = $true
    options = @{
        wait_after = 2000  # Wait 2 seconds after execution
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ Data extracted and visualization added!" -ForegroundColor Green
        
        # Show extracted stories
        if ($response.result.stories) {
            Write-Host "`nExtracted stories:" -ForegroundColor Yellow
            $i = 1
            foreach ($story in $response.result.stories) {
                Write-Host "  $i. $story" -ForegroundColor White
                $i++
            }
        }
        
        if ($response.screenshot) {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $filename = "hn_visualization_$timestamp.png"
            $bytes = [Convert]::FromBase64String($response.screenshot.data)
            [IO.File]::WriteAllBytes($filename, $bytes)
            Write-Host "`n📸 Screenshot with visualization saved to: $filename" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

Write-Host "`n✅ All tests completed!" -ForegroundColor Green
Write-Host "Check the generated PNG files to see the screenshots." -ForegroundColor Cyan