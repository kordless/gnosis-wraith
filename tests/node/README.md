# Gnosis Wraith Node.js Test Suite

This directory contains comprehensive Node.js tests for the Gnosis Wraith API endpoints.

## Prerequisites

- Node.js version 16 or higher
- Gnosis Wraith server running (locally or remote)
- API token for authentication

## Setup

1. Install dependencies:
```bash
npm install
```

2. Copy the environment template:
```bash
cp .env.example .env
```

3. Configure your `.env` file:
- `GNOSIS_URL`: Your Wraith server URL (default: http://localhost:5678)
- `GNOSIS_API_TOKEN`: Your API token (get from server logs or use local auth script)

### Getting an API Token

For local development, you can generate a token using:
```bash
npm run auth:local
```
This will create a token and display it in the console. Copy this token to your `.env` file.

## Available Tests

### Core Tests
- `test_api_markdown.js` - Basic markdown conversion functionality
- `test_batch_urls.js` - Batch URL processing
- `test_collate_batch.js` - Batch collation feature (combines multiple results)

### Advanced Tests
- `test_callbacks.js` - Internal callback/webhook functionality
- `test_callbacks_external.js` - External webhook integration
- `test_job_status.js` - Async job monitoring and status tracking
- `test_local_auth.js` - Local authentication flow

### Utilities
- `simple_test_api_markdown.js` - Simplified test for quick debugging
- `advanced_batch_markdown_test.js` - Complex batch scenarios
- `view-markdown.js` - View stored markdown results

## Running Tests

Run individual tests:
```bash
npm run test:markdown      # Basic markdown API test
npm run test:batch         # Batch processing test
npm run test:collate       # Collation feature test (combines multiple results)
npm run test:callbacks     # Callback mechanism test
npm run test:job-status    # Job monitoring test
npm run auth:local         # Generate local API token
```

Run all tests:
```bash
npm test
```

View saved markdown results:
```bash
npm run view:markdown      # Opens markdown viewer utility
```

## Test Output

Tests will display:
- API request/response details
- Processing times and statistics
- Success/failure status for each operation
- Detailed error messages if failures occur

## Troubleshooting

1. **Connection refused**: Ensure Wraith server is running on configured port
2. **401 Unauthorized**: Check your API token is valid
3. **500 errors**: Check server logs, may indicate storage or configuration issues
4. **Timeout errors**: Increase timeout values in test files for slower systems

## Notes

- Tests use `node-fetch` for HTTP requests
- All sensitive data (.env files) are gitignored
- Tests create real API requests - ensure test server is isolated from production
- Collation tests require multiple URLs to demonstrate functionality
