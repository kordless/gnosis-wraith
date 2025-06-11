# Transform Example.com into a Dumpster Fire 🔥
# This test demonstrates complete DOM manipulation with JavaScript

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

Write-Host "🔥 Transforming Example.com into Dumpster Fire" -ForegroundColor Red
Write-Host ("=" * 50) -ForegroundColor Yellow

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

# The transformation JavaScript
$body = @{
    url = "https://example.com"
    javascript = @'
// Transform example.com into a glorious dumpster fire website

// First, clear everything
document.body.innerHTML = '';

// Set the dumpster fire theme
document.body.style.cssText = `
    background: linear-gradient(45deg, #ff6b6b, #ff8e53, #ff6b6b);
    font-family: 'Comic Sans MS', cursive;
    padding: 0;
    margin: 0;
    min-height: 100vh;
    animation: fireGlow 2s ease-in-out infinite;
`;

// Add the CSS animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fireGlow {
        0%, 100% { background: linear-gradient(45deg, #ff6b6b, #ff8e53, #ff6b6b); }
        50% { background: linear-gradient(45deg, #ff8e53, #ff6b6b, #ff8e53); }
    }
    @keyframes burn {
        0% { transform: translateY(0) rotate(0deg); opacity: 1; }
        100% { transform: translateY(-100px) rotate(180deg); opacity: 0; }
    }
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
    .fire-emoji {
        position: fixed;
        font-size: 30px;
        animation: burn 3s infinite;
    }
    .shake {
        animation: shake 0.5s infinite;
    }
    .marquee {
        animation: scroll-left 10s linear infinite;
        white-space: nowrap;
    }
    @keyframes scroll-left {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
`;
document.head.appendChild(style);

// Create the main dumpster fire container
const container = document.createElement('div');
container.style.cssText = 'max-width: 800px; margin: 0 auto; padding: 20px; text-align: center;';

// Add the header
container.innerHTML = `
    <h1 style="font-size: 72px; color: #fff; text-shadow: 3px 3px 6px rgba(0,0,0,0.5); margin: 20px 0;" class="shake">
        🔥 DUMPSTER.COM 🔥
    </h1>
    
    <div class="marquee" style="background: #ffeb3b; color: #000; padding: 10px; font-size: 24px; margin: 20px 0;">
        🚨 EVERYTHING IS FINE! 🚨 THIS IS FINE! 🚨 ABSOLUTELY NOTHING WRONG HERE! 🚨
    </div>
    
    <h2 style="color: #fff; font-size: 36px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
        Welcome to the Internet's Hottest Mess! 🗑️🔥
    </h2>
    
    <div style="background: rgba(0,0,0,0.3); padding: 20px; margin: 20px 0; border-radius: 10px;">
        <h3 style="color: #ffeb3b; font-size: 28px;">Today's Dumpster Fire Features:</h3>
        <ul style="list-style: none; padding: 0; color: #fff; font-size: 20px; text-align: left; max-width: 500px; margin: 0 auto;">
            <li>🔥 404 errors that lead to more 404 errors</li>
            <li>🔥 Forms that submit to /dev/null</li>
            <li>🔥 Cookies that delete themselves</li>
            <li>🔥 A search bar that only finds disappointment</li>
            <li>🔥 Terms of Service written in wingdings</li>
            <li>🔥 Support chat staffed by angry raccoons</li>
        </ul>
    </div>
    
    <div style="margin: 30px 0;">
        <button style="
            font-size: 24px; 
            padding: 15px 30px; 
            background: #ff6b6b; 
            color: white; 
            border: none; 
            border-radius: 50px; 
            cursor: pointer;
            font-family: 'Comic Sans MS';
            transform: rotate(-5deg);
            box-shadow: 5px 5px 10px rgba(0,0,0,0.3);
        " onclick="alert('🔥 Congratulations! You just made it worse! 🔥')">
            MAKE IT WORSE
        </button>
    </div>
    
    <div style="background: #000; color: #0f0; font-family: monospace; padding: 20px; margin: 20px 0; text-align: left;">
        <pre>
SYSTEM ERROR 0x0000FIRE
The operation completed unsuccessfully.
* Your data has been encrypted by raccoons
* Please insert 3.5" floppy disk to continue
* Press any key to make things worse
* Have you tried setting it on fire?
        </pre>
    </div>
    
    <div style="color: #fff; font-size: 18px; margin-top: 40px;">
        <p>🏆 Proud winner of "Worst Website 2024" 🏆</p>
        <p>⭐ Rated -5 stars on TrustPilot ⭐</p>
        <p>🎖️ "It's so bad it's good" - Nobody 🎖️</p>
    </div>
    
    <footer style="margin-top: 50px; color: #fff; opacity: 0.7;">
        <p>© 2024 Dumpster.com - Where Good Design Comes to Die</p>
        <p style="font-size: 12px;">Not affiliated with actual dumpsters. Actual dumpsters have standards.</p>
    </footer>
`;

document.body.appendChild(container);

// Add floating fire emojis
for (let i = 0; i < 20; i++) {
    const fire = document.createElement('div');
    fire.className = 'fire-emoji';
    fire.textContent = '🔥';
    fire.style.left = Math.random() * 100 + '%';
    fire.style.top = Math.random() * 100 + '%';
    fire.style.animationDelay = Math.random() * 3 + 's';
    document.body.appendChild(fire);
}

// Change the title
document.title = "🔥 Dumpster.com - Everything is Fine! 🔥";

// Add a favicon (dumpster emoji as data URI)
const link = document.querySelector("link[rel*='icon']") || document.createElement('link');
link.type = 'image/x-icon';
link.rel = 'shortcut icon';
link.href = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🗑️</text></svg>';
document.getElementsByTagName('head')[0].appendChild(link);

// Return transformation summary
return {
    success: true,
    message: "Successfully transformed example.com into a dumpster fire!",
    features: {
        fireEmojis: 20,
        comicSans: true,
        angryRaccoons: "implied",
        userExperience: "catastrophic",
        designPrinciples: "violated"
    },
    timestamp: new Date().toISOString()
};
'@
    extract_markdown = $true
    take_screenshot = $true
    screenshot_options = @{
        full_page = $true
    }
    options = @{
        wait_after = 3000  # Give time for animations to start
    }
} | ConvertTo-Json -Depth 10

try {
    Write-Host "`n🚀 Executing dumpster fire transformation..." -ForegroundColor Yellow
    
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    if ($response.success) {
        Write-Host "✅ Transformation complete!" -ForegroundColor Green
        
        # Show JavaScript execution results
        Write-Host "`n📊 Transformation Results:" -ForegroundColor Cyan
        $response.result | ConvertTo-Json -Depth 5
        
        # Save and display markdown
        if ($response.markdown) {
            Write-Host "`n📝 Markdown extracted from the dumpster fire:" -ForegroundColor Yellow
            Write-Host ("=" * 50) -ForegroundColor Red
            
            # Show first 1000 chars
            $preview = if ($response.markdown.content.Length -gt 1000) {
                $response.markdown.content.Substring(0, 1000) + "`n... (truncated)"
            } else {
                $response.markdown.content
            }
            Write-Host $preview -ForegroundColor White
            Write-Host ("=" * 50) -ForegroundColor Red
            
            # Save markdown
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $mdFile = "dumpster_fire_$timestamp.md"
            $response.markdown.content | Out-File -FilePath $mdFile -Encoding UTF8
            Write-Host "`n📄 Full markdown saved to: $mdFile" -ForegroundColor Green
        }
        
        # Save screenshot
        if ($response.screenshot) {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $pngFile = "dumpster_fire_$timestamp.png"
            $bytes = [Convert]::FromBase64String($response.screenshot.data)
            [IO.File]::WriteAllBytes($pngFile, $bytes)
            Write-Host "📸 Screenshot saved to: $pngFile" -ForegroundColor Green
            Write-Host "   (Open this to see the glorious dumpster fire!)" -ForegroundColor Yellow
        }
        
        Write-Host "`n🎉 Transformation Summary:" -ForegroundColor Magenta
        Write-Host "   • example.com ➜ dumpster.com ✓" -ForegroundColor White
        Write-Host "   • Professional design ➜ Comic Sans chaos ✓" -ForegroundColor White
        Write-Host "   • Clean layout ➜ Burning garbage ✓" -ForegroundColor White
        Write-Host "   • User trust ➜ Angry raccoons ✓" -ForegroundColor White
        Write-Host "`n🔥 Mission accomplished! 🔥" -ForegroundColor Red
        
    } else {
        Write-Host "❌ Transformation failed: $($response.error)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

Write-Host "`n💡 Pro tip: Check the PNG file to see the full dumpster fire in all its glory!" -ForegroundColor Cyan