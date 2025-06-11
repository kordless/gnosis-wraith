"""HTML cleaning utilities"""
import re
import logging
from typing import List, Optional

logger = logging.getLogger("gnosis_wraith")

def clean_html(html: str, keep_structure: bool = True) -> str:
    """
    Clean HTML content by removing scripts, styles, and unnecessary elements.
    
    Args:
        html: Raw HTML content
        keep_structure: Whether to preserve basic HTML structure
        
    Returns:
        Cleaned HTML
    """
    logger.info("Cleaning HTML content")
    
    # Remove script tags and their content
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove style tags and their content
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    
    # Remove meta tags
    html = re.sub(r'<meta[^>]*>', '', html, flags=re.IGNORECASE)
    
    # Remove link tags (stylesheets, etc.)
    html = re.sub(r'<link[^>]*>', '', html, flags=re.IGNORECASE)
    
    if not keep_structure:
        # Remove all HTML tags
        html = re.sub(r'<[^>]+>', '', html)
        
        # Clean up whitespace
        html = re.sub(r'\s+', ' ', html)
        html = html.strip()
    else:
        # Keep only essential tags
        allowed_tags = [
            'p', 'div', 'span', 'a', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'thead', 'tbody',
            'strong', 'b', 'em', 'i', 'code', 'pre', 'blockquote', 'article',
            'section', 'nav', 'header', 'footer', 'main'
        ]
        
        # Remove dangerous attributes
        html = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
        html = re.sub(r'\s*javascript:\s*[^"\s>]*', '', html, flags=re.IGNORECASE)
        
        # Clean up excessive whitespace
        html = re.sub(r'\n\s*\n', '\n', html)
        html = re.sub(r'>\s+<', '><', html)
    
    return html.strip()

def extract_text_from_html(html: str) -> str:
    """
    Extract plain text from HTML.
    
    Args:
        html: HTML content
        
    Returns:
        Plain text
    """
    # Remove scripts and styles first
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Replace br tags with newlines
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    
    # Replace p and div tags with double newlines
    html = re.sub(r'</?(p|div)[^>]*>', '\n\n', html, flags=re.IGNORECASE)
    
    # Replace other block elements with newlines
    html = re.sub(r'</?(h[1-6]|li|tr)[^>]*>', '\n', html, flags=re.IGNORECASE)
    
    # Remove all remaining tags
    text = re.sub(r'<[^>]+>', '', html)
    
    # Decode HTML entities
    import html as html_module
    text = html_module.unescape(text)
    
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()