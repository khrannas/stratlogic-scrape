"""
Content extraction and processing for web pages.
"""

import re
import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.async_api import Page
from .config import WebScraperSettings


class ContentExtractor:
    """Extracts and processes content from web pages."""
    
    def __init__(self, settings: WebScraperSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    async def extract_content(
        self,
        page: Page,
        url: str,
        extract_images: bool = True,
        extract_links: bool = True
    ) -> Dict[str, Any]:
        """Extract comprehensive content from a web page."""
        
        try:
            # Get page content using Playwright
            page_content = await self._get_page_content(page)
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(page_content.get('html', ''), 'html.parser')
            
            # Extract basic information
            title = self._extract_title(soup, page_content.get('title', ''))
            description = self._extract_description(soup)
            text_content = self._extract_text(soup, page_content.get('text', ''))
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url, page_content.get('meta_tags', {}))
            
            # Extract images
            images = []
            if extract_images:
                images = self._extract_images(soup, url)
            
            # Extract links
            links = []
            if extract_links:
                links = self._extract_links(soup, url)
            
            # Calculate content hash
            content_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()
            
            # Calculate word count
            word_count = len(text_content.split())
            
            # Truncate content if too long
            if len(text_content) > self.settings.max_content_length:
                text_content = text_content[:self.settings.max_content_length] + "..."
            
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
                'extraction_timestamp': datetime.utcnow().isoformat(),
                'content_length': len(text_content),
                'image_count': len(images),
                'link_count': len(links)
            }
            
        except Exception as e:
            self.logger.error(f"Content extraction failed for {url}: {e}")
            return {
                'url': url,
                'error': str(e),
                'extraction_timestamp': datetime.utcnow().isoformat()
            }
    
    async def _get_page_content(self, page: Page) -> Dict[str, Any]:
        """Get raw page content using Playwright."""
        try:
            # Get HTML content
            html_content = await page.content()
            
            # Get page title
            title = await page.title()
            
            # Get text content
            text_content = await page.evaluate("""
                () => {
                    // Remove script and style elements
                    const scripts = document.querySelectorAll('script, style, noscript');
                    scripts.forEach(el => el.remove());
                    
                    // Get text content
                    return document.body ? document.body.innerText : document.documentElement.innerText;
                }
            """)
            
            # Get meta tags
            meta_tags = await page.evaluate("""
                () => {
                    const metas = document.querySelectorAll('meta');
                    const metaData = {};
                    metas.forEach(meta => {
                        const name = meta.getAttribute('name') || meta.getAttribute('property');
                        const content = meta.getAttribute('content');
                        if (name && content) {
                            metaData[name] = content;
                        }
                    });
                    return metaData;
                }
            """)
            
            return {
                'html': html_content,
                'title': title,
                'text': text_content,
                'meta_tags': meta_tags
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get page content: {e}")
            return {}
    
    def _extract_title(self, soup: BeautifulSoup, fallback_title: str = "") -> str:
        """Extract page title."""
        # Try meta title first
        meta_title = soup.find('meta', attrs={'property': 'og:title'})
        if meta_title and meta_title.get('content'):
            return meta_title['content'].strip()
        
        # Try title tag
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Try h1 tag
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        # Use fallback
        return fallback_title.strip()
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description."""
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
    
    def _extract_text(self, soup: BeautifulSoup, fallback_text: str = "") -> str:
        """Extract main text content."""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'noscript', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try to find main content area
        main_content = None
        
        # Look for common main content selectors
        main_selectors = [
            'main', '[role="main"]', '.main-content', '.content', 
            '#content', '#main', '.post-content', '.article-content'
        ]
        
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body') or soup
        
        # Extract text
        if main_content:
            text = main_content.get_text()
        else:
            text = fallback_text
        
        # Clean up text
        text = self._clean_text(text)
        
        return text
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}]', ' ', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str, meta_tags: Dict[str, str]) -> Dict[str, Any]:
        """Extract comprehensive page metadata."""
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc,
            'language': self._detect_language(soup, meta_tags),
            'author': self._extract_author(soup, meta_tags),
            'published_date': self._extract_published_date(soup, meta_tags),
            'keywords': self._extract_keywords(soup, meta_tags),
            'content_type': self._detect_content_type(soup, meta_tags),
            'robots': meta_tags.get('robots', ''),
            'viewport': meta_tags.get('viewport', ''),
            'charset': meta_tags.get('charset', ''),
            'canonical_url': self._extract_canonical_url(soup, url)
        }
        
        return metadata
    
    def _detect_language(self, soup: BeautifulSoup, meta_tags: Dict[str, str]) -> str:
        """Detect page language."""
        # Try meta language
        lang_meta = soup.find('meta', attrs={'http-equiv': 'content-language'})
        if lang_meta and lang_meta.get('content'):
            return lang_meta['content']
        
        # Try html lang attribute
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            return html_tag['lang']
        
        # Try Open Graph locale
        og_locale = meta_tags.get('og:locale', '')
        if og_locale:
            return og_locale
        
        return "en"  # Default to English
    
    def _extract_author(self, soup: BeautifulSoup, meta_tags: Dict[str, str]) -> str:
        """Extract author information."""
        # Try meta author
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta and author_meta.get('content'):
            return author_meta['content']
        
        # Try Open Graph author
        og_author = meta_tags.get('og:author', '')
        if og_author:
            return og_author
        
        # Try Twitter author
        twitter_author = meta_tags.get('twitter:creator', '')
        if twitter_author:
            return twitter_author
        
        return ""
    
    def _extract_published_date(self, soup: BeautifulSoup, meta_tags: Dict[str, str]) -> str:
        """Extract published date."""
        # Try various date meta tags
        date_selectors = [
            'meta[name="article:published_time"]',
            'meta[property="article:published_time"]',
            'meta[name="date"]',
            'meta[name="pubdate"]',
            'meta[property="og:updated_time"]',
            'time[datetime]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_value = element.get('content') or element.get('datetime')
                if date_value:
                    return date_value
        
        return ""
    
    def _extract_keywords(self, soup: BeautifulSoup, meta_tags: Dict[str, str]) -> List[str]:
        """Extract keywords."""
        keywords = []
        
        # Try meta keywords
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta and keywords_meta.get('content'):
            keywords.extend([k.strip() for k in keywords_meta['content'].split(',')])
        
        # Try Open Graph tags
        og_tags = meta_tags.get('og:tag', '')
        if og_tags:
            keywords.extend([k.strip() for k in og_tags.split(',')])
        
        return list(set(keywords))  # Remove duplicates
    
    def _detect_content_type(self, soup: BeautifulSoup, meta_tags: Dict[str, str]) -> str:
        """Detect content type."""
        # Try Open Graph type
        og_type = meta_tags.get('og:type', '')
        if og_type:
            return og_type
        
        # Try Twitter card type
        twitter_card = meta_tags.get('twitter:card', '')
        if twitter_card:
            return f"twitter:{twitter_card}"
        
        # Try to detect based on content
        if soup.find('article'):
            return "article"
        elif soup.find('main'):
            return "page"
        else:
            return "document"
    
    def _extract_canonical_url(self, soup: BeautifulSoup, current_url: str) -> str:
        """Extract canonical URL."""
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical and canonical.get('href'):
            return urljoin(current_url, canonical['href'])
        return current_url
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract images from the page."""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Make URL absolute
                absolute_url = urljoin(base_url, src)
                
                # Skip data URLs and small images
                if src.startswith('data:') or 'icon' in src.lower():
                    continue
                
                images.append({
                    'src': absolute_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'width': img.get('width'),
                    'height': img.get('height')
                })
        
        return images
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract links from the page."""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                # Make URL absolute
                absolute_url = urljoin(base_url, href)
                
                # Skip internal anchors and non-http links
                if absolute_url.startswith('http'):
                    links.append({
                        'url': absolute_url,
                        'text': link.get_text().strip(),
                        'title': link.get('title', ''),
                        'rel': link.get('rel', [])
                    })
        
        return links
    
    def calculate_content_score(self, content: Dict[str, Any]) -> float:
        """Calculate a quality score for the extracted content."""
        score = 0.0
        
        # Base score for having content
        if content.get('text_content'):
            score += 20
        
        # Title quality
        if content.get('title') and len(content['title']) > 10:
            score += 15
        
        # Description quality
        if content.get('description') and len(content['description']) > 50:
            score += 10
        
        # Word count bonus
        word_count = content.get('word_count', 0)
        if word_count > 100:
            score += 10
        if word_count > 500:
            score += 10
        if word_count > 1000:
            score += 5
        
        # Metadata completeness
        metadata = content.get('metadata', {})
        if metadata.get('author'):
            score += 5
        if metadata.get('published_date'):
            score += 5
        if metadata.get('keywords'):
            score += 5
        
        # Image content
        if content.get('images'):
            score += 5
        
        # Link content
        if content.get('links'):
            score += 5
        
        return min(score, 100.0)  # Cap at 100
