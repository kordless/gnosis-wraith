"""
Cryptocurrency toolbag - Tools for cryptocurrency data and analysis

This module contains tools for fetching cryptocurrency prices, market data, and analysis
that can be used with any AI provider (Anthropic, OpenAI, Ollama, etc.).
"""

from typing import Dict, Any, List
import logging
import asyncio
import time
from .decorators import tool

logger = logging.getLogger("gnosis_wraith")

# Rate limiting variables
last_request_time = 0
min_request_interval = 2  # Minimum seconds between API requests (more conservative than original)

@tool(description="Get current Bitcoin price and market data")
async def get_bitcoin_price(currency: str = "USD") -> Dict[str, Any]:
    """
    Get the current Bitcoin price from CoinGecko API.
    
    currency: The currency to get the price in (default: USD)
    
    Returns dict with these keys:
    - success (bool): Whether the request was successful
    - price (float): Current Bitcoin price in specified currency (only if success=true)
    - currency (str): Currency code used for pricing
    - market_cap (float): Market capitalization in specified currency (only if success=true)
    - volume_24h (float): 24-hour trading volume (only if success=true)
    - change_24h (float): 24-hour price change percentage (only if success=true)
    - last_updated_timestamp (int): Unix timestamp of last update (only if success=true)
    - source (str): Data source name ("CoinGecko") (only if success=true)
    - error (str): Error message (only if success=false)
    """
    global last_request_time, min_request_interval
    
    try:
        # Import aiohttp here to avoid dependency issues
        import aiohttp
    except ImportError:
        return {
            "success": False,
            "error": "aiohttp package not available. Please install with: pip install aiohttp"
        }
    
    try:
        # Enforce rate limiting
        current_time = time.time()
        time_since_last_request = current_time - last_request_time
        
        if time_since_last_request < min_request_interval:
            wait_time = min_request_interval - time_since_last_request
            logger.info(f"Rate limiting: Waiting {wait_time:.2f} seconds before making API request")
            await asyncio.sleep(wait_time)
        
        # Update the last request time
        last_request_time = time.time()
        
        # CoinGecko API - free tier, no authentication required
        url = f"https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies={currency.lower()}&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true&include_last_updated_at=true"
        
        logger.info(f"Making API request for Bitcoin price in {currency}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'bitcoin' in data:
                        bitcoin_data = data['bitcoin']
                        currency_lower = currency.lower()
                        
                        price = bitcoin_data.get(currency_lower, 0)
                        market_cap = bitcoin_data.get(f"{currency_lower}_market_cap", 0)
                        vol_24h = bitcoin_data.get(f"{currency_lower}_24h_vol", 0)
                        change_24h = bitcoin_data.get(f"{currency_lower}_24h_change", 0)
                        last_updated = bitcoin_data.get("last_updated_at", 0)
                        
                        return {
                            "success": True,
                            "price": price,
                            "currency": currency.upper(),
                            "market_cap": market_cap,
                            "volume_24h": vol_24h,
                            "change_24h": change_24h,
                            "last_updated_timestamp": last_updated,
                            "source": "CoinGecko"
                        }
                    else:
                        return {
                            "success": False,
                            "error": "Bitcoin data not found in API response"
                        }
                else:
                    return {
                        "success": False,
                        "error": f"API request failed with status code: {response.status}"
                    }
                    
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": "Request timed out. CoinGecko API may be unavailable."
        }
    except Exception as e:
        logger.error(f"Error fetching Bitcoin price: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to fetch Bitcoin price: {str(e)}"
        }

@tool(description="Get list of supported currencies for cryptocurrency pricing")
async def list_supported_currencies() -> Dict[str, Any]:
    """
    Get currencies supported by the CoinGecko API.
    
    Returns dict with these keys:
    - success (bool): Whether the request was successful
    - supported_currencies (list): List of currency codes (only if success=true)
    - currency_count (int): Number of supported currencies (only if success=true)
    - error (str): Error message (only if success=false)
    """
    global last_request_time, min_request_interval
    
    try:
        import aiohttp
    except ImportError:
        return {
            "success": False,
            "error": "aiohttp package not available. Please install with: pip install aiohttp"
        }
    
    try:
        # Enforce rate limiting
        current_time = time.time()
        time_since_last_request = current_time - last_request_time
        
        if time_since_last_request < min_request_interval:
            wait_time = min_request_interval - time_since_last_request
            logger.info(f"Rate limiting: Waiting {wait_time:.2f} seconds before making API request")
            await asyncio.sleep(wait_time)
        
        last_request_time = time.time()
        
        url = "https://api.coingecko.com/api/v3/simple/supported_vs_currencies"
        
        logger.info("Fetching supported currencies from CoinGecko")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    currencies = await response.json()
                    return {
                        "success": True,
                        "supported_currencies": currencies,
                        "currency_count": len(currencies)
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API request failed with status code: {response.status}"
                    }
                    
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": "Request timed out. CoinGecko API may be unavailable."
        }
    except Exception as e:
        logger.error(f"Error fetching supported currencies: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to fetch supported currencies: {str(e)}"
        }

@tool(description="Get Bitcoin price history for analysis")
async def get_bitcoin_history(days: int = 7, currency: str = "USD") -> Dict[str, Any]:
    """
    Get Bitcoin price history for specified time period.
    
    days: Number of days of history to retrieve (1, 7, 14, 30, 90, 180, 365) (default: 7)
    currency: The currency to get prices in (default: USD)
    
    Returns dict with these keys:
    - success (bool): Whether the request was successful
    - currency (str): Currency code used for pricing
    - days (int): Number of days of history retrieved
    - price_history (list): List of price data points with timestamp and price (only if success=true)
    - price_range (dict): Min and max prices in the period (only if success=true)
    - data_points (int): Number of price data points returned (only if success=true)
    - source (str): Data source name ("CoinGecko") (only if success=true)
    - error (str): Error message (only if success=false)
    """
    global last_request_time, min_request_interval
    
    try:
        import aiohttp
    except ImportError:
        return {
            "success": False,
            "error": "aiohttp package not available. Please install with: pip install aiohttp"
        }
    
    # Validate days parameter
    valid_days = [1, 7, 14, 30, 90, 180, 365]
    if days not in valid_days:
        # Find closest valid value
        days = min(valid_days, key=lambda x: abs(x - days))
    
    try:
        # Enforce rate limiting
        current_time = time.time()
        time_since_last_request = current_time - last_request_time
        
        if time_since_last_request < min_request_interval:
            wait_time = min_request_interval - time_since_last_request
            logger.info(f"Rate limiting: Waiting {wait_time:.2f} seconds before making API request")
            await asyncio.sleep(wait_time)
        
        last_request_time = time.time()
        
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency={currency.lower()}&days={days}"
        
        logger.info(f"Fetching Bitcoin price history: {days} days in {currency}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process the data to make it more usable
                    prices = []
                    min_price = float('inf')
                    max_price = float('-inf')
                    
                    if 'prices' in data and data['prices']:
                        # Limit to reasonable number of data points for readability
                        step = max(1, len(data['prices']) // 50)  # Max 50 data points
                        
                        for i in range(0, len(data['prices']), step):
                            timestamp, price = data['prices'][i]
                            prices.append({
                                "timestamp": timestamp,
                                "price": round(price, 2),
                                "date": time.strftime('%Y-%m-%d %H:%M', time.gmtime(timestamp/1000))
                            })
                            
                            min_price = min(min_price, price)
                            max_price = max(max_price, price)
                    
                    return {
                        "success": True,
                        "currency": currency.upper(),
                        "days": days,
                        "price_history": prices,
                        "price_range": {
                            "min_price": round(min_price, 2),
                            "max_price": round(max_price, 2),
                            "price_change": round(max_price - min_price, 2)
                        },
                        "data_points": len(prices),
                        "source": "CoinGecko"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API request failed with status code: {response.status}"
                    }
                    
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": "Request timed out. CoinGecko API may be unavailable."
        }
    except Exception as e:
        logger.error(f"Error fetching Bitcoin history: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to fetch Bitcoin history: {str(e)}"
        }

# Tool definitions for AI providers
def get_cryptocurrency_tools():
    """Get cryptocurrency tools in Claude/OpenAI compatible format."""
    from .decorators import get_tool_schemas
    return get_tool_schemas()

# Tool execution function
async def execute_cryptocurrency_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Execute a cryptocurrency tool by name."""
    from .decorators import execute_tool
    return await execute_tool(tool_name, **kwargs)

# Export functions
__all__ = ["get_cryptocurrency_tools", "execute_cryptocurrency_tool", "get_bitcoin_price", "list_supported_currencies", "get_bitcoin_history"]
