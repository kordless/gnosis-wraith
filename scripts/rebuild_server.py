#!/usr/bin/env python3
"""
Gnosis Wraith Rebuild Server
A simple HTTP server that triggers Docker rebuild on request
Listens on port 5679 by default
"""

import http.server
import socketserver
import json
import subprocess
import os
import time
import threading
import sys
from datetime import datetime
from pathlib import Path

# VSCode integration temporarily disabled
# VSCode extension will handle navigation now, no external dependencies needed

# Configuration
PORT = 5679
REBUILD_SCRIPT = "./rebuild.ps1"  # PowerShell rebuild script path
LOG_FILE = "rebuild_server.log"
GNOSIS_PATH = Path(os.getenv("GNOSIS_PATH", "C:/Users/kord/Code/gnosis/gnosis-wraith"))

# Global state
last_rebuild_output = ""
last_rebuild_time = None
last_rebuild_success = False
rebuild_in_progress = False
rebuild_lock = threading.Lock()

# VSCode navigation state - COMMENTED OUT FOR NOW
# vscode_target_line = None
# vscode_target_file = None
# vscode_lock = threading.Lock()

class RebuildRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override to add timestamps to log messages"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(f"[{timestamp}] {self.address_string()} - {format % args}\n")
        
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/":
            # Return HTML status page
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            status_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Gnosis Wraith Rebuild Server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
            background-color: #1e2129;
            color: #e2e2e2;
            padding: 20px;
            line-height: 1.6;
        }}
        h1, h2 {{
            color: #4e9eff;
            border-bottom: 1px solid #3a3f4b;
            padding-bottom: 10px;
        }}
        .status {{
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
        .success {{
            background-color: rgba(66, 211, 146, 0.15);
            border-left: 4px solid #42d392;
        }}
        .error {{
            background-color: rgba(255, 97, 97, 0.15);
            border-left: 4px solid #ff6161;
        }}
        .in-progress {{
            background-color: rgba(255, 192, 98, 0.15);
            border-left: 4px solid #ffc062;
        }}
        .idle {{
            background-color: rgba(78, 158, 255, 0.15);
            border-left: 4px solid #4e9eff;
        }}
        pre {{
            background-color: #282c34;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
            border: 1px solid #3a3f4b;
            white-space: pre-wrap;
        }}
        button {{
            background-color: #4e9eff;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-family: inherit;
            margin-bottom: 20px;
        }}
        button:hover {{
            background-color: #3b87e0;
        }}
        .footer {{
            margin-top: 30px;
            font-size: 0.9em;
            color: #a0a0a0;
            border-top: 1px solid #3a3f4b;
            padding-top: 10px;
        }}
    </style>
    <script>
        function triggerRebuild() {{
            fetch('/rebuild', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{ action: 'rebuild' }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    alert('Rebuild triggered! The page will refresh in 3 seconds.');
                    setTimeout(() => window.location.reload(), 3000);
                }} else {{
                    alert('Error: ' + data.message);
                }}
            }})
            .catch(error => {{
                alert('Error: ' + error);
            }});
        }}
        
        // Auto-refresh every 5 seconds if a rebuild is in progress
        {f'setTimeout(() => window.location.reload(), 5000);' if rebuild_in_progress else ''}
    </script>
</head>
<body>
    <h1>Gnosis Wraith Rebuild Server</h1>
    
    <div class="status {'success' if last_rebuild_success and not rebuild_in_progress else 'error' if not last_rebuild_success and not rebuild_in_progress else 'in-progress' if rebuild_in_progress else 'idle'}">
        <h3>Status: {'Rebuild In Progress' if rebuild_in_progress else 'Last Rebuild Successful' if last_rebuild_success else 'Last Rebuild Failed' if last_rebuild_time else 'Idle - No Rebuilds Yet'}</h3>
        {f'<p>Last rebuild: {last_rebuild_time.strftime("%Y-%m-%d %H:%M:%S")}</p>' if last_rebuild_time else ''}
    </div>
    
    <button onclick="triggerRebuild()" {'disabled' if rebuild_in_progress else ''}>
        {'Rebuild in progress...' if rebuild_in_progress else 'Trigger Rebuild'}
    </button>
    
    <h2>Output Log</h2>
    <pre>{last_rebuild_output or "No rebuild has been performed yet."}</pre>
    
    <div class="footer">
        <p>Gnosis Wraith Rebuild Server | Listening on port {PORT} | Working Directory: {GNOSIS_PATH}</p>
    </div>
</body>
</html>
"""
            self.wfile.write(status_html.encode())
            
        elif self.path == "/status":
            # Return JSON status
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            status = {
                "rebuild_in_progress": rebuild_in_progress,
                "last_rebuild_success": last_rebuild_success,
                "last_rebuild_time": last_rebuild_time.strftime("%Y-%m-%d %H:%M:%S") if last_rebuild_time else None,
                "last_rebuild_output_excerpt": last_rebuild_output[:500] + "..." if len(last_rebuild_output) > 500 else last_rebuild_output
            }
            self.wfile.write(json.dumps(status).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
    
    def do_POST(self):
        """Handle POST requests"""
        global last_rebuild_output, last_rebuild_time, last_rebuild_success, rebuild_in_progress
        # global vscode_target_file, vscode_target_line  # COMMENTED OUT FOR NOW
        
        if self.path == "/rebuild":
            # Parse the request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                # Check if rebuild is already in progress
                if rebuild_in_progress:
                    self.send_response(429)  # Too Many Requests
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": False,
                        "message": "A rebuild is already in progress"
                    }).encode())
                    return
                
                # Acquire lock to prevent concurrent rebuilds
                rebuild_lock.acquire()
                rebuild_in_progress = True
                
                # Start rebuild in a separate thread
                rebuild_thread = threading.Thread(target=self.run_rebuild)
                rebuild_thread.start()
                
                # Send response immediately
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": "Rebuild triggered"
                }).encode())
                
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Invalid JSON in request body"
                }).encode())
                
        # COMMENTED OUT FOR NOW - Handle requests from search_in_file_fuzzy tool
        # elif self.path == "/vscode-scroll":
        #     try:
        #         # Get the request data
        #         content_length = int(self.headers.get('Content-Length', 0))
        #         if content_length <= 0:
        #             self.send_response(400)
        #             self.send_header("Content-type", "application/json")
        #             self.end_headers()
        #             self.wfile.write(json.dumps({
        #                 "success": False,
        #                 "message": "Missing content length"
        #             }).encode())
        #             return
        #         
        #         # Read the request body
        #         post_data = self.rfile.read(content_length)
        #         data = json.loads(post_data.decode('utf-8'))
        #         
        #         # Extract file path and line number
        #         file_path = data.get('file', '')
        #         line_number = data.get('line', 0)
        #         search_text = data.get('search_text', '')
        #         
        #         # Set the target for VSCode
        #         with vscode_lock:
        #             # These variables are already defined at the global level
        #             global vscode_target_file, vscode_target_line
        #             vscode_target_file = file_path
        #             vscode_target_line = line_number
        #         
        #         print(f"SEARCH HIT: '{search_text}' at {os.path.basename(file_path)}:{line_number}")
        #         print(f"           → Setting VSCode target: {os.path.basename(file_path)}:{line_number}")
        #         
        #         # Send a success response
        #         self.send_response(200)
        #         self.send_header("Content-type", "application/json")
        #         self.end_headers()
        #         self.wfile.write(json.dumps({
        #             "success": True,
        #             "message": f"VSCode target set to line {line_number} in {file_path}"
        #         }).encode())
        #         
        #     except Exception as e:
        #         try:
        #             self.send_response(500)
        #             self.send_header("Content-type", "application/json")
        #             self.end_headers()
        #             self.wfile.write(json.dumps({
        #                 "success": False,
        #                 "message": f"Error: {str(e)}"
        #             }).encode())
        #         except:
        #             pass
        #         print(f"Error handling VSCode scroll request: {e}")
        
        elif self.path == "/webhook":
            # For future webhook integration
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "Webhook received"
            }).encode())
            
        # COMMENTED OUT FOR NOW - VSCode polling endpoint
        # elif self.path == "/vscode-poll":
        #     # Handle VSCode polling
        #     try:
        #         # Safe way to get content length
        #         try:
        #             content_length = int(self.headers.get('Content-Length', 0))
        #         except (ValueError, TypeError):
        #             content_length = 0
        #             
        #         if content_length <= 0:
        #             # No content or invalid content length
        #             # Check if we have a target to send anyway
        #             response = {"success": True}
        #             
        #             with vscode_lock:
        #                 if vscode_target_file and vscode_target_line:
        #                     # Include target file and line in the response
        #                     response["target_file"] = vscode_target_file
        #                     response["target_line"] = vscode_target_line
        #                     print(f"VSCode poll: Empty request - Sending target {os.path.basename(vscode_target_file)}:{vscode_target_line}")
        #                     
        #                     # Only clear if we're actually sending a target
        #                     if response.get("target_line") is not None:
        #                         vscode_target_line = None
        #                         vscode_target_file = None
        #                         print("→ Cleared navigation target after sending it")
        #                 else:
        #                     print(f"VSCode poll: Empty request (no content)")
        #             
        #             # Send the response
        #             self.send_response(200)
        #             self.send_header("Content-type", "application/json")
        #             self.end_headers()
        #             self.wfile.write(json.dumps(response).encode())
        #             return
        #         
        #         # Read the data
        #         post_data = self.rfile.read(content_length)
        #         data = json.loads(post_data.decode('utf-8'))
        #         
        #         current_file = data.get('file', '')
        #         current_line = data.get('current_line', 0)
        #         
        #         # Log the current VSCode state with active editor info
        #         file_basename = os.path.basename(current_file)
        #         print(f"VSCode poll: ACTIVE EDITOR - {file_basename}:{current_line}")
        #         
        #         response = {
        #             "success": True
        #         }
        #         
        #         # Check if we have a target line to navigate to
        #         with vscode_lock:
        #             if vscode_target_file and vscode_target_line:
        #                 # Always include target file and line in the response
        #                 # The extension will handle the decision whether to switch files
        #                 response["target_file"] = vscode_target_file
        #                 response["target_line"] = vscode_target_line
        #                 
        #                 # Log the navigation intent
        #                 if os.path.normpath(current_file) != os.path.normpath(vscode_target_file):
        #                     print(f"VSCode navigation: Different file {os.path.basename(current_file)} → {os.path.basename(vscode_target_file)}:{vscode_target_line}")
        #                 elif vscode_target_line != current_line:
        #                     print(f"VSCode navigation: Same file {os.path.basename(current_file)}, line {current_line} → {vscode_target_line}")
        #                 else:
        #                     print(f"VSCode navigation: No change needed (already at {os.path.basename(current_file)}:{current_line})")
        #                     
        #                 # Only clear the target if we're actually sending a target
        #                 # (if VSCode has an active editor and we're sending a target)
        #                 if response.get("target_line") is not None:
        #                     vscode_target_line = None
        #                     vscode_target_file = None
        #                     print("→ Cleared navigation target after sending it")
        #         
        #         # Log what we're sending back to VSCode
        #         if "target_line" in response:
        #             print(f"VSCode response: Sending navigation target (line {response.get('target_line')})")
        #         else:
        #             print(f"VSCode response: No navigation target")
        #         
        #         self.send_response(200)
        #         self.send_header("Content-type", "application/json")
        #         self.end_headers()
        #         self.wfile.write(json.dumps(response).encode())
        #         
        #     except json.JSONDecodeError as e:
        #         # Handle JSON parsing errors
        #         self.send_response(400)
        #         self.send_header("Content-type", "application/json")
        #         self.end_headers()
        #         self.wfile.write(json.dumps({
        #             "success": False,
        #             "message": f"Invalid JSON: {str(e)}"
        #         }).encode())
        #     except KeyError as e:
        #         # Handle missing headers
        #         self.send_response(400)
        #         self.send_header("Content-type", "application/json")
        #         self.end_headers()
        #         self.wfile.write(json.dumps({
        #             "success": False,
        #             "message": f"Missing required header: {str(e)}"
        #         }).encode())
        #     except Exception as e:
        #         # Handle all other errors
        #         try:
        #             self.send_response(500)
        #             self.send_header("Content-type", "application/json")
        #             self.end_headers()
        #             self.wfile.write(json.dumps({
        #                 "success": False,
        #                 "message": f"Server error: {str(e)}"
        #             }).encode())
        #         except:
        #             pass
        #         print(f"Error handling VSCode poll request: {e}")
                    
        # COMMENTED OUT FOR NOW - VSCode target setting endpoint  
        # elif self.path == "/set-vscode-target":
        #     # Handle setting a new target line/file for VSCode
        #     try:
        #         # Check if Content-Length header exists
        #         if 'Content-Length' not in self.headers:
        #             self.send_response(400)
        #             self.send_header("Content-type", "application/json")
        #             self.end_headers()
        #             self.wfile.write(json.dumps({
        #                 "success": False,
        #                 "message": "Missing Content-Length header"
        #             }).encode())
        #             return
        #             
        #         content_length = int(self.headers['Content-Length'])
        #         post_data = self.rfile.read(content_length)
        #         data = json.loads(post_data.decode('utf-8'))
        #         
        #         file_path = data.get('file', '')
        #         line = data.get('line', 0)
        #         
        #         if file_path and line > 0:
        #             with vscode_lock:
        #                 # Variables already declared global at method level
        #                 vscode_target_file = file_path
        #                 vscode_target_line = line
        #             
        #             print(f"Target set: {file_path}:{line}")
        #             
        #             self.send_response(200)
        #             self.send_header("Content-type", "application/json")
        #             self.end_headers()
        #             self.wfile.write(json.dumps({
        #                 "success": True,
        #                 "message": f"Target set to line {line} in {file_path}"
        #             }).encode())
        #         else:
        #             self.send_response(400)
        #             self.send_header("Content-type", "application/json")
        #             self.end_headers()
        #             self.wfile.write(json.dumps({
        #                 "success": False,
        #                 "message": "Invalid file path or line number"
        #             }).encode())
        #     except Exception as e:
        #         try:
        #             self.send_response(500)
        #             self.send_header("Content-type", "application/json")
        #             self.end_headers()
        #             self.wfile.write(json.dumps({
        #                 "success": False,
        #                 "message": f"Error: {str(e)}"
        #             }).encode())
        #         except:
        #             print(f"Error setting VSCode target: {e}")
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
    
    def run_rebuild(self):
        """Run the rebuild script and update global state"""
        global last_rebuild_output, last_rebuild_time, last_rebuild_success, rebuild_in_progress
        
        try:
            # Change to the Gnosis Wraith directory
            os.chdir(GNOSIS_PATH)
            print(f"Changed directory to {GNOSIS_PATH}")
            
            # Run the rebuild script
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Starting rebuild...")
            
            # Use PowerShell to execute the script
            process = subprocess.Popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", REBUILD_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Collect output
            stdout, stderr = process.communicate()
            
            # Update global state
            last_rebuild_time = datetime.now()
            last_rebuild_success = process.returncode == 0
            last_rebuild_output = f"=== REBUILD {timestamp} ===\n"
            
            if stdout:
                last_rebuild_output += "STDOUT:\n" + stdout + "\n"
            if stderr:
                last_rebuild_output += "STDERR:\n" + stderr + "\n"
                
            last_rebuild_output += f"\nExit code: {process.returncode}\n"
            last_rebuild_output += f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            last_rebuild_output += "=" * 50 + "\n"
            
            # Log the rebuild
            with open(LOG_FILE, "a") as f:
                f.write(last_rebuild_output + "\n")
            
            print(f"Rebuild completed with exit code {process.returncode}")
            
        except Exception as e:
            last_rebuild_time = datetime.now()
            last_rebuild_success = False
            last_rebuild_output = f"ERROR: {str(e)}"
            print(f"Error during rebuild: {e}")
            
        finally:
            rebuild_in_progress = False
            rebuild_lock.release()

def run_server():
    """Start the HTTP server"""
    with socketserver.TCPServer(("", PORT), RebuildRequestHandler) as httpd:
        print(f"""
╔════════════════════════════════════════════════════════╗
║                 Gnosis Wraith Rebuild Server                  ║
╚════════════════════════════════════════════════════════╝

Running in listening mode on port {PORT}
Working directory: {GNOSIS_PATH}

API Endpoints:
  GET  /              - Status page (HTML)
  GET  /status        - Status information (JSON)
  POST /rebuild       - Trigger rebuild (JSON)
  POST /webhook       - Webhook receiver (JSON)
  # POST /vscode-poll   - Poll for VSCode navigation targets (DISABLED)
  # POST /set-vscode-target - Set a new VSCode navigation target (DISABLED)

Press Ctrl+C to stop the server
""")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped by user")
        finally:
            httpd.server_close()

if __name__ == "__main__":
    # Create log file if it doesn't exist
    with open(LOG_FILE, "a") as f:
        f.write(f"=== SERVER STARTED {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    
    # Start the server
    run_server()
