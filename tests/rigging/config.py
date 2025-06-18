"""
Test Configuration Module

Handles loading test configuration from environment variables and .env files.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Find the tests directory
TESTS_DIR = Path(__file__).parent.parent
PROJECT_ROOT = TESTS_DIR.parent

# Load .env file if it exists
env_file = TESTS_DIR / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"✓ Loaded test configuration from {env_file}")
else:
    print(f"⚠️  No .env file found at {env_file}")
    print("   Copy .env.example to .env and add your API keys")

# Add project root to path
sys.path.insert(0, str(PROJECT_ROOT))


class TestConfig:
    """Test configuration singleton"""
    
    # Gnosis Wraith API Token
    GNOSIS_API_TOKEN = os.getenv('GNOSIS_API_TOKEN')
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Ollama Settings
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Test Settings
    BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:5000')
    TIMEOUT = int(os.getenv('TEST_TIMEOUT', '30'))
    TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'test@example.com')
    TEST_USER_PHONE = os.getenv('TEST_USER_PHONE', '+1234567890')
    
    # Feature Flags
    ENABLE_SCREENSHOT_TESTS = os.getenv('ENABLE_SCREENSHOT_TESTS', 'false').lower() == 'true'
    ENABLE_JAVASCRIPT_TESTS = os.getenv('ENABLE_JAVASCRIPT_TESTS', 'true').lower() == 'true'
    ENABLE_AI_TESTS = os.getenv('ENABLE_AI_TESTS', 'true').lower() == 'true'
    
    @classmethod
    def has_api_key(cls, provider: str) -> bool:
        """Check if API key is configured for a provider"""
        key_map = {
            'openai': cls.OPENAI_API_KEY,
            'anthropic': cls.ANTHROPIC_API_KEY,
            'google': cls.GOOGLE_API_KEY,
            'gemini': cls.GOOGLE_API_KEY
        }
        return bool(key_map.get(provider.lower()))
    
    @classmethod
    def get_api_key(cls, provider: str) -> Optional[str]:
        """Get API key for a provider"""
        key_map = {
            'openai': cls.OPENAI_API_KEY,
            'anthropic': cls.ANTHROPIC_API_KEY,
            'google': cls.GOOGLE_API_KEY,
            'gemini': cls.GOOGLE_API_KEY
        }
        return key_map.get(provider.lower())
    
    @classmethod
    def prompt_for_key(cls, provider: str) -> str:
        """Prompt user for API key if not set"""
        key = cls.get_api_key(provider)
        if not key:
            print(f"\n⚠️  No {provider.upper()} API key found in .env file")
            key = input(f"Enter your {provider} API key (or press Enter to skip): ").strip()
            if key:
                # Set it for this session
                if provider.lower() == 'openai':
                    cls.OPENAI_API_KEY = key
                    os.environ['OPENAI_API_KEY'] = key
                elif provider.lower() == 'anthropic':
                    cls.ANTHROPIC_API_KEY = key
                    os.environ['ANTHROPIC_API_KEY'] = key
                elif provider.lower() in ['google', 'gemini']:
                    cls.GOOGLE_API_KEY = key
                    os.environ['GOOGLE_API_KEY'] = key
        return key
    
    @classmethod
    def check_required_keys(cls, providers: list) -> bool:
        """Check if required API keys are available"""
        missing = []
        for provider in providers:
            if not cls.has_api_key(provider):
                missing.append(provider)
        
        if missing:
            print(f"\n⚠️  Missing API keys for: {', '.join(missing)}")
            print("   Add them to tests/.env or you'll be prompted when running tests")
            return False
        return True
    
    @classmethod
    def get_auth_headers(cls) -> Dict[str, str]:
        """Get authentication headers for Gnosis Wraith API"""
        if not cls.GNOSIS_API_TOKEN:
            print("\n⚠️  No GNOSIS_API_TOKEN found in .env file")
            print("   To get your token:")
            print("   1. Go to http://localhost:5000")
            print("   2. Log in with your phone number")
            print("   3. Click on the API Token button")
            print("   4. Copy the token to your .env file\n")
            
            token = input("Enter your Gnosis API token (or press Enter to skip): ").strip()
            if token:
                cls.GNOSIS_API_TOKEN = token
                os.environ['GNOSIS_API_TOKEN'] = token
        
        if cls.GNOSIS_API_TOKEN:
            return {
                'Authorization': f'Bearer {cls.GNOSIS_API_TOKEN}',
                'Content-Type': 'application/json'
            }
        return {}
    
    @classmethod
    def check_gnosis_auth(cls) -> bool:
        """Check if Gnosis API authentication is configured"""
        return bool(cls.GNOSIS_API_TOKEN)
    
    @classmethod
    def get_api_url(cls, endpoint: str) -> str:
        """Get full API URL for an endpoint"""
        endpoint = endpoint.lstrip('/')
        return f"{cls.BASE_URL}/{endpoint}"


# Create config instance
config = TestConfig()