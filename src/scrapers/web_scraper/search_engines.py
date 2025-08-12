from typing import List, Dict, Any, Optional
import asyncio
import logging
from urllib.parse import quote_plus, urlparse
import re
from datetime import datetime

from .playwright_manager import PlaywrightManager

class SearchEngineScraper:
    """
    Scrapes search results from various search engines
    """

    def __init__(self, playwright_manager: PlaywrightManager):
        self.playwright_manager = playwright_manager
        self.logger = logging.getLogger(__name__)

        # Rate limiting
        self.last_request_time = 0
        self.min_delay = 2.0  # Minimum delay between requests

    async def search_google(
        self,
        query: str,
        max_results: int = 10,
        delay: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Search Google and extract results"""

        await self._rate_limit(delay)

        browser = await self.playwright_manager.get_browser()
        page = await self.playwright_manager.create_page(browser)

        try:
            # Construct search URL
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"

            self.logger.info(f"Searching Google for: {query}")
            await page.goto(search_url, wait_until="networkidle")
            await self.playwright_manager.wait_for_load(page)

            # Extract search results
            results = await page.evaluate("""
                () => {
                    const results = [];
                    const elements = document.querySelectorAll('div.g, div[data-sokoban-container]');

                    elements.forEach((element, index) => {
                        const titleElement = element.querySelector('h3, .LC20lb');
                        const linkElement = element.querySelector('a[href]');
                        const snippetElement = element.querySelector('.VwiC3b, .st, .aCOpRe');

                        if (titleElement && linkElement) {
                            const url = linkElement.href;
                            // Filter out non-http URLs and Google's own pages
                            if (url && url.startsWith('http') && !url.includes('google.com')) {
                                results.push({
                                    title: titleElement.textContent.trim(),
                                    url: url,
                                    snippet: snippetElement ? snippetElement.textContent.trim() : '',
                                    position: index + 1,
                                    source: 'google'
                                });
                            }
                        }
                    });

                    return results;
                }
            """)

            self.logger.info(f"Found {len(results)} Google results for: {query}")
            return results[:max_results]

        except Exception as e:
            self.logger.error(f"Google search failed for '{query}': {e}")
            return []
        finally:
            await page.close()
            await self.playwright_manager.return_browser(browser)

    async def search_bing(
        self,
        query: str,
        max_results: int = 10,
        delay: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Search Bing and extract results"""

        await self._rate_limit(delay)

        browser = await self.playwright_manager.get_browser()
        page = await self.playwright_manager.create_page(browser)

        try:
            search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"

            self.logger.info(f"Searching Bing for: {query}")
            await page.goto(search_url, wait_until="networkidle")
            await self.playwright_manager.wait_for_load(page)

            results = await page.evaluate("""
                () => {
                    const results = [];
                    const elements = document.querySelectorAll('li.b_algo, .b_algo');

                    elements.forEach((element, index) => {
                        const titleElement = element.querySelector('h2 a, .b_title a');
                        const snippetElement = element.querySelector('.b_caption p, .b_snippet');

                        if (titleElement) {
                            const url = titleElement.href;
                            if (url && url.startsWith('http') && !url.includes('bing.com')) {
                                results.push({
                                    title: titleElement.textContent.trim(),
                                    url: url,
                                    snippet: snippetElement ? snippetElement.textContent.trim() : '',
                                    position: index + 1,
                                    source: 'bing'
                                });
                            }
                        }
                    });

                    return results;
                }
            """)

            self.logger.info(f"Found {len(results)} Bing results for: {query}")
            return results[:max_results]

        except Exception as e:
            self.logger.error(f"Bing search failed for '{query}': {e}")
            return []
        finally:
            await page.close()
            await self.playwright_manager.return_browser(browser)

    async def search_duckduckgo(
        self,
        query: str,
        max_results: int = 10,
        delay: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Search DuckDuckGo and extract results"""

        await self._rate_limit(delay)

        browser = await self.playwright_manager.get_browser()
        page = await self.playwright_manager.create_page(browser)

        try:
            search_url = f"https://duckduckgo.com/?q={quote_plus(query)}"

            self.logger.info(f"Searching DuckDuckGo for: {query}")
            await page.goto(search_url, wait_until="networkidle")
            await self.playwright_manager.wait_for_load(page)

            results = await page.evaluate("""
                () => {
                    const results = [];
                    const elements = document.querySelectorAll('.result, [data-testid="result"]');

                    elements.forEach((element, index) => {
                        const titleElement = element.querySelector('.result__title a, [data-testid="result-title"] a');
                        const snippetElement = element.querySelector('.result__snippet, [data-testid="result-snippet"]');

                        if (titleElement) {
                            const url = titleElement.href;
                            if (url && url.startsWith('http') && !url.includes('duckduckgo.com')) {
                                results.push({
                                    title: titleElement.textContent.trim(),
                                    url: url,
                                    snippet: snippetElement ? snippetElement.textContent.trim() : '',
                                    position: index + 1,
                                    source: 'duckduckgo'
                                });
                            }
                        }
                    });

                    return results;
                }
            """)

            self.logger.info(f"Found {len(results)} DuckDuckGo results for: {query}")
            return results[:max_results]

        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed for '{query}': {e}")
            return []
        finally:
            await page.close()
            await self.playwright_manager.return_browser(browser)

    async def search_all_engines(
        self,
        query: str,
        max_results_per_engine: int = 10,
        engines: List[str] = ['google', 'bing'],
        delay: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Search multiple engines and combine results"""

        all_results = []

        for engine in engines:
            try:
                if engine == 'google':
                    results = await self.search_google(query, max_results_per_engine, delay)
                elif engine == 'bing':
                    results = await self.search_bing(query, max_results_per_engine, delay)
                elif engine == 'duckduckgo':
                    results = await self.search_duckduckgo(query, max_results_per_engine, delay)
                else:
                    self.logger.warning(f"Unknown search engine: {engine}")
                    continue

                all_results.extend(results)

            except Exception as e:
                self.logger.error(f"Search failed for engine {engine}: {e}")
                continue

        # Remove duplicates based on URL
        unique_results = self._remove_duplicates(all_results)

        self.logger.info(f"Combined search returned {len(unique_results)} unique results for: {query}")
        return unique_results

    def _remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate search results based on URL"""
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results

    async def _rate_limit(self, delay: float):
        """Implement rate limiting between requests"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_request_time = asyncio.get_event_loop().time()

    def validate_url(self, url: str) -> bool:
        """Validate if URL is suitable for scraping"""
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ['http', 'https'] and
                parsed.netloc and
                not any(domain in parsed.netloc.lower() for domain in [
                    'google.com', 'bing.com', 'duckduckgo.com', 'youtube.com',
                    'facebook.com', 'twitter.com', 'instagram.com'
                ])
            )
        except Exception:
            return False

    def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics"""
        return {
            "last_request_time": self.last_request_time,
            "min_delay": self.min_delay,
            "timestamp": datetime.utcnow().isoformat()
        }
