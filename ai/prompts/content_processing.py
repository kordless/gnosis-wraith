"""Prompts for content processing and analysis using LLMs."""

CONTENT_ANALYSIS_PROMPT = """Analyze the following content for {analysis_type}.

Content:
{content}

Please provide a structured analysis focusing on {analysis_type}. Your response should be clear, accurate, and well-organized.

For entity extraction: List all relevant entities with their types (person, organization, location, etc.)
For sentiment analysis: Determine the overall sentiment and provide reasoning
For classification: Categorize the content and explain your reasoning
For summary: Provide a concise summary of the main points
For key facts: Extract the most important facts and information

Format your response in a clear, structured manner."""

MARKDOWN_CLEANUP_PROMPT = """Clean and optimize the following markdown content.

Markdown:
{markdown}

Goals for cleanup: {goals}
Elements to preserve: {preserve}
Cleaning mode: {mode}

Instructions:
1. Remove any content that appears to be advertisements, navigation, or boilerplate
2. Fix any formatting issues (broken links, inconsistent headers, etc.)
3. Simplify overly complex structures while maintaining readability
4. Preserve all elements marked for preservation
5. Apply {mode} cleaning - be {'very thorough in removing unnecessary content' if '{mode}' == 'aggressive' else 'careful to preserve potentially important content'}

Return only the cleaned markdown without any explanation or comments."""

CONTENT_SUMMARIZATION_PROMPT = """Create a {summary_type} summary of the following content.

Content:
{content}

Summary requirements:
- Type: {summary_type}
- Maximum length: {max_length} words
- Focus areas: {focus_areas}
- Output format: {output_format}

Instructions for different summary types:
- brief: 2-3 sentences capturing the essence
- detailed: Comprehensive summary with main points and supporting details
- bullet_points: Key points in bullet format
- key_facts: Only the most important facts and figures

For JSON format, structure as:
{{
  "summary": "main summary text",
  "key_points": ["point1", "point2", ...],
  "metadata": {{"type": "{summary_type}", "word_count": X}}
}}

Create the summary now:"""

STRUCTURED_DATA_EXTRACTION_PROMPT = """Extract structured data from the following content according to the provided schema.

Content:
{content}

Target Schema:
{schema}

Instructions:
1. Extract ONLY the data that matches the schema structure
2. Use null for missing required fields
3. Ensure all data types match the schema (string, number, boolean, array, object)
4. Do not add fields not present in the schema
5. Return ONLY valid JSON that conforms to the schema

Important: Your response must be valid JSON only, with no additional text or explanation."""

CODE_SUGGESTION_PROMPT = """Analyze the content and suggest code to process it according to the user's goal.

Content structure:
{content_preview}

User's goal: {goal}
Output format: {output_format}

Generate {output_format} code that will:
1. Process the content to achieve the user's goal
2. Handle edge cases and errors appropriately
3. Be efficient and well-commented
4. Follow best practices for {output_format}

For JavaScript: Use modern ES6+ syntax
For Python: Use Python 3.8+ features
For jq: Provide a complete jq expression

Return only the code without explanation."""

CONTENT_TRANSFORMATION_PROMPT = """Transform the content according to the specified requirements.

Original content:
{content}

Transformation requirements:
{requirements}

Target format: {target_format}

Apply the transformations while:
1. Preserving essential information
2. Following the target format specifications
3. Maintaining data integrity
4. Handling any format-specific requirements

Return only the transformed content."""