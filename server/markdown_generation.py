"""
# Markdown Generation Functionality from Crawl4AI

This module contains the core functionality for generating Markdown from HTML content,
extracted from the Crawl4AI project.

## Key Components:
1. Markdown generation strategies
2. Content filtering approaches 
3. HTML to Markdown conversion
4. Link conversion to citations

## Usage:
```python
from markdown_generation import DefaultMarkdownGenerator, PruningContentFilter

# Configure a content filter
content_filter = PruningContentFilter(threshold=0.48)

# Create the markdown generator
markdown_generator = DefaultMarkdownGenerator(content_filter=content_filter)

# Generate markdown from HTML
markdown_result = markdown_generator.generate_markdown(html_content, base_url="https://example.com")

# Access different types of markdown
raw_markdown = markdown_result.raw_markdown
markdown_with_citations = markdown_result.markdown_with_citations
references = markdown_result.references_markdown
fit_markdown = markdown_result.fit_markdown  # Filtered content
```
"""

import re
import urllib.parse as urlparse
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag, NavigableString, Comment
from collections import deque

# Pre-compile the regex pattern for links
LINK_PATTERN = re.compile(r'!?\[([^\]]+)\]\(([^)]+?)(?:\s+"([^"]*)")?\)')

# MarkdownGenerationResult class
@dataclass
class MarkdownGenerationResult:
    """Result of the markdown generation process."""
    raw_markdown: str
    markdown_with_citations: str
    references_markdown: str
    fit_markdown: Optional[str] = None
    fit_html: Optional[str] = None
    
    def __str__(self):
        return self.raw_markdown

# HTML2Text simplified implementation
class HTML2Text:
    """Convert HTML to Markdown."""
    
    def __init__(self, baseurl="", bodywidth=0):
        self.baseurl = baseurl
        self.body_width = bodywidth
        
        # Configuration options
        self.ignore_links = False
        self.ignore_images = False
        self.ignore_emphasis = False
        self.protect_links = False
        self.single_line_break = True  
        self.mark_code = True
        self.escape_snob = False
        self.unicode_snob = False
        
    def update_params(self, **kwargs):
        """Update parameters with custom values."""
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def handle(self, html):
        """Process HTML and return markdown."""
        # This is a simplified implementation
        # In a real implementation, this would parse HTML and convert to markdown
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for tag in ['script', 'style', 'iframe', 'noscript']:
            for element in soup.find_all(tag):
                element.decompose()
        
        text = self._process_element(soup.body or soup)
        return text
    
    def _process_element(self, element):
        """Process an HTML element and convert to markdown."""
        if isinstance(element, NavigableString):
            return str(element)
        
        if not hasattr(element, 'name'):
            return ""
        
        tag = element.name
        result = ""
        
        if tag == 'h1':
            result = "# " + self._get_text(element) + "\n\n"
        elif tag == 'h2':
            result = "## " + self._get_text(element) + "\n\n"
        elif tag == 'h3':
            result = "### " + self._get_text(element) + "\n\n"
        elif tag == 'h4':
            result = "#### " + self._get_text(element) + "\n\n"
        elif tag == 'h5':
            result = "##### " + self._get_text(element) + "\n\n"
        elif tag == 'h6':
            result = "###### " + self._get_text(element) + "\n\n"
        elif tag == 'p':
            result = self._get_text(element) + "\n\n"
        elif tag == 'a' and not self.ignore_links:
            href = element.get('href', '')
            if href:
                text = self._get_text(element)
                if self.protect_links:
                    href = "<" + href + ">"
                result = "[" + text + "](" + href + ")"
            else:
                result = self._get_text(element)
        elif tag == 'strong' or tag == 'b':
            if not self.ignore_emphasis:
                result = "**" + self._get_text(element) + "**"
            else:
                result = self._get_text(element)
        elif tag == 'em' or tag == 'i':
            if not self.ignore_emphasis:
                result = "_" + self._get_text(element) + "_"
            else:
                result = self._get_text(element)
        elif tag == 'code':
            result = "`" + self._get_text(element) + "`"
        elif tag == 'pre':
            result = "```\n" + self._get_text(element) + "\n```\n\n"
        elif tag == 'blockquote':
            lines = self._get_text(element).split('\n')
            result = "> " + "\n> ".join(lines) + "\n\n"
        elif tag == 'ul':
            for li in element.find_all('li', recursive=False):
                result += "* " + self._get_text(li) + "\n"
            result += "\n"
        elif tag == 'ol':
            for i, li in enumerate(element.find_all('li', recursive=False), 1):
                result += f"{i}. " + self._get_text(li) + "\n"
            result += "\n"
        elif tag == 'img' and not self.ignore_images:
            src = element.get('src', '')
            alt = element.get('alt', '')
            result = f"![{alt}]({src})"
        else:
            # Process children of the current element
            for child in element.children:
                result += self._process_element(child)
        
        return result
    
    def _get_text(self, element):
        """Get text content from an element, processing its children."""
        result = ""
        for child in element.children:
            result += self._process_element(child)
        return result

# Enhanced HTML2Text with improved code handling
class CustomHTML2Text(HTML2Text):
    """Enhanced HTML2Text with better handling for code blocks and more."""
    
    def __init__(self, *args, handle_code_in_pre=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.inside_pre = False
        self.inside_code = False
        self.inside_link = False
        self.preserve_tags = set()  # Set of tags to preserve
        self.current_preserved_tag = None
        self.preserved_content = []
        self.preserve_depth = 0
        self.handle_code_in_pre = handle_code_in_pre
    
    def handle(self, html):
        """Process HTML and return markdown with improved code handling."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for tag in ['script', 'style', 'iframe', 'noscript']:
            for element in soup.find_all(tag):
                element.decompose()
        
        text = self._process_element(soup.body or soup)
        return text
    
    def _process_element(self, element):
        """Process an element with enhanced code and pre block handling."""
        if isinstance(element, NavigableString):
            return str(element)
        
        if not hasattr(element, 'name'):
            return ""
        
        tag = element.name
        
        # Enhanced handling for preserved tags
        if tag in self.preserve_tags:
            # Format tag with attributes
            attrs_str = ' '.join(f'{k}="{v}"' for k, v in element.attrs.items())
            return f"<{tag} {attrs_str}>{element.decode_contents()}</{tag}>"
        
        # Enhanced pre and code handling
        if tag == 'pre':
            self.inside_pre = True
            content = "```\n" + self._get_text(element) + "\n```\n\n"
            self.inside_pre = False
            return content
        
        if tag == 'code':
            if self.inside_pre and not self.handle_code_in_pre:
                return self._get_text(element)
            else:
                return "`" + self._get_text(element) + "`"
        
        # Use the parent implementation for other tags
        return super()._process_element(element)


# Fast URL joining for performance (used in link conversion)
def fast_urljoin(base: str, url: str) -> str:
    """Fast URL joining for common cases."""
    if url.startswith(("http://", "https://", "mailto:", "//")):
        return url
    if url.startswith("/"):
        # Handle absolute paths
        if base.endswith("/"):
            return base[:-1] + url
        return base + url
    return urlparse.urljoin(base, url)


# Base class for Markdown generation strategies
class MarkdownGenerationStrategy(ABC):
    """Abstract base class for markdown generation strategies."""

    def __init__(
        self,
        content_filter=None,
        options=None,
        verbose=False,
        content_source="cleaned_html",
    ):
        self.content_filter = content_filter
        self.options = options or {}
        self.verbose = verbose
        self.content_source = content_source

    @abstractmethod
    def generate_markdown(
        self,
        input_html,
        base_url="",
        html2text_options=None,
        content_filter=None,
        citations=True,
        **kwargs,
    ) -> MarkdownGenerationResult:
        """Generate markdown from the selected input HTML."""
        pass


# Default implementation of Markdown generation strategy
class DefaultMarkdownGenerator(MarkdownGenerationStrategy):
    """
    Default implementation of markdown generation strategy.

    How it works:
    1. Generate raw markdown from cleaned HTML.
    2. Convert links to citations.
    3. Generate fit markdown if content filter is provided.
    4. Return MarkdownGenerationResult.
    """

    def __init__(
        self,
        content_filter=None,
        options=None,
        content_source="cleaned_html",
    ):
        super().__init__(content_filter, options, verbose=False, content_source=content_source)

    def convert_links_to_citations(
        self, markdown: str, base_url = ""
    ) -> Tuple[str, str]:
        """
        Convert links in markdown to citations.

        Args:
            markdown: Markdown text.
            base_url: Base URL for URL joins.

        Returns:
            Tuple containing converted markdown and references markdown.
        """
        link_map = {}
        url_cache = {}  # Cache for URL joins
        parts = []
        last_end = 0
        counter = 1

        for match in LINK_PATTERN.finditer(markdown):
            parts.append(markdown[last_end : match.start()])
            text, url, title = match.groups()

            # Use cached URL if available, otherwise compute and cache
            if base_url and not url.startswith(("http://", "https://", "mailto:")):
                if url not in url_cache:
                    url_cache[url] = fast_urljoin(base_url, url)
                url = url_cache[url]

            if url not in link_map:
                desc = []
                if title:
                    desc.append(title)
                if text and text != title:
                    desc.append(text)
                link_map[url] = (counter, ": " + " - ".join(desc) if desc else "")
                counter += 1

            num = link_map[url][0]
            parts.append(
                f"{text}⟨{num}⟩"
                if not match.group(0).startswith("!")
                else f"![{text}⟨{num}⟩]"
            )
            last_end = match.end()

        parts.append(markdown[last_end:])
        converted_text = "".join(parts)

        # Build reference strings
        references = ["\n\n## References\n\n"]
        references.extend(
            f"⟨{num}⟩ {url}{desc}\n"
            for url, (num, desc) in sorted(link_map.items(), key=lambda x: x[1][0])
        )

        return converted_text, "".join(references)

    def generate_markdown(
        self,
        input_html,
        base_url="",
        html2text_options=None,
        options=None,
        content_filter=None,
        citations=True,
        **kwargs,
    ) -> MarkdownGenerationResult:
        """
        Generate markdown with citations from the provided input HTML.

        Args:
            input_html: The HTML content to process.
            base_url: Base URL for URL joins.
            html2text_options: HTML2Text options.
            options: Additional options for markdown generation.
            content_filter: Content filter for generating fit markdown.
            citations: Whether to generate citations.

        Returns:
            MarkdownGenerationResult containing various markdown formats.
        """
        try:
            # Initialize HTML2Text with default options for better conversion
            h = CustomHTML2Text(baseurl=base_url)
            default_options = {
                "body_width": 0,  # Disable text wrapping
                "ignore_emphasis": False,
                "ignore_links": False,
                "ignore_images": False,
                "protect_links": False,
                "single_line_break": True,
                "mark_code": True,
                "escape_snob": False,
            }

            # Update with custom options if provided
            if html2text_options:
                default_options.update(html2text_options)
            elif options:
                default_options.update(options)
            elif self.options:
                default_options.update(self.options)

            h.update_params(**default_options)

            # Ensure we have valid input
            if not input_html:
                input_html = ""
            elif not isinstance(input_html, str):
                input_html = str(input_html)

            # Generate raw markdown
            try:
                raw_markdown = h.handle(input_html)
            except Exception as e:
                raw_markdown = f"Error converting HTML to markdown: {str(e)}"

            raw_markdown = raw_markdown.replace("    ```", "```")

            # Convert links to citations
            markdown_with_citations = raw_markdown
            references_markdown = ""
            if citations:
                try:
                    (
                        markdown_with_citations,
                        references_markdown,
                    ) = self.convert_links_to_citations(raw_markdown, base_url)
                except Exception as e:
                    markdown_with_citations = raw_markdown
                    references_markdown = f"Error generating citations: {str(e)}"

            # Generate fit markdown if content filter is provided
            fit_markdown = ""
            filtered_html = ""
            if content_filter or self.content_filter:
                try:
                    content_filter = content_filter or self.content_filter
                    filtered_html = content_filter.filter_content(input_html)
                    filtered_html = "\n".join(
                        "<div>{}</div>".format(s) for s in filtered_html
                    )
                    fit_markdown = h.handle(filtered_html)
                except Exception as e:
                    fit_markdown = f"Error generating fit markdown: {str(e)}"
                    filtered_html = ""

            return MarkdownGenerationResult(
                raw_markdown=raw_markdown or "",
                markdown_with_citations=markdown_with_citations or "",
                references_markdown=references_markdown or "",
                fit_markdown=fit_markdown or "",
                fit_html=filtered_html or "",
            )
        except Exception as e:
            # If anything fails, return empty strings with error message
            error_msg = f"Error in markdown generation: {str(e)}"
            return MarkdownGenerationResult(
                raw_markdown=error_msg,
                markdown_with_citations=error_msg,
                references_markdown="",
                fit_markdown="",
                fit_html="",
            )


# Base class for content filtering
class RelevantContentFilter(ABC):
    """Abstract base class for content filtering strategies"""

    def __init__(
        self,
        user_query=None,
        verbose=False,
        logger=None,
    ):
        """
        Initializes the RelevantContentFilter class with optional user query.

        Args:
            user_query: User query for filtering (optional).
            verbose: Enable verbose logging (default: False).
            logger: Optional logger instance.
        """
        self.user_query = user_query
        self.included_tags = {
            # Primary structure
            "article", "main", "section", "div",
            # List structures
            "ul", "ol", "li", "dl", "dt", "dd",
            # Text content
            "p", "span", "blockquote", "pre", "code",
            # Headers
            "h1", "h2", "h3", "h4", "h5", "h6",
            # Tables
            "table", "thead", "tbody", "tr", "td", "th",
            # Other semantic elements
            "figure", "figcaption", "details", "summary",
            # Text formatting
            "em", "strong", "b", "i", "mark", "small",
            # Rich content
            "time", "address", "cite", "q",
        }
        self.excluded_tags = {
            "nav", "footer", "header", "aside", 
            "script", "style", "form", "iframe", "noscript",
        }
        self.header_tags = {"h1", "h2", "h3", "h4", "h5", "h6"}
        self.negative_patterns = re.compile(
            r"nav|footer|header|sidebar|ads|comment|promo|advert|social|share", re.I
        )
        self.min_word_count = 2
        self.verbose = verbose
        self.logger = logger

    @abstractmethod
    def filter_content(self, html: str) -> List[str]:
        """Abstract method to be implemented by specific filtering strategies"""
        pass

    def extract_page_query(self, soup: BeautifulSoup, body: Tag) -> str:
        """Common method to extract page metadata with fallbacks"""
        if self.user_query:
            return self.user_query

        query_parts = []

        # Title
        try:
            title = soup.title.string
            if title:
                query_parts.append(title)
        except Exception:
            pass

        if soup.find("h1"):
            query_parts.append(soup.find("h1").get_text())

        # Meta tags
        temp = ""
        for meta_name in ["keywords", "description"]:
            meta = soup.find("meta", attrs={"name": meta_name})
            if meta and meta.get("content"):
                query_parts.append(meta["content"])
                temp += meta["content"]

        # If still empty, grab first significant paragraph
        if not temp:
            # Find the first tag P that has text containing more than 50 characters
            for p in body.find_all("p"):
                if len(p.get_text()) > 150:
                    query_parts.append(p.get_text()[:150])
                    break

        return " ".join(filter(None, query_parts))

    def extract_text_chunks(
        self, body: Tag, min_word_threshold=None
    ) -> List[Tuple[int, str, str, Tag]]:
        """
        Extracts text chunks from a BeautifulSoup body element while preserving order.
        Returns list of tuples (chunk_index, text, tag_type, tag) for classification.
        """
        # Tags to ignore - inline elements that shouldn't break text flow
        INLINE_TAGS = {
            "a", "abbr", "acronym", "b", "bdo", "big", "br", "button",
            "cite", "code", "dfn", "em", "i", "img", "input", "kbd",
            "label", "map", "object", "q", "samp", "script", "select",
            "small", "span", "strong", "sub", "sup", "textarea", "time",
            "tt", "var",
        }

        # Tags that typically contain meaningful headers
        HEADER_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "header"}

        chunks = []
        current_text = []
        chunk_index = 0

        def should_break_chunk(tag: Tag) -> bool:
            """Determine if a tag should cause a break in the current text chunk"""
            return tag.name not in INLINE_TAGS and not (
                tag.name == "p" and len(current_text) == 0
            )

        # Use deque for efficient push/pop operations
        stack = deque([(body, False)])

        while stack:
            element, visited = stack.pop()

            if visited:
                # End of block element - flush accumulated text
                if current_text and should_break_chunk(element):
                    text = " ".join("".join(current_text).split())
                    if text:
                        tag_type = "header" if element.name in HEADER_TAGS else "content"
                        chunks.append((chunk_index, text, tag_type, element))
                        chunk_index += 1
                    current_text = []
                continue

            if isinstance(element, NavigableString):
                if str(element).strip():
                    current_text.append(str(element).strip())
                continue

            # Pre-allocate children to avoid multiple list operations
            children = list(element.children)
            if not children:
                continue

            # Mark block for revisit after processing children
            stack.append((element, True))

            # Add children in reverse order for correct processing
            for child in reversed(children):
                if isinstance(child, (Tag, NavigableString)):
                    stack.append((child, False))

        # Handle any remaining text
        if current_text:
            text = " ".join("".join(current_text).split())
            if text:
                chunks.append((chunk_index, text, "content", body))

        if min_word_threshold:
            chunks = [
                chunk for chunk in chunks if len(chunk[1].split()) >= min_word_threshold
            ]

        return chunks

    def is_excluded(self, tag: Tag) -> bool:
        """Common method for exclusion logic"""
        if tag.name in self.excluded_tags:
            return True
        class_id = " ".join(
            filter(None, [" ".join(tag.get("class", [])), tag.get("id", "")])
        )
        return bool(self.negative_patterns.search(class_id))

    def clean_element(self, tag: Tag) -> str:
        """Common method for cleaning HTML elements with minimal overhead"""
        if not tag or not isinstance(tag, Tag):
            return ""

        unwanted_tags = {"script", "style", "aside", "form", "iframe", "noscript"}
        unwanted_attrs = {
            "style", "onclick", "onmouseover", "align", "bgcolor", "class", "id",
        }

        # Use string builder pattern for better performance
        builder = []

        def render_tag(elem):
            if not isinstance(elem, Tag):
                if isinstance(elem, str):
                    builder.append(elem.strip())
                return

            if elem.name in unwanted_tags:
                return

            # Start tag
            builder.append(f"<{elem.name}")

            # Add cleaned attributes
            attrs = {k: v for k, v in elem.attrs.items() if k not in unwanted_attrs}
            for key, value in attrs.items():
                builder.append(f' {key}="{value}"')

            builder.append(">")

            # Process children
            for child in elem.children:
                render_tag(child)

            # Close tag
            builder.append(f"</{elem.name}>")

        try:
            render_tag(tag)
            return "".join(builder)
        except Exception:
            return str(tag)  # Fallback to original if anything fails


# Simple pruning content filter implementation
class PruningContentFilter(RelevantContentFilter):
    """Content filtering using pruning algorithm with dynamic threshold."""

    def __init__(
        self,
        user_query=None,
        min_word_threshold=None,
        threshold_type="fixed",
        threshold=0.48,
    ):
        """
        Initializes the PruningContentFilter class.

        Args:
            user_query: User query for filtering (optional).
            min_word_threshold: Minimum word threshold for filtering (optional).
            threshold_type: Threshold type for dynamic threshold (default: 'fixed').
            threshold: Fixed threshold value (default: 0.48).
        """
        super().__init__(user_query)
        self.min_word_threshold = min_word_threshold
        self.threshold_type = threshold_type
        self.threshold = threshold

        # Tag importance for dynamic threshold
        self.tag_importance = {
            "article": 1.5,
            "main": 1.4,
            "section": 1.3,
            "p": 1.2,
            "h1": 1.4,
            "h2": 1.3,
            "h3": 1.2,
            "div": 0.7,
            "span": 0.6,
        }

        # Metric weights
        self.metric_weights = {
            "text_density": 0.4,
            "link_density": 0.2,
            "tag_weight": 0.2,
            "class_id_weight": 0.1,
            "text_length": 0.1,
        }

        self.tag_weights = {
            "div": 0.5,
            "p": 1.0,
            "article": 1.5,
            "section": 1.0,
            "span": 0.3,
            "li": 0.5,
            "ul": 0.5,
            "ol": 0.5,
            "h1": 1.2,
            "h2": 1.1,
            "h3": 1.0,
            "h4": 0.9,
            "h5": 0.8,
            "h6": 0.7,
        }

    def filter_content(self, html: str, min_word_threshold=None) -> List[str]:
        """
        Implements content filtering using pruning algorithm with dynamic threshold.

        Args:
            html: HTML content to be filtered.
            min_word_threshold: Minimum word threshold for filtering (optional).

        Returns:
            List of filtered text chunks as HTML strings.
        """
        if not html or not isinstance(html, str):
            return []

        soup = BeautifulSoup(html, 'html.parser')
        if not soup.body:
            soup = BeautifulSoup(f"<body>{html}</body>", 'html.parser')

        # Remove comments and unwanted tags
        self._remove_comments(soup)
        self._remove_unwanted_tags(soup)

        # Prune tree starting from body
        body = soup.find("body")
        self._prune_tree(body)

        # Extract remaining content as list of HTML strings
        content_blocks = []
        for element in body.children:
            if isinstance(element, str) or not hasattr(element, "name"):
                continue
            if len(element.get_text(strip=True)) > 0:
                content_blocks.append(str(element))

        return content_blocks

    def _remove_comments(self, soup):
        """Removes HTML comments"""
        for element in soup(text=lambda text: isinstance(text, Comment)):
            element.extract()

    def _remove_unwanted_tags(self, soup):
        """Removes unwanted tags"""
        for tag in self.excluded_tags:
            for element in soup.find_all(tag):
                element.decompose()

    def _prune_tree(self, node):
        """
        Prunes the tree starting from the given node.

        Args:
            node: The node from which the pruning starts.
        """
        if not node or not hasattr(node, "name") or node.name is None:
            return

        text_len = len(node.get_text(strip=True))
        tag_len = len(node.encode_contents().decode("utf-8"))
        link_text_len = sum(
            len(s.strip())
            for s in (a.string for a in node.find_all("a", recursive=False))
            if s
        )

        metrics = {
            "node": node,
            "tag_name": node.name,
            "text_len": text_len,
            "tag_len": tag_len,
            "link_text_len": link_text_len,
        }

        score = self._compute_composite_score(metrics, text_len, tag_len, link_text_len)

        if self.threshold_type == "fixed":
            should_remove = score < self.threshold
        else:  # dynamic
            tag_importance = self.tag_importance.get(node.name, 0.7)
            text_ratio = text_len / tag_len if tag_len > 0 else 0
            link_ratio = link_text_len / text_len if text_len > 0 else 1

            threshold = self.threshold  # base threshold
            if tag_importance > 1:
                threshold *= 0.8
            if text_ratio > 0.4:
                threshold *= 0.9
            if link_ratio > 0.6:
                threshold *= 1.2

            should_remove = score < threshold

        if should_remove:
            node.decompose()
        else:
            children = [child for child in node.children if hasattr(child, "name")]
            for child in children:
                self._prune_tree(child)

    def _compute_composite_score(self, metrics, text_len, tag_len, link_text_len):
        """Computes the composite score"""
        if self.min_word_threshold:
            # Get raw text from metrics node - avoid extra processing
            text = metrics["node"].get_text(strip=True)
            word_count = text.count(" ") + 1
            if word_count < self.min_word_threshold:
                return -1.0  # Guaranteed removal
                
        score = 0.0
        total_weight = 0.0

        # Text density
        density = text_len / tag_len if tag_len > 0 else 0
        score += self.metric_weights["text_density"] * density
        total_weight += self.metric_weights["text_density"]

        # Link density
        density = 1 - (link_text_len / text_len if text_len > 0 else 0)
        score += self.metric_weights["link_density"] * density
        total_weight += self.metric_weights["link_density"]

        # Tag weight
        tag_score = self.tag_weights.get(metrics["tag_name"], 0.5)
        score += self.metric_weights["tag_weight"] * tag_score
        total_weight += self.metric_weights["tag_weight"]

        # Class/ID weight
        class_score = self._compute_class_id_weight(metrics["node"])
        score += self.metric_weights["class_id_weight"] * max(0, class_score)
        total_weight += self.metric_weights["class_id_weight"]

        # Text length
        import math
        score += self.metric_weights["text_length"] * math.log(text_len + 1)
        total_weight += self.metric_weights["text_length"]

        return score / total_weight if total_weight > 0 else 0

    def _compute_class_id_weight(self, node):
        """Computes the class ID weight"""
        class_id_score = 0
        if "class" in node.attrs:
            classes = " ".join(node["class"])
            if self.negative_patterns.match(classes):
                class_id_score -= 0.5
        if "id" in node.attrs:
            element_id = node["id"]
            if self.negative_patterns.match(element_id):
                class_id_score -= 0.5
        return class_id_score


# Simplified implementation of the BM25 content filter
class SimpleBM25ContentFilter(RelevantContentFilter):
    """Simplified content filtering using relevance scores."""
    
    def __init__(self, user_query=None, threshold=0.5):
        super().__init__(user_query)
        self.threshold = threshold
        
    def filter_content(self, html: str) -> List[str]:
        """Simple implementation that keeps relevant content based on a threshold."""
        if not html or not isinstance(html, str):
            return []
            
        soup = BeautifulSoup(html, 'html.parser')
        if not soup.body:
            soup = BeautifulSoup(f"<body>{html}</body>", 'html.parser')
            
        body = soup.find('body')
        query = self.extract_page_query(soup, body)
        
        if not query:
            return []
            
        # Get content blocks
        candidates = []
        for tag in body.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if not self.is_excluded(tag) and len(tag.get_text().strip()) > 10:
                candidates.append(tag)
                
        # Filter content blocks by relevance
        results = []
        for tag in candidates:
            text = tag.get_text()
            # A simplified relevance score - in reality, use BM25
            score = 0
            for word in query.lower().split():
                if word in text.lower():
                    score += 0.1
                    
            # Apply importance based on tag
            if tag.name in ['h1', 'h2', 'h3']:
                score *= 1.5
                
            if score >= self.threshold:
                results.append(self.clean_element(tag))
                
        return results