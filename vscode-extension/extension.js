const vscode = require('vscode');
const https = require('https');
const http = require('http');

// Global state
let pollInterval = null;
let statusBarItem = null;
let isEnabled = false;
let lastPollTime = 0;
let currentEditorFocused = false;

/**
 * Fetch line information from the server
 */
async function pollServer() {
  try {
    // Only poll if we have focus and some time has passed since the last poll
    const now = Date.now();
    if (!currentEditorFocused || (now - lastPollTime < 500)) {
      return;
    }
    
    // Update poll time
    lastPollTime = now;
    
    // Get current file info
    const editor = vscode.window.activeTextEditor;
    
    // If no editor is open, poll without file info
    // This allows us to open a file when requested by the server
    if (!editor) {
      // Create endpoint URL
      const config = vscode.workspace.getConfiguration('gnosisWraith');
      const serverUrl = config.get('serverUrl');
      const requestUrl = `${serverUrl}/vscode-poll`;
      
      // Make HTTP request with empty body
      const response = await makeRequest(requestUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });
      
      // If we get a response with a target file, open it
      if (response && response.success && response.target_file && response.target_line) {
        const targetFile = response.target_file;
        const targetLine = response.target_line - 1; // VSCode lines are 0-based
        
        // Open the file
        vscode.workspace.openTextDocument(targetFile)
          .then(doc => {
            // Show the document and position cursor at the target line
            vscode.window.showTextDocument(doc)
              .then(editor => {
                // Wait a bit for the editor to fully load before navigating
                setTimeout(() => {
                  if (targetLine >= 0 && targetLine < doc.lineCount) {
                    // Create a selection at the target line
                    const position = new vscode.Position(targetLine, 0);
                    editor.selection = new vscode.Selection(position, position);
                    
                    // Reveal the target line in the editor
                    editor.revealRange(
                      new vscode.Range(position, position),
                      vscode.TextEditorRevealType.InCenter
                    );
                    
                    // Update status bar
                    statusBarItem.text = `$(arrow-right) ${doc.fileName.split(/[\/\\]/).pop()}:${response.target_line}`;
                    setTimeout(() => {
                      statusBarItem.text = '$(eye) Gnosis Wraith: Tracking';
                    }, 2000);
                  }
                }, 300);
              });
          })
          .catch(error => {
            console.error('Error opening file:', error);
            statusBarItem.text = '$(alert) Error opening file';
            setTimeout(() => {
              if (isEnabled) {
                statusBarItem.text = '$(eye) Gnosis Wraith: Tracking';
              }
            }, 3000);
          });
      }
      
      return;
    }
    
    const document = editor.document;
    const filePath = document.uri.fsPath;
    
    // Get server URL from configuration
    const config = vscode.workspace.getConfiguration('gnosisWraith');
    const serverUrl = config.get('serverUrl');
    
    // Create endpoint URL
    const requestUrl = `${serverUrl}/vscode-poll`;
    
    // Make HTTP request
    const response = await makeRequest(requestUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        file: filePath,
        current_line: editor.selection.active.line + 1
      })
    });
    
    // Process response
    if (response && response.success) {
      // Check if we need to switch to a different file
      if (response.target_file && response.target_line) {
        // If the target file is different from the current file, open it
        const targetFile = response.target_file;
        const targetLine = response.target_line - 1; // VSCode lines are 0-based
        
        // Only open if the file is different from the current one
        if (targetFile !== filePath) {
          // Open the file
          vscode.workspace.openTextDocument(targetFile)
            .then(doc => {
              // Show the document and position cursor at the target line
              vscode.window.showTextDocument(doc)
                .then(editor => {
                  // Wait a bit for the editor to fully load before navigating
                  setTimeout(() => {
                    if (targetLine >= 0 && targetLine < doc.lineCount) {
                      // Create a selection at the target line
                      const position = new vscode.Position(targetLine, 0);
                      editor.selection = new vscode.Selection(position, position);
                      
                      // Reveal the target line in the editor
                      editor.revealRange(
                        new vscode.Range(position, position),
                        vscode.TextEditorRevealType.InCenter
                      );
                      
                      // Update status bar
                      statusBarItem.text = `$(arrow-right) ${doc.fileName.split(/[\/\\]/).pop()}:${response.target_line}`;
                      setTimeout(() => {
                        statusBarItem.text = '$(eye) Gnosis Wraith: Tracking';
                      }, 2000);
                    }
                  }, 300);
                });
            })
            .catch(error => {
              console.error('Error opening file:', error);
              statusBarItem.text = '$(alert) Error opening file';
              setTimeout(() => {
                if (isEnabled) {
                  statusBarItem.text = '$(eye) Gnosis Wraith: Tracking';
                }
              }, 3000);
            });
        }
      }
      // If just target_line is provided, navigate in the current file
      else if (response.target_line) {
        // Navigate within the current file
        const targetLine = response.target_line - 1; // VSCode lines are 0-based
        
        if (targetLine >= 0 && targetLine < document.lineCount) {
          // Create a selection at the target line
          const position = new vscode.Position(targetLine, 0);
          editor.selection = new vscode.Selection(position, position);
          
          // Reveal the target line in the editor
          editor.revealRange(
            new vscode.Range(position, position),
            vscode.TextEditorRevealType.InCenter
          );
          
          // Update status bar
          statusBarItem.text = `$(arrow-right) Line ${response.target_line}`;
          setTimeout(() => {
            statusBarItem.text = '$(eye) Gnosis Wraith: Tracking';
          }, 2000);
        }
      }
    }
  } catch (error) {
    console.error('Error polling server:', error);
    statusBarItem.text = '$(alert) Gnosis Wraith: Error';
    setTimeout(() => {
      if (isEnabled) {
        statusBarItem.text = '$(eye) Gnosis Wraith: Tracking';
      }
    }, 3000);
  }
}

/**
 * Helper function to make HTTP/HTTPS requests
 */
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const requestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port || (urlObj.protocol === 'https:' ? 443 : 80),
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: options.headers || {}
    };
    
    const client = urlObj.protocol === 'https:' ? https : http;
    const req = client.request(requestOptions, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const parsedData = JSON.parse(data);
          resolve(parsedData);
        } catch (error) {
          reject(new Error(`Invalid JSON response: ${data}`));
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    if (options.body) {
      req.write(options.body);
    }
    
    req.end();
  });
}

/**
 * Enable tracking
 */
function enableTracking() {
  if (isEnabled) return;
  
  // Get configuration
  const config = vscode.workspace.getConfiguration('gnosisWraith');
  const interval = config.get('pollInterval');
  
  // Start polling
  pollInterval = setInterval(pollServer, interval);
  isEnabled = true;
  
  // Create or update status bar item
  if (!statusBarItem) {
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  }
  
  statusBarItem.text = '$(eye) Gnosis Wraith: Tracking';
  statusBarItem.tooltip = 'Gnosis Wraith is tracking line changes';
  statusBarItem.command = 'gnosis-wraith.disableTracking';
  statusBarItem.show();
  
  // Show notification
  vscode.window.showInformationMessage('Gnosis Wraith line tracking enabled');
}

/**
 * Disable tracking
 */
function disableTracking() {
  if (!isEnabled) return;
  
  // Stop polling
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
  
  isEnabled = false;
  
  // Update status bar
  if (statusBarItem) {
    statusBarItem.text = '$(eye-closed) Gnosis Wraith: Inactive';
    statusBarItem.tooltip = 'Gnosis Wraith line tracking is disabled';
    statusBarItem.command = 'gnosis-wraith.enableTracking';
  }
  
  // Show notification
  vscode.window.showInformationMessage('Gnosis Wraith line tracking disabled');
}

/**
 * Extension activation
 */
function activate(context) {
  console.log('Gnosis Wraith extension is now active');
  
  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('gnosis-wraith.enableTracking', enableTracking),
    vscode.commands.registerCommand('gnosis-wraith.disableTracking', disableTracking)
  );
  
  // Create status bar item
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBarItem.text = '$(eye-closed) Gnosis Wraith: Inactive';
  statusBarItem.tooltip = 'Click to enable Gnosis Wraith line tracking';
  statusBarItem.command = 'gnosis-wraith.enableTracking';
  statusBarItem.show();
  
  // Track window state
  vscode.window.onDidChangeWindowState(state => {
    currentEditorFocused = state.focused;
  });
  
  // Track editor focus
  vscode.window.onDidChangeActiveTextEditor(() => {
    if (vscode.window.activeTextEditor) {
      currentEditorFocused = true;
    }
  });
  
  // Auto-enable if configured
  const config = vscode.workspace.getConfiguration('gnosisWraith');
  if (config.get('autoEnable')) {
    enableTracking();
  }
}

/**
 * Extension deactivation
 */
function deactivate() {
  disableTracking();
  
  if (statusBarItem) {
    statusBarItem.dispose();
    statusBarItem = null;
  }
}

module.exports = {
  activate,
  deactivate
};
