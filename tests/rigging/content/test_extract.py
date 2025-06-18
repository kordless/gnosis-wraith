"""
Structured Data Extraction Tests
"""

import pytest
import sys
import json
from pathlib import Path
from typing import Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.test_base import BaseAPITest


class TestExtractEndpoint(BaseAPITest):
    """Test /v2/extract endpoint for structured data extraction"""
    
    def test_basic_extraction(self):
        """Test basic structured data extraction"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        iPhone 15 Pro Max - Premium Smartphone
        Price: $1,199
        Colors: Natural Titanium, Blue Titanium, White Titanium, Black Titanium
        Storage Options: 256GB, 512GB, 1TB
        
        Key Features:
        - A17 Pro chip with 6-core CPU
        - 6.7-inch Super Retina XDR display
        - Pro camera system with 48MP main camera
        - Titanium design with Action Button
        - All-day battery life
        
        Available at Apple Store and authorized retailers.
        Free shipping on orders over $50.
        """
        
        schema = {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "price": {"type": "number"},
                "currency": {"type": "string"},
                "colors": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "storage_options": {
                    "type": "array", 
                    "items": {"type": "string"}
                },
                "features": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "availability": {"type": "string"}
            }
        }
        
        response = self.make_request("POST", "/extract", json={
            "content": content,
            "schema": schema,
            **llm_config
        })
        
        data = self.assert_success_response(response)
        
        # Validate extracted data
        assert "data" in data
        extracted = data["data"]
        
        # Check required fields
        assert extracted["product_name"] == "iPhone 15 Pro Max"
        assert extracted["price"] == 1199
        assert extracted["currency"] == "USD"
        
        # Check arrays
        assert isinstance(extracted["colors"], list)
        assert len(extracted["colors"]) == 4
        assert "Natural Titanium" in extracted["colors"]
        
        assert isinstance(extracted["storage_options"], list)
        assert "256GB" in extracted["storage_options"]
        
        assert isinstance(extracted["features"], list)
        assert len(extracted["features"]) >= 5
    
    def test_nested_extraction(self):
        """Test extraction with nested schema"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        Company: TechCorp Inc.
        Founded: 2015
        Headquarters: San Francisco, CA
        
        Leadership Team:
        - CEO: Jane Smith (10 years experience, formerly at Google)
        - CTO: John Doe (15 years experience, PhD in Computer Science)
        - CFO: Mary Johnson (12 years experience, MBA from Harvard)
        
        Products:
        1. CloudSync Pro
           - Price: $99/month
           - Users: 50,000+
           - Launch Date: 2018
        
        2. DataAnalyzer
           - Price: $199/month
           - Users: 20,000+
           - Launch Date: 2020
        """
        
        schema = {
            "type": "object",
            "properties": {
                "company": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "founded_year": {"type": "number"},
                        "headquarters": {
                            "type": "object",
                            "properties": {
                                "city": {"type": "string"},
                                "state": {"type": "string"}
                            }
                        }
                    }
                },
                "leadership": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "position": {"type": "string"},
                            "name": {"type": "string"},
                            "experience_years": {"type": "number"},
                            "background": {"type": "string"}
                        }
                    }
                },
                "products": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price_per_month": {"type": "number"},
                            "user_count": {"type": "number"},
                            "launch_year": {"type": "number"}
                        }
                    }
                }
            }
        }
        
        response = self.make_request("POST", "/extract", json={
            "content": content,
            "schema": schema,
            **llm_config
        })
        
        data = self.assert_success_response(response)
        extracted = data["data"]
        
        # Validate nested structure
        assert extracted["company"]["name"] == "TechCorp Inc."
        assert extracted["company"]["founded_year"] == 2015
        assert extracted["company"]["headquarters"]["city"] == "San Francisco"
        assert extracted["company"]["headquarters"]["state"] == "CA"
        
        # Check leadership array
        assert len(extracted["leadership"]) == 3
        ceo = next(l for l in extracted["leadership"] if l["position"] == "CEO")
        assert ceo["name"] == "Jane Smith"
        assert ceo["experience_years"] == 10
        
        # Check products
        assert len(extracted["products"]) == 2
        cloudsync = next(p for p in extracted["products"] if "CloudSync" in p["name"])
        assert cloudsync["price_per_month"] == 99
        assert cloudsync["user_count"] >= 50000
    
    def test_extraction_with_validation(self):
        """Test extraction with schema validation"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        Event: AI Conference 2025
        Date: March 15-17, 2025
        Time: 9:00 AM - 5:00 PM PST
        Location: Moscone Center, San Francisco
        
        Ticket Prices:
        - Early Bird: $299 (until Feb 1)
        - Regular: $399
        - Student: $99 (with valid ID)
        - VIP: $799 (includes workshops)
        
        Expected Attendance: 5000+ professionals
        """
        
        schema = {
            "type": "object",
            "properties": {
                "event_name": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 100
                },
                "dates": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "string", "format": "date"},
                        "end": {"type": "string", "format": "date"}
                    }
                },
                "time_zone": {
                    "type": "string",
                    "enum": ["PST", "EST", "CST", "MST"]
                },
                "venue": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "city": {"type": "string"}
                    },
                    "required": ["name", "city"]
                },
                "tickets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "price": {"type": "number", "minimum": 0},
                            "conditions": {"type": "string"}
                        }
                    },
                    "minItems": 1
                },
                "expected_attendance": {
                    "type": "number",
                    "minimum": 0
                }
            },
            "required": ["event_name", "dates", "venue"]
        }
        
        response = self.make_request("POST", "/extract", json={
            "content": content,
            "schema": schema,
            **llm_config
        })
        
        data = self.assert_success_response(response)
        extracted = data["data"]
        
        # Validate against schema requirements
        assert "event_name" in extracted
        assert "dates" in extracted
        assert "venue" in extracted
        
        # Check specific validations
        assert extracted["time_zone"] in ["PST", "EST", "CST", "MST"]
        assert len(extracted["tickets"]) >= 1
        
        for ticket in extracted["tickets"]:
            assert ticket["price"] >= 0
        
        assert extracted["expected_attendance"] >= 0
    
    def test_extraction_with_arrays(self):
        """Test extraction of array data"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        Recipe: Chocolate Chip Cookies
        
        Ingredients:
        - 2 1/4 cups all-purpose flour
        - 1 tsp baking soda
        - 1 tsp salt
        - 1 cup butter, softened
        - 3/4 cup granulated sugar
        - 3/4 cup brown sugar
        - 2 large eggs
        - 2 tsp vanilla extract
        - 2 cups chocolate chips
        
        Instructions:
        1. Preheat oven to 375°F
        2. Mix flour, baking soda, and salt
        3. Beat butter and sugars until creamy
        4. Add eggs and vanilla
        5. Gradually mix in flour mixture
        6. Stir in chocolate chips
        7. Drop by spoonfuls onto baking sheet
        8. Bake for 9-11 minutes
        
        Yield: 48 cookies
        Prep Time: 15 minutes
        Cook Time: 10 minutes
        """
        
        schema = {
            "type": "object",
            "properties": {
                "recipe_name": {"type": "string"},
                "ingredients": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item": {"type": "string"},
                            "amount": {"type": "string"},
                            "unit": {"type": "string"}
                        }
                    }
                },
                "instructions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "yield": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "unit": {"type": "string"}
                    }
                },
                "times": {
                    "type": "object",
                    "properties": {
                        "prep_minutes": {"type": "number"},
                        "cook_minutes": {"type": "number"},
                        "total_minutes": {"type": "number"}
                    }
                }
            }
        }
        
        response = self.make_request("POST", "/extract", json={
            "content": content,
            "schema": schema,
            **llm_config
        })
        
        data = self.assert_success_response(response)
        extracted = data["data"]
        
        # Check arrays
        assert len(extracted["ingredients"]) >= 9
        assert len(extracted["instructions"]) >= 8
        
        # Check ingredient structure
        flour = next((i for i in extracted["ingredients"] if "flour" in i["item"].lower()), None)
        assert flour is not None
        assert "2 1/4" in flour["amount"] or "2.25" in flour["amount"]
        
        # Check yield
        assert extracted["yield"]["amount"] == 48
        assert "cookie" in extracted["yield"]["unit"].lower()
        
        # Check times
        assert extracted["times"]["prep_minutes"] == 15
        assert extracted["times"]["cook_minutes"] == 10
    
    def test_extraction_without_schema(self):
        """Test extraction without predefined schema"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        Breaking News: Tech Giant Acquires Startup
        
        Mountain View, CA - Global technology leader MegaCorp announced today the acquisition
        of AI startup InnovateLab for $2.5 billion. The deal, expected to close in Q2 2025,
        will integrate InnovateLab's cutting-edge natural language processing technology
        into MegaCorp's product suite.
        
        "This acquisition strengthens our position in the AI market," said John Smith,
        CEO of MegaCorp. "InnovateLab's team of 150 engineers will join our AI division."
        
        InnovateLab, founded in 2019 by Stanford graduates, has raised $300 million in
        funding and serves over 1 million users worldwide.
        """
        
        response = self.make_request("POST", "/extract", json={
            "content": content,
            "prompt": "Extract all key information about this acquisition including companies, financial details, people, and dates",
            **llm_config
        })
        
        data = self.assert_success_response(response)
        
        # Without schema, should still extract relevant data
        if "data" in data:
            extracted = data["data"]
            
            # Should extract key information
            extracted_str = json.dumps(extracted).lower()
            assert "megacorp" in extracted_str
            assert "innovatelab" in extracted_str
            assert "2.5" in extracted_str or "2500000000" in extracted_str
            assert "john smith" in extracted_str
            assert "2025" in extracted_str
    
    def test_confidence_scores(self):
        """Test extraction with confidence scores"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        The product seems to cost around $50-60, though the exact price isn't clear.
        It might be available in blue or green colors. The warranty is probably 1 year,
        but could be 2 years for premium customers.
        """
        
        schema = {
            "type": "object",
            "properties": {
                "price_range": {
                    "type": "object",
                    "properties": {
                        "min": {"type": "number"},
                        "max": {"type": "number"}
                    }
                },
                "colors": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "warranty_years": {"type": "number"}
            }
        }
        
        response = self.make_request("POST", "/extract", json={
            "content": content,
            "schema": schema,
            **llm_config,
            "options": {
                "include_confidence": True
            }
        })
        
        data = self.assert_success_response(response)
        
        # Check confidence scores if provided
        if "confidence" in data:
            assert 0 <= data["confidence"] <= 1
            
            # Lower confidence expected due to uncertain language
            assert data["confidence"] < 0.9


class TestExtractWithDifferentFormats(BaseAPITest):
    """Test extraction from different content formats"""
    
    def test_extract_from_markdown(self):
        """Test extraction from markdown content"""
        
        llm_config = self.get_llm_config("anthropic")
        
        markdown_content = """
        # Product Specification
        
        ## Basic Information
        - **Model**: XR-2000
        - **Manufacturer**: TechCorp
        - **Release Date**: January 2025
        
        ## Technical Specs
        
        | Feature | Specification |
        |---------|--------------|
        | Processor | Quantum X5 |
        | Memory | 16GB DDR5 |
        | Storage | 1TB NVMe |
        | Display | 15.6" 4K OLED |
        
        ## Pricing
        - Base Model: $1,299
        - Pro Model: $1,799
        - Enterprise: Contact Sales
        """
        
        schema = {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "manufacturer": {"type": "string"},
                "release_date": {"type": "string"},
                "specs": {
                    "type": "object",
                    "properties": {
                        "processor": {"type": "string"},
                        "memory": {"type": "string"},
                        "storage": {"type": "string"},
                        "display": {"type": "string"}
                    }
                },
                "pricing": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tier": {"type": "string"},
                            "price": {"type": "number"}
                        }
                    }
                }
            }
        }
        
        response = self.make_request("POST", "/extract", json={
            "content": markdown_content,
            "schema": schema,
            **llm_config
        })
        
        data = self.assert_success_response(response)
        extracted = data["data"]
        
        # Should extract from markdown format
        assert extracted["model"] == "XR-2000"
        assert extracted["manufacturer"] == "TechCorp"
        assert extracted["specs"]["processor"] == "Quantum X5"
        assert extracted["specs"]["memory"] == "16GB DDR5"
        
        # Check pricing extraction
        assert len(extracted["pricing"]) >= 2
        base_price = next(p for p in extracted["pricing"] if p["tier"] == "Base Model")
        assert base_price["price"] == 1299
    
    def test_extract_from_json_like(self):
        """Test extraction from JSON-like content"""
        
        llm_config = self.get_llm_config("openai")
        
        json_like_content = """
        API Response:
        {
            "user": {
                "id": 12345,
                "name": "John Doe",
                "email": "john@example.com",
                "roles": ["admin", "developer"],
                "metadata": {
                    "last_login": "2025-01-06T10:30:00Z",
                    "account_type": "premium"
                }
            },
            "stats": {
                "projects": 15,
                "storage_used_gb": 45.2,
                "api_calls_month": 50000
            }
        }
        """
        
        schema = {
            "type": "object",
            "properties": {
                "user_id": {"type": "number"},
                "user_name": {"type": "string"},
                "email": {"type": "string"},
                "roles": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "account_type": {"type": "string"},
                "usage_stats": {
                    "type": "object",
                    "properties": {
                        "projects": {"type": "number"},
                        "storage_gb": {"type": "number"},
                        "monthly_api_calls": {"type": "number"}
                    }
                }
            }
        }
        
        response = self.make_request("POST", "/extract", json={
            "content": json_like_content,
            "schema": schema,
            **llm_config
        })
        
        data = self.assert_success_response(response)
        extracted = data["data"]
        
        # Should parse JSON-like structure
        assert extracted["user_id"] == 12345
        assert extracted["user_name"] == "John Doe"
        assert extracted["email"] == "john@example.com"
        assert "admin" in extracted["roles"]
        assert extracted["account_type"] == "premium"
        assert extracted["usage_stats"]["storage_gb"] == 45.2


class TestExtractErrorHandling(BaseAPITest):
    """Test error handling for extract endpoint"""
    
    def test_invalid_schema(self):
        """Test extraction with invalid schema"""
        
        llm_config = self.get_llm_config("anthropic")
        
        # Invalid schema - wrong type format
        response = self.make_request("POST", "/extract", json={
            "content": "Test content",
            "schema": {
                "type": "invalid_type",
                "properties": {}
            },
            **llm_config
        })
        
        assert response.status_code == 400
        self.assert_error_response(response, "INVALID_SCHEMA")
    
    def test_missing_required_fields(self):
        """Test extraction when content missing required fields"""
        
        llm_config = self.get_llm_config("openai")
        
        content = "This content has limited information."
        
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
                "email": {"type": "string"}
            },
            "required": ["name", "age", "email"]  # All required but not in content
        }
        
        response = self.make_request("POST", "/extract", json={
            "content": content,
            "schema": schema,
            **llm_config
        })
        
        # Should handle missing data gracefully
        if response.status_code == 200:
            data = response.json()
            # Might return nulls or defaults
        else:
            assert response.status_code in [422, 400]
    
    def test_schema_too_complex(self):
        """Test extraction with overly complex schema"""
        
        llm_config = self.get_llm_config("anthropic")
        
        # Create deeply nested schema
        deep_schema = {"type": "object", "properties": {}}
        current = deep_schema["properties"]
        
        # Create 10 levels of nesting
        for i in range(10):
            current[f"level{i}"] = {
                "type": "object",
                "properties": {}
            }
            current = current[f"level{i}"]["properties"]
        
        response = self.make_request("POST", "/extract", json={
            "content": "Simple content",
            "schema": deep_schema,
            **llm_config
        })
        
        # Should handle but might simplify or error
        assert response.status_code in [200, 400]
    
    def test_conflicting_schema_content(self):
        """Test when schema expects different data than content provides"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        List of animals:
        - Dog
        - Cat
        - Bird
        """
        
        schema = {
            "type": "object",
            "properties": {
                "employees": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "salary": {"type": "number"},
                            "department": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        response = self.make_request("POST", "/extract", json={
            "content": content,
            "schema": schema,
            **llm_config
        })
        
        # Should handle mismatch gracefully
        if response.status_code == 200:
            data = response.json()
            # Might return empty array or null
            if "employees" in data["data"]:
                assert isinstance(data["data"]["employees"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])