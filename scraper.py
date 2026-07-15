"""
OptiSigns Article Scraper
Downloads articles from support.optisigns.com and converts to Markdown
"""
import os
import re
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
import html2text

log = logging.getLogger(__name__)

# Base URL for OptiSigns support (Zendesk)
BASE_URL = "https://support.optisigns.com"
ARTICLES_URL = f"{BASE_URL}/api/v2/help_center/en-us/articles.json"

class OptiSignsScraper:
    """Scrapes articles from OptiSigns Zendesk support center"""

    def __init__(self, content_dir: str = "content", dry_run: bool = False):
        self.content_dir = Path(content_dir)
        self.content_dir.mkdir(exist_ok=True)
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AlphaBot/1.0 (Educational Project)'
        })
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.body_width = 0  # No wrapping

        # Track metadata
        self.metadata_file = self.content_dir / ".metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load previous scrape metadata"""
        import json
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                return json.load(f)
        return {"articles": {}, "last_run": None}

    def _save_metadata(self):
        """Save scrape metadata"""
        import json
        self.metadata["last_run"] = datetime.now().isoformat()
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content"""
        return hashlib.sha256(content.encode()).hexdigest()

    def _fetch_json(self, url: str) -> Optional[Dict]:
        """Fetch JSON from URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            log.error(f"Failed to fetch {url}: {e}")
            return None

    def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML from URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            log.error(f"Failed to fetch {url}: {e}")
            return None

    def _clean_html(self, html: str) -> str:
        """Remove nav, ads, sidebar from HTML"""
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unwanted elements
        unwanted = [
            'nav', 'header', 'footer', 'aside',
            'script', 'style', 'noscript',
            '.nav', '.navigation', '.sidebar', '.advertisement',
            '.ads', '.social-share', '.related-articles',
            '[class*="nav"]', '[class*="menu"]', '[class*="footer"]'
        ]
        for selector in unwanted:
            for elem in soup.select(selector):
                elem.decompose()

        # Find main content area
        main = soup.find('article') or soup.find('main') or soup.find('div', class_='article-body')
        if main:
            return str(main)
        return str(soup)

    def _html_to_markdown(self, html: str, title: str = "", url: str = "") -> str:
        """Convert cleaned HTML to Markdown"""
        # Apply cleaning first
        cleaned = self._clean_html(html)

        # Convert to markdown
        md = self.h2t.handle(cleaned)

        # Prepend title and source
        lines = [f"# {title}", ""]
        if url:
            lines.append(f"Source: {url}")
            lines.append("")
        lines.append(md)

        return "\n".join(lines)

    def _slugify(self, title: str) -> str:
        """Convert title to URL-safe slug"""
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = slug.strip('-')
        return slug[:100]  # Limit length

    def get_article_list(self, max_pages: int = 5) -> List[Dict]:
        """Get list of all articles"""
        articles = []
        page = 1

        while page <= max_pages:
            url = f"{ARTICLES_URL}?page={page}"
            log.info(f"Fetching article list page {page}...")
            data = self._fetch_json(url)

            if not data or 'articles' not in data:
                break

            for article in data['articles']:
                articles.append({
                    'id': article['id'],
                    'title': article['title'],
                    'url': article['html_url'],
                    'updated_at': article.get('updated_at'),
                    'created_at': article.get('created_at')
                })

            # Check if more pages
            if not data.get('next_page'):
                break
            page += 1

        log.info(f"Found {len(articles)} articles")
        return articles

    def scrape_article(self, article: Dict) -> Optional[str]:
        """Scrape single article and return markdown content"""
        url = article['url']
        log.info(f"Scraping: {article['title']}")

        html = self._fetch_html(url)
        if not html:
            return None

        # Check if changed
        content_hash = self._compute_hash(html)
        article_id = str(article['id'])

        if article_id in self.metadata['articles']:
            if self.metadata['articles'][article_id]['hash'] == content_hash:
                log.debug(f"Article unchanged, skipping: {article['title']}")
                return None  # Unchanged

        # Convert to markdown
        title = article['title']
        md = self._html_to_markdown(html, title=title, url=url)

        # Save file
        slug = self._slugify(title)
        filename = self.content_dir / f"{slug}.md"

        if not self.dry_run:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(md)

        # Update metadata
        self.metadata['articles'][article_id] = {
            'title': title,
            'url': url,
            'hash': content_hash,
            'filename': str(filename),
            'updated_at': article['updated_at']
        }

        log.info(f"Saved: {filename.name}")
        return str(filename)

    def scrape_all(self, max_articles: int = 50) -> List[str]:
        """Scrape all articles"""
        saved_files = []

        # Get article list
        articles = self.get_article_list()
        articles = articles[:max_articles]

        # Track stats
        stats = {'added': 0, 'updated': 0, 'skipped': 0}

        for article in articles:
            result = self.scrape_article(article)
            if result:
                article_id = str(article['id'])
                if article_id in self.metadata['articles']:
                    # Check if this was an update or new
                    if self.metadata['articles'][article_id].get('filename'):
                        stats['updated'] += 1
                    else:
                        stats['added'] += 1
                saved_files.append(result)
            else:
                stats['skipped'] += 1

        # Save metadata
        self._save_metadata()

        log.info(f"Stats: added={stats['added']}, updated={stats['updated']}, skipped={stats['skipped']}")
        return saved_files


if __name__ == "__main__":
    scraper = OptiSignsScraper()
    files = scraper.scrape_all()
    print(f"\nScraped {len(files)} articles to content/")
