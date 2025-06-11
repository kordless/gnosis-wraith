# Hacker News JavaScript Execution Test - Fixed Version
# This script tests the JavaScript execution API by extracting stories from Hacker News

param(
    [Parameter(Mandatory=$false)]
    [string]$Token = $env:GNOSIS_API_TOKEN,
    
    [Parameter(Mandatory=$false)]
    [string]$BaseUrl = "http://localhost:5678"
)

# Check if token is provided
if (-not $Token) {
    Write-Host "Error: No API token provided!" -ForegroundColor Red
    Write-Host "Usage: .\test_hackernews_fixed.ps1 -Token YOUR_TOKEN" -ForegroundColor Yellow
    Write-Host "Or set environment variable: `$env:GNOSIS_API_TOKEN = 'YOUR_TOKEN'" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Testing JavaScript Execution on Hacker News" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Cyan

# Set up headers
$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

# Test 1: Basic - Get page title
Write-Host "`n📋 Test 1: Get Page Title" -ForegroundColor Yellow
$body = @{
    url = "https://news.ycombinator.com"
    javascript = "return document.title;"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ Success!" -ForegroundColor Green
        Write-Host "   Title: $($response.result)" -ForegroundColor Gray
        Write-Host "   Execution time: $($response.execution_time)ms" -ForegroundColor Gray
    } else {
        Write-Host "❌ Failed: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

# Test 2: Extract top stories with better selectors
Write-Host "`n📋 Test 2: Extract Top 10 Stories (Improved)" -ForegroundColor Yellow
$body = @{
    url = "https://news.ycombinator.com"
    javascript = @'
// Extract stories from Hacker News with better selectors
const stories = [];

// Get all story title links
const titleLinks = document.querySelectorAll('.titleline > a');

// Process up to 10 stories
for (let i = 0; i < Math.min(10, titleLinks.length); i++) {
    const link = titleLinks[i];
    
    // Get the story row (parent of parent)
    const storyRow = link.closest('tr.athing');
    if (!storyRow) continue;
    
    // Get the metadata row (next sibling)
    const metaRow = storyRow.nextElementSibling;
    
    // Extract data
    const story = {
        rank: i + 1,
        title: link.textContent.trim(),
        url: link.href,
        domain: link.hostname || 'news.ycombinator.com'
    };
    
    // Get metadata if available
    if (metaRow) {
        const score = metaRow.querySelector('.score');
        const user = metaRow.querySelector('.hnuser');
        const age = metaRow.querySelector('.age');
        const commentsLink = Array.from(metaRow.querySelectorAll('a'))
            .find(a => a.textContent.includes('comment'));
        
        story.points = score ? score.textContent : '0 points';
        story.user = user ? user.textContent : 'unknown';
        story.age = age ? age.textContent : 'unknown';
        story.comments = commentsLink ? commentsLink.textContent : '0 comments';
    } else {
        story.points = '0 points';
        story.user = 'unknown';
        story.age = 'unknown';
        story.comments = '0 comments';
    }
    
    stories.push(story);
}

return {
    count: stories.length,
    stories: stories
};
'@
    options = @{
        wait_before = 3000
        timeout = 30000
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        $result = $response.result
        Write-Host "✅ Success! Found $($result.count) stories" -ForegroundColor Green
        
        # Display the stories
        foreach ($story in $result.stories) {
            Write-Host "`n$($story.rank). $($story.title)" -ForegroundColor White
            Write-Host "   🔗 $($story.domain)" -ForegroundColor Blue
            Write-Host "   📊 $($story.points) by $($story.user) ($($story.age))" -ForegroundColor Gray
            Write-Host "   💬 $($story.comments)" -ForegroundColor Gray
        }
    } else {
        Write-Host "❌ Failed: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Yellow
}

# Test 3: Simple data extraction
Write-Host "`n📋 Test 3: Count Elements on Page" -ForegroundColor Yellow
$body = @{
    url = "https://news.ycombinator.com"
    javascript = @'
// Count various elements
return {
    totalLinks: document.querySelectorAll('a').length,
    storyLinks: document.querySelectorAll('.titleline > a').length,
    users: document.querySelectorAll('.hnuser').length,
    scores: document.querySelectorAll('.score').length
};
'@
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ Success! Page statistics:" -ForegroundColor Green
        $stats = $response.result
        Write-Host "   Total links: $($stats.totalLinks)" -ForegroundColor Gray
        Write-Host "   Story links: $($stats.storyLinks)" -ForegroundColor Gray
        Write-Host "   User mentions: $($stats.users)" -ForegroundColor Gray
        Write-Host "   Score elements: $($stats.scores)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Failed: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

# Test 4: Test validation with safe code
Write-Host "`n📋 Test 4: Validate Safe Code" -ForegroundColor Yellow
$body = @{
    javascript = "return document.querySelectorAll('a').length;"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/validate" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.is_safe) {
        Write-Host "✅ Code validated as safe!" -ForegroundColor Green
    } else {
        Write-Host "❌ Code marked as unsafe: $($response.violations -join ', ')" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

# Test 5: Test validation with dangerous code
Write-Host "`n📋 Test 5: Validate Dangerous Code (Should Fail)" -ForegroundColor Yellow
$body = @{
    javascript = "eval('alert(1)');"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/validate" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.is_safe -eq $false) {
        Write-Host "✅ Correctly blocked dangerous code!" -ForegroundColor Green
        Write-Host "   Violations: $($response.violations -join ', ')" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Warning: Dangerous code was not blocked!" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

Write-Host "`n✅ All tests completed!" -ForegroundColor Green