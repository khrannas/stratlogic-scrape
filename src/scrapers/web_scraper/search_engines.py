"""
Search engine scrapers for web content discovery.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urlparse
import re
from .playwright_manager import PlaywrightManager
from .config import WebScraperSettings


class SearchEngineScraper:
    """Scrapes search results from various search engines."""
    
    def __init__(self, playwright_manager: PlaywrightManager, settings: WebScraperSettings):
        self.playwright_manager = playwright_manager
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    async def search_google(
        self,
        query: str,
        max_results: int = 10,
        delay: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Search Google and extract results."""
        
        browser = await self.playwright_manager.get_browser()
        page = await self.playwright_manager.create_page(browser)
        
        try:
            # Construct search URL
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"
            
            self.logger.info(f"Searching Google for: {query}")
            await page.goto(search_url, wait_until="networkidle")
            await asyncio.sleep(delay)
            
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
                            // Only include actual search results, not ads or other elements
                            if (url && !url.includes('google.com/search') && !url.includes('google.com/url')) {
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
            
            # Filter and limit results
            filtered_results = []
            for result in results:
                if result.get('url') and not self._is_blocked_domain(result['url']):
                    filtered_results.append(result)
                    if len(filtered_results) >= max_results:
                        break
            
            self.logger.info(f"Found {len(filtered_results)} Google results for: {query}")
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Google search failed for query '{query}': {e}")
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
        """Search Bing and extract results."""
        
        browser = await self.playwright_manager.get_browser()
        page = await self.playwright_manager.create_page(browser)
        
        try:
            search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"
            
            self.logger.info(f"Searching Bing for: {query}")
            await page.goto(search_url, wait_until="networkidle")
            await asyncio.sleep(delay)
            
            results = await page.evaluate("""
                () => {
                    const results = [];
                    const elements = document.querySelectorAll('li.b_algo, .b_algo');
                    
                    elements.forEach((element, index) => {
                        const titleElement = element.querySelector('h2 a, .b_title a');
                        const snippetElement = element.querySelector('.b_caption p, .b_snippet');
                        
                        if (titleElement) {
                            const url = titleElement.href;
                            if (url && !url.includes('bing.com/search')) {
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
            
            # Filter and limit results
            filtered_results = []
            for result in results:
                if result.get('url') and not self._is_blocked_domain(result['url']):
                    filtered_results.append(result)
                    if len(filtered_results) >= max_results:
                        break
            
            self.logger.info(f"Found {len(filtered_results)} Bing results for: {query}")
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Bing search failed for query '{query}': {e}")
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
        """Search DuckDuckGo and extract results."""
        
        browser = await self.playwright_manager.get_browser()
        page = await self.playwright_manager.create_page(browser)
        
        try:
            search_url = f"https://duckduckgo.com/?q={quote_plus(query)}"
            
            self.logger.info(f"Searching DuckDuckGo for: {query}")
            await page.goto(search_url, wait_until="networkidle")
            await asyncio.sleep(delay)
            
            results = await page.evaluate("""
                () => {
                    const results = [];
                    const elements = document.querySelectorAll('.result, [data-testid="result"]');
                    
                    elements.forEach((element, index) => {
                        const titleElement = element.querySelector('.result__title a, [data-testid="result-title-a"]');
                        const snippetElement = element.querySelector('.result__snippet, [data-testid="result-snippet"]');
                        
                        if (titleElement) {
                            const url = titleElement.href;
                            if (url && !url.includes('duckduckgo.com')) {
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
            
            # Filter and limit results
            filtered_results = []
            for result in results:
                if result.get('url') and not self._is_blocked_domain(result['url']):
                    filtered_results.append(result)
                    if len(filtered_results) >= max_results:
                        break
            
            self.logger.info(f"Found {len(filtered_results)} DuckDuckGo results for: {query}")
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed for query '{query}': {e}")
            return []
        finally:
            await page.close()
            await self.playwright_manager.return_browser(browser)
    
    async def search_multiple_engines(
        self,
        query: str,
        engines: List[str] = None,
        max_results_per_engine: int = 10,
        delay: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Search multiple engines and combine results."""
        
        if engines is None:
            engines = self.settings.default_search_engines
        
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
                
                # Add delay between engines
                if engine != engines[-1]:  # Not the last engine
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                self.logger.error(f"Search failed for engine {engine}: {e}")
                continue
        
        # Remove duplicates
        unique_results = self._remove_duplicates(all_results)
        
        self.logger.info(f"Combined search results: {len(unique_results)} unique results from {len(engines)} engines")
        return unique_results
    
    def _is_blocked_domain(self, url: str) -> bool:
        """Check if the domain is in the blocked list."""
        blocked_domains = {
            'google.com', 'bing.com', 'duckduckgo.com', 'youtube.com',
            'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com'
        }
        
        try:
            domain = urlparse(url).netloc.lower()
            return domain in blocked_domains or any(blocked in domain for blocked in blocked_domains)
        except Exception:
            return True
    
    def _remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate search results based on URL."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    async def validate_url(self, url: str) -> bool:
        """Validate if a URL is accessible."""
        browser = await self.playwright_manager.get_browser()
        page = await self.playwright_manager.create_page(browser)
        
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=10000)
            return response and response.status < 400
        except Exception as e:
            self.logger.debug(f"URL validation failed for {url}: {e}")
            return False
        finally:
            await page.close()
            await self.playwright_manager.return_browser(browser)
