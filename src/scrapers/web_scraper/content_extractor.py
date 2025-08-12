from typing import Dict, Any, Optional, List
import re
from bs4 import BeautifulSoup
import hashlib
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime
from playwright.async_api import Page

class ContentExtractor:
    """
    Extracts and processes content from web pages
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Content cleaning patterns
        self.noise_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<style[^>]*>.*?</style>',
            r'<nav[^>]*>.*?</nav>',
            r'<footer[^>]*>.*?</footer>',
            r'<header[^>]*>.*?</header>',
            r'<aside[^>]*>.*?</aside>',
            r'<!--.*?-->',
            r'<div[^>]*class="[^"]*ad[^"]*"[^>]*>.*?</div>',
            r'<div[^>]*id="[^"]*ad[^"]*"[^>]*>.*?</div>'
        ]

        # Text cleaning patterns
        self.text_cleanup_patterns = [
            (r'\s+', ' '),  # Multiple whitespace to single space
            (r'\n\s*\n', '\n'),  # Multiple newlines to single newline
            (r'^\s+|\s+$', ''),  # Trim whitespace
        ]

    async def extract_content(
        self,
        page: Page,
        url: str,
        extract_images: bool = True,
        extract_links: bool = True
    ) -> Dict[str, Any]:
        """Extract content from a web page"""

        try:
            # Get page content
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract basic information
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            text_content = self._extract_text(soup)

            # Extract metadata
            metadata = self._extract_metadata(soup, url)

            # Extract images
            images = []
            if extract_images:
                images = self._extract_images(soup, url)

            # Extract links
            links = []
            if extract_links:
                links = self._extract_links(soup, url)

            # Calculate content hash
            content_hash = hashlib.sha256(text_content.encode()).hexdigest()

            # Calculate word count
            word_count = len(text_content.split())

            return {
                'url': url,
                'title': title,
                'description': description,
                'text_content': text_content,
                'metadata': metadata,
                'images': images,
                'links': links,
                'content_hash': content_hash,
                'word_count': word_count,
                'extraction_timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Content extraction failed for {url}: {e}")
            return {}

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        # Try meta title first
        meta_title = soup.find('meta', attrs={'property': 'og:title'})
        if meta_title and meta_title.get('content'):
            return meta_title['content'].strip()

        # Try regular title tag
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()

        # Fallback to h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()

        return ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description"""
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()

        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()

        # Try Twitter description
        twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_desc and twitter_desc.get('content'):
            return twitter_desc['content'].strip()

        return ""

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content"""
        # Remove noise elements
        for pattern in self.noise_patterns:
            for element in soup.find_all(text=re.compile(pattern, re.DOTALL | re.IGNORECASE)):
                element.decompose()

        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()

        # Try to find main content area
        main_content = None

        # Look for main content selectors
        selectors = [
            'main',
            '[role="main"]',
            '.main-content',
            '.content',
            '.post-content',
            '.article-content',
            '#content',
            '#main'
        ]

        for selector in selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body')

        if main_content:
            text = main_content.get_text()
        else:
            text = soup.get_text()

        # Clean up text
        text = self._clean_text(text)

        return text

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Apply cleanup patterns
        for pattern, replacement in self.text_cleanup_patterns:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE)

        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)

        return text

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract page metadata"""
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc,
            'language': self._detect_language(soup),
            'author': self._extract_author(soup),
            'published_date': self._extract_published_date(soup),
            'keywords': self._extract_keywords(soup),
            'canonical_url': self._extract_canonical_url(soup),
            'robots': self._extract_robots(soup)
        }

        return metadata

    def _detect_language(self, soup: BeautifulSoup) -> str:
        """Detect page language"""
        # Try html lang attribute
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            return html_tag['lang']

        # Try meta language
        meta_lang = soup.find('meta', attrs={'http-equiv': 'content-language'})
        if meta_lang and meta_lang.get('content'):
            return meta_lang['content']

        return "unknown"

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author information"""
        # Try meta author
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            return meta_author['content'].strip()

        # Try Open Graph author
        og_author = soup.find('meta', attrs={'property': 'article:author'})
        if og_author and og_author.get('content'):
            return og_author['content'].strip()

        # Try schema.org author
        schema_author = soup.find('meta', attrs={'property': 'schema:author'})
        if schema_author and schema_author.get('content'):
            return schema_author['content'].strip()

        return ""

    def _extract_published_date(self, soup: BeautifulSoup) -> str:
        """Extract published date"""
        # Try various date meta tags
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="pubdate"]',
            'meta[name="publishdate"]',
            'meta[property="og:published_time"]',
            'time[datetime]'
        ]

        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_value = element.get('content') or element.get('datetime')
                if date_value:
                    return date_value.strip()

        return ""

    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords"""
        keywords = []

        # Try meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords.extend([kw.strip() for kw in meta_keywords['content'].split(',')])

        # Try Open Graph tags
        og_tags = soup.find_all('meta', attrs={'property': re.compile(r'^article:tag$')})
        for tag in og_tags:
            if tag.get('content'):
                keywords.append(tag['content'].strip())

        return list(set(keywords))  # Remove duplicates

    def _extract_canonical_url(self, soup: BeautifulSoup) -> str:
        """Extract canonical URL"""
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical and canonical.get('href'):
            return canonical['href'].strip()
        return ""

    def _extract_robots(self, soup: BeautifulSoup) -> str:
        """Extract robots meta tag"""
        robots = soup.find('meta', attrs={'name': 'robots'})
        if robots and robots.get('content'):
            return robots['content'].strip()
        return ""

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract images from the page"""
        images = []

        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Make URL absolute
                absolute_url = urljoin(base_url, src)

                # Skip data URLs and very small images
                if not src.startswith('data:') and not src.startswith('blob:'):
                    images.append({
                        'src': absolute_url,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', ''),
                        'width': img.get('width'),
                        'height': img.get('height')
                    })

        return images

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract links from the page"""
        links = []

        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                # Make URL absolute
                absolute_url = urljoin(base_url, href)

                # Skip internal anchors and non-http URLs
                if not absolute_url.startswith('#'):
                    links.append({
                        'url': absolute_url,
                        'text': link.get_text().strip(),
                        'title': link.get('title', ''),
                        'rel': link.get('rel', [])
                    })

        return links

    def validate_content(self, content: Dict[str, Any]) -> bool:
        """Validate extracted content"""
        required_fields = ['url', 'title', 'text_content']

        for field in required_fields:
            if not content.get(field):
                return False

        # Check minimum content length
        if len(content.get('text_content', '')) < 50:
            return False

        return True

    def get_content_stats(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics about extracted content"""
        text_content = content.get('text_content', '')

        return {
            'word_count': len(text_content.split()),
            'character_count': len(text_content),
            'image_count': len(content.get('images', [])),
            'link_count': len(content.get('links', [])),
            'has_title': bool(content.get('title')),
            'has_description': bool(content.get('description')),
            'content_hash': content.get('content_hash', ''),
            'timestamp': datetime.utcnow().isoformat()
        }
