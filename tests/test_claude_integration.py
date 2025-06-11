"""
Integration test for Claude tool calling with enhanced tool system

This test verifies that Claude can successfully call our enhanced tools
and that the tool execution works end-to-end.

Required: pip install anthropic python-dotenv
"""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_dependencies():
    """Check if required packages are installed."""
    missing_packages = []
    
    try:
        import anthropic
    except ImportError:
        missing_packages.append("anthropic")
    
    try:
        import dotenv
    except ImportError:
        missing_packages.append("python-dotenv")
    
    if missing_packages:
        print("❌ Missing required packages!")
        print("\nPlease install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        print("\nOr install all requirements:")
        print("pip install anthropic python-dotenv")
        return False
    
    return True

def check_api_key():
    """Check if ANTHROPIC_API_KEY is available in .env file."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found!")
        print("\nPlease add your Anthropic API key to your .env file:")
        print("echo 'ANTHROPIC_API_KEY=your-api-key-here' >> .env")
        print("\nOr set it as an environment variable:")
        print("export ANTHROPIC_API_KEY=your-api-key-here")
        print("\nGet your API key from: https://console.anthropic.com/settings/keys")
        return None
    
    # Mask the key for logging
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
    print(f"✅ Found API key: {masked_key}")
    return api_key

async def test_claude_with_tools():
    """Test Claude tool calling with our enhanced tool system."""
    
    print("=" * 60)
    print("CLAUDE TOOL CALLING INTEGRATION TEST")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check API key
    api_key = check_api_key()
    if not api_key:
        return False
    
    try:
        # Import our tool system
        from ai.tools.decorators import tool, get_tool_schemas, execute_tool, clear_tools
        from ai.anthropic import process_with_anthropic_tools
        
        print("✅ Successfully imported tool system")
        
    except ImportError as e:
        print(f"❌ Error importing tool system: {e}")
        print("Make sure you're running from the gnosis-wraith directory")
        return False
    
    # Clear existing tools and define test tools
    clear_tools()
    
    @tool(description="Perform mathematical calculations with precision control")
    async def calculate_advanced(
        expression: str, 
        precision: int = 2,
        show_steps: bool = False
    ) -> dict:
        """
        Calculate mathematical expressions with options.
        
        expression: Math expression to evaluate (e.g., "25 * 31 + sqrt(16)")
        precision: Number of decimal places for rounding (default: 2)
        show_steps: Whether to show calculation steps (default: false)
        """
        try:
            import math
            
            # Safe evaluation context
            safe_dict = {
                "__builtins__": {},
                "abs": abs, "round": round, "pow": pow,
                "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
                "tan": math.tan, "log": math.log, "pi": math.pi, "e": math.e
            }
            
            if show_steps:
                steps = [f"Original expression: {expression}"]
                
            result = eval(expression, safe_dict)
            
            if precision is not None:
                result = round(result, precision)
                if show_steps:
                    steps.append(f"Rounded to {precision} decimal places: {result}")
            
            response = {
                "success": True,
                "expression": expression,
                "result": result,
                "precision": precision
            }
            
            if show_steps:
                response["calculation_steps"] = steps
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "expression": expression,
                "error": str(e),
                "help": "Use basic math operators (+, -, *, /) and functions like sqrt(), sin(), cos()"
            }
    
    @tool(description="Convert between temperature units")
    async def temperature_converter(temp_value: float, from_unit: str, to_unit: str = "celsius") -> dict:
        """
        Convert temperature between Celsius, Fahrenheit, and Kelvin.
        
        temp_value: Temperature value to convert
        from_unit: Source unit (celsius, fahrenheit, kelvin)
        to_unit: Target unit (default: celsius)
        """
        units = ["celsius", "fahrenheit", "kelvin"]
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        
        if from_unit not in units or to_unit not in units:
            return {
                "success": False,
                "error": f"Invalid unit. Supported units: {', '.join(units)}"
            }
        
        # Convert to Celsius first
        if from_unit == "fahrenheit":
            celsius = (temp_value - 32) * 5/9
        elif from_unit == "kelvin":
            celsius = temp_value - 273.15
        else:
            celsius = temp_value
        
        # Convert from Celsius to target
        if to_unit == "fahrenheit":
            result = (celsius * 9/5) + 32
        elif to_unit == "kelvin":
            result = celsius + 273.15
        else:
            result = celsius
        
        return {
            "success": True,
            "original": {"value": temp_value, "unit": from_unit},
            "converted": {"value": round(result, 2), "unit": to_unit},
            "formula_used": f"{from_unit} → {to_unit}"
        }
    
    @tool(description="Get current Bitcoin price and market data")
    async def get_bitcoin_price(currency: str = "USD") -> dict:
        """
        Get current Bitcoin price (test version with mock data).
        
        currency: Currency to get price in (default: USD)
        """
        # Mock data for testing (avoid API calls during tests)
        mock_prices = {
            "USD": 45000.50,
            "EUR": 41250.75,
            "GBP": 36500.25
        }
        
        price = mock_prices.get(currency.upper(), 45000.50)
        
        return {
            "success": True,
            "price": price,
            "currency": currency.upper(),
            "market_cap": price * 19000000,  # Approximate circulating supply
            "volume_24h": price * 25000,
            "change_24h": 2.5,
            "source": "Mock Data (Test)"
        }
    
    # Test 1: Check tool schemas
    print("\n1. TESTING TOOL SCHEMA GENERATION")
    print("-" * 40)
    
    schemas = get_tool_schemas()
    print(f"✅ Generated {len(schemas)} tool schemas")
    
    for schema in schemas:
        print(f"  • {schema['name']}: {schema['description']}")
        required_params = schema['input_schema']['required']
        optional_params = [p for p in schema['input_schema']['properties'] 
                          if p not in required_params]
        print(f"    Required: {required_params}")
        if optional_params:
            print(f"    Optional: {optional_params}")
    
    # Test 2: Claude integration
    print("\n2. TESTING CLAUDE INTEGRATION")
    print("-" * 40)
    
    test_prompts = [
        "what is the square root of the price of bitcoin yesterday?",
        "Calculate 25 times 31 plus the square root of 144",
        "What's 100 degrees Fahrenheit in Celsius?",
        "Calculate sin(pi/2) with 4 decimal places and show the steps",
        "What's the current Bitcoin price in USD?",
        "Get Bitcoin price history for the last 30 days"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n🧠 Test {i}: {prompt}")
        print("⏳ Sending to Claude...")
        
        try:
            result = await process_with_anthropic_tools(
                text=prompt,
                token=api_key,
                tools=schemas,  # Pass our tool schemas
                system_prompt="You are a helpful assistant with access to calculation and temperature conversion tools. Use the tools when appropriate to answer user questions accurately.",
                model="claude-3-haiku-20240307",
                max_iterations=3
            )
            
            print(f"✅ Claude Response: {result['response']}")
            print(f"🔧 Tools used: {result['tool_calls_used']}")
            print(f"🔄 Iterations: {result['iterations']}")
            
            if result['tool_calls']:
                print(f"📞 Tool calls made: {len(result['tool_calls'])}")
                for j, tool_call in enumerate(result['tool_calls'], 1):
                    print(f"   {j}. {tool_call['name']} with {tool_call['input']}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            if "API key" in str(e):
                print("💡 Check your ANTHROPIC_API_KEY in .env file")
            return False
    
    # Test 3: Direct tool execution
    print("\n3. TESTING DIRECT TOOL EXECUTION")
    print("-" * 40)
    
    direct_tests = [
        ("calculate_advanced", {"expression": "pi * 2", "precision": 3}),
        ("temperature_converter", {"temp_value": 100, "from_unit": "celsius", "to_unit": "fahrenheit"}),
        ("get_bitcoin_price", {"currency": "EUR"}),
        ("calculate_advanced", {"expression": "invalid_expr"})  # Error case
    ]
    
    for tool_name, params in direct_tests:
        print(f"\n🔧 Direct test: {tool_name}({params})")
        result = await execute_tool(tool_name, **params)
        print(f"   Result: {json.dumps(result, indent=6)}")
    
    print("\n" + "=" * 60)
    print("✅ CLAUDE TOOL CALLING TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    print("🚀 Starting Claude Tool Calling Integration Test\n")
    
    # Check if we're in the right directory
    if not os.path.exists("ai/tools/decorators.py"):
        print("❌ Error: Run this test from the gnosis-wraith root directory")
        print("Current directory:", os.getcwd())
        sys.exit(1)
    
    success = asyncio.run(test_claude_with_tools())
    
    if success:
        print("\n🎉 All tests passed! Your enhanced tool system is working with Claude.")
    else:
        print("\n💥 Some tests failed. Check the error messages above.")
        sys.exit(1)
