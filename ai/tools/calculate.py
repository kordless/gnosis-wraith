"""
Calculate toolbag - Mathematical calculation tools for AI providers

This module contains tools for performing mathematical calculations that can be used
with any AI provider (Anthropic, OpenAI, Ollama, etc.).
"""

from typing import Dict, Any
import logging
import math
import re
from .decorators import tool

logger = logging.getLogger("gnosis_wraith")

@tool(description="Perform basic arithmetic calculations safely")
async def calculate(expression: str) -> Dict[str, Any]:
    """
    Perform basic arithmetic calculations safely.
    
    expression: Mathematical expression to evaluate (e.g., "25 * 31", "sqrt(16) + 5")
    
    Returns dict with these keys:
    - success (bool): Whether calculation was successful
    - expression (str): Original expression that was evaluated
    - result (float|int): Calculated result (only if success=true)
    - result_type (str): Type of result ("int", "float") (only if success=true)
    - error (str): Error message explaining what went wrong (only if success=false)
    - error_type (str): Type of error that occurred (only if success=false)
    """
    try:
        # Clean the expression
        expression = expression.strip()
        
        # Allow basic math operations and common functions
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
        }
        
        # Evaluate the expression safely
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        
        logger.info(f"Calculated: {expression} = {result}")
        
        return {
            "success": True,
            "expression": expression,
            "result": result,
            "result_type": type(result).__name__
        }
        
    except Exception as e:
        error_msg = f"Error calculating '{expression}': {str(e)}"
        logger.error(error_msg)
        
        return {
            "success": False,
            "expression": expression,
            "error": str(e),
            "error_type": type(e).__name__
        }

@tool(description="Calculate percentages with different operations")
async def percentage_calculator(value: float, percentage: float, operation: str = "of") -> Dict[str, Any]:
    """
    Calculate percentages with different operations.
    
    Args:
        value: The base value
        percentage: The percentage value
        operation: Type of operation ("of", "increase", "decrease", "change")
        
    Returns:
        Dictionary with percentage calculation result
    """
    try:
        if operation == "of":
            # X% of Y
            result = (percentage / 100) * value
            description = f"{percentage}% of {value}"
        elif operation == "increase":
            # Y increased by X%
            result = value * (1 + percentage / 100)
            description = f"{value} increased by {percentage}%"
        elif operation == "decrease":
            # Y decreased by X%
            result = value * (1 - percentage / 100)
            description = f"{value} decreased by {percentage}%"
        elif operation == "change":
            # Percentage change from value to percentage
            if value == 0:
                return {
                    "success": False,
                    "error": "Cannot calculate percentage change from zero"
                }
            result = ((percentage - value) / value) * 100
            description = f"Percentage change from {value} to {percentage}"
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}. Use 'of', 'increase', 'decrease', or 'change'"
            }
        
        logger.info(f"Percentage calculation: {description} = {result}")
        
        return {
            "success": True,
            "operation": operation,
            "input_value": value,
            "percentage": percentage,
            "result": result,
            "description": description
        }
        
    except Exception as e:
        error_msg = f"Error in percentage calculation: {str(e)}"
        logger.error(error_msg)
        
        return {
            "success": False,
            "error": str(e),
            "operation": operation,
            "input_value": value,
            "percentage": percentage
        }

@tool(description="Convert between different units of measurement")
async def unit_converter(value: float, from_unit: str, to_unit: str, unit_type: str = "length") -> Dict[str, Any]:
    """
    Convert between different units of measurement.
    
    Args:
        value: The value to convert
        from_unit: Source unit (e.g., "meters", "feet", "celsius")
        to_unit: Target unit (e.g., "feet", "meters", "fahrenheit")  
        unit_type: Type of units ("length", "weight", "temperature", "volume")
        
    Returns:
        Dictionary with conversion result
    """
    try:
        # Unit conversion factors (to base unit)
        conversions = {
            "length": {
                "base": "meters",
                "factors": {
                    "mm": 0.001, "millimeters": 0.001,
                    "cm": 0.01, "centimeters": 0.01,
                    "m": 1.0, "meters": 1.0,
                    "km": 1000.0, "kilometers": 1000.0,
                    "in": 0.0254, "inches": 0.0254,
                    "ft": 0.3048, "feet": 0.3048,
                    "yd": 0.9144, "yards": 0.9144,
                    "mi": 1609.34, "miles": 1609.34
                }
            },
            "weight": {
                "base": "grams",
                "factors": {
                    "mg": 0.001, "milligrams": 0.001,
                    "g": 1.0, "grams": 1.0,
                    "kg": 1000.0, "kilograms": 1000.0,
                    "oz": 28.3495, "ounces": 28.3495,
                    "lb": 453.592, "pounds": 453.592
                }
            },
            "volume": {
                "base": "liters",
                "factors": {
                    "ml": 0.001, "milliliters": 0.001,
                    "l": 1.0, "liters": 1.0,
                    "gal": 3.78541, "gallons": 3.78541,
                    "qt": 0.946353, "quarts": 0.946353,
                    "pt": 0.473176, "pints": 0.473176,
                    "cup": 0.236588, "cups": 0.236588,
                    "fl_oz": 0.0295735, "fluid_ounces": 0.0295735
                }
            }
        }
        
        # Special handling for temperature
        if unit_type == "temperature":
            result = convert_temperature(value, from_unit.lower(), to_unit.lower())
        else:
            if unit_type not in conversions:
                return {
                    "success": False,
                    "error": f"Unsupported unit type: {unit_type}"
                }
            
            conv = conversions[unit_type]
            from_factor = conv["factors"].get(from_unit.lower())
            to_factor = conv["factors"].get(to_unit.lower())
            
            if from_factor is None:
                return {
                    "success": False,
                    "error": f"Unknown {unit_type} unit: {from_unit}"
                }
                
            if to_factor is None:
                return {
                    "success": False,
                    "error": f"Unknown {unit_type} unit: {to_unit}"
                }
            
            # Convert to base unit, then to target unit
            base_value = value * from_factor
            result = base_value / to_factor
        
        logger.info(f"Unit conversion: {value} {from_unit} = {result} {to_unit}")
        
        return {
            "success": True,
            "original_value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "unit_type": unit_type,
            "result": result,
            "description": f"{value} {from_unit} = {result} {to_unit}"
        }
        
    except Exception as e:
        error_msg = f"Error in unit conversion: {str(e)}"
        logger.error(error_msg)
        
        return {
            "success": False,
            "error": str(e),
            "original_value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "unit_type": unit_type
        }

def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """Convert temperature between Celsius, Fahrenheit, and Kelvin."""
    # Convert to Celsius first
    if from_unit == "fahrenheit" or from_unit == "f":
        celsius = (value - 32) * 5/9
    elif from_unit == "kelvin" or from_unit == "k":
        celsius = value - 273.15
    elif from_unit == "celsius" or from_unit == "c":
        celsius = value
    else:
        raise ValueError(f"Unknown temperature unit: {from_unit}")
    
    # Convert from Celsius to target
    if to_unit == "fahrenheit" or to_unit == "f":
        return (celsius * 9/5) + 32
    elif to_unit == "kelvin" or to_unit == "k":
        return celsius + 273.15
    elif to_unit == "celsius" or to_unit == "c":
        return celsius
    else:
        raise ValueError(f"Unknown temperature unit: {to_unit}")

# Import decorator system to register tools
from .decorators import get_tool_schemas, execute_tool

# Tool definitions for AI providers  
def get_calculation_tools():
    """Get calculation tools in Claude/OpenAI compatible format."""
    return get_tool_schemas()

# Tool execution function
async def execute_calculation_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Execute a calculation tool by name."""
    return await execute_tool(tool_name, **kwargs)

# Export functions
__all__ = ["get_calculation_tools", "execute_calculation_tool", "calculate", "percentage_calculator", "unit_converter"]
