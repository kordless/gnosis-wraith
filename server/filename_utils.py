"""
Unified filename generation utilities for Gnosis Wraith.

This module provides consistent naming across screenshots, reports, and other files
using a domain_encoded pattern for better organization and shorter filenames.
The encoding is REVERSIBLE so we can decode filenames back to original URLs.
"""

import re
import base64
import json
import zlib
from urllib.parse import urlparse, quote, unquote, urlunparse
from typing import Optional, Tuple


# Emoji encoding for super compact, fun filenames
EMOJI_DIGITS = ['🔥', '💎', '⚡', '🌟', '🎯', '🚀', '💫', '🎨', '🎪', '🎭', 
                '🎮', '🎲', '🎸', '🎺', '🎻', '🏆']  # 16 emojis = base16

def encode_to_emojis(data: str) -> str:
    """Encode string data to emoji sequence (base16 using emojis)."""
    # Convert to bytes, then to hex, then to emojis
    hex_data = data.encode('utf-8').hex()
    emoji_result = ''.join(EMOJI_DIGITS[int(char, 16)] for char in hex_data)
    return emoji_result

def decode_from_emojis(emoji_data: str) -> str:
    """Decode emoji sequence back to original string."""
    # Convert emojis back to hex digits
    hex_chars = []
    for emoji in emoji_data:
        if emoji in EMOJI_DIGITS:
            hex_chars.append(hex(EMOJI_DIGITS.index(emoji))[2:])  # Remove '0x' prefix
    
    hex_string = ''.join(hex_chars)
    # Convert hex back to bytes, then to string
    try:
        return bytes.fromhex(hex_string).decode('utf-8')
    except:
        return ""

def encode_to_base36(data: str) -> str:
    """Encode string to base36 (numbers + lowercase letters)."""
    # Convert string to integer via bytes
    data_bytes = data.encode('utf-8')
    data_int = int.from_bytes(data_bytes, byteorder='big')
    
    # Convert to base36
    if data_int == 0:
        return '0'
    
    digits = '0123456789abcdefghijklmnopqrstuvwxyz'
    result = ''
    while data_int > 0:
        result = digits[data_int % 36] + result
        data_int //= 36
    
    return result

def decode_from_base36(encoded: str) -> str:
    """Decode base36 string back to original."""
    digits = '0123456789abcdefghijklmnopqrstuvwxyz'
    
    # Convert base36 to integer
    data_int = 0
    for char in encoded.lower():
        if char in digits:
            data_int = data_int * 36 + digits.index(char)
    
    # Convert integer back to bytes, then to string
    if data_int == 0:
        return ""
    
    try:
        byte_length = (data_int.bit_length() + 7) // 8
        data_bytes = data_int.to_bytes(byte_length, byteorder='big')
        return data_bytes.decode('utf-8')
    except:
        return ""

def encode_to_base64_safe(data: str) -> str:
    """Encode to filesystem-safe base64 (using - and _ instead of + and /)."""
    encoded = base64.b64encode(data.encode('utf-8')).decode('ascii')
    # Make filesystem safe
    return encoded.replace('+', '-').replace('/', '_').rstrip('=')

def decode_from_base64_safe(encoded: str) -> str:
    """Decode from filesystem-safe base64."""
    # Restore original base64 characters
    restored = encoded.replace('-', '+').replace('_', '/')
    # Add padding if needed
    missing_padding = len(restored) % 4
    if missing_padding:
        restored += '=' * (4 - missing_padding)
    
    try:
        return base64.b64decode(restored).decode('utf-8')
    except:
        return ""

def compress_and_encode(data: str, compression_level: int = 6) -> str:
    """Compress data with zlib and encode as URL-safe base64."""
    try:
        compressed = zlib.compress(data.encode('utf-8'), level=compression_level)
        encoded = base64.urlsafe_b64encode(compressed).decode('utf-8').rstrip('=')
        return encoded
    except Exception:
        # Fallback to regular base64 if compression fails
        return encode_to_base64_safe(data)

def decompress_and_decode(encoded_data: str) -> str:
    """Decompress URL-safe base64 encoded data."""
    try:
        # Add padding if needed
        missing_padding = len(encoded_data) % 4
        if missing_padding:
            encoded_data += '=' * (4 - missing_padding)
        
        compressed = base64.urlsafe_b64decode(encoded_data)
        decompressed = zlib.decompress(compressed).decode('utf-8')
        return decompressed
    except Exception:
        # Fallback to regular base64 decode
        return decode_from_base64_safe(encoded_data)

def generate_compressed_url_filename(url: str, custom_title: Optional[str] = None, 
                                   extension: str = "png") -> str:
    """
    Generate filename using compressed URL approach: Run + compressed_metadata + domain.
    
    Args:
        url: The URL being processed
        custom_title: Optional custom title
        extension: File extension
        
    Returns:
        Filename like: Run_eJwLycgsVgCi4vzcVIXM3IL8opLEvBKFlMSSRIXk_NyCotTiYgAgFw6w_splunk_com.png
    """
    # Extract domain from URL
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Replace dots with underscores for safe filename
        domain_safe = domain.replace('.', '_')
        
    except Exception:
        domain_safe = "unknown_site"
    
    # Create metadata to compress
    metadata = {
        "url": url,
        "title": custom_title.strip() if custom_title and custom_title.strip() else None,
        "domain": domain,
        "path": parsed.path if 'parsed' in locals() else "",
        "query": parsed.query if 'parsed' in locals() else ""
    }
    
    # Convert to compact JSON and compress
    json_data = json.dumps(metadata, separators=(',', ':'))
    compressed_data = compress_and_encode(json_data)
    
    # Generate filename: Run + compressed_data + domain
    filename = f"Run_{compressed_data}_{domain_safe}.{extension}"
    
    return filename

def decode_compressed_url_filename(filename: str) -> Optional[dict]:
    """
    Decode a compressed URL filename back to metadata.
    
    Args:
        filename: Filename to decode (e.g., Run_eJwL...._splunk_com.png)
        
    Returns:
        Dictionary with metadata or None if decoding fails
    """
    try:
        # Remove extension
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Check if it starts with Run_
        if not name_without_ext.startswith('Run_'):
            return None
        
        # Remove Run_ prefix
        data_part = name_without_ext[4:]  # Remove "Run_"
        
        # Find the last underscore to separate compressed data from domain
        last_underscore = data_part.rfind('_')
        if last_underscore == -1:
            return None
            
        compressed_data = data_part[:last_underscore]
        domain_part = data_part[last_underscore + 1:]
        
        # Decompress the data
        json_data = decompress_and_decode(compressed_data)
        if not json_data:
            return None
        
        # Parse JSON metadata
        metadata = json.loads(json_data)
        return metadata
        
    except Exception:
        return None

def generate_encoded_filename(url: str, custom_title: Optional[str] = None, extension: str = "md", 
                            encoding_type: str = "md5") -> str:
    """
    Generate a filename with various encoding options.
    
    Args:
        url: The URL to encode in filename
        custom_title: Optional custom title to include in hash
        extension: File extension (without dot)
        encoding_type: Type of encoding:
            - "md5": Short 8-char hash (default, fast, collision risk)
            - "compressed_url": Run_compressed_metadata_domain format (preserves metadata)
            - "base36", "base64", "emoji": Legacy complex encoding options
        
    Returns:
        String in format depending on encoding_type:
        - md5: domain_hash.ext (e.g., splunk_com_a1b2c3d4.md)
        - compressed_url: Run_metadata_domain.ext (e.g., Run_eJwL..._splunk_com.png)
        
    Examples:
        >>> generate_encoded_filename("https://splunk.com/hiring", "Hiring Info")
        'splunk_com_2183a8fj.md'  # MD5 hash (default)
        
        >>> generate_encoded_filename("https://splunk.com", "Site", "png", "compressed_url")
        'Run_eJwLycgsVgCi4vzcVIXM3IL8opLEvBKFlMSSRIXk_splunk_com.png'  # Compressed URL
    """
    # Extract domain from URL
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Replace dots with underscores for safe filename
        domain_safe = domain.replace('.', '_')
        
    except Exception:
        # Fallback for invalid URLs
        domain_safe = "unknown_site"
    
    # Use compressed URL approach for metadata preservation
    if encoding_type == "compressed_url":
        return generate_compressed_url_filename(url, custom_title, extension)
    
    # Use MD5 hash for short, consistent filenames (default behavior)
    elif encoding_type == "md5" or encoding_type not in ["compressed_url", "base36", "base64", "emoji"]:
        # Create content for hashing (URL + optional title)
        hash_content = url
        if custom_title and custom_title.strip():
            hash_content += f":{custom_title.strip()}"
        
        # Generate 8-character MD5 hash for shorter filenames
        import hashlib
        url_hash = hashlib.md5(hash_content.encode()).hexdigest()[:8]
        filename = f"{domain_safe}_{url_hash}.{extension}"
        return filename
    
    # Fallback to old complex encoding for special cases (reversible but longer)
    else:
        # Create data to encode (store as JSON for structured data)
        data_to_encode = {
            "url": url,
            "title": custom_title.strip() if custom_title and custom_title.strip() else None
        }
        
        # Convert to compact JSON string
        json_data = json.dumps(data_to_encode, separators=(',', ':'))
        
        # Encode based on selected type
        if encoding_type == "emoji":
            encoded_data = encode_to_emojis(json_data)
        elif encoding_type == "base64":
            encoded_data = encode_to_base64_safe(json_data)
        else:  # base36
            encoded_data = encode_to_base36(json_data)
        
        # Combine domain and encoded data
        filename = f"{domain_safe}_{encoded_data}.{extension}"
        return filename

def decode_filename_data(filename: str) -> Optional[dict]:
    """
    Decode a filename back to its original URL and metadata.
    
    Args:
        filename: Encoded filename to decode
        
    Returns:
        Dictionary with 'url' and 'title' keys, or None if decoding fails
        
    Examples:
        >>> decode_filename_data("splunk_com_1x2y3z4w.md")
        {'url': 'https://splunk.com/hiring', 'title': 'Hiring Info'}
    """
    try:
        # Remove extension
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Split domain and encoded data
        if '_' not in name_without_ext:
            return None
            
        # Find the last underscore to separate domain from encoded data
        last_underscore = name_without_ext.rfind('_')
        domain_part = name_without_ext[:last_underscore]
        encoded_part = name_without_ext[last_underscore + 1:]
        
        if not encoded_part:
            return None
        
        # Try different decoding methods
        decoded_json = None
        
        # Try emoji decoding first (check if contains emojis)
        if any(char in EMOJI_DIGITS for char in encoded_part):
            decoded_json = decode_from_emojis(encoded_part)
        
        # Try base64 decoding (check for base64 chars)
        if not decoded_json and any(char in '-_' for char in encoded_part):
            decoded_json = decode_from_base64_safe(encoded_part)
        
        # Try base36 decoding (alphanumeric)
        if not decoded_json:
            decoded_json = decode_from_base36(encoded_part)
        
        if not decoded_json:
            return None
        
        # Parse JSON data
        data = json.loads(decoded_json)
        return data
        
    except Exception as e:
        return None

def is_encoded_filename(filename: str) -> bool:
    """
    Check if a filename uses the new encoded naming pattern.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if filename can be decoded
    """
    return decode_filename_data(filename) is not None


def generate_screenshot_filename(url: str, custom_title: Optional[str] = None, 
                                encoding_type: str = "md5") -> str:
    """
    Generate screenshot filename using short MD5 hash pattern.
    
    Args:
        url: The URL being screenshotted
        custom_title: Optional custom title for unique naming
        encoding_type: Type of encoding to use (md5 for short hashes recommended)
        
    Returns:
        Screenshot filename (e.g., splunk_com_a1b2c3d4.png)
    """
    return generate_encoded_filename(url, custom_title, "png", encoding_type)


def generate_report_filename(url: str, custom_title: Optional[str] = None, 
                           format_type: str = "md", encoding_type: str = "md5") -> str:
    """
    Generate report filename using short MD5 hash pattern.
    
    Args:
        url: The primary URL from the crawl results
        custom_title: Optional custom title for the report
        format_type: Report format (md, json, html)
        encoding_type: Type of encoding to use (md5 for short hashes recommended)
        
    Returns:
        Report filename (e.g., splunk_com_a1b2c3d4.md)
    """
    return generate_encoded_filename(url, custom_title, format_type, encoding_type)




def extract_url_from_crawl_results(crawl_results) -> Optional[str]:
    """
    Extract the primary URL from crawl results for filename generation.
    
    Args:
        crawl_results: Single result dict or list of result dicts
        
    Returns:
        Primary URL string or None if not found
    """
    # Handle single result
    if isinstance(crawl_results, dict):
        return crawl_results.get('url')
    
    # Handle list of results - get first valid URL
    if isinstance(crawl_results, list) and crawl_results:
        for result in crawl_results:
            if isinstance(result, dict) and 'url' in result:
                url = result.get('url')
                if url and isinstance(url, str):
                    return url
    
    return None


def legacy_to_hash_filename(legacy_filename: str) -> Optional[str]:
    """
    Convert legacy long filenames to hash-based format when possible.
    
    Args:
        legacy_filename: Old format filename like "Minimal_Crawl_-_https___www_example_com_path_20250530_181911.md"
        
    Returns:
        New hash format filename or None if conversion not possible
    """
    try:
        # Extract URL from legacy filename pattern
        # Look for patterns like "_-_https___domain_com_" or similar
        url_pattern = r'_-_(https?[_]+[^_]+(?:_[^_]*)*?)(?:_\d{8}_\d{6})?(?:\.[^.]+)?$'
        match = re.search(url_pattern, legacy_filename)
        
        if match:
            # Extract the URL part and decode it
            encoded_url = match.group(1)
            # Replace ___ with :// and remaining _ with /
            decoded_url = encoded_url.replace('___', '://').replace('_', '/')
            
            # Extract extension
            ext_match = re.search(r'\.([^.]+)$', legacy_filename)
            extension = ext_match.group(1) if ext_match else 'md'
            
            # Generate new hash-based filename
            return generate_encoded_filename(decoded_url, extension=extension)
    
    except Exception:
        pass
    
    return None


# Validation function
def is_hash_filename(filename: str) -> bool:
    """
    Check if a filename follows the hash-based naming pattern.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if filename matches domain_hash.ext pattern
    """
    pattern = r'^[a-zA-Z0-9_-]+_[a-f0-9]{8}\.[a-zA-Z0-9]+$'
    return bool(re.match(pattern, filename))


if __name__ == "__main__":
    # Test the functions
    test_urls = [
        "https://splunk.com/hiring",
        "https://www.example.com/path?param=1",
        "https://subdomain.domain.co.uk/very/long/path/here"
    ]
    
    print("Testing filename generation:")
    for url in test_urls:
        print(f"URL: {url}")
        print(f"  Report: {generate_report_filename(url)}")
        print(f"  Screenshot: {generate_screenshot_filename(url)}")
        print(f"  With title: {generate_report_filename(url, 'Custom Title')}")
        print()
    
    # Test legacy conversion
    legacy_files = [
        "Minimal_Crawl_-_https___www_allrecipes_com_recipe_16409_ham-sandwich__20250530_181911.md",
        "Direct_Crawl_-_https___google_com_search_20250530_120000.json"
    ]
    
    print("Testing legacy conversion:")
    for legacy in legacy_files:
        converted = legacy_to_hash_filename(legacy)
        print(f"Legacy: {legacy}")
        print(f"  New: {converted}")
        print(f"  Valid: {is_hash_filename(converted) if converted else False}")
        print()
