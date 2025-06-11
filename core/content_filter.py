"""Content filtering utilities"""
import logging
from typing import List
import re

logger = logging.getLogger("gnosis_wraith")

def apply_bm25_filter(content: str, query: str, top_k: int = 10) -> str:
    """
    Apply BM25 ranking to filter content based on query relevance.
    
    This is a simplified implementation. A full BM25 implementation would
    require proper tokenization, IDF calculation, and scoring.
    
    Args:
        content: The content to filter
        query: The search query
        top_k: Number of top results to return
        
    Returns:
        Filtered content
    """
    logger.info(f"Applying BM25 filter with query: {query}")
    
    # Split content into paragraphs or sentences
    lines = content.split('\n')
    
    # Simple relevance scoring based on query term presence
    query_terms = query.lower().split()
    scored_lines = []
    
    for line in lines:
        if not line.strip():
            continue
        
        line_lower = line.lower()
        score = 0
        
        # Count occurrences of query terms
        for term in query_terms:
            score += line_lower.count(term)
        
        if score > 0:
            scored_lines.append((score, line))
    
    # Sort by score and take top k
    scored_lines.sort(key=lambda x: x[0], reverse=True)
    
    # Return filtered content
    filtered_lines = [line for _, line in scored_lines[:top_k]]
    
    if not filtered_lines:
        return content  # Return original if no matches
    
    return '\n'.join(filtered_lines)

def apply_keyword_filter(content: str, keywords: List[str], mode: str = 'any') -> str:
    """
    Filter content based on keyword presence.
    
    Args:
        content: The content to filter
        keywords: List of keywords to search for
        mode: 'any' (match any keyword) or 'all' (match all keywords)
        
    Returns:
        Filtered content
    """
    lines = content.split('\n')
    filtered_lines = []
    
    for line in lines:
        line_lower = line.lower()
        
        if mode == 'any':
            # Include line if it contains any keyword
            if any(keyword.lower() in line_lower for keyword in keywords):
                filtered_lines.append(line)
        else:  # mode == 'all'
            # Include line if it contains all keywords
            if all(keyword.lower() in line_lower for keyword in keywords):
                filtered_lines.append(line)
    
    return '\n'.join(filtered_lines) if filtered_lines else content