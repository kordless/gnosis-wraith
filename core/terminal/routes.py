"""
Terminal Routes for Gnosis Wraith
Implements the shell interface similar to Mitta's /c and /j endpoints
"""

import json
import os
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional

from quart import Blueprint, render_template, render_template_string, request, jsonify, make_response
from werkzeug.exceptions import BadRequest

# Import our terminal parser
from .parser import TerminalParser, TimeParser


terminal_bp = Blueprint('terminal', __name__)


class TerminalContext:
    """Manages terminal session context and state"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or self._generate_session_id()
        self.command_history = []
        self.settings = self._load_default_settings()
        self.timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """Load default terminal settings"""
        return {
            "theme": "dark",
            "prompt": "wraith",
            "ai_model": "claude",
            "auto_complete": True,
            "command_echo": True
        }
    
    def add_to_history(self, command: str):
        """Add command to history"""
        if command and command not in self.command_history[-10:]:  # Avoid recent duplicates
            self.command_history.append(command)
            # Keep only last 100 commands
            if len(self.command_history) > 100:
                self.command_history = self.command_history[-100:]


class CommandManager:
    """Manages available commands and their execution"""
    
    def __init__(self):
        self.commands_dir = os.path.join(os.path.dirname(__file__), 'commands')
        self._built_in_commands = [
            'help', 'crawl', 'search', 'ai', 'history', 'clear', 
            'settings', 'jobs', 'report', 'config', 'upgrade'
        ]
    
    def get_available_commands(self) -> list:
        """Get list of available commands"""
        commands = ["!" + cmd for cmd in self._built_in_commands]
        
        # Add custom commands from files
        try:
            if os.path.exists(self.commands_dir):
                for filename in os.listdir(self.commands_dir):
                    if filename.endswith('.js'):
                        cmd_name = filename[:-3]  # Remove .js extension
                        commands.append("!" + cmd_name)
        except Exception as e:
            print(f"Error loading custom commands: {e}")
        
        return sorted(commands)
    
    def command_exists(self, command: str) -> bool:
        """Check if a command exists"""
        clean_command = command.lstrip('!')
        
        # Check built-in commands
        if clean_command in self._built_in_commands:
            return True
        
        # Check file-based commands
        command_file = os.path.join(self.commands_dir, f"{clean_command}.js")
        return os.path.exists(command_file)
    
    def get_command_template(self, command: str) -> Optional[str]:
        """Get command template content"""
        clean_command = command.lstrip('!')
        command_file = os.path.join(self.commands_dir, f"{clean_command}.js")
        
        try:
            if os.path.exists(command_file):
                with open(command_file, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"Error loading command template {command}: {e}")
        
        return None


# Global instances
command_manager = CommandManager()


@terminal_bp.route('/c')
def console():
    """Main terminal interface (Mitta compatibility route)"""
    return render_template('terminal/console.html')


@terminal_bp.route('/j', methods=['POST'])
def execute_command():
    """
    Execute terminal commands (equivalent to Mitta's /j endpoint)
    Processes command input and returns JavaScript for execution
    """
    try:
        # Get request data
        data = request.get_json() or {}
        line = data.get('line', '').strip()
        target_id = data.get('target_id', 'terminal_output')
        session_id = data.get('session_id', 'default')
        
        if not line:
            return "terminal.output('No command provided', 'error');", 200, {'Content-Type': 'application/javascript'}
        
        # Parse the command
        parser = TerminalParser(line)
        parsing_info = parser.get_parsing_info()
        
        # Create execution context
        context = _build_execution_context(parser, target_id, session_id)
        
        # Determine command to execute
        command = parser.get_command()
        
        # Check if command exists
        if not command_manager.command_exists(command):
            return _render_command_response('notfound', context, {
                'error_message': f"Command '{command}' not found. Try !help for available commands."
            })
        
        # Load and render command template
        return _execute_command(command, context, parser)
    
    except Exception as e:
        error_js = f"terminal.output('Command execution failed: {str(e)}', 'error');"
        return error_js, 500, {'Content-Type': 'application/javascript'}


@terminal_bp.route('/history')
def get_command_history():
    """Get command history for the terminal"""
    try:
        session_id = request.args.get('session_id', 'default')
        # In a real implementation, this would retrieve from storage
        # For now, return empty history
        return jsonify({"history": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@terminal_bp.route('/commands')
def list_commands():
    """List available commands"""
    try:
        commands = command_manager.get_available_commands()
        return jsonify({"commands": commands})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _build_execution_context(parser: TerminalParser, target_id: str, session_id: str) -> Dict[str, Any]:
    """Build context for command execution"""
    return {
        # Basic info
        'app_id': _generate_app_id(),
        'target_id': target_id,
        'session_id': session_id,
        'timestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        
        # Parsed command info
        'line': parser.get_line(),
        'command': parser.get_command(),
        'text': parser.get_text(),
        'clean_text': parser.get_text(include_url=False, include_fields=False),
        'url': parser.find_urls(encoded=False) or '',
        'url_encoded': parser.find_urls(encoded=True) or '',
        
        # Power marks
        'entity': parser.get_entity(),
        'tags': parser.get_tags(),
        'timeword': parser.get_timeword(),
        'view': parser.get_view(),
        'document_id': parser.get_document_id(),
        'fields': parser.get_fields_dict(),
        
        # Terminal info
        'commands': command_manager.get_available_commands(),
        'is_question': parser.is_question(),
        
        # Settings (would come from user session in real implementation)
        'user_id': 'anonymous',
        'username': 'user',
        'theme': 'dark',
        'prompt': 'wraith'
    }


def _execute_command(command: str, context: Dict[str, Any], parser: TerminalParser) -> Any:
    """Execute a specific command with context"""
    try:
        # Get command template
        template_content = command_manager.get_command_template(command)
        
        if template_content:
            # Render template with context
            response = make_response(render_template_string(template_content, **context))
            response.headers['Content-Type'] = 'application/javascript'
            return response
        else:
            # Use built-in command logic
            return _execute_builtin_command(command, context, parser)
    
    except Exception as e:
        return _render_command_response('error', context, {
            'error_message': f"Command execution error: {str(e)}"
        })


def _execute_builtin_command(command: str, context: Dict[str, Any], parser: TerminalParser) -> Any:
    """Execute built-in commands that don't have templates"""
    
    if command == 'help':
        return _render_command_response('help', context)
    
    elif command == 'history':
        return _render_command_response('history', context)
    
    elif command == 'clear':
        js_code = "terminal.clear();"
        return make_response(js_code, 200, {'Content-Type': 'application/javascript'})
    
    elif command == 'crawl':
        url = parser.find_urls(encoded=False)
        if url:
            return _render_command_response('crawl', context, {'crawl_url': url})
        else:
            return _render_command_response('error', context, {
                'error_message': 'No URL provided for crawl command. Usage: !crawl https://example.com'
            })
    
    elif command == 'upgrade':
        return _render_command_response('upgrade', context)
    
    else:
        return _render_command_response('notfound', context)


def _render_command_response(template_name: str, context: Dict[str, Any], extra_context: Dict[str, Any] = None) -> Any:
    """Render a command response using built-in templates"""
    
    if extra_context:
        context.update(extra_context)
    
    # Built-in templates as strings (in a real implementation, these might be files)
    templates = {
        'help': '''
terminal.output('🚀 Gnosis Wraith Terminal Help', 'system');
terminal.output('==================================', 'system');
terminal.output('');
terminal.output('🌐 Web Crawling:', 'info');
terminal.output('  !crawl https://example.com - Crawl and analyze a webpage');
terminal.output('  !search python tutorials - Search crawled content');
terminal.output('');
terminal.output('🤖 AI Commands:', 'info');
terminal.output('  !ai analyze this text - AI-powered analysis');
terminal.output('  what is machine learning? - Ask questions naturally');
terminal.output('');
terminal.output('⚙️ System:', 'info');
terminal.output('  !history - Show command history');
terminal.output('  !clear - Clear terminal');
terminal.output('  !settings - Terminal settings');
terminal.output('');
terminal.output('💡 Power Marks:', 'info');
terminal.output('  + time constraints (+today, +lastweek)');
terminal.output('  # tags (#important)');
terminal.output('  | output format (|json)');
terminal.output('  ^ sorting (^date_desc)');
terminal.output('');
terminal.output('🔥 Want More? Upgrade to Premium GUI!', 'success');
terminal.output('  • Visual drag & drop interface', 'success');
terminal.output('  • Rich HTML reports with images', 'success');
terminal.output('  • Batch processing multiple URLs', 'success');
terminal.output('  • Real-time crawl monitoring', 'success');
terminal.output('  • Export to multiple formats', 'success');
terminal.output('');
terminal.output('Visit /wraith for the full GUI experience!', 'info');
        ''',
        
        'history': '''
terminal.output('📜 Command history feature coming soon...', 'info');
        ''',
        
        'crawl': '''
var url = "{{ crawl_url or '' }}";
if (url) {
    terminal.output('🕷️  Crawling: ' + url, 'info');
    terminal.output('⏳ Processing... (this would integrate with Wraith\\'s crawler)', 'system');
} else {
    terminal.output('❌ No URL provided for crawl command', 'error');
}
        ''',
        
        'error': '''
terminal.output('❌ Error: {{ error_message or "Unknown error occurred" }}', 'error');
        ''',
        
        'upgrade': '''
terminal.output('🔥 UPGRADE TO PREMIUM GUI', 'success');
terminal.output('═══════════════════════════', 'success');
terminal.output('');
terminal.output('You\\'re currently using the FREE terminal interface.', 'info');
terminal.output('Upgrade to unlock the full visual experience!', 'info');
terminal.output('');
terminal.output('✨ PREMIUM FEATURES:', 'success');
terminal.output('  🎯 Visual Drag & Drop Interface', 'info');
terminal.output('  📊 Rich HTML Reports with Screenshots', 'info');
terminal.output('  ⚡ Batch Process Multiple URLs', 'info');
terminal.output('  📱 Real-time Crawl Monitoring', 'info');
terminal.output('  💾 Export to Multiple Formats', 'info');
terminal.output('  🤖 Advanced AI Analysis', 'info');
terminal.output('  ☁️  Cloud Storage Integration', 'info');
terminal.output('  📈 Analytics & Insights Dashboard', 'info');
terminal.output('');
terminal.output('🚀 READY TO UPGRADE?', 'success');
terminal.output('Visit: http://localhost:5678/wraith', 'success');
terminal.output('');
terminal.output('Or continue using the terminal - it\\'s still powerful!', 'info');
        ''',
        
        'notfound': '''
terminal.output('❓ Command not found: {{ command }}', 'error');
terminal.output('💡 Try !help for available commands', 'info');
        '''
    }
    
    template_content = templates.get(template_name, templates['error'])
    
    try:
        response = make_response(render_template_string(template_content, **context))
        response.headers['Content-Type'] = 'application/javascript'
        return response
    except Exception as e:
        # Fallback error response
        error_js = f'terminal.output("❌ Template error: {str(e)}", "error");'
        return make_response(error_js, 200, {'Content-Type': 'application/javascript'})


def _generate_app_id() -> str:
    """Generate unique app ID for command execution"""
    import uuid
    return str(uuid.uuid4())[:8]


# Error handlers
@terminal_bp.errorhandler(404)
def terminal_not_found(error):
    return jsonify({"error": "Terminal endpoint not found"}), 404


@terminal_bp.errorhandler(500)
def terminal_error(error):
    return jsonify({"error": "Terminal internal error"}), 500
