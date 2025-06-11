# Transform White House Website to Dumpster Fire House
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

Write-Host "🔥 Transforming White House Website" -ForegroundColor Red
Write-Host ("=" * 50) -ForegroundColor Yellow

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

# JavaScript to replace "White" with "Dumpster Fire" and "work" with "bullshit"
$transformJS = @'
// Replace all instances of "White" with "Dumpster Fire" and "work" with "bullshit"
function replaceText(node) {
    if (node.nodeType === Node.TEXT_NODE) {
        // Replace White/white/WHITE
        node.textContent = node.textContent.replace(/White/g, 'Dumpster Fire');
        node.textContent = node.textContent.replace(/white/g, 'dumpster fire');
        node.textContent = node.textContent.replace(/WHITE/g, 'DUMPSTER FIRE');
        
        // Replace work/Work/WORK
        node.textContent = node.textContent.replace(/work/g, 'bullshit');
        node.textContent = node.textContent.replace(/Work/g, 'Bullshit');
        node.textContent = node.textContent.replace(/WORK/g, 'BULLSHIT');
    } else {
        for (let child of node.childNodes) {
            replaceText(child);
        }
    }
}

// Replace in the entire document
replaceText(document.body);

// Also update the title
document.title = document.title.replace(/White/g, 'Dumpster Fire');
document.title = document.title.replace(/white/g, 'dumpster fire');
document.title = document.title.replace(/work/g, 'bullshit');
document.title = document.title.replace(/Work/g, 'Bullshit');

// Update any alt text in images
document.querySelectorAll('img').forEach(img => {
    if (img.alt) {
        img.alt = img.alt.replace(/White/g, 'Dumpster Fire');
        img.alt = img.alt.replace(/white/g, 'dumpster fire');
        img.alt = img.alt.replace(/work/g, 'bullshit');
        img.alt = img.alt.replace(/Work/g, 'Bullshit');
    }
});

// Add some visual flair
const style = document.createElement('style');
style.textContent = `
    body {
        animation: fireGlow 3s ease-in-out infinite;
    }
    @keyframes fireGlow {
        0%, 100% { filter: hue-rotate(0deg) brightness(1); }
        50% { filter: hue-rotate(20deg) brightness(1.1); }
    }
`;
document.head.appendChild(style);

return {
    success: true,
    message: "Successfully transformed White House to Dumpster Fire House and work to bullshit!",
    transformations: {
        "White": "Dumpster Fire",
        "work": "bullshit"
    },
    timestamp: new Date().toISOString()
};
'@

$body = @{
    url = "https://www.whitehouse.gov"
    javascript = $transformJS
    take_screenshot = $true
    extract_markdown = $true
    screenshot_options = @{
        full_page = $false
    }
    options = @{
        wait_before = 3000
        wait_after = 2000
    }
} | ConvertTo-Json -Depth 10

try {
    Write-Host "`n🚀 Executing transformation..." -ForegroundColor Yellow
    
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ Transformation successful!" -ForegroundColor Green
        Write-Host "   Result: $($response.result | ConvertTo-Json -Compress)" -ForegroundColor Gray
        
        # Save screenshot
        if ($response.screenshot) {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $filename = "dumpster_fire_house_$timestamp.png"
            
            $bytes = [Convert]::FromBase64String($response.screenshot.data)
            [IO.File]::WriteAllBytes($filename, $bytes)
            
            Write-Host "`n📸 Screenshot saved to: $filename" -ForegroundColor Green
            Write-Host "   Size: $("{0:N0}" -f $bytes.Length) bytes" -ForegroundColor Gray
        }
        
        # Save markdown
        if ($response.markdown) {
            $mdFilename = "dumpster_fire_house_$timestamp.md"
            $response.markdown.content | Out-File -FilePath $mdFilename -Encoding UTF8
            
            Write-Host "📝 Markdown saved to: $mdFilename" -ForegroundColor Green
            
            # Check if transformation worked
            if ($response.markdown.content -match "Dumpster Fire") {
                Write-Host "`n✅ Transformation confirmed in content!" -ForegroundColor Green
            }
            
            # Show preview
            Write-Host "`n📄 Content preview:" -ForegroundColor Cyan
            Write-Host ("-" * 40) -ForegroundColor Gray
            $preview = if ($response.markdown.content.Length -gt 500) {
                $response.markdown.content.Substring(0, 500) + "..."
            } else {
                $response.markdown.content
            }
            Write-Host $preview -ForegroundColor White
            Write-Host ("-" * 40) -ForegroundColor Gray
        }
        
        Write-Host "`n🎉 Mission accomplished!" -ForegroundColor Magenta
        Write-Host "   The White House is now the Dumpster Fire House! 🔥" -ForegroundColor Red
        
    } else {
        Write-Host "❌ Execution failed: $($response.error)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

Write-Host "`n💡 Tip: Open the PNG file to see the transformed webpage!" -ForegroundColor Cyan