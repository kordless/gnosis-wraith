# VS Code Markdown Extensions

## Recommended Extensions for Better Markdown Experience

### 1. Markdown All in One
- **ID**: yzhang.markdown-all-in-one
- **Features**: 
  - Table of contents
  - Auto preview
  - List editing
  - Math support
  - Export to HTML/PDF

### 2. Markdown Preview Enhanced
- **ID**: shd101wyy.markdown-preview-enhanced
- **Features**:
  - Live preview with scroll sync
  - Math typesetting
  - Mermaid diagrams
  - Export to multiple formats
  - Custom CSS themes

### 3. Markdownlint
- **ID**: DavidAnson.vscode-markdownlint
- **Features**:
  - Linting and style checking
  - Auto-fix common issues
  - Customizable rules

## Quick Install Commands

```bash
# Install all three
code --install-extension yzhang.markdown-all-in-one
code --install-extension shd101wyy.markdown-preview-enhanced
code --install-extension DavidAnson.vscode-markdownlint
```

## VS Code Settings for Better Markdown

Add to your settings.json:

```json
{
    // Auto-open preview to side
    "markdown.preview.openMarkdownLinks": "inPreview",
    
    // Preview settings
    "markdown.preview.fontSize": 14,
    "markdown.preview.lineHeight": 1.6,
    
    // Editor settings for markdown
    "[markdown]": {
        "editor.wordWrap": "on",
        "editor.quickSuggestions": false,
        "editor.lineNumbers": "off"
    }
}
```
