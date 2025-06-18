"""
API Endpoint Aliases

This module provides aliasing functionality to:
1. Expose certain API endpoints at the root level (/)
2. Map /api/* to the current API version (e.g., /api/v2/*)
3. Support version migration (when v3 comes out, /api/* -> /api/v3/*)

Example:
    /health -> /api/v2/health
    /api/crawl -> /api/v2/crawl  (current version)
    /api/v2/crawl -> /api/v2/crawl (explicit version)
    /api/v3/crawl -> /api/v3/crawl (future version)
"""


from quart import Blueprint, redirect, request
from typing import Optional, Dict, Any


# Create alias blueprint (no prefix - serves at root)
alias_bp = Blueprint('alias', __name__)


# ============================================================================
# Configuration
# ============================================================================

# Current API version - change this when migrating to new version
CURRENT_API_VERSION = 'v2'

# Root-level aliases (convenience shortcuts)
ROOT_ALIASES = {
    '/health': '/api/health',  # Direct to actual endpoint
    '/status': '/api/health',  # Direct to actual endpoint
    '/md': '/api/markdown',  # Markdown extraction shortcut
}


# ============================================================================
# Version Management
# ============================================================================

@alias_bp.route('/api/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
async def api_current_version(endpoint: str):
    """
    Map /api/* to the current API version (e.g., /api/v2/*)
    
    This allows /api/crawl to always point to the latest version's crawl endpoint.
    When migrating from v2 to v3, just update CURRENT_API_VERSION.
    """
    # Check if the endpoint already contains a version prefix
    # to avoid infinite redirect loops
    version_prefixes = ['v1/', 'v2/', 'v3/', 'v4/']  # Add more as needed
    for prefix in version_prefixes:
        if endpoint.startswith(prefix):
            # This is already a versioned endpoint, don't redirect
            # Let it pass through to the actual endpoint
            from quart import abort
            abort(404)  # Return 404 to let the actual route handler take over
    
    # Preserve method and query parameters
    query_string = request.query_string.decode() if request.query_string else ''
    url = f'/api/{CURRENT_API_VERSION}/{endpoint}'
    if query_string:
        url += f'?{query_string}'
    
    return redirect(url, 308)



# ============================================================================
# Root Level Aliases
# ============================================================================

@alias_bp.route('/health', methods=['GET', 'HEAD'])
async def health_alias():
    """Alias /health to API health endpoint"""
    query_string = request.query_string.decode() if request.query_string else ''
    url = '/api/health'
    if query_string:
        url += f'?{query_string}'
    return redirect(url, 308)


@alias_bp.route('/status', methods=['GET', 'HEAD'])
async def status_alias():
    """Alias /status to API health endpoint"""
    query_string = request.query_string.decode() if request.query_string else ''
    url = '/api/health'
    if query_string:
        url += f'?{query_string}'
    return redirect(url, 308)



# ============================================================================
# Dynamic Alias System
# ============================================================================

# Additional dynamic aliases - can be loaded from config
DYNAMIC_ALIASES = {
    # Add any additional root-level shortcuts here
    # These are separate from version management
}



def register_dynamic_aliases(app):
    """
    Register dynamic aliases based on configuration.
    
    Args:
        app: The Quart application instance
    """
    all_aliases = {**ROOT_ALIASES, **DYNAMIC_ALIASES}
    
    for alias_path, target_path in all_aliases.items():
        # Create a route handler for each alias
        async def create_alias_handler(target):
            """Create an alias handler that redirects to target"""
            async def alias_handler(**kwargs):
                # Build target URL with path parameters
                url = target
                for key, value in kwargs.items():
                    url = url.replace(f'<{key}>', str(value))
                
                # Preserve query parameters
                query_string = request.query_string.decode() if request.query_string else ''
                if query_string:
                    url += f'?{query_string}'
                
                # Redirect to target endpoint
                return redirect(url, 308)
            
            return alias_handler
        
        # Register the alias route
        handler = create_alias_handler(target_path)
        handler.__name__ = f'alias_{alias_path.replace("/", "_")}'
        app.add_url_rule(
            alias_path,
            endpoint=handler.__name__,
            view_func=handler,
            methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
        )



# ============================================================================
# Convenience Aliases (Optional)
# ============================================================================

# Uncomment if you want to allow version shortcuts like /v2/crawl -> /api/v2/crawl
# @alias_bp.route('/v2/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
# async def v2_shortcut(endpoint: str):
#     """Allow /v2/* as shortcut to /api/v2/*"""
#     query_string = request.query_string.decode() if request.query_string else ''
#     url = f'/api/v2/{endpoint}'
#     if query_string:
#         url += f'?{query_string}'
#     return redirect(url, 308)



# ============================================================================
# Utility Functions
# ============================================================================

def set_current_api_version(version: str):
    """
    Update the current API version. This will change where /api/* points to.
    
    Args:
        version: The new version string (e.g., 'v3')
    """
    global CURRENT_API_VERSION
    CURRENT_API_VERSION = version
    # Note: Health endpoints remain at /api/health regardless of version



def get_current_api_version() -> str:
    """Get the current API version."""
    return CURRENT_API_VERSION


def add_dynamic_alias(alias_path: str, target_path: str):
    """
    Add a new dynamic alias.
    
    Args:
        alias_path: The path to create an alias for (e.g., '/quick-search')
        target_path: The target API path (e.g., '/api/v2/search')
    """
    DYNAMIC_ALIASES[alias_path] = target_path


def remove_dynamic_alias(alias_path: str):
    """
    Remove a dynamic alias.
    
    Args:
        alias_path: The alias path to remove
    """
    if alias_path in DYNAMIC_ALIASES:
        del DYNAMIC_ALIASES[alias_path]


def get_all_aliases() -> Dict[str, str]:
    """
    Get all configured aliases (root + dynamic).
    
    Returns:
        Dictionary of alias_path: target_path mappings
    """
    return {**ROOT_ALIASES, **DYNAMIC_ALIASES}



# ============================================================================
# Development/Debug Endpoint
# ============================================================================

@alias_bp.route('/aliases', methods=['GET'])
async def list_aliases():
    """
    List all configured aliases (useful for debugging).
    
    This endpoint should be disabled in production.
    """
    from quart import jsonify
    return jsonify({
        "current_api_version": CURRENT_API_VERSION,
        "api_version_mapping": {
            "description": "All /api/* requests map to the current version",
            "example": f"/api/crawl -> /api/{CURRENT_API_VERSION}/crawl"
        },
        "root_aliases": ROOT_ALIASES,
        "dynamic_aliases": DYNAMIC_ALIASES,
        "all_aliases": get_all_aliases(),
        "note": "This endpoint should be disabled in production"
    })

