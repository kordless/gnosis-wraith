# Gnosis Wraith PowerShell API Examples

This directory contains PowerShell examples for testing the Gnosis Wraith API v2 endpoints.

## Setup

1. First, set your API token in the scripts or use the `Set-GnosisConfig.ps1` script
2. Make sure your Gnosis Wraith server is running (default: http://localhost:5678)
3. Run any of the example scripts

## Available Examples

- `Set-GnosisConfig.ps1` - Configure your API tokens and preferences
- `Test-BasicCrawl.ps1` - Basic web crawling examples
- `Test-JavaScriptExecution.ps1` - JavaScript execution examples
- `Test-DataExtraction.ps1` - Extract structured data from websites
- `Test-LLMIntegration.ps1` - LLM-powered JavaScript generation
- `Test-PageInteraction.ps1` - Automated page interactions
- `Test-SecurityValidation.ps1` - Security validation tests

## Quick Start

```powershell
# Set your configuration
.\Set-GnosisConfig.ps1

# Run a basic test
.\Test-BasicCrawl.ps1

# Extract data from a website
.\Test-DataExtraction.ps1
```