import asyncio
import json
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from ..state.validators import ValidationError


class SearchResult:
    """Represents a single search result"""
    
    def __init__(self, title: str, url: str, snippet: str, source: str = "", 
                 relevance_score: float = 0.0, timestamp: Optional[str] = None):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
        self.relevance_score = relevance_score
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "relevance_score": self.relevance_score,
            "timestamp": self.timestamp
        }


class SearchEngine:
    """Base class for search engines"""
    
    def __init__(self, name: str, base_url: str, timeout: int = 30):
        self.name = name
        self.base_url = base_url
        self.timeout = timeout
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Perform a search and return results"""
        raise NotImplementedError


class DuckDuckGoSearch(SearchEngine):
    """DuckDuckGo search engine implementation"""
    
    def __init__(self, timeout: int = 30):
        super().__init__("DuckDuckGo", "https://html.duckduckgo.com", timeout)
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using DuckDuckGo"""
        results = []
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                # DuckDuckGo search URL
                search_url = f"{self.base_url}/html/?q={quote_plus(query)}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(search_url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        results = self._parse_results(html, max_results)
                    else:
                        raise ValidationError(f"DuckDuckGo search failed with status {response.status}")
        
        except asyncio.TimeoutError:
            raise ValidationError(f"DuckDuckGo search timed out after {self.timeout} seconds")
        except Exception as e:
            raise ValidationError(f"DuckDuckGo search failed: {str(e)}")
        
        return results
    
    def _parse_results(self, html: str, max_results: int) -> List[SearchResult]:
        """Parse HTML results from DuckDuckGo"""
        results = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find result containers
            result_containers = soup.find_all('div', class_='result')
            
            for container in result_containers[:max_results]:
                try:
                    # Extract title and URL
                    title_link = container.find('a', class_='result__a')
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    url = title_link.get('href', '')
                    
                    # Extract snippet
                    snippet_elem = container.find('a', class_='result__snippet')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    # Extract source domain
                    source = urlparse(url).netloc if url else ""
                    
                    # Calculate relevance score based on title and snippet
                    relevance_score = self._calculate_relevance(title, snippet)
                    
                    if title and url:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            source=source,
                            relevance_score=relevance_score
                        ))
                
                except Exception:
                    continue
        
        except Exception as e:
            raise ValidationError(f"Failed to parse DuckDuckGo results: {str(e)}")
        
        return results
    
    def _calculate_relevance(self, title: str, snippet: str) -> float:
        """Calculate relevance score for a result"""
        # Simple relevance scoring based on content length and keywords
        score = 0.0
        
        # Base score from title length (longer titles often more descriptive)
        score += min(len(title) / 100.0, 0.3)
        
        # Base score from snippet length
        score += min(len(snippet) / 200.0, 0.4)
        
        # Bonus for common technical terms
        technical_terms = ['api', 'documentation', 'tutorial', 'guide', 'example', 'code', 'github', 'stackoverflow']
        content = (title + " " + snippet).lower()
        for term in technical_terms:
            if term in content:
                score += 0.1
        
        return min(score, 1.0)


class GoogleSearch(SearchEngine):
    """Google search engine implementation (using web scraping)"""
    
    def __init__(self, timeout: int = 30):
        super().__init__("Google", "https://www.google.com", timeout)
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using Google (web scraping approach)"""
        results = []
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                search_url = f"{self.base_url}/search?q={quote_plus(query)}&num={max_results}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(search_url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        results = self._parse_results(html, max_results)
                    else:
                        raise ValidationError(f"Google search failed with status {response.status}")
        
        except asyncio.TimeoutError:
            raise ValidationError(f"Google search timed out after {self.timeout} seconds")
        except Exception as e:
            raise ValidationError(f"Google search failed: {str(e)}")
        
        return results
    
    def _parse_results(self, html: str, max_results: int) -> List[SearchResult]:
        """Parse HTML results from Google"""
        results = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find result containers (Google's structure)
            result_containers = soup.find_all('div', class_='g')
            
            for container in result_containers[:max_results]:
                try:
                    # Extract title and URL
                    title_link = container.find('h3')
                    if not title_link:
                        continue
                    
                    link_elem = title_link.find('a')
                    if not link_elem:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    url = link_elem.get('href', '')
                    
                    # Extract snippet
                    snippet_elem = container.find('span', class_='aCOpRe')
                    if not snippet_elem:
                        snippet_elem = container.find('div', class_='VwiC3b')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    # Extract source domain
                    source = urlparse(url).netloc if url else ""
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance(title, snippet)
                    
                    if title and url:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            source=source,
                            relevance_score=relevance_score
                        ))
                
                except Exception:
                    continue
        
        except Exception as e:
            raise ValidationError(f"Failed to parse Google results: {str(e)}")
        
        return results
    
    def _calculate_relevance(self, title: str, snippet: str) -> float:
        """Calculate relevance score for a result"""
        # Similar to DuckDuckGo but with Google-specific adjustments
        score = 0.0
        
        # Base score from title length
        score += min(len(title) / 100.0, 0.3)
        
        # Base score from snippet length
        score += min(len(snippet) / 200.0, 0.4)
        
        # Bonus for authoritative sources
        authoritative_domains = ['github.com', 'stackoverflow.com', 'docs.python.org', 'developer.mozilla.org', 'w3schools.com']
        content = (title + " " + snippet).lower()
        for domain in authoritative_domains:
            if domain in content:
                score += 0.2
        
        return min(score, 1.0)


class SearchCache:
    """Simple in-memory cache for search results"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[List[SearchResult], datetime]] = {}
    
    def get(self, query: str) -> Optional[List[SearchResult]]:
        """Get cached results for a query"""
        if query not in self.cache:
            return None
        
        results, timestamp = self.cache[query]
        
        # Check if cache entry has expired
        if datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds):
            del self.cache[query]
            return None
        
        return results
    
    def set(self, query: str, results: List[SearchResult]) -> None:
        """Cache results for a query"""
        # Remove oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            oldest_query = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_query]
        
        self.cache[query] = (results, datetime.now())
    
    def clear(self) -> None:
        """Clear all cached results"""
        self.cache.clear()


class WebSearchManager:
    """Manages web search operations with multiple engines and caching"""
    
    def __init__(self):
        self.search_engines = {
            'duckduckgo': DuckDuckGoSearch(),
            'google': GoogleSearch()
        }
        self.cache = SearchCache()
        self.default_engine = 'duckduckgo'
    
    async def search(self, query: str, engine: str = None, max_results: int = 10, 
                    use_cache: bool = True, timeout: int = 30) -> List[SearchResult]:
        """Perform a web search"""
        # Validate query
        if not query or not query.strip():
            raise ValidationError("Search query cannot be empty")
        
        query = query.strip()
        
        # Check cache first
        if use_cache:
            cached_results = self.cache.get(query)
            if cached_results:
                return cached_results[:max_results]
        
        # Select search engine
        if engine is None:
            engine = self.default_engine
        
        if engine not in self.search_engines:
            raise ValidationError(f"Unknown search engine: {engine}. Available: {list(self.search_engines.keys())}")
        
        # Perform search
        search_engine = self.search_engines[engine]
        search_engine.timeout = timeout
        
        results = await search_engine.search(query, max_results)
        
        # Cache results
        if use_cache and results:
            self.cache.set(query, results)
        
        return results
    
    def get_available_engines(self) -> List[str]:
        """Get list of available search engines"""
        return list(self.search_engines.keys())
    
    def clear_cache(self) -> None:
        """Clear search cache"""
        self.cache.clear()


# Global search manager instance
search_manager = WebSearchManager()


def validate_search_params(params: Dict[str, Any]) -> None:
    """Validate search parameters"""
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    if "query" not in params:
        raise ValidationError("Missing required field: query")
    
    query = params["query"]
    if not isinstance(query, str) or not query.strip():
        raise ValidationError("Query must be a non-empty string")
    
    # Validate max_results
    max_results = params.get("max_results", 10)
    if not isinstance(max_results, int) or max_results <= 0 or max_results > 50:
        raise ValidationError("max_results must be an integer between 1 and 50")
    
    # Validate timeout
    timeout = params.get("timeout", 30)
    if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 120:
        raise ValidationError("timeout must be a number between 1 and 120 seconds")
    
    # Validate engine
    engine = params.get("engine")
    if engine is not None and engine not in search_manager.get_available_engines():
        raise ValidationError(f"Unknown search engine: {engine}. Available: {search_manager.get_available_engines()}")


async def web_search(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform a web search and return results.
    
    Parameters:
        params: Dictionary containing:
            - query: Search query string (required)
            - engine: Search engine to use (optional: duckduckgo, google)
            - max_results: Maximum number of results (optional, defaults to 10, max 50)
            - timeout: Search timeout in seconds (optional, defaults to 30, max 120)
            - use_cache: Whether to use cached results (optional, defaults to True)
    
    Returns:
        Dictionary with search results and metadata
    """
    # Validate parameters
    validate_search_params(params)
    
    query = params["query"].strip()
    engine = params.get("engine")
    max_results = params.get("max_results", 10)
    timeout = params.get("timeout", 30)
    use_cache = params.get("use_cache", True)
    
    try:
        # Perform search
        results = await search_manager.search(
            query=query,
            engine=engine,
            max_results=max_results,
            use_cache=use_cache,
            timeout=timeout
        )
        
        # Convert results to dictionaries
        results_dict = [result.to_dict() for result in results]
        
        # Calculate summary statistics
        total_results = len(results_dict)
        avg_relevance = sum(r["relevance_score"] for r in results_dict) / total_results if total_results > 0 else 0.0
        
        # Get unique sources
        sources = list(set(r["source"] for r in results_dict if r["source"]))
        
        return {
            "success": True,
            "query": query,
            "engine": engine or search_manager.default_engine,
            "total_results": total_results,
            "max_results": max_results,
            "avg_relevance_score": round(avg_relevance, 3),
            "sources": sources,
            "results": results_dict,
            "cached": use_cache and search_manager.cache.get(query) is not None,
            "timestamp": datetime.now().isoformat()
        }
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Web search failed: {str(e)}")
