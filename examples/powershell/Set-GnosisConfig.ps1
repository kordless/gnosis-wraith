# Gnosis Wraith Configuration Script
# This script helps you set up and save your API tokens and preferences

param(
    [switch]$Show,
    [switch]$Reset
)

$configPath = "$env:USERPROFILE\.gnosis-wraith\config.json"
$configDir = Split-Path $configPath -Parent

# Create config directory if it doesn't exist
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# Function to encrypt sensitive data (basic protection)
function Protect-String {
    param([string]$String)
    if ([string]::IsNullOrEmpty($String)) { return "" }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($String)
    $protected = [System.Convert]::ToBase64String($bytes)
    return $protected
}

function Unprotect-String {
    param([string]$String)
    if ([string]::IsNullOrEmpty($String)) { return "" }
    try {
        $bytes = [System.Convert]::FromBase64String($String)
        $unprotected = [System.Text.Encoding]::UTF8.GetString($bytes)
        return $unprotected
    } catch {
        return $String
    }
}

# Load existing config
$config = @{
    ServerUrl = "http://localhost:5678"
    ApiToken = ""
    LLMProvider = "anthropic"
    LLMModel = "claude-3-sonnet-20240229"
    AnthropicApiKey = ""
    OpenAIApiKey = ""
    GeminiApiKey = ""
    DefaultMarkdownMode = "enhanced"
    DefaultScreenshotMode = "top"
    DefaultOCR = $false
}

if (Test-Path $configPath) {
    $existingConfig = Get-Content $configPath | ConvertFrom-Json
    foreach ($key in $config.Keys) {
        if ($existingConfig.PSObject.Properties[$key]) {
            $config[$key] = $existingConfig.$key
        }
    }
}

# Show current config
if ($Show) {
    Write-Host "`nCurrent Gnosis Wraith Configuration:" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host "Server URL: $($config.ServerUrl)" -ForegroundColor Green
    Write-Host "API Token: $(if ($config.ApiToken) { '***' + $config.ApiToken.Substring([Math]::Max(0, $config.ApiToken.Length - 4)) } else { 'Not set' })" -ForegroundColor Green
    Write-Host "LLM Provider: $($config.LLMProvider)" -ForegroundColor Green
    Write-Host "LLM Model: $($config.LLMModel)" -ForegroundColor Green
    Write-Host "Anthropic API Key: $(if ($config.AnthropicApiKey) { '***' + (Unprotect-String $config.AnthropicApiKey).Substring([Math]::Max(0, (Unprotect-String $config.AnthropicApiKey).Length - 4)) } else { 'Not set' })" -ForegroundColor Green
    Write-Host "OpenAI API Key: $(if ($config.OpenAIApiKey) { '***' + (Unprotect-String $config.OpenAIApiKey).Substring([Math]::Max(0, (Unprotect-String $config.OpenAIApiKey).Length - 4)) } else { 'Not set' })" -ForegroundColor Green
    Write-Host "Gemini API Key: $(if ($config.GeminiApiKey) { '***' + (Unprotect-String $config.GeminiApiKey).Substring([Math]::Max(0, (Unprotect-String $config.GeminiApiKey).Length - 4)) } else { 'Not set' })" -ForegroundColor Green
    Write-Host "Default Markdown: $($config.DefaultMarkdownMode)" -ForegroundColor Green
    Write-Host "Default Screenshot: $($config.DefaultScreenshotMode)" -ForegroundColor Green
    Write-Host "Default OCR: $($config.DefaultOCR)" -ForegroundColor Green
    Write-Host "`nConfig file: $configPath" -ForegroundColor Yellow
    return
}

# Reset config
if ($Reset) {
    if (Test-Path $configPath) {
        Remove-Item $configPath -Force
        Write-Host "Configuration reset successfully!" -ForegroundColor Green
    }
    return
}

# Interactive configuration
Write-Host "`nGnosis Wraith Configuration Setup" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "Press Enter to keep current value, or type new value`n" -ForegroundColor Yellow

# Server URL
$newServerUrl = Read-Host "Server URL [$($config.ServerUrl)]"
if ($newServerUrl) { $config.ServerUrl = $newServerUrl }

# API Token
Write-Host "`nAPI Token (from Profile Settings in Gnosis Wraith UI)" -ForegroundColor Yellow
$currentTokenDisplay = if ($config.ApiToken) { "***" + $config.ApiToken.Substring([Math]::Max(0, $config.ApiToken.Length - 4)) } else { "Not set" }
$newApiToken = Read-Host "API Token [$currentTokenDisplay]"
if ($newApiToken) { $config.ApiToken = $newApiToken }

# LLM Provider
Write-Host "`nLLM Provider Options: anthropic, openai, gemini" -ForegroundColor Yellow
$newProvider = Read-Host "LLM Provider [$($config.LLMProvider)]"
if ($newProvider -and $newProvider -in @('anthropic', 'openai', 'gemini')) { 
    $config.LLMProvider = $newProvider 
}

# LLM Model
$modelOptions = @{
    anthropic = @("claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307")
    openai = @("gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo")
    gemini = @("gemini-pro", "gemini-pro-vision")
}

if ($config.LLMProvider -in $modelOptions.Keys) {
    Write-Host "`nAvailable models for $($config.LLMProvider):" -ForegroundColor Yellow
    $modelOptions[$config.LLMProvider] | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
}

$newModel = Read-Host "LLM Model [$($config.LLMModel)]"
if ($newModel) { $config.LLMModel = $newModel }

# API Keys
Write-Host "`nLLM API Keys (will be stored encoded)" -ForegroundColor Yellow

# Anthropic
$currentAnthropicDisplay = if ($config.AnthropicApiKey) { 
    $key = Unprotect-String $config.AnthropicApiKey
    "***" + $key.Substring([Math]::Max(0, $key.Length - 4)) 
} else { "Not set" }
$newAnthropicKey = Read-Host "Anthropic API Key [$currentAnthropicDisplay]"
if ($newAnthropicKey) { $config.AnthropicApiKey = Protect-String $newAnthropicKey }

# OpenAI
$currentOpenAIDisplay = if ($config.OpenAIApiKey) { 
    $key = Unprotect-String $config.OpenAIApiKey
    "***" + $key.Substring([Math]::Max(0, $key.Length - 4)) 
} else { "Not set" }
$newOpenAIKey = Read-Host "OpenAI API Key [$currentOpenAIDisplay]"
if ($newOpenAIKey) { $config.OpenAIApiKey = Protect-String $newOpenAIKey }

# Gemini
$currentGeminiDisplay = if ($config.GeminiApiKey) { 
    $key = Unprotect-String $config.GeminiApiKey
    "***" + $key.Substring([Math]::Max(0, $key.Length - 4)) 
} else { "Not set" }
$newGeminiKey = Read-Host "Gemini API Key [$currentGeminiDisplay]"
if ($newGeminiKey) { $config.GeminiApiKey = Protect-String $newGeminiKey }

# Default settings
Write-Host "`nDefault Crawl Settings" -ForegroundColor Yellow

# Markdown mode
Write-Host "Markdown modes: enhanced, basic, none" -ForegroundColor Gray
$newMarkdown = Read-Host "Default Markdown Mode [$($config.DefaultMarkdownMode)]"
if ($newMarkdown -and $newMarkdown -in @('enhanced', 'basic', 'none')) { 
    $config.DefaultMarkdownMode = $newMarkdown 
}

# Screenshot mode
Write-Host "Screenshot modes: off, top, full" -ForegroundColor Gray
$newScreenshot = Read-Host "Default Screenshot Mode [$($config.DefaultScreenshotMode)]"
if ($newScreenshot -and $newScreenshot -in @('off', 'top', 'full')) { 
    $config.DefaultScreenshotMode = $newScreenshot 
}

# OCR
$ocrInput = Read-Host "Enable OCR by default? (y/n) [$($config.DefaultOCR)]"
if ($ocrInput -eq 'y') { $config.DefaultOCR = $true }
elseif ($ocrInput -eq 'n') { $config.DefaultOCR = $false }

# Save config
$config | ConvertTo-Json | Set-Content $configPath

Write-Host "`nConfiguration saved successfully!" -ForegroundColor Green
Write-Host "Config file: $configPath" -ForegroundColor Yellow

# Create helper function file
$helperPath = "$configDir\GnosisHelper.ps1"
@'
# Gnosis Wraith PowerShell Helper Functions

function Get-GnosisConfig {
    $configPath = "$env:USERPROFILE\.gnosis-wraith\config.json"
    if (Test-Path $configPath) {
        $config = Get-Content $configPath | ConvertFrom-Json
        
        # Decode protected strings
        if ($config.AnthropicApiKey) {
            $bytes = [System.Convert]::FromBase64String($config.AnthropicApiKey)
            $config.AnthropicApiKey = [System.Text.Encoding]::UTF8.GetString($bytes)
        }
        if ($config.OpenAIApiKey) {
            $bytes = [System.Convert]::FromBase64String($config.OpenAIApiKey)
            $config.OpenAIApiKey = [System.Text.Encoding]::UTF8.GetString($bytes)
        }
        if ($config.GeminiApiKey) {
            $bytes = [System.Convert]::FromBase64String($config.GeminiApiKey)
            $config.GeminiApiKey = [System.Text.Encoding]::UTF8.GetString($bytes)
        }
        
        return $config
    }
    return $null
}

function Get-GnosisHeaders {
    param([string]$ApiToken)
    
    $config = Get-GnosisConfig
    $token = if ($ApiToken) { $ApiToken } else { $config.ApiToken }
    
    return @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
}

function Invoke-GnosisApi {
    param(
        [string]$Endpoint,
        [string]$Method = "POST",
        [object]$Body,
        [string]$ApiToken
    )
    
    $config = Get-GnosisConfig
    $baseUrl = $config.ServerUrl
    $headers = Get-GnosisHeaders -ApiToken $ApiToken
    
    $params = @{
        Uri = "$baseUrl$Endpoint"
        Method = $Method
        Headers = $headers
    }
    
    if ($Body) {
        if ($Body -is [string]) {
            $params.Body = $Body
        } else {
            $params.Body = $Body | ConvertTo-Json -Depth 10
        }
    }
    
    try {
        $response = Invoke-RestMethod @params
        return $response
    } catch {
        Write-Error "API Error: $_"
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $errorBody = $reader.ReadToEnd()
            Write-Error "Response: $errorBody"
        }
        return $null
    }
}

Write-Host "Gnosis Helper Functions Loaded" -ForegroundColor Green
'@ | Set-Content $helperPath

Write-Host "`nHelper functions saved to: $helperPath" -ForegroundColor Yellow
Write-Host "To use in scripts, add: . `"$helperPath`"" -ForegroundColor Cyan