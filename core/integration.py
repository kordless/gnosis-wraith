"""
Integration layer connecting toolbag, MCP tools, and core functions.
Provides high-level workflows that combine multiple tools.
"""

import logging
from typing import Dict, Any, List, Optional
from ai.toolbag import ToolBag
from ai.tools import get_tools_by_names, TOOL_LIMITS
from core.crawl_functions import crawl_url_direct
from core.browser_session import session_manager

logger = logging.getLogger("gnosis_wraith")

class WraithIntegration:
    """
    Central integration point for Gnosis Wraith's agentic system.
    """
    
    def __init__(self):
        self.toolbag = ToolBag(provider='anthropic')
        self.active_sessions = {}
        
        # Apply tool limits from registry
        for tool_name, limit in TOOL_LIMITS.items():
            self.toolbag.set_tool_limit(tool_name, limit)
    
    async def execute_workflow(
        self,
        workflow_name: str,
        parameters: Dict[str, Any],
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a predefined workflow.
        
        Workflows combine multiple tools in intelligent sequences.
        """
        workflows = {
            "analyze_website": self._workflow_analyze_website,
            "monitor_changes": self._workflow_monitor_changes,
            "extract_data": self._workflow_extract_data,
            "research_topic": self._workflow_research_topic
        }
        
        if workflow_name not in workflows:
            return {
                "success": False,
                "error": f"Unknown workflow: {workflow_name}"
            }
        
        try:
            logger.info(f"Executing workflow: {workflow_name}")
            return await workflows[workflow_name](parameters, api_key)
        except Exception as e:
            logger.error(f"Workflow error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workflow": workflow_name
            }
    
    async def _workflow_analyze_website(
        self,
        params: Dict[str, Any],
        api_key: Optional[str]
    ) -> Dict[str, Any]:
        """
        Analyze a website workflow:
        1. Crawl homepage
        2. Analyze structure
        3. Extract key information
        4. Generate report
        """
        url = params.get('url')
        if not url:
            return {"success": False, "error": "URL required"}
        
        logger.info(f"Starting website analysis for {url}")
        
        # Step 1: Initial crawl with smart execution
        crawl_result = await self.toolbag.execute(
            tools=['crawl_webpage_with_smart_execution'],
            query=f"Crawl the website {url} to understand its content and structure",
            api_key=api_key
        )
        
        if not crawl_result.get('success'):
            return crawl_result
        
        # Extract session if created
        session_id = crawl_result.get('session_id')
        
        # Step 2: Analyze structure
        structure_result = await self.toolbag.execute(
            tools=['analyze_website_structure'],
            query=f"Analyze the structure and navigation of {url}",
            api_key=api_key,
            previous_result=crawl_result
        )
        
        # Step 3: Extract key information
        extract_result = await self.toolbag.execute(
            tools=['extract_key_information_points'],
            query="Extract the most important information from this website",
            api_key=api_key,
            previous_result=structure_result
        )
        
        # Step 4: Generate summary
        summary_result = await self.toolbag.execute(
            tools=['summarize_long_text_intelligently'],
            query="Create a comprehensive summary of the website analysis",
            api_key=api_key,
            previous_result=extract_result
        )
        
        return {
            "success": True,
            "workflow": "analyze_website",
            "url": url,
            "steps_completed": 4,
            "session_id": session_id,
            "analysis": summary_result.get('response', 'No summary available'),
            "structure": structure_result.get('response', 'No structure analysis'),
            "key_points": extract_result.get('response', 'No key points extracted')
        }
    
    async def _workflow_monitor_changes(
        self,
        params: Dict[str, Any],
        api_key: Optional[str]
    ) -> Dict[str, Any]:
        """
        Monitor website for changes:
        1. Crawl current state
        2. Compare with previous crawl
        3. Identify changes
        4. Alert on significant changes
        """
        url = params.get('url')
        previous_crawl_id = params.get('previous_crawl_id')
        
        if not url:
            return {"success": False, "error": "URL required"}
        
        # Step 1: Crawl current state
        current_crawl = await self.toolbag.execute(
            tools=['crawl_webpage_with_smart_execution'],
            query=f"Crawl {url} to get its current state",
            api_key=api_key
        )
        
        if not current_crawl.get('success'):
            return current_crawl
        
        # Step 2: Search for previous crawls if no ID provided
        if not previous_crawl_id:
            search_result = await self.toolbag.execute(
                tools=['search_previous_crawl_results'],
                query=f"Find previous crawls of {url}",
                api_key=api_key
            )
            
            # Extract previous crawl if found
            if search_result.get('success') and search_result.get('results'):
                previous_crawl_id = search_result['results'][0].get('id')
        
        # Step 3: Compare content
        comparison_query = "Compare the current website content with the previous version and identify changes"
        if previous_crawl_id:
            comparison_query += f" (previous crawl ID: {previous_crawl_id})"
        
        comparison_result = await self.toolbag.execute(
            tools=['analyze_content_sentiment_and_entities'],
            query=comparison_query,
            api_key=api_key,
            previous_result=current_crawl
        )
        
        return {
            "success": True,
            "workflow": "monitor_changes",
            "url": url,
            "current_crawl_id": current_crawl.get('storage_id'),
            "previous_crawl_id": previous_crawl_id,
            "changes_detected": comparison_result.get('response', 'No changes analyzed'),
            "timestamp": current_crawl.get('timestamp')
        }
    
    async def _workflow_extract_data(
        self,
        params: Dict[str, Any],
        api_key: Optional[str]
    ) -> Dict[str, Any]:
        """
        Extract structured data:
        1. Crawl target pages
        2. Apply extraction schema
        3. Validate data
        4. Export results
        """
        urls = params.get('urls', [])
        schema = params.get('schema', {})
        
        if not urls:
            return {"success": False, "error": "URLs required"}
        
        if not schema:
            return {"success": False, "error": "Extraction schema required"}
        
        extracted_data = []
        
        # Process each URL
        for url in urls:
            # Step 1: Crawl page
            crawl_result = await self.toolbag.execute(
                tools=['crawl_webpage_with_smart_execution'],
                query=f"Crawl {url} to extract structured data",
                api_key=api_key
            )
            
            if not crawl_result.get('success'):
                extracted_data.append({
                    "url": url,
                    "success": False,
                    "error": crawl_result.get('error')
                })
                continue
            
            # Step 2: Extract structured data
            extract_result = await self.toolbag.execute(
                tools=['extract_structured_data_with_schema'],
                query=f"Extract data from {url} using the provided schema: {schema}",
                api_key=api_key,
                previous_result=crawl_result
            )
            
            extracted_data.append({
                "url": url,
                "success": extract_result.get('success', False),
                "data": extract_result.get('extracted_data', {})
            })
        
        # Step 3: Summarize results
        summary_result = await self.toolbag.execute(
            tools=['summarize_long_text_intelligently'],
            query=f"Summarize the data extraction results from {len(urls)} pages",
            api_key=api_key
        )
        
        return {
            "success": True,
            "workflow": "extract_data",
            "total_urls": len(urls),
            "successful_extractions": sum(1 for d in extracted_data if d['success']),
            "extracted_data": extracted_data,
            "summary": summary_result.get('response', 'No summary available')
        }
    
    async def _workflow_research_topic(
        self,
        params: Dict[str, Any],
        api_key: Optional[str]
    ) -> Dict[str, Any]:
        """
        Research a topic across multiple sources:
        1. Generate search queries
        2. Crawl multiple sources
        3. Extract relevant information
        4. Synthesize findings
        """
        topic = params.get('topic')
        sources = params.get('sources', ['general'])
        max_sources = params.get('max_sources', 5)
        
        if not topic:
            return {"success": False, "error": "Topic required"}
        
        logger.info(f"Starting research on topic: {topic}")
        
        # Step 1: Generate URLs to research
        url_result = await self.toolbag.execute(
            tools=['suggest_url'],
            query=f"Suggest {max_sources} authoritative websites to research about: {topic}",
            api_key=api_key
        )
        
        if not url_result.get('success'):
            return url_result
        
        # Extract URLs from result
        # This would need parsing based on the actual tool response format
        research_urls = []
        if 'urls' in url_result:
            research_urls = url_result['urls'][:max_sources]
        elif 'response' in url_result:
            # Parse URLs from response text
            import re
            url_pattern = r'https?://[^\s]+'
            found_urls = re.findall(url_pattern, str(url_result['response']))
            research_urls = found_urls[:max_sources]
        
        if not research_urls:
            return {
                "success": False,
                "error": "Could not generate research URLs"
            }
        
        # Step 2: Crawl sources
        research_data = []
        for url in research_urls:
            crawl_result = await self.toolbag.execute(
                tools=['crawl_webpage_with_smart_execution'],
                query=f"Crawl {url} to gather information about {topic}",
                api_key=api_key
            )
            
            if crawl_result.get('success'):
                # Extract relevant content
                extract_result = await self.toolbag.execute(
                    tools=['extract_key_information_points'],
                    query=f"Extract information relevant to the topic: {topic}",
                    api_key=api_key,
                    previous_result=crawl_result
                )
                
                research_data.append({
                    "url": url,
                    "key_points": extract_result.get('response', 'No information extracted')
                })
        
        # Step 3: Synthesize findings
        synthesis_query = f"Synthesize the research findings about {topic} from {len(research_data)} sources"
        synthesis_result = await self.toolbag.execute(
            tools=['summarize_long_text_intelligently'],
            query=synthesis_query,
            api_key=api_key
        )
        
        return {
            "success": True,
            "workflow": "research_topic",
            "topic": topic,
            "sources_analyzed": len(research_data),
            "research_data": research_data,
            "synthesis": synthesis_result.get('response', 'No synthesis available')
        }
    
    async def execute_tool_chain(
        self,
        tools: List[str],
        initial_query: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a custom chain of tools.
        
        Args:
            tools: List of tool names to execute in order
            initial_query: Starting query for the chain
            api_key: API key for tool execution
            **kwargs: Additional parameters
            
        Returns:
            Chain execution results
        """
        try:
            result = await self.toolbag.execute_chain(
                tools=tools,
                query=initial_query,
                api_key=api_key,
                **kwargs
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Tool chain execution error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """Get information about active browser sessions."""
        return session_manager.get_active_sessions()
    
    async def cleanup_sessions(self):
        """Clean up expired browser sessions."""
        await session_manager.cleanup_expired_sessions()

# Global integration instance
integration = WraithIntegration()