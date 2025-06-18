# Test JavaScript Execution with Gnosis Wraith
# This script demonstrates JavaScript execution capabilities

# Load helper functions
. "$env:USERPROFILE\.gnosis-wraith\GnosisHelper.ps1"

Write-Host "`nGnosis Wraith JavaScript Execution Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Test 1: Basic JavaScript Execution
Write-Host "`n1. Basic JavaScript Execution" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/execute" -Body @{
    url = "https://example.com"
    javascript = "return document.title;"
}

if ($result.success) {
    Write-Host "✓ Execution successful!" -ForegroundColor Green
    Write-Host "  Result: $($result.result)" -ForegroundColor Gray
    Write-Host "  Execution time: $($result.execution_time)ms" -ForegroundColor Gray
} else {
    Write-Host "✗ Execution failed: $($result.error)" -ForegroundColor Red
}

# Test 2: Extract All Links
Write-Host "`n2. Extract All Links from Hacker News" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/execute" -Body @{
    url = "https://news.ycombinator.com"
    javascript = @"
// Hacker News uses different selectors - let's try multiple options
const selectors = [
    '.titleline > a',           // Current main selector
    'a.storylink',              // Legacy selector
    'a.titlelink',              // Another legacy selector
    '.athing .title > a',       // Alternative structure
    'span.titleline > a'        // With span wrapper
];

let links = [];
for (const selector of selectors) {
    const found = Array.from(document.querySelectorAll(selector));
    if (found.length > 0) {
        console.log(`Found ${found.length} links with selector: ${selector}`);
        links = found;
        break;
    }
}

// If still no links, try a more general approach
if (links.length === 0) {
    // Find all links that look like story titles
    links = Array.from(document.querySelectorAll('a')).filter(a => {
        const parent = a.parentElement;
        return parent && (
            parent.className.includes('title') ||
            parent.className.includes('storylink') ||
            parent.className.includes('titleline')
        ) && a.href && !a.href.includes('item?id=');
    });
}

return links.slice(0, 10).map(link => ({
    text: link.textContent.trim(),
    href: link.href,
    selector: link.parentElement?.className || 'unknown'
}));
"@
}

if ($result.success) {
    Write-Host "✓ Links extracted!" -ForegroundColor Green
    $links = $result.result
    if ($links.Count -eq 0) {
        Write-Host "  ⚠ No links found - HN might have changed their HTML structure" -ForegroundColor Yellow
        Write-Host "  Try running with javascript_enabled = true" -ForegroundColor Yellow
    } else {
        Write-Host "  Found $($links.Count) links" -ForegroundColor Gray
        foreach ($link in $links) {
            Write-Host "  - $($link.text)" -ForegroundColor Gray
            Write-Host "    $($link.href)" -ForegroundColor DarkGray
            if ($link.selector) {
                Write-Host "    (selector: $($link.selector))" -ForegroundColor DarkGray
            }
        }
    }
} else {
    Write-Host "✗ Link extraction failed: $($result.error)" -ForegroundColor Red
}

# Test 3: Get Page Metrics
Write-Host "`n3. Get Page Metrics" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/execute" -Body @{
    url = "https://www.wikipedia.org"
    javascript = @"
return {
    title: document.title,
    linkCount: document.querySelectorAll('a').length,
    imageCount: document.querySelectorAll('img').length,
    headingCount: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
    formCount: document.querySelectorAll('form').length,
    scriptCount: document.querySelectorAll('script').length,
    metaTags: Array.from(document.querySelectorAll('meta')).map(m => ({
        name: m.getAttribute('name'),
        content: m.getAttribute('content')
    })).filter(m => m.name)
};
"@
}

if ($result.success) {
    Write-Host "✓ Metrics collected!" -ForegroundColor Green
    $metrics = $result.result
    Write-Host "  Title: $($metrics.title)" -ForegroundColor Gray
    Write-Host "  Links: $($metrics.linkCount)" -ForegroundColor Gray
    Write-Host "  Images: $($metrics.imageCount)" -ForegroundColor Gray
    Write-Host "  Headings: $($metrics.headingCount)" -ForegroundColor Gray
    Write-Host "  Forms: $($metrics.formCount)" -ForegroundColor Gray
    Write-Host "  Scripts: $($metrics.scriptCount)" -ForegroundColor Gray
    Write-Host "  Meta tags: $($metrics.metaTags.Count)" -ForegroundColor Gray
} else {
    Write-Host "✗ Metrics collection failed: $($result.error)" -ForegroundColor Red
}

# Test 4: Complex Data Extraction
Write-Host "`n4. Extract Structured Data from GitHub Trending" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/execute" -Body @{
    url = "https://github.com/trending"
    javascript = @"
const repos = Array.from(document.querySelectorAll('article.Box-row')).slice(0, 5);
return repos.map(repo => {
    const link = repo.querySelector('h2 a');
    const description = repo.querySelector('p');
    const language = repo.querySelector('[itemprop="programmingLanguage"]');
    const stars = repo.querySelector('a[href*="/stargazers"]');
    const forks = repo.querySelector('a[href*="/forks"]');
    
    return {
        name: link ? link.textContent.trim().replace(/\s+/g, ' ') : '',
        url: link ? 'https://github.com' + link.getAttribute('href') : '',
        description: description ? description.textContent.trim() : '',
        language: language ? language.textContent.trim() : 'Unknown',
        stars: stars ? stars.textContent.trim() : '0',
        forks: forks ? forks.textContent.trim() : '0'
    };
});
"@
}

if ($result.success -and $result.result) {
    Write-Host "✓ Trending repos extracted!" -ForegroundColor Green
    foreach ($repo in $result.result) {
        Write-Host "`n  Repository: $($repo.name)" -ForegroundColor Cyan
        Write-Host "  URL: $($repo.url)" -ForegroundColor Gray
        Write-Host "  Description: $($repo.description)" -ForegroundColor Gray
        Write-Host "  Language: $($repo.language)" -ForegroundColor Yellow
        Write-Host "  Stars: $($repo.stars) | Forks: $($repo.forks)" -ForegroundColor Gray
    }
} else {
    Write-Host "✗ Repo extraction failed: $($result.error)" -ForegroundColor Red
}

# Test 5: Wait and Extract Dynamic Content
Write-Host "`n5. Extract Dynamic Content with Wait" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/execute" -Body @{
    url = "https://httpbin.org/delay/1"
    javascript = @"
// Wrap in async function to use await
(async () => {
    // Wait for any dynamic content
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Extract JSON response if available
    const pre = document.querySelector('pre');
    if (pre) {
        try {
            return JSON.parse(pre.textContent);
        } catch (e) {
            return { text: pre.textContent };
        }
    }
    return { error: 'No content found' };
})()
"@
    javascript_enabled = $true
    javascript_settle_time = 2000
}

if ($result.success) {
    Write-Host "✓ Dynamic content extracted!" -ForegroundColor Green
    Write-Host "  Result: $($result.result | ConvertTo-Json -Compress)" -ForegroundColor Gray
} else {
    Write-Host "✗ Dynamic extraction failed: $($result.error)" -ForegroundColor Red
}

Write-Host "`nJavaScript execution tests completed!" -ForegroundColor Cyan