# Gnosis Wraith Storage Directory

This directory contains all persistent data for Gnosis Wraith. It is mounted as a volume in Docker containers to ensure data persists between container restarts.

## Directory Structure

```
storage/
├── reports/        # Generated reports in MD, HTML, and JSON formats
├── screenshots/    # Page screenshots captured during crawling
├── system/         # System-wide data and cache
├── logs/           # Application logs
└── data/           # General application data
```

## Important Notes

- This directory is mounted to `/data` inside Docker containers
- All files here persist between container restarts
- You can browse reports directly in the `reports/` subdirectory
- Screenshots are automatically linked to their corresponding reports
- Backup this directory to preserve your crawl history

## Usage

The storage directory is automatically used when running with Docker:

```bash
# Using docker-compose (recommended)
docker-compose up -d

# Or with development compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Files will appear here as you crawl websites through the Gnosis Wraith interface.