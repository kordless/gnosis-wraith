# Enhanced Markdown Generation for Gnosis Wraith

## Overview

This enhanced markdown generation module incorporates the best practices and clean architecture from the `html-to-markdown` library while maintaining full compatibility with Gnosis Wraith's existing pipeline.

## Key Improvements

### 1. **Cleaner Architecture**
- Separated conversion logic from processing logic
- Each HTML element has its own dedicated converter function
- Easy to extend with new element types

### 2. **Better Table Support**
- Proper handling of `colspan` attributes
- Automatic header row detection
- Clean markdown table formatting with proper separators

### 3. **Improved Text Processing**
- Smart whitespace normalization (preserves whitespace in `<pre>` tags)
- Better handling of inline elements within block elements
- Proper escaping of special Markdown characters

### 4. **Enhanced List Handling**
- Correct indentation for nested lists
- Support for ordered lists with custom start values
- Configurable bullet characters for different nesting levels

### 5. **Flexible Heading Styles**
- ATX style: `# Heading`
- ATX closed style: `# Heading #`
- Underlined style (Setext): `Heading\n======`

### 6. **Better Code Block Detection**
- Automatically detects language from `class="language-*"` attributes
- Preserves formatting within code blocks
- Configurable default language

## Usage

### Basic Usage

```python
from core.markdown_generation_enhanced import EnhancedMarkdownGenerator

# Create generator with default options
generator = EnhancedMarkdownGenerator()

# Convert HTML to Markdown
result = generator.generate_markdown(html_content)
print(result.raw_markdown)
```

### Custom Options

```python
# Create generator with custom options
generator = EnhancedMarkdownGenerator(options={
    'heading_style': 'atx',        # Use # style headers
    'bullets': '-+*',              # Bullet characters for lists
    'strong_em_symbol': '_',       # Use _ for emphasis
    'code_language': 'python',     # Default language for code blocks
    'escape_asterisks': True,      # Escape * characters
    'wrap': True,                  # Enable text wrapping
    'wrap_width': 80,              # Wrap at 80 characters
})
```

### With Content Filtering

```python
from core.markdown_generation import PruningContentFilter

# Use with existing content filter
content_filter = PruningContentFilter(threshold=0.48)
generator = EnhancedMarkdownGenerator(content_filter=content_filter)

result = generator.generate_markdown(html_content)
print(result.fit_markdown)  # Filtered content
```

## Comparison with Original

| Feature | Original | Enhanced |
|---------|----------|----------|
| Table Support | Basic | Full with colspan |
| Heading Styles | Underlined only | ATX, ATX closed, Underlined |
| Code Language Detection | No | Yes (from class attributes) |
| List Nesting | Limited | Full support |
| Text Processing | Basic | Smart whitespace handling |
| Architecture | Monolithic | Modular converters |

## Integration with Existing Pipeline

The enhanced generator is designed as a drop-in replacement:

```python
# Before
from core.markdown_generation import DefaultMarkdownGenerator

# After (no other changes needed)
from core.markdown_generation_enhanced import EnhancedMarkdownGenerator as DefaultMarkdownGenerator
```

## Future Enhancements

1. **Custom Converters**: Allow users to register custom converters for specific tags
2. **Plugin System**: Support for markdown extensions (footnotes, definition lists, etc.)
3. **Performance Optimization**: Cache compiled regex patterns and reuse converter instances
4. **Better Error Handling**: Graceful degradation for malformed HTML

## Testing

Run the test script to see the improvements:

```bash
python test_markdown_enhanced.py
```

This will show side-by-side comparisons of the original and enhanced generators with various HTML elements.
