# Test Data Extraction with Gnosis Wraith
# This script demonstrates extracting structured data from various websites

# Load helper functions
. "$env:USERPROFILE\.gnosis-wraith\GnosisHelper.ps1"

Write-Host "`nGnosis Wraith Data Extraction Tests" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

# Test 1: Extract Product Information from Amazon
Write-Host "`n1. Extract Product Information" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/execute" -Body @{
    url = "https://www.amazon.com/dp/B08N5WRWNW"  # Echo Dot example
    javascript = @"
const result = {
    title: document.querySelector('#productTitle')?.textContent.trim(),
    price: document.querySelector('.a-price-whole')?.textContent.trim() || 
           document.querySelector('.a-price')?.textContent.trim(),
    rating: document.querySelector('span.a-icon-alt')?.textContent.trim(),
    availability: document.querySelector('#availability span')?.textContent.trim(),
    features: Array.from(document.querySelectorAll('.a-unordered-list.a-vertical.feature-bullets li span'))
        .map(el => el.textContent.trim())
        .filter(text => text && !text.includes('Make sure'))
        .slice(0, 5)
};
return result;
"@
    javascript_enabled = $true
    javascript_settle_time = 3000
}

if ($result.success -and $result.result.title) {
    Write-Host "✓ Product info extracted!" -ForegroundColor Green
    $product = $result.result
    Write-Host "  Title: $($product.title)" -ForegroundColor Gray
    Write-Host "  Price: $($product.price)" -ForegroundColor Gray
    Write-Host "  Rating: $($product.rating)" -ForegroundColor Gray
    Write-Host "  Availability: $($product.availability)" -ForegroundColor Gray
    if ($product.features) {
        Write-Host "  Features:" -ForegroundColor Gray
        foreach ($feature in $product.features) {
            Write-Host "    - $feature" -ForegroundColor DarkGray
        }
    }
} else {
    Write-Host "✗ Product extraction failed or no data found" -ForegroundColor Red
}

# Test 2: Extract News Headlines
Write-Host "`n2. Extract News Headlines from BBC" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/execute" -Body @{
    url = "https://www.bbc.com/news"
    javascript = @"
const headlines = Array.from(document.querySelectorAll('h3')).slice(0, 10);
return headlines.map(h => {
    const link = h.querySelector('a') || h.closest('a');
    return {
        text: h.textContent.trim(),
        url: link ? (link.href.startsWith('http') ? link.href : 'https://www.bbc.com' + link.href) : null
    };
}).filter(item => item.text && item.url);
"@
}

if ($result.success -and $result.result) {
    Write-Host "✓ Headlines extracted!" -ForegroundColor Green
    foreach ($headline in $result.result) {
        Write-Host "  • $($headline.text)" -ForegroundColor Gray
    }
} else {
    Write-Host "✗ Headline extraction failed" -ForegroundColor Red
}

# Test 3: Extract Stock Information
Write-Host "`n3. Extract Stock Data from Yahoo Finance" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/execute" -Body @{
    url = "https://finance.yahoo.com/quote/AAPL"
    javascript = @"
// Wait for data to load
await new Promise(resolve => setTimeout(resolve, 2000));

const getTextContent = (selector) => {
    const element = document.querySelector(selector);
    return element ? element.textContent.trim() : null;
};

return {
    symbol: 'AAPL',
    price: getTextContent('[data-symbol="AAPL"][data-field="regularMarketPrice"]'),
    change: getTextContent('[data-symbol="AAPL"][data-field="regularMarketChange"]'),
    changePercent: getTextContent('[data-symbol="AAPL"][data-field="regularMarketChangePercent"]'),
    dayRange: getTextContent('[data-test="DAYS_RANGE-value"]'),
    volume: getTextContent('[data-test="TD_VOLUME-value"]'),
    marketCap: getTextContent('[data-test="MARKET_CAP-value"]'),
    pe: getTextContent('[data-test="PE_RATIO-value"]'),
    time: new Date().toLocaleString()
};
"@
    javascript_enabled = $true
    javascript_settle_time = 3000
}

if ($result.success -and $result.result) {
    Write-Host "✓ Stock data extracted!" -ForegroundColor Green
    $stock = $result.result
    Write-Host "  Symbol: $($stock.symbol)" -ForegroundColor Gray
    Write-Host "  Price: $($stock.price)" -ForegroundColor Gray
    Write-Host "  Change: $($stock.change) ($($stock.changePercent))" -ForegroundColor Gray
    Write-Host "  Day Range: $($stock.dayRange)" -ForegroundColor Gray
    Write-Host "  Volume: $($stock.volume)" -ForegroundColor Gray
    Write-Host "  Market Cap: $($stock.marketCap)" -ForegroundColor Gray
    Write-Host "  P/E: $($stock.pe)" -ForegroundColor Gray
    Write-Host "  Time: $($stock.time)" -ForegroundColor Gray
} else {
    Write-Host "✗ Stock data extraction failed" -ForegroundColor Red
}

# Test 4: Extract Search Results
Write-Host "`n4. Extract DuckDuckGo Search Results" -ForegroundColor Yellow
$searchQuery = "gnosis wraith"
$result = Invoke-GnosisApi -Endpoint "/api/v2/execute" -Body @{
    url = "https://duckduckgo.com/?q=$([System.Uri]::EscapeDataString($searchQuery))"
    javascript = @"
// Wait for results to load
await new Promise(resolve => setTimeout(resolve, 2000));

const results = Array.from(document.querySelectorAll('[data-testid="result"]')).slice(0, 5);
return results.map(result => {
    const titleEl = result.querySelector('h2');
    const linkEl = result.querySelector('a[href]');
    const snippetEl = result.querySelector('[data-result="snippet"]');
    
    return {
        title: titleEl ? titleEl.textContent.trim() : '',
        url: linkEl ? linkEl.href : '',
        snippet: snippetEl ? snippetEl.textContent.trim() : ''
    };
}).filter(r => r.title && r.url);
"@
    javascript_enabled = $true
    javascript_settle_time = 3000
}

if ($result.success -and $result.result -and $result.result.Count -gt 0) {
    Write-Host "✓ Search results extracted!" -ForegroundColor Green
    foreach ($item in $result.result) {
        Write-Host "`n  Title: $($item.title)" -ForegroundColor Cyan
        Write-Host "  URL: $($item.url)" -ForegroundColor Gray
        Write-Host "  Snippet: $($item.snippet)" -ForegroundColor DarkGray
    }
} else {
    Write-Host "✗ Search results extraction failed" -ForegroundColor Red
}

# Test 5: Extract Table Data
Write-Host "`n5. Extract Table Data from Wikipedia" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/execute" -Body @{
    url = "https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)"
    javascript = @"
const table = document.querySelector('table.wikitable');
if (!table) return { error: 'Table not found' };

const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
const rows = Array.from(table.querySelectorAll('tr')).slice(1, 11); // Top 10 countries

const data = rows.map(row => {
    const cells = Array.from(row.querySelectorAll('td'));
    return {
        rank: cells[0]?.textContent.trim(),
        country: cells[1]?.textContent.trim(),
        population: cells[2]?.textContent.trim(),
        percentage: cells[3]?.textContent.trim()
    };
}).filter(row => row.country);

return {
    title: document.querySelector('h1').textContent.trim(),
    headers: headers.slice(0, 4),
    data: data
};
"@
}

if ($result.success -and $result.result.data) {
    Write-Host "✓ Table data extracted!" -ForegroundColor Green
    Write-Host "  Title: $($result.result.title)" -ForegroundColor Gray
    Write-Host "`n  Top 10 Countries by Population:" -ForegroundColor Gray
    
    foreach ($country in $result.result.data) {
        Write-Host "    $($country.rank). $($country.country): $($country.population)" -ForegroundColor DarkGray
    }
} else {
    Write-Host "✗ Table extraction failed" -ForegroundColor Red
}

Write-Host "`nData extraction tests completed!" -ForegroundColor Cyan