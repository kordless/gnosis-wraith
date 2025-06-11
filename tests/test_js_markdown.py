#!/usr/bin/env python3
"""Test JavaScript execution with markdown extraction"""

import requests
import json
import sys

# Get token from command line or environment
token = sys.argv[1] if len(sys.argv) > 1 else "YOUR_TOKEN_HERE"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("📝 Testing JavaScript + Markdown Extraction")
print("=" * 50)

# Test: Modify page and extract markdown
payload = {
    "url": "https://example.com",
    "javascript": """
// Add custom content
const article = document.createElement('article');
article.innerHTML = `
    <h1>JavaScript-Generated Content</h1>
    <p>This was added by Gnosis Wraith!</p>
    <h2>Features</h2>
    <ul>
        <li>Execute JavaScript</li>
        <li>Extract markdown</li>
        <li>Take screenshots</li>
    </ul>
`;
document.body.insertBefore(article, document.body.firstChild);
return { success: true, elementsAdded: 1 };
""",
    "extract_markdown": True,
    "take_screenshot": True,
    "markdown_options": {
        "include_links": True,
        "extract_main_content": True
    }
}

try:
    response = requests.post(
        "http://localhost:5678/api/v2/execute",
        json=payload,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get('success'):
            print("✅ JavaScript executed successfully!")
            print(f"   Result: {result.get('result')}")
            
            if result.get('markdown'):
                print(f"\n📝 Markdown extracted ({result['markdown']['length']} chars):")
                print("-" * 40)
                print(result['markdown']['content'][:500] + "...")
                print("-" * 40)
                
                # Save markdown
                with open('extracted.md', 'w', encoding='utf-8') as f:
                    f.write(result['markdown']['content'])
                print("   Saved to: extracted.md")
            
            if result.get('screenshot'):
                import base64
                img_data = base64.b64decode(result['screenshot']['data'])
                with open('screenshot.png', 'wb') as f:
                    f.write(img_data)
                print("📸 Screenshot saved to: screenshot.png")
        else:
            print(f"❌ Execution failed: {result.get('error')}")
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")