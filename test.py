import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://theguardian.org")
        print(result.markdown[:300])  # Print first 300 chars

if __name__ == "__main__":
    asyncio.run(main())