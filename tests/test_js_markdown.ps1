# Test JavaScript Execution with Markdown Extraction
# This script demonstrates executing JavaScript and extracting markdown from the modified DOM

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

Write-Host "📝 Testing JavaScript Execution with Markdown Extraction" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

# Test 1: Modify content and extract markdown
Write-Host "`n📋 Test 1: Add content to page and extract as markdown" -ForegroundColor Yellow
$body = @{
    url = "https://example.com"
    javascript = @'
// Add some structured content to the page
const article = document.createElement('article');
article.innerHTML = `
    <h1>JavaScript-Generated Content</h1>
    <p>This content was added by Gnosis Wraith's JavaScript execution.</p>
    <h2>Features Demonstrated</h2>
    <ul>
        <li>Dynamic content injection</li>
        <li>Markdown extraction after JS execution</li>
        <li>Complete control over page content</li>
    </ul>
    <h2>Example Code Block</h2>
    <pre><code>const result = await fetch('/api/v2/execute');
console.log(result);</code></pre>
    <p>Visit <a href="https://github.com">GitHub</a> for more examples.</p>
`;

// Insert at the beginning of body
document.body.insertBefore(article, document.body.firstChild);

// Also modify the existing content
const h1 = document.querySelector('h1');
if (h1 && h1.textContent.includes('Example Domain')) {
    h1.textContent = 'Example Domain - Modified by Gnosis Wraith';
}

return {
    contentAdded: true,
    elementsModified: 1
};
'@
    extract_markdown = $true
    markdown_options = @{
        include_links = $true
        include_images = $true
        extract_main_content = $true
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ JavaScript executed successfully!" -ForegroundColor Green
        Write-Host "   JS Result: $($response.result | ConvertTo-Json -Compress)" -ForegroundColor Gray
        
        if ($response.markdown) {
            Write-Host "`n📝 Markdown extracted ($($response.markdown.length) chars):" -ForegroundColor Green
            Write-Host "----------------------------------------" -ForegroundColor Gray
            # Show first 500 chars of markdown
            $preview = if ($response.markdown.content.Length -gt 500) {
                $response.markdown.content.Substring(0, 500) + "..."
            } else {
                $response.markdown.content
            }
            Write-Host $preview -ForegroundColor White
            Write-Host "----------------------------------------" -ForegroundColor Gray
            
            # Save to file
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $filename = "extracted_markdown_$timestamp.md"
            $response.markdown.content | Out-File -FilePath $filename -Encoding UTF8
            Write-Host "   Saved to: $filename" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

# Test 2: Clean up a messy page and extract clean markdown
Write-Host "`n📋 Test 2: Clean up page and extract simplified markdown" -ForegroundColor Yellow
$body = @{
    url = "https://news.ycombinator.com"
    javascript = @'
// Remove unnecessary elements
document.querySelectorAll('.hnmore, .comment-tree, .fatitem').forEach(el => el.remove());

// Simplify the page to just story titles and links
const stories = Array.from(document.querySelectorAll('.athing')).slice(0, 10);
const cleanContent = document.createElement('div');
cleanContent.innerHTML = '<h1>Top 10 Hacker News Stories</h1>';

stories.forEach((story, index) => {
    const titleLink = story.querySelector('.titleline > a');
    if (titleLink) {
        const storyDiv = document.createElement('div');
        storyDiv.innerHTML = `
            <h2>${index + 1}. ${titleLink.textContent}</h2>
            <p><a href="${titleLink.href}">Read more</a></p>
        `;
        cleanContent.appendChild(storyDiv);
    }
});

// Replace body content
document.body.innerHTML = '';
document.body.appendChild(cleanContent);

return {
    storiesProcessed: stories.length,
    pageSimplified: true
};
'@
    extract_markdown = $true
    take_screenshot = $true  # Also take a screenshot
    screenshot_options = @{
        full_page = $false
    }
    markdown_options = @{
        extract_main_content = $true
        skip_internal_links = $true
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ Page simplified and content extracted!" -ForegroundColor Green
        
        if ($response.markdown) {
            Write-Host "`n📝 Simplified markdown:" -ForegroundColor Green
            Write-Host "----------------------------------------" -ForegroundColor Gray
            Write-Host $response.markdown.content -ForegroundColor White
            Write-Host "----------------------------------------" -ForegroundColor Gray
            
            # Save markdown
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $mdFile = "hn_simplified_$timestamp.md"
            $response.markdown.content | Out-File -FilePath $mdFile -Encoding UTF8
            Write-Host "   Markdown saved to: $mdFile" -ForegroundColor Green
        }
        
        if ($response.screenshot) {
            # Save screenshot
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $pngFile = "hn_simplified_$timestamp.png"
            $bytes = [Convert]::FromBase64String($response.screenshot.data)
            [IO.File]::WriteAllBytes($pngFile, $bytes)
            Write-Host "   Screenshot saved to: $pngFile" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

# Test 3: Extract data, modify DOM, and get both results and markdown
Write-Host "`n📋 Test 3: Complex operation - extract data AND markdown" -ForegroundColor Yellow
$body = @{
    url = "https://example.com"
    javascript = @'
// First, extract some data
const originalTitle = document.title;
const linkCount = document.querySelectorAll('a').length;

// Then modify the page
document.body.innerHTML = `
<div style="max-width: 800px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
    <h1>Page Analysis Report</h1>
    <h2>Original Information</h2>
    <ul>
        <li><strong>Original Title:</strong> ${originalTitle}</li>
        <li><strong>Link Count:</strong> ${linkCount}</li>
        <li><strong>Analyzed at:</strong> ${new Date().toLocaleString()}</li>
    </ul>
    
    <h2>Extraction Capabilities</h2>
    <p>This demonstrates how Gnosis Wraith can:</p>
    <ol>
        <li>Execute JavaScript to analyze pages</li>
        <li>Modify the DOM based on analysis</li>
        <li>Extract the modified content as clean markdown</li>
        <li>Return both data and formatted content</li>
    </ol>
    
    <h2>Use Cases</h2>
    <p>Perfect for:</p>
    <ul>
        <li>Creating reports from web data</li>
        <li>Reformatting messy pages</li>
        <li>Extracting and restructuring content</li>
        <li>Building documentation from web sources</li>
    </ul>
    
    <blockquote>
        <p>"Transform any webpage into structured, clean content with JavaScript + Markdown extraction!"</p>
    </blockquote>
</div>
`;

// Return both data and indicate success
return {
    originalData: {
        title: originalTitle,
        linkCount: linkCount
    },
    reportGenerated: true,
    timestamp: new Date().toISOString()
};
'@
    extract_markdown = $true
    take_screenshot = $true
    markdown_options = @{
        include_links = $true
        extract_main_content = $true
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ Complex operation completed!" -ForegroundColor Green
        Write-Host "`nJavaScript returned data:" -ForegroundColor Yellow
        $response.result | ConvertTo-Json -Depth 5
        
        if ($response.markdown) {
            Write-Host "`n📝 Generated report as markdown:" -ForegroundColor Green
            Write-Host "----------------------------------------" -ForegroundColor Gray
            Write-Host $response.markdown.content -ForegroundColor White
            Write-Host "----------------------------------------" -ForegroundColor Gray
            
            # Save both files
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            
            # Save markdown
            $mdFile = "analysis_report_$timestamp.md"
            $response.markdown.content | Out-File -FilePath $mdFile -Encoding UTF8
            Write-Host "`n   Markdown saved to: $mdFile" -ForegroundColor Green
            
            # Save JSON data
            $jsonFile = "analysis_data_$timestamp.json"
            $response.result | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonFile -Encoding UTF8
            Write-Host "   Data saved to: $jsonFile" -ForegroundColor Green
        }
        
        if ($response.screenshot) {
            $pngFile = "analysis_report_$timestamp.png"
            $bytes = [Convert]::FromBase64String($response.screenshot.data)
            [IO.File]::WriteAllBytes($pngFile, $bytes)
            Write-Host "   Screenshot saved to: $pngFile" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

Write-Host "`n✅ All tests completed!" -ForegroundColor Green
Write-Host "`nYou now have:" -ForegroundColor Cyan
Write-Host "  • JavaScript execution results (data)" -ForegroundColor Gray
Write-Host "  • Markdown extraction of the modified DOM" -ForegroundColor Gray
Write-Host "  • Screenshots of the final page state" -ForegroundColor Gray
Write-Host "`nPerfect for creating reports, documentation, and analysis!" -ForegroundColor Yellow