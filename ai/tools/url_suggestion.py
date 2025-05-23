"""
URL Suggestion toolbag - Tools for suggesting and analyzing URLs

This module contains tools for URL suggestion and web analysis that can be used
with any AI provider (Anthropic, OpenAI, Ollama, etc.).
"""

from typing import Dict, Any, List
import logging
import re
import urllib.parse
from .decorators import tool

logger = logging.getLogger("gnosis_wraith")

# Domains that typically block crawlers
BLOCKED_DOMAINS = [
    "google.com", "reuters.com", "nytimes.com", "bloomberg.com", "ft.com",
    "wsj.com", "washingtonpost.com", "medium.com", "twitter.com", "instagram.com",
    "facebook.com", "linkedin.com", "patreon.com", "economist.com", "newyorker.com"
]

@tool(description="Suggest and validate a complete URL (not just a site name) based on a topic or query")
async def suggest_url(
    suggested_url: str,
    query: str = "",
    check_accessibility: bool = True,
    simple_response_to_users_odd_inquiry: str = ""
) -> Dict[str, Any]:
    """
    Validate a suggested URL and check if it's accessible for crawling.
    
    IMPORTANT: suggested_url must be a complete URL starting with http:// or https://, 
    not just a site name like 'Google' or 'Hacker News'. 
    Examples of valid URLs: 'https://news.ycombinator.com/', 'https://reddit.com/r/programming'
    Examples of INVALID inputs for URLs: 'Hacker News', 'Reddit', 'Google'
    
    suggested_url: The complete URL that Claude currently suggests for crawling no matter whether the inquiry is odd or not (must start with http:// or https://)
    query: Optional original query for context
    check_accessibility: Whether to perform HEAD request to check if URL is reachable
    simple_response_to_users_odd_inquiry: ONLY use this parameter if the user seems to be trying to chat with the AI instead of providing a URL to crawl. Put a friendly response here that will be visible in the JSON crawling_notes field, addressing their question or comment directly.
    
    Returns dict with these keys:
    - success (bool): Whether URL validation was successful
    - suggested_url (str): The URL that was validated
    - query (str): Original query (if provided)
    - domain (str): Extracted domain name
    - is_accessible (bool): Whether URL responds to HEAD request (if check_accessibility=true)
    - status_code (int): HTTP status code from HEAD request (if accessible)
    - javascript_recommended (bool): Whether JavaScript is recommended for this domain
    - javascript_settle_time_ms (int): How long to wait for JavaScript to load content (milliseconds)
    - likely_to_block_crawlers (bool): Whether domain is known to block crawlers
    - crawling_notes (str): Recommendations for crawling this URL (or AI response if simple_response_to_users_odd_inquiry is used)
    - error (str): Error message if validation failed
    - dns_error (bool): Whether domain lookup failed
    - connection_error (bool): Whether connection to URL failed
    """
    try:
        # DEBUG: Log what Claude is passing to us
        logger.info(f"🔍 suggest_url called with:")
        logger.info(f"  suggested_url: '{suggested_url}'")
        logger.info(f"  query: '{query}'")
        logger.info(f"  check_accessibility: {check_accessibility}")
        logger.info(f"  simple_response_to_users_odd_inquiry: '{simple_response_to_users_odd_inquiry}'")
        
        # Validate URL format - if invalid, try to create a search URL
        if not is_valid_url(suggested_url):
            logger.warning(f"Invalid URL format detected: '{suggested_url}', attempting search fallback")
            
            # Try to create a search URL using the invalid input as search terms
            search_url = create_search_url(suggested_url, query)
            
            if search_url:
                logger.info(f"Generated search URL fallback: {search_url}")
                return {
                    "success": True,
                    "suggested_url": search_url,
                    "query": query,
                    "original_input": suggested_url,
                    "fallback_used": True,
                    "search_engine": extract_search_engine(search_url),
                    "crawling_notes": f"Converted '{suggested_url}' to search URL: {search_url}"
                }
            else:
                return {
                    "success": False,
                    "suggested_url": suggested_url,
                    "query": query,
                    "error": "Invalid URL format and search fallback failed",
                    "crawling_notes": "URL format is invalid and cannot be crawled"
                }
        
        # Extract domain
        domain = extract_domain(suggested_url)
        
        # Check if domain is known to block crawlers
        is_blocked = any(blocked in domain.lower() for blocked in BLOCKED_DOMAINS)
        
        # Check if JavaScript is recommended for this domain
        js_recommended = needs_javascript(domain)
        
        # Get JavaScript settle time recommendation
        settle_time = get_javascript_settle_time(domain)
        
        # Initialize response
        result = {
            "success": True,
            "suggested_url": suggested_url,
            "query": query,
            "original_query": query,  # Always include the original query for reference
            "domain": domain,
            "javascript_recommended": js_recommended,
            "javascript_settle_time_ms": settle_time,
            "likely_to_block_crawlers": is_blocked
        }
        
        # Perform accessibility check if requested
        if check_accessibility:
            try:
                import aiohttp
                import asyncio
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.head(suggested_url, allow_redirects=True) as response:
                        result["is_accessible"] = True
                        result["status_code"] = response.status
                        
                        if response.status >= 400:
                            result["crawling_notes"] = f"URL returns {response.status} status but will attempt crawl"
                        else:
                            result["crawling_notes"] = f"URL is accessible (HTTP {response.status})"
                            
            except aiohttp.ClientError as e:
                if "Name or service not known" in str(e) or "No address associated" in str(e):
                    result["dns_error"] = True
                    result["is_accessible"] = False
                    result["crawling_notes"] = f"DNS lookup failed for {domain}, but will attempt crawl anyway"
                else:
                    result["connection_error"] = True
                    result["is_accessible"] = False
                    result["crawling_notes"] = f"Connection failed ({str(e)}), but will attempt crawl anyway"
                    
            except Exception as e:
                result["is_accessible"] = False
                result["crawling_notes"] = f"Accessibility check failed ({str(e)}), but will attempt crawl anyway"
        else:
            result["crawling_notes"] = "URL format is valid, accessibility not checked"
        
        # Add crawler blocking warnings
        if is_blocked:
            existing_notes = result.get("crawling_notes", "")
            result["crawling_notes"] = f"{existing_notes}. WARNING: Domain known to block crawlers"
        
        # Add JavaScript recommendations
        if js_recommended:
            existing_notes = result.get("crawling_notes", "")
            result["crawling_notes"] = f"{existing_notes}. Recommend enabling JavaScript for better content extraction"
        
        logger.info(f"URL validation: {suggested_url} -> {result.get('crawling_notes', 'OK')}")
        return result
        
    except Exception as e:
        logger.error(f"Error validating URL {suggested_url}: {str(e)}")
        return {
            "success": False,
            "suggested_url": suggested_url,
            "query": query,
            "error": str(e),
            "crawling_notes": "URL validation failed"
        }

@tool(description="Validate a URL and provide information about its crawlability")
async def validate_url(url: str) -> Dict[str, Any]:
    """
    Validate a URL and provide information about its crawlability.
    
    url: The URL to validate and analyze
    
    Returns dict with these keys:
    - success (bool): Whether URL validation was successful
    - url (str): Original URL provided
    - valid (bool): Whether URL format is valid (only if success=true)
    - domain (str): Extracted domain name (only if valid=true)
    - likely_to_block_crawlers (bool): Whether site may block crawler access
    - javascript_recommended (bool): Whether JavaScript is needed for this site
    - crawlable (bool): Overall assessment if site can be crawled
    - notes (str): Analysis summary and recommendations
    - error (str): Error message (only if success=false or valid=false)
    """
    try:
        if not is_valid_url(url):
            return {
                "success": False,
                "url": url,
                "valid": False,
                "error": "Invalid URL format"
            }
        
        domain = extract_domain(url)
        is_blocked = any(blocked in domain.lower() for blocked in BLOCKED_DOMAINS)
        
        # Determine if JavaScript is likely needed
        js_needed = needs_javascript(domain)
        
        return {
            "success": True,
            "url": url,
            "valid": True,
            "domain": domain,
            "likely_to_block_crawlers": is_blocked,
            "javascript_recommended": js_needed,
            "crawlable": not is_blocked,
            "notes": f"Domain analysis for {domain}"
        }
        
    except Exception as e:
        logger.error(f"Error validating URL {url}: {str(e)}")
        return {
            "success": False,
            "url": url,
            "error": str(e)
        }

@tool(description="Analyze a domain for crawling characteristics")
async def analyze_domain(domain: str) -> Dict[str, Any]:
    """
    Analyze a domain for crawling characteristics.
    
    domain: The domain to analyze (e.g., "example.com")
    
    Returns dict with these keys:
    - success (bool): Whether domain analysis was successful
    - domain (str): Cleaned domain name that was analyzed
    - likely_to_block_crawlers (bool): Whether site may block crawler access
    - javascript_recommended (bool): Whether JavaScript is needed for this domain
    - domain_type (str): Category of domain ("news", "social_media", "technical", "documentation", "educational", "government", "general")
    - crawlable (bool): Overall assessment if domain can be crawled
    - recommendations (list): List of specific crawling recommendations
    - error (str): Error message (only if success=false)
    """
    try:
        # Clean domain input
        domain = domain.lower().strip()
        if domain.startswith(('http://', 'https://')):
            domain = extract_domain(domain)
        
        is_blocked = any(blocked in domain for blocked in BLOCKED_DOMAINS)
        js_needed = needs_javascript(domain)
        
        # Categorize domain type
        domain_type = categorize_domain(domain)
        
        return {
            "success": True,
            "domain": domain,
            "likely_to_block_crawlers": is_blocked,
            "javascript_recommended": js_needed,
            "domain_type": domain_type,
            "crawlable": not is_blocked,
            "recommendations": get_crawling_recommendations(domain, is_blocked, js_needed)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing domain {domain}: {str(e)}")
        return {
            "success": False,
            "domain": domain,
            "error": str(e)
        }

# Helper functions

def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return url

def is_potential_security_risk(query: str) -> bool:
    """Check if query contains potential security risks."""
    suspicious_patterns = [
        r'[\'"];?\s*(drop|delete|insert|update|select)\s+',
        r'<script[^>]*>',
        r'javascript:',
        r'data:text/html',
        r'file://',
        r'\.\./\.\.',
        r'exec\s*\(',
        r'eval\s*\('
    ]
    
    query_lower = query.lower()
    return any(re.search(pattern, query_lower, re.IGNORECASE) for pattern in suspicious_patterns)

def suggest_url_for_topic(query: str) -> str:
    """Suggest a URL based on topic."""
    topic_mapping = {
        'python': 'https://docs.python.org',
        'javascript': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript',
        'programming': 'https://stackoverflow.com',
        'tech news': 'https://news.ycombinator.com',
        'ai': 'https://arxiv.org/list/cs.AI/recent',
        'machine learning': 'https://arxiv.org/list/cs.LG/recent',
        'cybersecurity': 'https://krebsonsecurity.com',
        'web development': 'https://web.dev',
        'documentation': 'https://devdocs.io',
        'tutorials': 'https://freecodecamp.org',
        'news': 'https://news.ycombinator.com',
        'science': 'https://arxiv.org',
        'research': 'https://scholar.google.com',
        'github': 'https://github.com',
        'open source': 'https://opensource.com'
    }
    
    query_lower = query.lower()
    
    # Check for exact matches first
    for topic, url in topic_mapping.items():
        if topic in query_lower:
            return url
    
    # Default fallback
    return 'https://news.ycombinator.com'

def needs_javascript(domain: str) -> bool:
    """Determine if a domain typically needs JavaScript."""
    js_heavy_domains = [
        'twitter.com', 'facebook.com', 'instagram.com', 'linkedin.com',
        'reddit.com', 'youtube.com', 'gmail.com', 'docs.google.com'
    ]
    
    return any(js_domain in domain.lower() for js_domain in js_heavy_domains)

def get_javascript_settle_time(domain: str) -> int:
    """Get recommended JavaScript settle time in milliseconds for a domain."""
    # Domains that need extra time for images and dynamic content to load
    settle_times = {
        'reddit.com': 5000,      # Reddit images load slowly
        'twitter.com': 4000,     # Twitter images and embeds
        'instagram.com': 6000,   # Instagram images need time
        'facebook.com': 4000,    # Facebook dynamic content
        'youtube.com': 3000,     # YouTube thumbnails and embeds  
        'linkedin.com': 3000,    # LinkedIn images and posts
        'medium.com': 2500,      # Medium images and formatting
        'pinterest.com': 5000,   # Pinterest images load slowly
        'imgur.com': 3000,       # Image hosting site
        'flickr.com': 4000,      # Photo sharing site
        'tumblr.com': 4000,      # Image-heavy social platform
        'tiktok.com': 6000,      # Video thumbnails and content
        'discord.com': 3000,     # Chat interface elements
        'slack.com': 2500,       # Workspace content loading
        'notion.so': 3000,       # Rich content blocks
        'airtable.com': 3000,    # Database views loading
        'figma.com': 4000,       # Design files and previews
        'canva.com': 4000,       # Design templates loading
        'docs.google.com': 2500, # Google Docs content
        'sheets.google.com': 2500, # Google Sheets data
        'drive.google.com': 3000,  # Google Drive previews
    }
    
    domain_lower = domain.lower()
    
    # Check for exact matches first
    for site_domain, settle_time in settle_times.items():
        if site_domain in domain_lower:
            return settle_time
    
    # Check for general patterns
    if any(pattern in domain_lower for pattern in ['shop', 'store', 'ecommerce']):
        return 3000  # E-commerce sites often have dynamic pricing/images
    elif any(pattern in domain_lower for pattern in ['news', 'blog', 'article']):
        return 2000  # News sites usually load faster
    elif any(pattern in domain_lower for pattern in ['docs', 'wiki', 'documentation']):
        return 1500  # Documentation sites are usually static
    elif domain_lower.endswith('.gov') or domain_lower.endswith('.edu'):
        return 1500  # Government and educational sites are usually simpler
    
    # Default for sites that need JavaScript
    if needs_javascript(domain):
        return 2500  # Default settle time for JS-heavy sites
    else:
        return 0     # No settle time needed for static sites

def categorize_domain(domain: str) -> str:
    """Categorize the type of domain."""
    if any(news in domain for news in ['news', 'times', 'post', 'reuters', 'bloomberg']):
        return 'news'
    elif any(social in domain for social in ['twitter', 'facebook', 'instagram', 'linkedin']):
        return 'social_media'
    elif any(tech in domain for tech in ['github', 'stackoverflow', 'developer']):
        return 'technical'
    elif any(docs in domain for docs in ['docs', 'documentation', 'wiki']):
        return 'documentation'
    elif domain.endswith('.edu'):
        return 'educational'
    elif domain.endswith('.gov'):
        return 'government'
    else:
        return 'general'

def get_crawling_recommendations(domain: str, is_blocked: bool, needs_js: bool) -> List[str]:
    """Get crawling recommendations for a domain."""
    recommendations = []
    
    if is_blocked:
        recommendations.append("This domain is known to block crawlers")
        recommendations.append("Consider using alternative sources")
    else:
        recommendations.append("Domain appears to be crawlable")
    
    if needs_js:
        recommendations.append("Enable JavaScript for better content extraction")
    else:
        recommendations.append("Static crawling should work fine")
    
    return recommendations

def create_search_url(invalid_input: str, original_query: str = "") -> str:
    """
    Create a search URL from invalid input using crawler-friendly search engines.
    
    Args:
        invalid_input: The invalid URL input (e.g., "Hacker News")
        original_query: Original user query for context
        
    Returns:
        A valid search URL or empty string if creation fails
    """
    import random
    import urllib.parse
    
    # Crawler-friendly search engines (avoid Google, Bing which block crawlers)
    search_engines = [
        {
            "name": "Yahoo",
            "url": "https://search.yahoo.com/search?p=",
            "weight": 3  # Higher weight = more likely to be selected
        },
        {
            "name": "Startpage",
            "url": "https://www.startpage.com/do/search?query=",
            "weight": 2
        }
    ]
    
    try:
        # Create search terms from the invalid input and original query
        search_terms = []
        
        # Add the invalid input (cleaned up)
        cleaned_input = invalid_input.strip().replace('"', '').replace("'", "")
        if cleaned_input:
            search_terms.append(cleaned_input)
        
        # Add original query if it's different and meaningful
        if original_query and original_query.strip() != cleaned_input:
            # Take key words from the original query
            query_words = original_query.strip().split()
            # Add up to 3 meaningful words (skip common words)
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'like', 'such', 'this', 'that', 'these', 'those'}
            meaningful_words = [word for word in query_words if word.lower() not in stop_words and len(word) > 2]
            search_terms.extend(meaningful_words[:3])
        
        # Create the search query
        search_query = " ".join(search_terms)
        if not search_query.strip():
            return ""
            
        # URL encode the search query
        encoded_query = urllib.parse.quote_plus(search_query)
        
        # Select search engine using weighted random selection
        weighted_engines = []
        for engine in search_engines:
            weighted_engines.extend([engine] * engine["weight"])
        
        selected_engine = random.choice(weighted_engines)
        search_url = selected_engine["url"] + encoded_query
        
        logger.info(f"Created search URL using {selected_engine['name']}: {search_url}")
        return search_url
        
    except Exception as e:
        logger.error(f"Error creating search URL: {str(e)}")
        return ""

def extract_search_engine(url: str) -> str:
    """Extract the search engine name from a search URL."""
    try:
        if "yahoo.com" in url:
            return "Yahoo"
        elif "duckduckgo.com" in url:
            return "DuckDuckGo"
        elif "startpage.com" in url:
            return "Startpage"  
        else:
            return "Unknown"
    except:
        return "Unknown"

# Import decorator system to register tools

from .decorators import get_tool_schemas, execute_tool

# Function to get tools for AI providers
def get_url_suggestion_tools():
    """Get URL suggestion tools in Claude/OpenAI compatible format."""
    return get_tool_schemas()

# Tool execution function
async def execute_url_suggestion_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Execute a URL suggestion tool by name."""
    return await execute_tool(tool_name, **kwargs)

# Export functions
__all__ = ["get_url_suggestion_tools", "execute_url_suggestion_tool", "suggest_url", "validate_url", "analyze_domain"]
