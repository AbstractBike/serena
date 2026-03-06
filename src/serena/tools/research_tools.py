"""Firecrawl-powered web research tools for scraping, searching, mapping, and crawling."""

import json
import os
import time

import requests

from serena.tools import Tool, ToolMarkerOptional


def _read_api_key() -> str | None:
    key_path = os.path.expanduser("~/.config/firecrawl/api_key")
    if os.path.exists(key_path):
        with open(key_path) as f:
            return f.read().strip()
    return os.environ.get("FIRECRAWL_API_KEY")


def _firecrawl_base_url() -> str:
    return os.environ.get("FIRECRAWL_BASE_URL", "http://192.168.0.4:3002")


def _firecrawl_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


class WebScrapeTool(Tool, ToolMarkerOptional):
    """Scrape a web page and return its content as markdown."""

    def apply(
        self,
        url: str,
        formats: str = "markdown",
        only_main_content: bool = True,
        max_answer_chars: int = -1,
    ) -> str:
        """
        Scrape a single web page using Firecrawl and return its content.

        :param url: the URL to scrape
        :param formats: comma-separated output formats (markdown, html, links)
        :param only_main_content: if True, extract only the main content (skip nav, footer, etc.)
        :param max_answer_chars: maximum characters in response (-1 for config default)
        :return: scraped page content in the requested format(s)
        """
        api_key = _read_api_key()
        if not api_key:
            return "Error: Firecrawl API key not found. Set ~/.config/firecrawl/api_key or FIRECRAWL_API_KEY env var."

        payload: dict = {
            "url": url,
            "formats": [f.strip() for f in formats.split(",")],
            "onlyMainContent": only_main_content,
        }

        try:
            resp = requests.post(
                f"{_firecrawl_base_url()}/v2/scrape",
                json=payload,
                headers=_firecrawl_headers(api_key),
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            if not data.get("success"):
                return f"Firecrawl scrape failed: {json.dumps(data)}"

            result_data = data.get("data", {})
            parts = []
            if "markdown" in result_data:
                parts.append(result_data["markdown"])
            elif "html" in result_data:
                parts.append(result_data["html"])

            metadata = result_data.get("metadata", {})
            if metadata:
                header = f"**Source:** {metadata.get('sourceURL', url)}\n**Title:** {metadata.get('title', 'N/A')}\n---\n"
                parts.insert(0, header)

            return self._limit_length(
                "\n".join(parts) if parts else json.dumps(result_data, indent=2),
                max_answer_chars,
            )

        except requests.exceptions.RequestException as e:
            return f"Firecrawl API error: {e}"


class WebSearchTool(Tool, ToolMarkerOptional):
    """Search the web and return structured results."""

    def apply(
        self,
        query: str,
        limit: int = 10,
        scrape_results: bool = False,
        max_answer_chars: int = -1,
    ) -> str:
        """
        Search the web using Firecrawl and return results.

        :param query: the search query
        :param limit: maximum number of results to return (default 10)
        :param scrape_results: if True, also scrape each result page for full content
        :param max_answer_chars: maximum characters in response (-1 for config default)
        :return: search results with title, URL, and description (and content if scrape_results=True)
        """
        api_key = _read_api_key()
        if not api_key:
            return "Error: Firecrawl API key not found. Set ~/.config/firecrawl/api_key or FIRECRAWL_API_KEY env var."

        payload: dict = {"query": query, "limit": limit}
        if scrape_results:
            payload["scrapeOptions"] = {"formats": ["markdown"]}

        try:
            resp = requests.post(
                f"{_firecrawl_base_url()}/v2/search",
                json=payload,
                headers=_firecrawl_headers(api_key),
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            if not data.get("success"):
                return f"Firecrawl search failed: {json.dumps(data)}"

            results = data.get("data", {})
            parts = []
            for source_type, items in results.items():
                if not isinstance(items, list):
                    continue
                parts.append(f"## {source_type.title()} Results\n")
                for item in items:
                    title = item.get("title", "N/A")
                    url = item.get("url", "N/A")
                    desc = item.get("description", item.get("snippet", ""))
                    parts.append(f"**{title}**\n{url}\n{desc}\n")

            return self._limit_length("\n".join(parts) if parts else "No results found.", max_answer_chars)

        except requests.exceptions.RequestException as e:
            return f"Firecrawl API error: {e}"


class WebMapTool(Tool, ToolMarkerOptional):
    """Discover all URLs on a website."""

    def apply(
        self,
        url: str,
        search: str = "",
        limit: int = 100,
        max_answer_chars: int = -1,
    ) -> str:
        """
        Map the structure of a website by discovering all its URLs.

        :param url: the root URL to map
        :param search: optional search term to filter and rank discovered URLs by relevance
        :param limit: maximum number of URLs to return (default 100)
        :param max_answer_chars: maximum characters in response (-1 for config default)
        :return: list of discovered URLs with titles and descriptions
        """
        api_key = _read_api_key()
        if not api_key:
            return "Error: Firecrawl API key not found. Set ~/.config/firecrawl/api_key or FIRECRAWL_API_KEY env var."

        payload: dict = {"url": url, "limit": limit}
        if search:
            payload["search"] = search

        try:
            resp = requests.post(
                f"{_firecrawl_base_url()}/v2/map",
                json=payload,
                headers=_firecrawl_headers(api_key),
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            if not data.get("success"):
                return f"Firecrawl map failed: {json.dumps(data)}"

            links = data.get("links", [])
            parts = [f"## Site Map: {url}\n**{len(links)} URLs discovered**\n"]
            for link in links:
                if isinstance(link, dict):
                    parts.append(f"- {link.get('url', 'N/A')} — {link.get('title', '')}")
                else:
                    parts.append(f"- {link}")

            return self._limit_length("\n".join(parts), max_answer_chars)

        except requests.exceptions.RequestException as e:
            return f"Firecrawl API error: {e}"


class WebCrawlTool(Tool, ToolMarkerOptional):
    """Crawl a website recursively and return all page contents."""

    def apply(
        self,
        url: str,
        limit: int = 5,
        max_depth: int = 2,
        poll_interval: int = 3,
        poll_timeout: int = 120,
        max_answer_chars: int = -1,
    ) -> str:
        """
        Start an async crawl of a website and poll until completion.
        Returns the combined content of all crawled pages.

        :param url: the starting URL to crawl
        :param limit: maximum number of pages to crawl (default 5, keep low to avoid long waits)
        :param max_depth: maximum crawl depth (default 2)
        :param poll_interval: seconds between status checks (default 3)
        :param poll_timeout: maximum seconds to wait for crawl completion (default 120)
        :param max_answer_chars: maximum characters in response (-1 for config default)
        :return: combined markdown content of all crawled pages
        """
        api_key = _read_api_key()
        if not api_key:
            return "Error: Firecrawl API key not found. Set ~/.config/firecrawl/api_key or FIRECRAWL_API_KEY env var."

        headers = _firecrawl_headers(api_key)
        base_url = _firecrawl_base_url()

        payload: dict = {
            "url": url,
            "limit": limit,
            "maxDiscoveryDepth": max_depth,
            "scrapeOptions": {"formats": ["markdown"]},
        }

        try:
            resp = requests.post(f"{base_url}/v2/crawl", json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            start_data = resp.json()

            if not start_data.get("success"):
                return f"Firecrawl crawl failed to start: {json.dumps(start_data)}"

            crawl_id = start_data["id"]
            elapsed = 0

            while elapsed < poll_timeout:
                time.sleep(poll_interval)
                elapsed += poll_interval

                status_resp = requests.get(f"{base_url}/v2/crawl/status/{crawl_id}", headers=headers, timeout=15)
                status_resp.raise_for_status()
                status_data = status_resp.json()

                status = status_data.get("status", "unknown")
                if status == "completed":
                    pages = status_data.get("data", [])
                    parts = [f"## Crawl Results: {url}\n**{len(pages)} pages crawled**\n"]
                    for page in pages:
                        source = page.get("metadata", {}).get("sourceURL", "unknown")
                        content = page.get("markdown", "")
                        parts.append(f"### {source}\n{content}\n---\n")
                    return self._limit_length("\n".join(parts), max_answer_chars)
                elif status == "failed":
                    return f"Crawl failed: {json.dumps(status_data)}"

            return f"Crawl timed out after {poll_timeout}s. Crawl ID: {crawl_id} — check status manually."

        except requests.exceptions.RequestException as e:
            return f"Firecrawl API error: {e}"
