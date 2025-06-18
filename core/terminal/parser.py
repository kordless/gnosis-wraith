"""
Terminal Command Parser for Gnosis Wraith
Ported from Mitta's Builder class with enhancements
"""

import re
import urllib.parse
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta


class PowerMarks:
    """Power mark constants for command parsing"""
    TIME = "+"      # time nouns (+lastweek, +today)
    COMMAND = "!"   # commands (!crawl, !search)
    VIEW = "|"      # views to render results (|json, |table)
    OFFSET = "_"    # pagination (_start=42, _rows=21)
    ORDER = "^"     # sorting (^field_desc, ^field_asc)
    TAG = "#"       # filter results with tags (#important)
    SETTING = "$"   # setting or variable name ($theme)
    VALUE = "="     # setting or variable value (=dark)
    ENTITY = "@"    # named entities (@user, @bot)
    DOCUMENT = "~"  # document IDs (~abc123)
    EVAL = ";"      # javascript eval (;2+2)

    ALL = [TIME, COMMAND, VIEW, OFFSET, ORDER, TAG, SETTING, VALUE, ENTITY, DOCUMENT, EVAL]


def split_powermarks(line: str) -> List[str]:
    """Split line into powermarks (words starting with power mark symbols)"""
    line_split = urllib.parse.unquote(line).split(" ")
    powermarks = []
    
    for word in line_split:
        if word and word[0] in PowerMarks.ALL:
            powermarks.append(word)
    
    return powermarks


class TerminalParser:
    """
    Command parser for terminal interface
    Handles power marks and command parsing similar to Mitta's Builder class
    """
    
    def __init__(self, line: str):
        self.line = line.strip()
        self.powermarks = split_powermarks(self.line)
    
    def get_line(self) -> str:
        """Get sanitized line"""
        return self.line.replace("\n", "").replace('"', '\\"').replace("'", "\\'").replace("&amp;", "&")
    
    def is_question(self) -> bool:
        """Check if the line is a question"""
        return self.line.rstrip().endswith('?')
    
    def get_commands(self, default: Optional[List[str]] = None) -> List[str]:
        """Get all !commands from line"""
        commands = [mark for mark in self.powermarks if mark.startswith(PowerMarks.COMMAND)]
        return commands if commands else (default or [])
    
    def get_command(self, default: str = "chat", include_bang: bool = False) -> str:
        """Get the first command from line"""
        try:
            commands = self.get_commands()
            if not commands:
                return default
            
            command = commands[0]
            return command if include_bang else command[1:]
        except Exception:
            return default
    
    def get_entity(self, default: str = "") -> str:
        """Get @entity reference"""
        entities = [mark for mark in self.powermarks if mark.startswith(PowerMarks.ENTITY)]
        return entities[0][1:].strip() if entities else default
    
    def get_document_id(self, default: str = "", include_tilde: bool = False) -> str:
        """Get ~document_id reference"""
        try:
            doc_ids = [mark for mark in self.powermarks if mark.startswith(PowerMarks.DOCUMENT)]
            if not doc_ids:
                return default
            
            doc_id = doc_ids[0]
            return doc_id if include_tilde else doc_id[1:]
        except Exception:
            return default
    
    def get_setting(self, default: str = "$none") -> str:
        """Get $setting name"""
        settings = [mark for mark in self.powermarks if mark.startswith(PowerMarks.SETTING)]
        return settings[0] if settings else default
    
    def get_value(self, default: str = "=null") -> str:
        """Get =value"""
        values = [mark for mark in self.powermarks if mark.startswith(PowerMarks.VALUE)]
        return values[0] if values else default
    
    def get_timeword(self, default: str = "+alltime") -> str:
        """Get +timeword from line"""
        timewords = [mark for mark in self.powermarks if mark.startswith(PowerMarks.TIME)]
        return timewords[0] if timewords else default
    
    def get_view(self, default: str = "") -> str:
        """Get |view from line"""
        views = [mark for mark in self.powermarks if mark.startswith(PowerMarks.VIEW)]
        return views[0] if views else default
    
    def get_tags(self) -> List[str]:
        """Get all #tags from line"""
        return [mark for mark in self.powermarks if mark.startswith(PowerMarks.TAG)]
    
    def get_orders(self) -> List[str]:
        """Get ^ordering directives"""
        return [mark for mark in self.powermarks if mark.startswith(PowerMarks.ORDER)]
    
    def get_offsets(self) -> List[str]:
        """Get _offset directives (_start=10, _rows=20)"""
        return [mark for mark in self.powermarks if mark.startswith(PowerMarks.OFFSET)]
    
    def find_urls(self, encoded: bool = True) -> Optional[str]:
        """Find URLs in the line"""
        # Simple URL regex - could be enhanced
        url_pattern = r'https?://[^\s<>"]+'
        urls = re.findall(url_pattern, self.line)
        
        if not urls:
            return None
        
        url = urls[0]  # Return first URL found
        return urllib.parse.quote(url, safe=':/?#[]@!$&\'()*+,;=') if encoded else url
    
    def strip_command(self) -> str:
        """Remove the command from the line, leaving the rest"""
        command = self.get_command(include_bang=True)
        if not command:
            return self.line
        
        # Split on command and space
        parts = self.line.split(command + " ", 1)
        
        if len(parts) == 2:
            return parts[1]  # Return text after command
        elif len(parts) == 1 and not parts[0]:
            return ""  # Line was just the command
        else:
            return parts[0]  # Text before command
    
    def get_text(self, include_url: bool = True, include_fields: bool = True) -> str:
        """
        Get clean text from line, optionally excluding URLs and fields
        Strips commands and power marks, leaving readable text
        """
        text = self.line
        
        # Remove powermarks
        for mark in self.powermarks:
            text = text.replace(mark, "").strip()
        
        # Handle URL exclusion
        if not include_url:
            url = self.find_urls(encoded=False)
            if url:
                text = text.replace(url, "").strip()
        
        # Handle field exclusion (field:value pairs)
        if not include_fields:
            # Remove field:value patterns
            field_pattern = r'\w+:\S+'
            text = re.sub(field_pattern, '', text).strip()
        
        return " ".join(text.split())  # Normalize whitespace
    
    def get_fields_dict(self) -> Dict[str, str]:
        """
        Extract field:value pairs from the line
        Returns dictionary of field names to values
        """
        # Regex to match field:value patterns
        field_pattern = r'(\w+):([^\s]+|"[^"]*")'
        matches = re.findall(field_pattern, self.line)
        
        fields = {}
        for field, value in matches:
            # Remove quotes from values
            clean_value = value.strip('"').strip("'")
            fields[field] = clean_value
        
        return fields
    
    def get_parsing_info(self) -> Dict:
        """Get comprehensive parsing information for debugging"""
        return {
            "original_line": self.line,
            "powermarks": self.powermarks,
            "command": self.get_command(),
            "text": self.get_text(),
            "entity": self.get_entity(),
            "tags": self.get_tags(),
            "timeword": self.get_timeword(),
            "view": self.get_view(),
            "url": self.find_urls(encoded=False),
            "fields": self.get_fields_dict(),
            "is_question": self.is_question()
        }


class TimeParser:
    """Handle time-related parsing for +timewords"""
    
    TIME_MAPPINGS = {
        "+today": (0, 1),
        "+yesterday": (-1, 0),
        "+lastweek": (-7, 0),
        "+lastmonth": (-30, 0),
        "+lastyear": (-365, 0),
        "+alltime": (-3650, 0)  # 10 years back
    }
    
    @classmethod
    def parse_timeword(cls, timeword: str) -> tuple:
        """
        Parse timeword into start and end dates
        Returns tuple of (start_date, end_date) as ISO strings
        """
        if timeword in cls.TIME_MAPPINGS:
            days_back, days_forward = cls.TIME_MAPPINGS[timeword]
            
            now = datetime.now()
            start_date = now + timedelta(days=days_back)
            end_date = now + timedelta(days=days_forward)
            
            return (
                start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        
        # Default to all time
        return cls.parse_timeword("+alltime")


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_commands = [
        "!crawl https://example.com +today #important",
        "!search python tutorials author:john +lastweek",
        "!help",
        "@bot what is the weather like?",
        "!report ~doc123 |json ^date_desc _start=10",
        "analyze this data with AI"
    ]
    
    for cmd in test_commands:
        parser = TerminalParser(cmd)
        info = parser.get_parsing_info()
        print(f"\nCommand: {cmd}")
        print(f"Parsed: {info}")
