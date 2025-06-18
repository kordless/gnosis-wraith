"""
Content Cleaning Tests
"""

import pytest
import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.test_base import BaseAPITest


class TestCleanEndpoint(BaseAPITest):
    """Test /v2/clean endpoint for content cleaning"""
    
    def test_basic_cleaning(self):
        """Test basic markdown cleaning"""
        
        llm_config = self.get_llm_config("anthropic")
        
        messy_content = """
        # Welcome!!!!! 🎉🎉🎉🎉🎉
        
        
        
        This is    a poorly formatted     document...
        
        
        ## Click here!! ➡️➡️ [LINK](http://example.com) ⬅️⬅️
        
        * item one
        + item two  
        - item three
            * nested item
        
        Visit our website at http://example.com or https://example.com!!!
        
        EMAIL US: test@example.com!!!!!
        """
        
        response = self.make_request("POST", "/clean", json={
            "content": messy_content,
            **llm_config,
            "options": {
                "remove_emojis": True,
                "fix_formatting": True,
                "standardize_links": True,
                "remove_excessive_punctuation": True
            }
        })
        
        data = self.assert_success_response(response)
        
        # Should have cleaned content
        assert "cleaned_content" in data
        cleaned = data["cleaned_content"]
        
        # Check improvements
        assert "!!!!!" not in cleaned  # Excessive punctuation removed
        assert "🎉" not in cleaned  # Emojis removed
        assert "   " not in cleaned  # Multiple spaces fixed
        
        # Should still have structure
        assert "# Welcome" in cleaned or "# welcome" in cleaned.lower()
        assert "item one" in cleaned
        assert "item two" in cleaned
        
        # Check statistics
        if "statistics" in data:
            stats = data["statistics"]
            assert stats["cleaned_length"] < stats["original_length"]
    
    def test_whitespace_normalization(self):
        """Test whitespace and formatting fixes"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        Title


        First paragraph with     too many spaces.
        
        
        
        
        Second paragraph.
        	Tab characters here.
        
        Line with trailing spaces    
        """
        
        response = self.make_request("POST", "/clean", json={
            "content": content,
            **llm_config,
            "options": {
                "normalize_whitespace": True,
                "fix_line_breaks": True
            }
        })
        
        data = self.assert_success_response(response)
        cleaned = data["cleaned_content"]
        
        # Should normalize whitespace
        assert "     " not in cleaned  # Multiple spaces
        assert "\t" not in cleaned  # Tabs removed/converted
        assert not cleaned.endswith(" ")  # No trailing spaces
        
        # Should have reasonable paragraph spacing
        lines = cleaned.split('\n')
        consecutive_empty = 0
        max_consecutive = 0
        for line in lines:
            if line.strip() == "":
                consecutive_empty += 1
                max_consecutive = max(max_consecutive, consecutive_empty)
            else:
                consecutive_empty = 0
        
        assert max_consecutive <= 1  # No more than 1 empty line between paragraphs
    
    def test_link_standardization(self):
        """Test link formatting and standardization"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        Check out these links:
        - Raw URL: https://example.com/page
        - Another: www.example.com
        - Email: contact@example.com
        - Already formatted: [Example](https://example.com)
        - Broken markdown: [Broken link(https://example.com)
        
        Visit https://example.com/very/long/url/that/should/be/converted/to/markdown for more info.
        """
        
        response = self.make_request("POST", "/clean", json={
            "content": content,
            **llm_config,
            "options": {
                "standardize_links": True,
                "convert_to_markdown_links": True
            }
        })
        
        data = self.assert_success_response(response)
        cleaned = data["cleaned_content"]
        
        # Raw URLs should be converted to markdown links
        assert "[" in cleaned and "](" in cleaned
        
        # Email might be converted or left as-is
        assert "contact@example.com" in cleaned
        
        # Already formatted links should remain
        assert "[Example](https://example.com)" in cleaned
    
    def test_list_standardization(self):
        """Test list formatting standardization"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        Mixed list styles:
        
        * First item
        + Second item
        - Third item
        * Fourth item
        
        Numbered list:
        1. First
        2) Second
        3. Third
        
        Nested lists:
        - Parent 1
          * Child 1
          + Child 2
        - Parent 2
            - Deep child
        """
        
        response = self.make_request("POST", "/clean", json={
            "content": content,
            **llm_config,
            "options": {
                "standardize_lists": True
            }
        })
        
        data = self.assert_success_response(response)
        cleaned = data["cleaned_content"]
        
        # Should standardize bullet points
        lines = cleaned.split('\n')
        list_items = [l for l in lines if l.strip() and l.strip()[0] in '*+-']
        
        if list_items:
            # Check if standardized to one marker
            markers = {l.strip()[0] for l in list_items}
            assert len(markers) == 1  # All use same marker
    
    def test_heading_hierarchy(self):
        """Test heading hierarchy fixing"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        ### Deep heading without parent
        
        Some content
        
        # Main Title
        
        #### Skipped a level
        
        ## Correct Level
        
        ### Correct Sub-level
        
        ##### Too deep
        """
        
        response = self.make_request("POST", "/clean", json={
            "content": content,
            **llm_config,
            "options": {
                "fix_heading_hierarchy": True
            }
        })
        
        data = self.assert_success_response(response)
        cleaned = data["cleaned_content"]
        
        # Should have proper hierarchy
        lines = cleaned.split('\n')
        heading_lines = [l for l in lines if l.strip().startswith('#')]
        
        # First heading should be h1 or h2
        if heading_lines:
            first_heading = heading_lines[0].strip()
            assert first_heading.startswith('# ') or first_heading.startswith('## ')
    
    def test_code_block_formatting(self):
        """Test code block formatting"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        Here's some code:
        
        ```
        def hello():
            print("Hello")
        ```
        
        Inline code: `variable` and more `code here`.
        
        Bad code block:
        '''python
        # Wrong quotes
        x = 1
        '''
        
        Indented code:
            function test() {
                return true;
            }
        """
        
        response = self.make_request("POST", "/clean", json={
            "content": content,
            **llm_config,
            "options": {
                "format_code_blocks": True,
                "preserve_code": True
            }
        })
        
        data = self.assert_success_response(response)
        cleaned = data["cleaned_content"]
        
        # Should preserve code blocks
        assert "```" in cleaned
        assert "def hello():" in cleaned
        assert "`variable`" in cleaned
        
        # Should fix wrong quotes if possible
        assert "'''" not in cleaned or "```" in cleaned
    
    def test_preserve_meaning(self):
        """Test that cleaning preserves content meaning"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        IMPORTANT: This is a critical message!!!
        
        The price is $99.99 (was $149.99).
        
        Features:
        - Feature 1
        - Feature 2
        - Feature 3
        
        Contact: support@example.com or call 1-800-EXAMPLE
        """
        
        response = self.make_request("POST", "/clean", json={
            "content": content,
            **llm_config,
            "options": {
                "preserve_meaning": True,
                "remove_excessive_punctuation": True
            }
        })
        
        data = self.assert_success_response(response)
        cleaned = data["cleaned_content"]
        
        # Should preserve important information
        assert "IMPORTANT" in cleaned or "important" in cleaned.lower()
        assert "$99.99" in cleaned
        assert "$149.99" in cleaned
        assert "Feature 1" in cleaned
        assert "support@example.com" in cleaned
        assert "1-800-EXAMPLE" in cleaned
    
    def test_selective_emoji_removal(self):
        """Test selective emoji handling"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        Welcome! 👋
        
        Check these out:
        ✅ Completed task
        ❌ Failed task
        ⚠️ Warning message
        
        Fun stuff 🎉🎊🎈🎆
        
        Technical: → ← ↑ ↓ • · × ÷
        """
        
        response = self.make_request("POST", "/clean", json={
            "content": content,
            **llm_config,
            "options": {
                "remove_emojis": True,
                "preserve_meaning": True
            }
        })
        
        data = self.assert_success_response(response)
        cleaned = data["cleaned_content"]
        
        # Fun emojis should be removed
        assert "🎉" not in cleaned
        assert "🎊" not in cleaned
        
        # Meaningful symbols might be preserved or replaced
        # Check that the meaning is preserved somehow
        assert "completed" in cleaned.lower() or "✅" in cleaned
        assert "failed" in cleaned.lower() or "❌" in cleaned
        
        # Technical symbols usually preserved
        assert any(symbol in cleaned for symbol in ["→", "•", "×", "-", "*"])
    
    def test_changes_tracking(self):
        """Test tracking of changes made"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        # TITLE!!!!!
        
        
        
        Text with    spaces and 🎉 emojis.
        
        http://example.com
        """
        
        response = self.make_request("POST", "/clean", json={
            "content": content,
            **llm_config,
            "options": {
                "remove_emojis": True,
                "fix_formatting": True,
                "remove_excessive_punctuation": True,
                "standardize_links": True
            }
        })
        
        data = self.assert_success_response(response)
        
        # Should report changes made
        if "changes_made" in data:
            changes = data["changes_made"]
            assert isinstance(changes, list)
            assert len(changes) > 0
            
            # Should mention specific changes
            changes_str = " ".join(changes).lower()
            assert any(term in changes_str for term in ["emoji", "punctuation", "space", "whitespace", "link"])


class TestCleanErrorHandling(BaseAPITest):
    """Test error handling for clean endpoint"""
    
    def test_missing_content(self):
        """Test cleaning without content"""
        
        llm_config = self.get_llm_config("anthropic")
        
        response = self.make_request("POST", "/clean", json={
            **llm_config,
            "options": {
                "fix_formatting": True
            }
        })
        
        assert response.status_code == 400
    
    def test_empty_content(self):
        """Test cleaning empty content"""
        
        llm_config = self.get_llm_config("openai")
        
        response = self.make_request("POST", "/clean", json={
            "content": "",
            **llm_config
        })
        
        assert response.status_code == 400
    
    def test_non_text_content(self):
        """Test cleaning non-text content"""
        
        llm_config = self.get_llm_config("anthropic")
        
        # Binary-like content
        response = self.make_request("POST", "/clean", json={
            "content": "\x00\x01\x02\x03\x04",
            **llm_config
        })
        
        # Should handle gracefully
        assert response.status_code in [200, 400]
    
    def test_malformed_markdown(self):
        """Test cleaning severely malformed markdown"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        [Unclosed link(http://example.com
        ![Broken image(image.jpg)
        ```
        Unclosed code block
        
        **Unclosed bold
        *Unclosed italic
        
        >>> Weird quotation
        |||||| Too many pipes
        """
        
        response = self.make_request("POST", "/clean", json={
            "content": content,
            **llm_config,
            "options": {
                "fix_formatting": True
            }
        })
        
        # Should handle gracefully
        if response.status_code == 200:
            data = response.json()
            cleaned = data["cleaned_content"]
            # Should attempt to fix or remove malformed elements
            assert "[Unclosed link(http://example.com" not in cleaned


class TestCleanEdgeCases(BaseAPITest):
    """Test edge cases for clean endpoint"""
    
    def test_mixed_languages(self):
        """Test cleaning content with mixed languages"""
        
        llm_config = self.get_llm_config("anthropic")
        
        content = """
        # Welcome 欢迎 ようこそ
        
        This is English text.
        这是中文文本。
        これは日本語のテキストです。
        
        Mixed: Hello 你好 こんにちは!!!
        """
        
        response = self.make_request("POST", "/clean", json={
            "content": content,
            **llm_config,
            "options": {
                "remove_excessive_punctuation": True,
                "preserve_meaning": True
            }
        })
        
        data = self.assert_success_response(response)
        cleaned = data["cleaned_content"]
        
        # Should preserve all languages
        assert "Welcome" in cleaned
        assert "欢迎" in cleaned
        assert "ようこそ" in cleaned
        assert "English" in cleaned
        assert "中文" in cleaned
        assert "日本語" in cleaned
    
    def test_special_markdown_elements(self):
        """Test cleaning special markdown elements"""
        
        llm_config = self.get_llm_config("openai")
        
        content = """
        | Header 1 | Header 2 |
        |----------|----------|
        | Cell 1   | Cell 2   |
        
        ---
        
        > Blockquote with **bold** and *italic*
        
        - [ ] Todo item 1
        - [x] Todo item 2 (completed)
        
        ~~Strikethrough text~~
        
        Footnote reference[^1]
        
        [^1]: Footnote text
        """
        
        response = self.make_request("POST", "/clean", json={
            "content": content,
            **llm_config,
            "options": {
                "preserve_meaning": True,
                "fix_formatting": True
            }
        })
        
        data = self.assert_success_response(response)
        cleaned = data["cleaned_content"]
        
        # Should preserve special elements
        assert "|" in cleaned  # Table
        assert ">" in cleaned  # Blockquote
        assert "- [ ]" in cleaned or "- []" in cleaned  # Todo
        assert "[^" in cleaned or "footnote" in cleaned.lower()  # Footnote


if __name__ == "__main__":
    pytest.main([__file__, "-v"])