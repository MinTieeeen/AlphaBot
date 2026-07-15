"""
AlphaBot - OptiSigns Support Assistant
Main entry point for scrape → upload workflow
"""
import argparse
import os
import sys
import logging

# Handle missing dotenv gracefully
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback: try to load from environment manually
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='AlphaBot - OptiSigns Support Assistant')
    parser.add_argument('--scrape', action='store_true', help='Scrape articles from OptiSigns')
    parser.add_argument('--upload', action='store_true', help='Upload markdown files to vector store')
    parser.add_argument('--all', action='store_true', help='Run both scrape and upload')
    parser.add_argument('--test', type=str, help='Test the assistant with a question')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without making changes')

    args = parser.parse_args()

    # Default: run all steps if no args provided
    if not any([args.scrape, args.upload, args.all, args.test]):
        args.all = True

    if args.dry_run:
        log.info("Dry run mode - no changes will be made")

    # Import modules
    from scraper import OptiSignsScraper
    from uploader import VectorStoreUploader

    # Scrape
    if args.scrape or args.all:
        log.info("=== Starting Scraper ===")
        scraper = OptiSignsScraper(dry_run=args.dry_run)
        articles = scraper.scrape_all()
        log.info(f"Scraped {len(articles)} articles")

    # Upload
    if args.upload or args.all:
        log.info("=== Starting Uploader ===")
        uploader = VectorStoreUploader(dry_run=args.dry_run)
        result = uploader.upload_all()
        log.info(f"Uploaded {result['files']} files, {result['chunks']} chunks")

    # Test
    if args.test:
        log.info(f"=== Testing with question: {args.test} ===")
        from assistant import Assistant
        bot = Assistant()
        response = bot.ask(args.test)
        print("\n" + "="*50)
        print("RESPONSE:")
        print(response)
        print("="*50)

if __name__ == "__main__":
    main()
