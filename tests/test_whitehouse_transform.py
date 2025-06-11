#!/usr/bin/env python3
"""Transform webpage content and capture screenshot"""

import requests
import json
import sys
import base64
from datetime import datetime

# Get token from command line or environment
token = sys.argv[1] if len(sys.argv) > 1 else "YOUR_TOKEN_HERE"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("🔥 Transforming White House Website")
print("=" * 50)

# JavaScript to replace "White" with "Dumpster Fire" and "work" with "bullshit"
transform_js = """
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
"""

# Execute the transformation
payload = {
    "url": "https://www.whitehouse.gov",
    "javascript": transform_js,
    "take_screenshot": True,
    "extract_markdown": True,
    "screenshot_options": {
        "full_page": False  # Just capture viewport
    },
    "options": {
        "wait_before": 3000,  # Wait for page to load
        "wait_after": 2000    # Wait after transformation
    }
}

try:
    print("\n🚀 Executing transformation...")
    response = requests.post(
        "http://localhost:5678/api/v2/execute",
        json=payload,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get('success'):
            print("✅ Transformation successful!")
            print(f"   Result: {result.get('result')}")
            
            # Save screenshot
            if result.get('screenshot'):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"dumpster_fire_house_{timestamp}.png"
                
                img_data = base64.b64decode(result['screenshot']['data'])
                with open(filename, 'wb') as f:
                    f.write(img_data)
                
                print(f"\n📸 Screenshot saved to: {filename}")
                print(f"   Size: {len(img_data):,} bytes")
            
            # Save markdown
            if result.get('markdown'):
                md_filename = f"dumpster_fire_house_{timestamp}.md"
                with open(md_filename, 'w', encoding='utf-8') as f:
                    f.write(result['markdown']['content'])
                
                print(f"📝 Markdown saved to: {md_filename}")
                
                # Show preview of transformed content
                print("\n📄 Content preview:")
                print("-" * 40)
                preview = result['markdown']['content'][:500]
                if 'Dumpster Fire' in preview:
                    print("✅ Transformation confirmed in content!")
                print(preview + "...")
                print("-" * 40)
            
            print("\n🎉 Mission accomplished!")
            print("   The White House is now the Dumpster Fire House! 🔥")
            
        else:
            print(f"❌ Execution failed: {result.get('error')}")
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n💡 Tip: Open the PNG file to see the transformed webpage!")