"""
Enhanced Markdown Generation for Gnosis Wraith

This module incorporates the best parts of html-to-markdown library
while maintaining compatibility with the existing Gnosis Wraith pipeline.

Key improvements:
- Better inline element handling
- Improved table support with colspan
- Cleaner heading conversion
- More robust text processing
- Better handling of nested elements
"""

import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple, List, Callable, Literal
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag, NavigableString, Comment
from functools import partial
import urllib.parse as urlparse

# Import base class from original module
from core.markdown_generation import MarkdownGenerationStrategy

# Pre-compile regex patterns

LINK_PATTERN = re.compile(r'!?\[([^\]]+)\](\([^)]+?)(?:\s+"([^"]*)")?\)')
WHITESPACE_RE = re.compile(r'\s+')
LINE_BEGINNING_RE = re.compile(r'^', re.MULTILINE)

# Constants
ATX = 'atx'
ATX_CLOSED = 'atx_closed'
UNDERLINED = 'underlined'
SPACES = 'spaces'
BACKSLASH = 'backslash'

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


def chomp(text: str) -> Tuple[str, str, str]:
    """
    Separate leading/trailing whitespace from text content.
    Returns (prefix, text, suffix)
    """
    prefix = ''
    suffix = ''
    
    # Extract leading whitespace
    match = re.match(r'^(\s*)', text)
    if match:
        prefix = match.group(1)
        text = text[len(prefix):]
    
    # Extract trailing whitespace
    match = re.search(r'(\s*)$', text)
    if match:
        suffix = match.group(1)
        text = text[:-len(suffix)] if suffix else text
    
    return prefix, suffix, text


def escape(text: str, escape_misc: bool = True, escape_asterisks: bool = True, 
           escape_underscores: bool = True) -> str:
    """Escape special Markdown characters."""
    if not text:
        return text
    
    # Escape backslashes first
    text = text.replace('\\', '\\\\')
    
    if escape_misc:
        # Escape other special characters
        for char in ['`', '!', '#', '>', '+', '-', '=', '|', '{', '}', '.', '[', ']', '(', ')']:
            text = text.replace(char, f'\\{char}')
    
    if escape_asterisks:
        text = text.replace('*', '\\*')
    
    if escape_underscores:
        text = text.replace('_', '\\_')
    
    return text


class EnhancedMarkdownConverter:
    """Enhanced converter with better element handling."""
    
    def __init__(self, 
                 heading_style: Literal['atx', 'atx_closed', 'underlined'] = ATX,
                 bullets: str = '*+-',
                 strong_em_symbol: str = '*',
                 code_language: str = '',
                 escape_asterisks: bool = True,
                 escape_underscores: bool = True,
                 escape_misc: bool = True,
                 newline_style: str = SPACES,
                 wrap: bool = False,
                 wrap_width: int = 80,
                 convert_as_inline: bool = False,
                 autolinks: bool = True,
                 default_title: bool = False):
        
        self.heading_style = heading_style
        self.bullets = bullets
        self.strong_em_symbol = strong_em_symbol
        self.code_language = code_language
        self.escape_asterisks = escape_asterisks
        self.escape_underscores = escape_underscores
        self.escape_misc = escape_misc
        self.newline_style = newline_style
        self.wrap = wrap
        self.wrap_width = wrap_width
        self.convert_as_inline = convert_as_inline
        self.autolinks = autolinks
        self.default_title = default_title
        
        # Build converters map
        self.converters = self._build_converters()
    
    def _build_converters(self) -> Dict[str, Callable]:
        """Build the converters map for different HTML elements."""
        return {
            'a': self._convert_a,
            'b': partial(self._create_inline_converter, self.strong_em_symbol * 2),
            'strong': partial(self._create_inline_converter, self.strong_em_symbol * 2),
            'em': partial(self._create_inline_converter, self.strong_em_symbol),
            'i': partial(self._create_inline_converter, self.strong_em_symbol),
            'code': partial(self._create_inline_converter, '`'),
            'kbd': partial(self._create_inline_converter, '`'),
            'samp': partial(self._create_inline_converter, '`'),
            'del': partial(self._create_inline_converter, '~~'),
            's': partial(self._create_inline_converter, '~~'),
            'sub': partial(self._create_inline_converter, '~'),
            'sup': partial(self._create_inline_converter, '^'),
            'h1': partial(self._convert_heading, 1),
            'h2': partial(self._convert_heading, 2),
            'h3': partial(self._convert_heading, 3),
            'h4': partial(self._convert_heading, 4),
            'h5': partial(self._convert_heading, 5),
            'h6': partial(self._convert_heading, 6),
            'p': self._convert_p,
            'br': self._convert_br,
            'hr': lambda tag, text: '\n\n---\n\n',
            'blockquote': self._convert_blockquote,
            'pre': self._convert_pre,
            'ul': self._convert_list,
            'ol': self._convert_list,
            'li': self._convert_li,
            'img': self._convert_img,
            'table': lambda tag, text: f'\n\n{text}\n',
            'thead': lambda tag, text: text,
            'tbody': lambda tag, text: text,
            'tr': self._convert_tr,
            'td': self._convert_td,
            'th': self._convert_th,
            'script': lambda tag, text: '',
            'style': lambda tag, text: '',
        }
    
    def _create_inline_converter(self, markup: str, tag: Tag, text: str) -> str:
        """Generic inline converter for bold, italic, code, etc."""
        if tag.find_parent(['pre', 'code', 'kbd', 'samp']):
            return text
        
        if not text.strip():
            return ''
        
        prefix, suffix, text = chomp(text)
        
        # Handle closing tags for sub/sup
        if markup in ['^', '~']:
            return f'{prefix}{markup}{text}{markup}{suffix}'
        
        return f'{prefix}{markup}{text}{markup}{suffix}'
    
    def _convert_a(self, tag: Tag, text: str) -> str:
        """Convert anchor tags to markdown links."""
        prefix, suffix, text = chomp(text)
        if not text:
            return ''
        
        href = tag.get('href', '')
        title = tag.get('title', '')
        
        # Handle autolinks
        if self.autolinks and text.replace(r'\_', '_') == href and not title:
            return f'<{href}>'
        
        # Add default title if requested
        if self.default_title and not title:
            title = href
        
        # Format the link
        title_part = f' "{title}"' if title else ''
        return f'{prefix}[{text}]({href}{title_part}){suffix}' if href else text
    
    def _convert_heading(self, level: int, tag: Tag, text: str) -> str:
        """Convert heading tags."""
        if self.convert_as_inline:
            return text
        
        text = text.strip()
        if not text:
            return ''
        
        if self.heading_style == UNDERLINED and level <= 2:
            char = '=' if level == 1 else '-'
            return f'\n{text}\n{char * len(text)}\n\n'
        
        hashes = '#' * level
        if self.heading_style == ATX_CLOSED:
            return f'{hashes} {text} {hashes}\n\n'
        
        return f'{hashes} {text}\n\n'
    
    def _convert_p(self, tag: Tag, text: str) -> str:
        """Convert paragraph tags."""
        if self.convert_as_inline:
            return text
        
        if self.wrap and text:
            # Simple wrapping - can be enhanced with textwrap
            import textwrap
            text = textwrap.fill(text, width=self.wrap_width)
        
        return f'{text}\n\n' if text else ''
    
    def _convert_br(self, tag: Tag, text: str) -> str:
        """Convert line break tags."""
        if self.convert_as_inline:
            return ''
        
        return '\\\\n' if self.newline_style == BACKSLASH else '  \n'
    
    def _convert_blockquote(self, tag: Tag, text: str) -> str:
        """Convert blockquote tags."""
        if self.convert_as_inline:
            return text
        
        if not text:
            return ''
        
        # Add > prefix to each line
        lines = text.strip().split('\n')
        quoted = '\n'.join(f'> {line}' for line in lines)
        return f'\n{quoted}\n\n'
    
    def _convert_pre(self, tag: Tag, text: str) -> str:
        """Convert preformatted text tags."""
        if not text:
            return ''
        
        # Check for code tag inside pre
        code_tag = tag.find('code')
        if code_tag:
            # Try to detect language from class
            classes = code_tag.get('class', [])
            lang = ''
            for cls in classes:
                if cls.startswith('language-'):
                    lang = cls[9:]
                    break
            
            lang = lang or self.code_language
        else:
            lang = self.code_language
        
        return f'\n```{lang}\n{text}\n```\n'
    
    def _convert_list(self, tag: Tag, text: str) -> str:
        """Convert list tags."""
        # Check if nested
        parent_li = tag.find_parent('li')
        if parent_li:
            # For nested lists, just add a newline before
            return '\n' + text.rstrip()
        
        # Add newline after list if there's a following sibling
        if tag.next_sibling and hasattr(tag.next_sibling, 'name'):
            return text + '\n'
        
        return text

    
    def _convert_li(self, tag: Tag, text: str) -> str:
        """Convert list item tags."""
        parent = tag.parent
        if parent and parent.name == 'ol':
            # Ordered list - get the number
            start = int(parent.get('start', 1))
            index = len([t for t in parent.find_all('li') if t is tag or t.sourceline < tag.sourceline])
            bullet = f'{start + index - 1}.'
        else:
            # Unordered list - get appropriate bullet
            depth = len(list(tag.find_parents(['ul', 'ol']))) - 1
            bullet = self.bullets[depth % len(self.bullets)]
        
        text = text.strip()
        return f'{bullet} {text}\n'
    
    def _convert_img(self, tag: Tag, text: str) -> str:
        """Convert image tags."""
        alt = tag.get('alt', '')
        src = tag.get('src', '')
        title = tag.get('title', '')
        
        if self.convert_as_inline:
            return alt
        
        title_part = f' "{title}"' if title else ''
        return f'![{alt}]({src}{title_part})'
    
    def _get_colspan(self, tag: Tag) -> int:
        """Get colspan value from table cell."""
        colspan = tag.get('colspan', '1')
        try:
            return int(colspan)
        except (ValueError, TypeError):
            return 1
    
    def _convert_td(self, tag: Tag, text: str) -> str:
        """Convert table data cell."""
        colspan = self._get_colspan(tag)
        text = text.strip().replace('\n', ' ')
        return ' ' + text + ' |' * colspan
    
    def _convert_th(self, tag: Tag, text: str) -> str:
        """Convert table header cell."""
        return self._convert_td(tag, text)
    
    def _convert_tr(self, tag: Tag, text: str) -> str:
        """Convert table row."""
        cells = tag.find_all(['td', 'th'])
        if not cells:
            return ''
        
        # Check if this is a header row
        is_header = all(cell.name == 'th' for cell in cells)
        
        # Check if first row of table
        is_first_row = not tag.previous_sibling or tag.previous_sibling.name != 'tr'
        
        result = '|' + text + '\n'
        
        # Add separator after header row
        if is_header and is_first_row:
            total_cols = sum(self._get_colspan(cell) for cell in cells)
            result += '| ' + ' | '.join(['---'] * total_cols) + ' |\n'
        
        return result
    
    def _process_tag(self, tag: Tag, convert_as_inline: bool = False) -> str:
        """Process a single tag and its children."""
        tag_name = tag.name.lower()
        
        # Get the converter for this tag
        converter = self.converters.get(tag_name)
        
        # Process children first
        text = ''
        is_heading = tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        is_cell = tag_name in ['td', 'th']
        child_inline = convert_as_inline or is_heading or is_cell
        
        for child in tag.children:
            if isinstance(child, NavigableString):
                text += self._process_text(child, tag)
            elif isinstance(child, Tag):
                text += self._process_tag(child, child_inline)
        
        # Apply converter if available
        if converter:
            return converter(tag, text)
        
        return text
    
    def _process_text(self, text: NavigableString, parent: Tag) -> str:
        """Process text nodes."""
        content = str(text)
        
        # Don't modify whitespace in pre tags
        if not parent or parent.find_parent('pre') is None:
            content = WHITESPACE_RE.sub(' ', content)
        
        # Escape special characters unless in code/pre
        if not parent or parent.find_parent(['pre', 'code', 'kbd', 'samp']) is None:
            content = escape(
                content,
                escape_misc=self.escape_misc,
                escape_asterisks=self.escape_asterisks,
                escape_underscores=self.escape_underscores
            )
        
        return content
    
    def convert(self, html: str) -> str:
        """Convert HTML to markdown."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove comments
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Process all top-level elements
        result = ''
        for element in soup.children:
            if isinstance(element, NavigableString):
                result += self._process_text(element, None)
            elif isinstance(element, Tag):
                result += self._process_tag(element, self.convert_as_inline)
        
        # Clean up excessive newlines
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result.strip()


class EnhancedMarkdownGenerator(MarkdownGenerationStrategy):
    """
    Enhanced markdown generator that uses the improved conversion logic
    while maintaining compatibility with Gnosis Wraith.
    """
    
    def __init__(self, content_filter=None, options=None, content_source="cleaned_html"):
        super().__init__(content_filter, options, verbose=False, content_source=content_source)
        
        # Default options
        self.default_options = {
            'heading_style': ATX,
            'bullets': '*+-',
            'strong_em_symbol': '*',
            'code_language': '',
            'escape_asterisks': True,
            'escape_underscores': True,
            'escape_misc': True,
            'newline_style': SPACES,
            'wrap': False,
            'wrap_width': 80,
            'autolinks': True,
            'default_title': False,
        }
        
        if options:
            self.default_options.update(options)
    
    def convert_links_to_citations(self, markdown: str, base_url="") -> Tuple[str, str]:
        """Convert links in markdown to citations (maintains compatibility)."""
        link_map = {}
        url_cache = {}
        parts = []
        last_end = 0
        counter = 1

        # Updated regex to properly capture markdown links
        link_pattern = re.compile(r'(!?)\[([^\]]+)\]\(([^)]+?)(?:\s+"([^"]*)")?\)')
        
        for match in link_pattern.finditer(markdown):
            parts.append(markdown[last_end:match.start()])
            is_image, text, url, title = match.groups()

            # Handle relative URLs
            if base_url and not url.startswith(("http://", "https://", "mailto:")):
                if url not in url_cache:
                    url_cache[url] = urlparse.urljoin(base_url, url)
                url = url_cache[url]

            if url not in link_map:
                desc = []
                if title:
                    desc.append(title)
                if text and text != title and text != url:
                    desc.append(text)
                link_map[url] = (counter, ": " + " - ".join(desc) if desc else "")
                counter += 1

            num = link_map[url][0]
            if is_image:
                parts.append(f"![{text}⟨{num}⟩]")
            else:
                parts.append(f"{text}⟨{num}⟩")
            
            last_end = match.end()

        parts.append(markdown[last_end:])
        converted_text = "".join(parts)

        # Build references - fixed format
        references = ["\n\n## References\n\n"]
        for url, (num, desc) in sorted(link_map.items(), key=lambda x: x[1][0]):
            references.append(f"⟨{num}⟩ {url}{desc}\n")

        return converted_text, "".join(references)

    
    def generate_markdown(self, input_html, base_url="", html2text_options=None,
                         options=None, content_filter=None, citations=True, **kwargs) -> MarkdownGenerationResult:
        """Generate markdown from HTML using enhanced converter."""
        try:
            # Merge options
            converter_options = self.default_options.copy()
            if html2text_options:
                converter_options.update(html2text_options)
            if options:
                converter_options.update(options)
            if self.options:
                converter_options.update(self.options)
            
            # Create converter
            converter = EnhancedMarkdownConverter(**converter_options)
            
            # Convert to markdown
            raw_markdown = converter.convert(input_html)
            
            # Handle citations
            markdown_with_citations = raw_markdown
            references_markdown = ""
            if citations:
                try:
                    markdown_with_citations, references_markdown = self.convert_links_to_citations(
                        raw_markdown, base_url
                    )
                except Exception as e:
                    # Fallback if citation conversion fails
                    markdown_with_citations = raw_markdown
                    references_markdown = f"Error generating citations: {str(e)}"
            
            # Generate fit markdown if content filter provided
            fit_markdown = ""
            filtered_html = ""
            if content_filter or self.content_filter:
                try:
                    filter_to_use = content_filter or self.content_filter
                    filtered_html = filter_to_use.filter_content(input_html)
                    filtered_html = "\n".join(f"<div>{s}</div>" for s in filtered_html)
                    fit_markdown = converter.convert(filtered_html)
                except Exception as e:
                    fit_markdown = f"Error generating fit markdown: {str(e)}"
            
            return MarkdownGenerationResult(
                raw_markdown=raw_markdown,
                markdown_with_citations=markdown_with_citations,
                references_markdown=references_markdown,
                fit_markdown=fit_markdown,
                fit_html=filtered_html,
            )
        
        except Exception as e:
            # Return error result
            error_msg = f"Error in markdown generation: {str(e)}"
            return MarkdownGenerationResult(
                raw_markdown=error_msg,
                markdown_with_citations=error_msg,
                references_markdown="",
                fit_markdown="",
                fit_html="",
            )


# For backwards compatibility
DefaultMarkdownGenerator = EnhancedMarkdownGenerator
