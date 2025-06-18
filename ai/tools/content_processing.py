"""
Content processing MCP tools for analyzing and transforming crawled content.
"""

from typing import Dict, Any, Optional, List
from ai.tools.decorators import tool
import logging
import json
import re

logger = logging.getLogger("gnosis_wraith")

@tool(
    name="extract_structured_data_with_schema",
    description="Extract structured data from crawled content using a schema"
)
async def extract_structured_data_with_schema(
    content: str,
    schema: Dict[str, str],
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract structured data based on schema.
    
    Args:
        content: The content to process
        schema: Dictionary defining fields to extract
        session_id: Optional session for context
        
    Returns:
        Extracted structured data
    """
    try:
        # Import AI processing if available
        from ai.anthropic import process_with_anthropic
        import os
        
        # Build extraction prompt
        schema_str = json.dumps(schema, indent=2)
        prompt = f"""Extract the following fields from this content according to the schema:

Schema:
{schema_str}

Content:
{content[:3000]}  # Limit content length

Return the extracted data as JSON matching the schema structure."""
        
        # Use AI to extract if API key available
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if api_key:
            result_text = await process_with_anthropic(prompt, api_key)
            
            # Try to parse as JSON
            try:
                extracted_data = json.loads(result_text)
            except:
                # Fallback to text response
                extracted_data = {"raw_extraction": result_text}
        else:
            # Fallback to regex extraction
            extracted_data = {}
            for field, description in schema.items():
                # Simple pattern matching
                pattern = rf"{field}[:\s]+([^\n]+)"
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    extracted_data[field] = match.group(1).strip()
        
        return {
            "success": True,
            "tool_name": "extract_structured_data_with_schema",
            "extracted_data": extracted_data,
            "schema_used": schema,
            "content_length": len(content)
        }
    except Exception as e:
        logger.error(f"Error extracting structured data: {str(e)}")
        return {
            "success": False,
            "tool_name": "extract_structured_data_with_schema",
            "error": str(e)
        }

@tool(
    name="convert_html_to_clean_markdown",
    description="Convert HTML content to clean, readable Markdown"
)
async def convert_html_to_clean_markdown(
    html: str,
    preserve_links: bool = True,
    preserve_images: bool = True
) -> Dict[str, Any]:
    """
    Convert HTML to Markdown.
    
    Args:
        html: HTML content to convert
        preserve_links: Keep hyperlinks in output
        preserve_images: Keep image references
        
    Returns:
        Clean Markdown content
    """
    try:
        from core.markdown_generation import MarkdownGenerator
        
        generator = MarkdownGenerator()
        markdown = await generator.convert(
            html,
            options={
                'preserve_links': preserve_links,
                'preserve_images': preserve_images
            }
        )
        
        return {
            "success": True,
            "tool_name": "convert_html_to_clean_markdown",
            "markdown": markdown,
            "original_length": len(html),
            "markdown_length": len(markdown),
            "compression_ratio": len(markdown) / max(1, len(html))
        }
    except ImportError:
        # Fallback to simple conversion
        # Remove common HTML tags
        markdown = html
        replacements = [
            (r'<br\s*/?>', '\n'),
            (r'<p[^>]*>', '\n\n'),
            (r'</p>', ''),
            (r'<h1[^>]*>', '\n# '),
            (r'</h1>', '\n'),
            (r'<h2[^>]*>', '\n## '),
            (r'</h2>', '\n'),
            (r'<h3[^>]*>', '\n### '),
            (r'</h3>', '\n'),
            (r'<[^>]+>', '')  # Remove remaining tags
        ]
        
        for pattern, replacement in replacements:
            markdown = re.sub(pattern, replacement, markdown, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        markdown = markdown.strip()
        
        return {
            "success": True,
            "tool_name": "convert_html_to_clean_markdown",
            "markdown": markdown,
            "original_length": len(html),
            "markdown_length": len(markdown),
            "note": "Simple conversion used"
        }
    except Exception as e:
        logger.error(f"Error converting HTML to Markdown: {str(e)}")
        return {
            "success": False,
            "tool_name": "convert_html_to_clean_markdown",
            "error": str(e)
        }

@tool(
    name="analyze_content_sentiment_and_entities",
    description="Analyze content for sentiment, entities, and key topics"
)
async def analyze_content_sentiment_and_entities(
    content: str,
    analyze_sentiment: bool = True,
    extract_entities: bool = True,
    identify_topics: bool = True
) -> Dict[str, Any]:
    """
    Perform content analysis.
    
    Args:
        content: Text content to analyze
        analyze_sentiment: Perform sentiment analysis
        extract_entities: Extract named entities
        identify_topics: Identify main topics
        
    Returns:
        Analysis results
    """
    results = {
        "success": True,
        "tool_name": "analyze_content_sentiment_and_entities",
        "content_length": len(content)
    }
    
    try:
        # Try AI-powered analysis if available
        from ai.anthropic import process_with_anthropic
        import os
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if api_key and (analyze_sentiment or extract_entities or identify_topics):
            analysis_prompt = f"""Analyze the following content:

{content[:2000]}

Please provide:
{"- Sentiment analysis (positive/negative/neutral with confidence score)" if analyze_sentiment else ""}
{"- Named entities (people, organizations, locations, etc.)" if extract_entities else ""}
{"- Main topics and themes" if identify_topics else ""}

Format the response as JSON."""

            analysis_result = await process_with_anthropic(analysis_prompt, api_key)
            
            try:
                analysis_data = json.loads(analysis_result)
                results.update(analysis_data)
            except:
                # Parse text response
                if analyze_sentiment:
                    results["sentiment"] = {"analysis": analysis_result}
                if extract_entities:
                    results["entities"] = {"raw": analysis_result}
                if identify_topics:
                    results["topics"] = {"raw": analysis_result}
        else:
            # Fallback analysis
            if analyze_sentiment:
                # Simple keyword-based sentiment
                positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'best']
                negative_words = ['bad', 'terrible', 'awful', 'worst', 'poor', 'horrible']
                
                content_lower = content.lower()
                pos_count = sum(1 for word in positive_words if word in content_lower)
                neg_count = sum(1 for word in negative_words if word in content_lower)
                
                if pos_count > neg_count:
                    sentiment = "positive"
                    score = 0.6 + (0.4 * min(1, pos_count / 10))
                elif neg_count > pos_count:
                    sentiment = "negative"
                    score = 0.6 + (0.4 * min(1, neg_count / 10))
                else:
                    sentiment = "neutral"
                    score = 0.5
                
                results["sentiment"] = {
                    "label": sentiment,
                    "score": score
                }
            
            if extract_entities:
                # Simple regex-based entity extraction
                entities = []
                
                # Capital words (potential names/organizations)
                capital_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
                matches = re.findall(capital_pattern, content)
                for match in matches[:20]:  # Limit to 20
                    if len(match) > 2:  # Skip short matches
                        entities.append({"text": match, "type": "UNKNOWN"})
                
                results["entities"] = entities
            
            if identify_topics:
                # Word frequency for topics
                words = re.findall(r'\b\w{4,}\b', content.lower())
                word_freq = {}
                for word in words:
                    word_freq[word] = word_freq.get(word, 0) + 1
                
                # Get top words as topics
                top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
                results["topics"] = [word for word, _ in top_words]
        
        return results
        
    except Exception as e:
        logger.error(f"Error analyzing content: {str(e)}")
        return {
            "success": False,
            "tool_name": "analyze_content_sentiment_and_entities",
            "error": str(e)
        }

@tool(
    name="summarize_long_text_intelligently",
    description="Create concise summaries of long text content"
)
async def summarize_long_text_intelligently(
    text: str,
    max_length: int = 500,
    style: str = "bullet_points"
) -> Dict[str, Any]:
    """
    Summarize long text content.
    
    Args:
        text: Text to summarize
        max_length: Maximum summary length
        style: Summary style (bullet_points, paragraph, key_points)
        
    Returns:
        Summary content
    """
    try:
        from ai.anthropic import process_with_anthropic
        import os
        
        style_prompts = {
            "bullet_points": "Summarize the following content in clear bullet points:",
            "paragraph": "Summarize the following content in a concise paragraph:",
            "key_points": "Extract the key points from the following content:"
        }
        
        prompt = f"""{style_prompts.get(style, style_prompts['bullet_points'])}

{text[:3000]}

Keep the summary under {max_length} characters."""
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if api_key:
            summary = await process_with_anthropic(prompt, api_key)
            
            # Truncate if needed
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
        else:
            # Simple extractive summary
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
            
            if style == "bullet_points":
                # Take first few sentences as bullet points
                summary_sentences = sentences[:5]
                summary = "\n• " + "\n• ".join(summary_sentences)
            else:
                # Take first few sentences as paragraph
                summary = ". ".join(sentences[:3]) + "."
            
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
        
        return {
            "success": True,
            "tool_name": "summarize_long_text_intelligently",
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary),
            "compression_ratio": len(summary) / max(1, len(text)),
            "style": style
        }
    except Exception as e:
        logger.error(f"Error summarizing text: {str(e)}")
        return {
            "success": False,
            "tool_name": "summarize_long_text_intelligently",
            "error": str(e)
        }

@tool(
    name="extract_key_information_points",
    description="Extract the most important information points from content"
)
async def extract_key_information_points(
    content: str,
    max_points: int = 10,
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Extract key information points.
    
    Args:
        content: Content to analyze
        max_points: Maximum number of key points
        include_metadata: Include metadata about each point
        
    Returns:
        Key information points
    """
    try:
        key_points = []
        
        # Try AI extraction first
        from ai.anthropic import process_with_anthropic
        import os
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if api_key:
            prompt = f"""Extract the {max_points} most important information points from this content:

{content[:3000]}

Format each point as a clear, concise statement."""
            
            result = await process_with_anthropic(prompt, api_key)
            
            # Parse points
            lines = result.strip().split('\n')
            for line in lines[:max_points]:
                line = line.strip()
                if line and len(line) > 10:
                    # Remove bullet points or numbers
                    line = re.sub(r'^[\d\-•*]+\.?\s*', '', line)
                    key_points.append({
                        "text": line,
                        "importance": "high" if len(key_points) < 3 else "medium"
                    })
        else:
            # Fallback: Extract sentences with important keywords
            important_keywords = [
                'important', 'key', 'critical', 'essential', 'main',
                'primary', 'significant', 'major', 'crucial', 'vital'
            ]
            
            sentences = re.split(r'[.!?]+', content)
            scored_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20:
                    continue
                
                # Score based on keywords and length
                score = 0
                sentence_lower = sentence.lower()
                for keyword in important_keywords:
                    if keyword in sentence_lower:
                        score += 2
                
                # Bonus for sentences with numbers
                if re.search(r'\d+', sentence):
                    score += 1
                
                scored_sentences.append((sentence, score))
            
            # Sort by score and take top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            
            for sentence, score in scored_sentences[:max_points]:
                key_points.append({
                    "text": sentence,
                    "importance": "high" if score > 3 else "medium" if score > 1 else "low"
                })
        
        result = {
            "success": True,
            "tool_name": "extract_key_information_points",
            "key_points": key_points,
            "total_points": len(key_points),
            "content_length": len(content)
        }
        
        if include_metadata:
            result["metadata"] = {
                "extraction_method": "ai" if api_key else "keyword-based",
                "max_points_requested": max_points
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting key points: {str(e)}")
        return {
            "success": False,
            "tool_name": "extract_key_information_points",
            "error": str(e)
        }

@tool(
    name="classify_content_by_topic",
    description="Classify content into predefined or discovered topics/categories"
)
async def classify_content_by_topic(
    content: str,
    categories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Classify content by topic.
    
    Args:
        content: Content to classify
        categories: Optional list of categories to classify into
        
    Returns:
        Classification results
    """
    try:
        default_categories = [
            "technology", "business", "science", "health", "education",
            "entertainment", "sports", "politics", "finance", "other"
        ]
        
        categories = categories or default_categories
        
        # Try AI classification
        from ai.anthropic import process_with_anthropic
        import os
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if api_key:
            prompt = f"""Classify the following content into one or more of these categories:
{', '.join(categories)}

Content:
{content[:2000]}

Return the most relevant categories with confidence scores (0-1)."""
            
            result = await process_with_anthropic(prompt, api_key)
            
            # Parse result
            classification = {}
            lines = result.strip().split('\n')
            for line in lines:
                for category in categories:
                    if category.lower() in line.lower():
                        # Try to extract score
                        score_match = re.search(r'(\d*\.?\d+)', line)
                        score = float(score_match.group(1)) if score_match else 0.7
                        classification[category] = min(1.0, score)
            
            if not classification:
                classification = {"other": 0.5}
        else:
            # Fallback: keyword matching
            classification = {}
            content_lower = content.lower()
            
            keyword_map = {
                "technology": ["software", "computer", "internet", "app", "digital", "tech"],
                "business": ["company", "market", "profit", "revenue", "business", "corporate"],
                "science": ["research", "study", "experiment", "scientific", "discovery"],
                "health": ["health", "medical", "disease", "treatment", "patient", "doctor"],
                "education": ["school", "university", "student", "teacher", "learning", "education"],
                "entertainment": ["movie", "music", "game", "show", "entertainment", "celebrity"],
                "sports": ["game", "player", "team", "score", "championship", "sport"],
                "politics": ["government", "election", "policy", "political", "president", "congress"],
                "finance": ["money", "investment", "stock", "bank", "financial", "economy"]
            }
            
            for category, keywords in keyword_map.items():
                score = sum(1 for keyword in keywords if keyword in content_lower)
                if score > 0:
                    classification[category] = min(1.0, score * 0.2)
            
            if not classification:
                classification = {"other": 0.5}
        
        # Sort by confidence
        sorted_classification = sorted(
            classification.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return {
            "success": True,
            "tool_name": "classify_content_by_topic",
            "primary_category": sorted_classification[0][0] if sorted_classification else "other",
            "all_categories": dict(sorted_classification),
            "confidence": sorted_classification[0][1] if sorted_classification else 0,
            "content_length": len(content)
        }
        
    except Exception as e:
        logger.error(f"Error classifying content: {str(e)}")
        return {
            "success": False,
            "tool_name": "classify_content_by_topic",
            "error": str(e)
        }

def get_content_processing_tools():
    """Get all content processing tools for registration."""
    return [
        extract_structured_data_with_schema,
        convert_html_to_clean_markdown,
        analyze_content_sentiment_and_entities,
        summarize_long_text_intelligently,
        extract_key_information_points,
        classify_content_by_topic
    ]