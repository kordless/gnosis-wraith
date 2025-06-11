#!/usr/bin/env python3
"""Test content processing endpoints (analyze, clean, summarize)"""

import requests
import json
import sys
import os

# Get token from command line or environment
token = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GNOSIS_API_TOKEN", "YOUR_TOKEN_HERE")
anthropic_token = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_KEY")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

base_url = "http://localhost:5678/api/v2"

# Sample content for testing
sample_content = """
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

"This is the biggest shift in software development since the introduction of high-level programming languages," says Dr. Jane Smith, CTO of TechCorp. "We're seeing junior developers become as productive as seniors, and seniors achieving what was previously impossible."

### Statistics:
- 75% of developers now use AI tools daily
- Bug rates have decreased by 60%
- Development cycles shortened by 40%

## Challenges Remain

Despite the progress, challenges persist:
- AI-generated code sometimes lacks creativity
- Security concerns about AI accessing codebases
- Need for human oversight remains critical

## Looking Forward

The future of software development will be a collaboration between human creativity and AI efficiency. As these tools continue to evolve, we can expect even more dramatic changes in how software is created and maintained.

Contact: tech@example.com
Follow us on Twitter: @TechNews
Advertisement: Try our AI coding assistant today!
Navigation: Home | News | About | Contact
Copyright 2025 TechNews Inc.
"""

def test_analyze_content():
    """Test content analysis endpoint"""
    print("\n🔍 Testing Content Analysis")
    print("=" * 50)
    
    # Test entity extraction
    print("\n1. Entity Extraction:")
    payload = {
        "content": sample_content,
        "analysis_type": "entities",
        "llm_provider": "anthropic",
        "llm_token": anthropic_token
    }
    
    response = requests.post(f"{base_url}/analyze", json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Entity extraction successful!")
            print(f"   Found entities: {json.dumps(result.get('analysis', {}), indent=2)}")
        else:
            print(f"❌ Analysis failed: {result.get('error')}")
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")
    
    # Test sentiment analysis
    print("\n2. Sentiment Analysis:")
    payload["analysis_type"] = "sentiment"
    
    response = requests.post(f"{base_url}/analyze", json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Sentiment analysis successful!")
            print(f"   Sentiment: {result.get('analysis', {}).get('sentiment')}")
        else:
            print(f"❌ Analysis failed: {result.get('error')}")
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")

def test_clean_markdown():
    """Test markdown cleaning endpoint"""
    print("\n🧹 Testing Markdown Cleanup")
    print("=" * 50)
    
    payload = {
        "markdown": sample_content,
        "goals": ["remove_ads", "remove_boilerplate", "fix_formatting"],
        "preserve": ["links", "headers", "lists"],
        "aggressive": True,
        "llm_provider": "anthropic",
        "llm_token": anthropic_token
    }
    
    response = requests.post(f"{base_url}/clean", json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Markdown cleanup successful!")
            improvements = result.get('improvements', {})
            print(f"   Chars removed: {improvements.get('chars_removed', 0)}")
            print(f"   Reduction: {improvements.get('reduction_percentage', 0)}%")
            print(f"\n   Cleaned preview (first 500 chars):")
            print(result.get('markdown', '')[:500] + "...")
        else:
            print(f"❌ Cleanup failed: {result.get('error')}")
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")

def test_summarize_content():
    """Test content summarization endpoint"""
    print("\n📝 Testing Content Summarization")
    print("=" * 50)
    
    # Test brief summary
    print("\n1. Brief Summary:")
    payload = {
        "content": sample_content,
        "summary_type": "brief",
        "max_length": 50,
        "output_format": "text",
        "llm_provider": "anthropic",
        "llm_token": anthropic_token
    }
    
    response = requests.post(f"{base_url}/summarize", json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Brief summary successful!")
            print(f"   Summary: {result.get('summary')}")
            print(f"   Compression ratio: {result.get('compression_ratio')}")
        else:
            print(f"❌ Summarization failed: {result.get('error')}")
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")
    
    # Test bullet points
    print("\n2. Bullet Points Summary:")
    payload["summary_type"] = "bullet_points"
    payload["output_format"] = "markdown"
    
    response = requests.post(f"{base_url}/summarize", json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Bullet points summary successful!")
            print(f"   Summary:\n{result.get('summary')}")
        else:
            print(f"❌ Summarization failed: {result.get('error')}")
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")

def test_extract_structured():
    """Test structured data extraction"""
    print("\n🏗️ Testing Structured Data Extraction")
    print("=" * 50)
    
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "author": {"type": "string"},
            "date": {"type": "string"},
            "key_statistics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "metric": {"type": "string"},
                        "value": {"type": "string"}
                    }
                }
            },
            "main_topics": {
                "type": "array",
                "items": {"type": "string"}
            },
            "companies_mentioned": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
    
    payload = {
        "content": sample_content,
        "schema": schema,
        "llm_provider": "anthropic",
        "llm_token": anthropic_token
    }
    
    response = requests.post(f"{base_url}/extract", json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Data extraction successful!")
            print(f"   Extracted data:")
            print(json.dumps(result.get('data', {}), indent=2))
        else:
            print(f"❌ Extraction failed: {result.get('error')}")
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")

def main():
    """Run all tests"""
    print("🧪 Testing Gnosis Wraith Content Processing API")
    print(f"Token: {token[:10]}...")
    print(f"Anthropic token: {anthropic_token[:10] if anthropic_token else 'NOT SET'}...")
    
    if not anthropic_token or anthropic_token == "YOUR_ANTHROPIC_KEY":
        print("\n⚠️  Warning: No Anthropic API key provided!")
        print("Usage: python test_content_processing.py <gnosis_token> <anthropic_token>")
        print("Or set ANTHROPIC_API_KEY environment variable")
        return
    
    # Run all tests
    test_analyze_content()
    test_clean_markdown()
    test_summarize_content()
    test_extract_structured()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()