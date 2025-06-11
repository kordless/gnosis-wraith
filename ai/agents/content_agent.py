"""Content processing agent for analysis, cleaning, and summarization using LLMs."""
import json
import logging
from typing import Dict, Any, Optional, List
from ai.anthropic import AnthropicClient
from ai.openai import OpenAIClient
from ai.gemini import GeminiClient
from ai.prompts.content_processing import (
    CONTENT_ANALYSIS_PROMPT,
    MARKDOWN_CLEANUP_PROMPT,
    CONTENT_SUMMARIZATION_PROMPT,
    STRUCTURED_DATA_EXTRACTION_PROMPT
)

logger = logging.getLogger("gnosis_wraith")

class ContentAgent:
    """Agent for processing content using LLMs."""
    
    def __init__(self):
        self.anthropic_client = None
        self.openai_client = None
        self.gemini_client = None
    
    async def analyze_content(
        self,
        content: str,
        analysis_type: str,
        custom_prompt: Optional[str],
        llm_provider: str,
        llm_token: str,
        llm_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze content using LLM.
        
        Args:
            content: The content to analyze
            analysis_type: Type of analysis (entities, sentiment, classification, etc.)
            custom_prompt: Custom analysis prompt to override defaults
            llm_provider: LLM provider to use
            llm_token: API token for the provider
            llm_model: Optional specific model to use
            
        Returns:
            Analysis results
        """
        try:
            # Prepare the analysis prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = CONTENT_ANALYSIS_PROMPT.format(
                    analysis_type=analysis_type,
                    content=content[:5000]  # Limit content length
                )
            
            # Get response from LLM
            response = await self._call_llm(
                prompt=prompt,
                provider=llm_provider,
                token=llm_token,
                model=llm_model,
                system_prompt="You are a content analysis expert. Analyze the provided content and return structured insights."
            )
            
            if not response['success']:
                return response
            
            # Parse the analysis
            try:
                analysis = self._parse_analysis_response(response['content'], analysis_type)
                return {
                    'success': True,
                    'analysis': analysis,
                    'analysis_type': analysis_type,
                    'tokens_used': response.get('tokens_used', 0)
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to parse analysis response: {str(e)}',
                    'raw_response': response['content']
                }
            
        except Exception as e:
            logger.error(f"Content analysis error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def clean_markdown(
        self,
        markdown: str,
        goals: List[str],
        preserve: List[str],
        llm_provider: str,
        llm_token: str,
        llm_model: Optional[str] = None,
        aggressive: bool = False
    ) -> Dict[str, Any]:
        """
        Clean and optimize markdown content using LLM.
        
        Args:
            markdown: The markdown content to clean
            goals: Cleanup goals (remove_ads, fix_formatting, simplify_structure, etc.)
            preserve: Elements to preserve (links, images, tables, etc.)
            llm_provider: LLM provider to use
            llm_token: API token for the provider
            llm_model: Optional specific model to use
            aggressive: Whether to use aggressive cleaning
            
        Returns:
            Cleaned markdown and metadata
        """
        try:
            # Handle large documents by chunking if needed
            if len(markdown) > 10000:
                return await self._clean_markdown_chunked(
                    markdown, goals, preserve, llm_provider, llm_token, llm_model, aggressive
                )
            
            # Prepare the cleanup prompt
            prompt = MARKDOWN_CLEANUP_PROMPT.format(
                markdown=markdown,
                goals=", ".join(goals),
                preserve=", ".join(preserve),
                mode="aggressive" if aggressive else "conservative"
            )
            
            # Get response from LLM
            response = await self._call_llm(
                prompt=prompt,
                provider=llm_provider,
                token=llm_token,
                model=llm_model,
                system_prompt="You are a markdown optimization expert. Clean and improve the provided markdown while preserving important content."
            )
            
            if not response['success']:
                return response
            
            cleaned_markdown = response['content']
            
            # Calculate improvements
            original_lines = markdown.count('\n')
            cleaned_lines = cleaned_markdown.count('\n')
            original_chars = len(markdown)
            cleaned_chars = len(cleaned_markdown)
            
            return {
                'success': True,
                'markdown': cleaned_markdown,
                'improvements': {
                    'lines_removed': original_lines - cleaned_lines,
                    'chars_removed': original_chars - cleaned_chars,
                    'reduction_percentage': round((1 - cleaned_chars/original_chars) * 100, 2) if original_chars > 0 else 0
                },
                'goals_applied': goals,
                'preserved': preserve,
                'tokens_used': response.get('tokens_used', 0)
            }
            
        except Exception as e:
            logger.error(f"Markdown cleanup error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def summarize_content(
        self,
        content: str,
        summary_type: str,
        max_length: Optional[int],
        focus_areas: Optional[List[str]],
        output_format: str,
        llm_provider: str,
        llm_token: str,
        llm_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Summarize content using LLM.
        
        Args:
            content: The content to summarize
            summary_type: Type of summary (brief, detailed, bullet_points, key_facts)
            max_length: Maximum length of summary in words
            focus_areas: Specific areas to focus on
            output_format: Output format (text, markdown, json)
            llm_provider: LLM provider to use
            llm_token: API token for the provider
            llm_model: Optional specific model to use
            
        Returns:
            Summary and metadata
        """
        try:
            # Prepare the summarization prompt
            prompt = CONTENT_SUMMARIZATION_PROMPT.format(
                content=content[:8000],  # Limit content length
                summary_type=summary_type,
                max_length=max_length or "appropriate length",
                focus_areas=", ".join(focus_areas) if focus_areas else "all key points",
                output_format=output_format
            )
            
            # Get response from LLM
            response = await self._call_llm(
                prompt=prompt,
                provider=llm_provider,
                token=llm_token,
                model=llm_model,
                system_prompt="You are an expert at creating concise, informative summaries. Summarize the provided content according to the specifications."
            )
            
            if not response['success']:
                return response
            
            summary = response['content']
            
            # Parse JSON if requested
            if output_format == 'json':
                try:
                    summary = json.loads(summary)
                except:
                    # If JSON parsing fails, return as text
                    pass
            
            return {
                'success': True,
                'summary': summary,
                'summary_type': summary_type,
                'output_format': output_format,
                'original_length': len(content),
                'summary_length': len(str(summary)),
                'compression_ratio': round(len(str(summary)) / len(content), 3) if len(content) > 0 else 0,
                'tokens_used': response.get('tokens_used', 0)
            }
            
        except Exception as e:
            logger.error(f"Content summarization error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def extract_structured_data(
        self,
        content: str,
        schema: Dict[str, Any],
        llm_provider: str,
        llm_token: str,
        llm_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from content according to a schema.
        
        Args:
            content: The content to extract from
            schema: JSON schema describing the desired output structure
            llm_provider: LLM provider to use
            llm_token: API token for the provider
            llm_model: Optional specific model to use
            
        Returns:
            Extracted structured data
        """
        try:
            # Prepare the extraction prompt
            prompt = STRUCTURED_DATA_EXTRACTION_PROMPT.format(
                content=content[:6000],
                schema=json.dumps(schema, indent=2)
            )
            
            # Get response from LLM
            response = await self._call_llm(
                prompt=prompt,
                provider=llm_provider,
                token=llm_token,
                model=llm_model,
                system_prompt="You are a data extraction expert. Extract structured data from the content according to the provided schema. Always return valid JSON."
            )
            
            if not response['success']:
                return response
            
            # Parse the extracted data
            try:
                extracted_data = json.loads(response['content'])
                return {
                    'success': True,
                    'data': extracted_data,
                    'schema': schema,
                    'tokens_used': response.get('tokens_used', 0)
                }
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f'Failed to parse extracted data as JSON: {str(e)}',
                    'raw_response': response['content']
                }
            
        except Exception as e:
            logger.error(f"Structured data extraction error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _clean_markdown_chunked(
        self,
        markdown: str,
        goals: List[str],
        preserve: List[str],
        llm_provider: str,
        llm_token: str,
        llm_model: Optional[str],
        aggressive: bool
    ) -> Dict[str, Any]:
        """Handle large markdown documents by chunking."""
        # Split into chunks at heading boundaries
        chunks = self._split_markdown_chunks(markdown, max_chunk_size=8000)
        cleaned_chunks = []
        total_tokens = 0
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Cleaning chunk {i+1}/{len(chunks)}")
            
            result = await self.clean_markdown(
                markdown=chunk,
                goals=goals,
                preserve=preserve,
                llm_provider=llm_provider,
                llm_token=llm_token,
                llm_model=llm_model,
                aggressive=aggressive
            )
            
            if not result['success']:
                return result
            
            cleaned_chunks.append(result['markdown'])
            total_tokens += result.get('tokens_used', 0)
        
        # Combine chunks
        cleaned_markdown = "\n\n".join(cleaned_chunks)
        
        # Calculate improvements
        original_chars = len(markdown)
        cleaned_chars = len(cleaned_markdown)
        
        return {
            'success': True,
            'markdown': cleaned_markdown,
            'improvements': {
                'chunks_processed': len(chunks),
                'chars_removed': original_chars - cleaned_chars,
                'reduction_percentage': round((1 - cleaned_chars/original_chars) * 100, 2) if original_chars > 0 else 0
            },
            'goals_applied': goals,
            'preserved': preserve,
            'tokens_used': total_tokens
        }
    
    def _split_markdown_chunks(self, markdown: str, max_chunk_size: int) -> List[str]:
        """Split markdown into chunks at heading boundaries."""
        lines = markdown.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            
            # Check if this is a heading
            is_heading = line.strip().startswith('#')
            
            # Start new chunk if:
            # 1. Adding this line would exceed max size AND we have content
            # 2. This is a major heading (# or ##) AND we have substantial content
            if (current_size + line_size > max_chunk_size and current_chunk) or \
               (is_heading and line.strip().startswith(('# ', '## ')) and current_size > max_chunk_size / 2):
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def _parse_analysis_response(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """Parse analysis response based on type."""
        # Try to parse as JSON first
        try:
            return json.loads(response)
        except:
            pass
        
        # Parse based on analysis type
        if analysis_type == 'entities':
            # Simple entity extraction
            entities = []
            for line in response.split('\n'):
                if ':' in line:
                    entity_type, entity_value = line.split(':', 1)
                    entities.append({
                        'type': entity_type.strip(),
                        'value': entity_value.strip()
                    })
            return {'entities': entities}
        
        elif analysis_type == 'sentiment':
            # Simple sentiment parsing
            lower_response = response.lower()
            if 'positive' in lower_response:
                sentiment = 'positive'
            elif 'negative' in lower_response:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            return {
                'sentiment': sentiment,
                'explanation': response
            }
        
        elif analysis_type == 'classification':
            # Return first line as category
            lines = response.strip().split('\n')
            return {
                'category': lines[0] if lines else 'unknown',
                'explanation': '\n'.join(lines[1:]) if len(lines) > 1 else ''
            }
        
        else:
            # Generic analysis
            return {
                'analysis': response,
                'type': analysis_type
            }
    
    async def _call_llm(
        self,
        prompt: str,
        provider: str,
        token: str,
        model: Optional[str],
        system_prompt: str
    ) -> Dict[str, Any]:
        """Call the appropriate LLM provider."""
        try:
            if provider == 'anthropic':
                if not self.anthropic_client:
                    self.anthropic_client = AnthropicClient(api_key=token)
                
                result = await self.anthropic_client.generate(
                    prompt=prompt,
                    system=system_prompt,
                    model=model or "claude-3-opus-20240229",
                    max_tokens=4000
                )
                
                return {
                    'success': True,
                    'content': result.content[0].text,
                    'tokens_used': result.usage.input_tokens + result.usage.output_tokens
                }
                
            elif provider == 'openai':
                if not self.openai_client:
                    self.openai_client = OpenAIClient(api_key=token)
                
                result = await self.openai_client.chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    model=model or "gpt-4-turbo-preview",
                    max_tokens=4000
                )
                
                return {
                    'success': True,
                    'content': result['choices'][0]['message']['content'],
                    'tokens_used': result['usage']['total_tokens']
                }
                
            elif provider == 'gemini':
                if not self.gemini_client:
                    self.gemini_client = GeminiClient(api_key=token)
                
                result = await self.gemini_client.generate_content(
                    prompt=f"{system_prompt}\n\n{prompt}",
                    model=model or "gemini-pro"
                )
                
                return {
                    'success': True,
                    'content': result['candidates'][0]['content']['parts'][0]['text'],
                    'tokens_used': 0  # Gemini doesn't provide token count
                }
                
            else:
                return {
                    'success': False,
                    'error': f'Unsupported LLM provider: {provider}'
                }
                
        except Exception as e:
            logger.error(f"LLM call error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }