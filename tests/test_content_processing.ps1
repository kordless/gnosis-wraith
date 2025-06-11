# Test Content Processing Endpoints
# This script tests the analyze, clean, and summarize endpoints

param(
    [Parameter(Mandatory=$false)]
    [string]$Token = $env:GNOSIS_API_TOKEN,
    
    [Parameter(Mandatory=$false)]
    [string]$AnthropicToken = $env:ANTHROPIC_API_KEY,
    
    [Parameter(Mandatory=$false)]
    [string]$BaseUrl = "http://localhost:5678"
)

if (-not $Token) {
    Write-Host "Error: No API token provided!" -ForegroundColor Red
    Write-Host "Usage: .\test_content_processing.ps1 -Token <token> -AnthropicToken <token>"
    exit 1
}

if (-not $AnthropicToken) {
    Write-Host "Error: No Anthropic API token provided!" -ForegroundColor Red
    Write-Host "Set ANTHROPIC_API_KEY environment variable or use -AnthropicToken parameter"
    exit 1
}

Write-Host "🧪 Testing Content Processing API" -ForegroundColor Cyan
Write-Host "Gnosis Token: $($Token.Substring(0,10))..." -ForegroundColor Gray
Write-Host "Anthropic Token: $($AnthropicToken.Substring(0,10))..." -ForegroundColor Gray
Write-Host ("=" * 50) -ForegroundColor Yellow

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

# Sample content
$sampleContent = @'
# Breaking News: AI Revolution in Software Development

Published: January 6, 2025
By: Tech Reporter

In a groundbreaking development, artificial intelligence has transformed the landscape of software development. Major tech companies including Google, Microsoft, and OpenAI have announced new AI-powered tools that can write, debug, and optimize code with unprecedented accuracy.

## Key Developments

### 1. Code Generation
AI models can now generate complete applications from natural language descriptions. Developers report 10x productivity gains.

### 2. Bug Detection
Machine learning algorithms detect bugs before code is even run, reducing debugging time by 80%.

### 3. Performance Optimization
AI automatically optimizes code for better performance, often finding improvements human developers miss.

## Industry Impact

"This is the biggest shift in software development since the introduction of high-level programming languages," says Dr. Jane Smith, CTO of TechCorp.

### Statistics:
- 75% of developers now use AI tools daily
- Bug rates have decreased by 60%
- Development cycles shortened by 40%

Contact: tech@example.com
Advertisement: Try our AI coding assistant today!
'@

# Test 1: Content Analysis
Write-Host "`n🔍 Test 1: Content Analysis" -ForegroundColor Yellow
Write-Host "Testing entity extraction..." -ForegroundColor Gray

$body = @{
    content = $sampleContent
    analysis_type = "entities"
    llm_provider = "anthropic"
    llm_token = $AnthropicToken
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/analyze" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ Entity extraction successful!" -ForegroundColor Green
        Write-Host "   Analysis:" -ForegroundColor Gray
        $response.analysis | ConvertTo-Json -Depth 3
    } else {
        Write-Host "❌ Analysis failed: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# Test 2: Markdown Cleanup
Write-Host "`n🧹 Test 2: Markdown Cleanup" -ForegroundColor Yellow
Write-Host "Cleaning markdown with aggressive mode..." -ForegroundColor Gray

$body = @{
    markdown = $sampleContent
    goals = @("remove_ads", "remove_boilerplate", "fix_formatting")
    preserve = @("headers", "lists", "emphasis")
    aggressive = $true
    llm_provider = "anthropic"
    llm_token = $AnthropicToken
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/clean" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ Markdown cleanup successful!" -ForegroundColor Green
        Write-Host "   Improvements:" -ForegroundColor Gray
        Write-Host "   - Chars removed: $($response.improvements.chars_removed)" -ForegroundColor White
        Write-Host "   - Reduction: $($response.improvements.reduction_percentage)%" -ForegroundColor White
        Write-Host "`n   Cleaned preview:" -ForegroundColor Gray
        $preview = if ($response.markdown.Length -gt 300) {
            $response.markdown.Substring(0, 300) + "..."
        } else {
            $response.markdown
        }
        Write-Host $preview -ForegroundColor White
    } else {
        Write-Host "❌ Cleanup failed: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# Test 3: Content Summarization
Write-Host "`n📝 Test 3: Content Summarization" -ForegroundColor Yellow
Write-Host "Creating bullet point summary..." -ForegroundColor Gray

$body = @{
    content = $sampleContent
    summary_type = "bullet_points"
    max_length = 100
    output_format = "markdown"
    llm_provider = "anthropic"
    llm_token = $AnthropicToken
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/summarize" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ Summarization successful!" -ForegroundColor Green
        Write-Host "   Compression ratio: $($response.compression_ratio)" -ForegroundColor Gray
        Write-Host "`n   Summary:" -ForegroundColor Gray
        Write-Host $response.summary -ForegroundColor White
    } else {
        Write-Host "❌ Summarization failed: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# Test 4: Structured Data Extraction
Write-Host "`n🏗️ Test 4: Structured Data Extraction" -ForegroundColor Yellow
Write-Host "Extracting data according to schema..." -ForegroundColor Gray

$schema = @{
    type = "object"
    properties = @{
        title = @{ type = "string" }
        author = @{ type = "string" }
        date = @{ type = "string" }
        companies_mentioned = @{
            type = "array"
            items = @{ type = "string" }
        }
        key_statistics = @{
            type = "array"
            items = @{
                type = "object"
                properties = @{
                    metric = @{ type = "string" }
                    value = @{ type = "string" }
                }
            }
        }
    }
}

$body = @{
    content = $sampleContent
    schema = $schema
    llm_provider = "anthropic"
    llm_token = $AnthropicToken
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/extract" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ Data extraction successful!" -ForegroundColor Green
        Write-Host "   Extracted data:" -ForegroundColor Gray
        $response.data | ConvertTo-Json -Depth 5
    } else {
        Write-Host "❌ Extraction failed: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

Write-Host "`n✅ All tests completed!" -ForegroundColor Green