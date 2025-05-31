# Gnosis Wraith Extension for VSCode

A VSCode extension that polls the Gnosis Wraith rebuild server for line navigation requests. This extension will automatically navigate to specific lines in your code when requested by the Gnosis Wraith server.

## Features

- Polls the Gnosis Wraith server at configurable intervals
- Automatically navigates to requested lines in your code
- Only active when VSCode has focus
- Status bar indicator shows current tracking status
- Commands to enable/disable tracking manually

## Requirements

- VSCode 1.60.0 or higher
- Running Gnosis Wraith rebuild server (default: http://localhost:5679)

## Installation

1. Copy this extension folder to `~/.vscode/extensions/` or your VSCode extensions directory
2. Restart VSCode
3. The extension will auto-enable if configured (see status bar)

## Configuration

Open VSCode settings and search for "Gnosis Wraith" to configure:

- `gnosisWraith.serverUrl`: URL of the Gnosis Wraith rebuild server
- `gnosisWraith.pollInterval`: How often to poll the server (in milliseconds)
- `gnosisWraith.autoEnable`: Whether to automatically enable tracking on startup

## Commands

- `Gnosis Wraith: Enable Line Tracking`: Start polling the server
- `Gnosis Wraith: Disable Line Tracking`: Stop polling the server

## Status Bar

The extension shows its status in the VSCode status bar:

- `Gnosis Wraith: Tracking`: Extension is active and polling
- `Gnosis Wraith: Inactive`: Extension is installed but not polling
- `Gnosis Wraith: Error`: An error occurred during polling

## Server API

The extension expects the server to implement a `/vscode-poll` endpoint that:

- Accepts POST requests with JSON payload: `{ "file": "path/to/file", "current_line": 123 }`
- Returns JSON response: `{ "success": true, "target_line": 456 }` if navigation is needed
- Returns `{ "success": true }` with no target_line if no navigation is needed
