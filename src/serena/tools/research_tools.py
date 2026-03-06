"""Firecrawl-powered web research tools for scraping, searching, mapping, and crawling."""

import json
import os

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
