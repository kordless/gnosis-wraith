# Generated PowerShell script for: ${query}

class GnosisWraithClient {
    [string]$ServerUrl
    
    GnosisWraithClient([string]$serverUrl = "http://localhost:5678") {
        $this.ServerUrl = $serverUrl
    }
    
    [object] Crawl([string]$url, [hashtable]$options = @{}) {
        $payload = @{ url = $url } + $options
        $body = $payload | ConvertTo-Json -Depth 10
        
        try {
            $response = Invoke-RestMethod -Uri "$($this.ServerUrl)/api/crawl" -Method Post -Body $body -ContentType "application/json"
            return $response
        }
        catch {
            throw "Crawl failed: $($_.Exception.Message)"
        }
    }
}

# Usage example based on query: ${query}
$client = [GnosisWraithClient]::new()
$result = $client.Crawl("https://example.com")
$result | ConvertTo-Json -Depth 10