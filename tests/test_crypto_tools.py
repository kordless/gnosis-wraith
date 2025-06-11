"""
Quick test for the new cryptocurrency tools
"""

import asyncio
from ai.tools.cryptocurrency import get_bitcoin_price, list_supported_currencies, get_bitcoin_history

async def test_crypto_tools():
    """Test cryptocurrency tools directly."""
    
    print("🪙 Testing Cryptocurrency Tools")
    print("=" * 40)
    
    # Test 1: Get Bitcoin price
    print("\n1. Testing get_bitcoin_price:")
    result = await get_bitcoin_price()
    if result["success"]:
        print(f"   ✅ Bitcoin Price: ${result['price']:,.2f} {result['currency']}")
        print(f"   📈 24h Change: {result['change_24h']:.2f}%")
        print(f"   💰 Market Cap: ${result['market_cap']:,.0f}")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    # Test 2: Get Bitcoin price in EUR
    print("\n2. Testing get_bitcoin_price with EUR:")
    result = await get_bitcoin_price("EUR")
    if result["success"]:
        print(f"   ✅ Bitcoin Price: €{result['price']:,.2f} {result['currency']}")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    # Test 3: List supported currencies (just count them)
    print("\n3. Testing list_supported_currencies:")
    result = await list_supported_currencies()
    if result["success"]:
        print(f"   ✅ Found {result['currency_count']} supported currencies")
        print(f"   💱 First 10: {result['supported_currencies'][:10]}")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    # Test 4: Get short price history
    print("\n4. Testing get_bitcoin_history (7 days):")
    result = await get_bitcoin_history(7)
    if result["success"]:
        print(f"   ✅ Retrieved {result['data_points']} price points")
        print(f"   📊 Price Range: ${result['price_range']['min_price']:,.2f} - ${result['price_range']['max_price']:,.2f}")
        print(f"   📅 Latest: {result['price_history'][-1]['date']} - ${result['price_history'][-1]['price']:,.2f}")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    print("\n" + "=" * 40)
    print("✅ Cryptocurrency tools test complete!")

if __name__ == "__main__":
    print("🚀 Starting cryptocurrency tools test...")
    print("💡 Note: This requires internet access to CoinGecko API")
    
    asyncio.run(test_crypto_tools())
