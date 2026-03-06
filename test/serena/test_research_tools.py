"""Tests for Firecrawl research tools."""

from unittest.mock import MagicMock, patch


def _make_tool(tool_cls):
    """Create a tool instance with mocked agent."""
    tool = object.__new__(tool_cls)
    tool.agent = MagicMock()
    tool.agent.serena_config.default_max_tool_answer_chars = 50000
    return tool


class TestWebScrapeTool:
    def test_scrape_success(self):
        from serena.tools.research_tools import WebScrapeTool

        tool = _make_tool(WebScrapeTool)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "markdown": "# Test Page\nContent here",
                "metadata": {"title": "Test Page", "sourceURL": "https://example.com"},
            },
        }
        mock_response.raise_for_status = MagicMock()

        with (
            patch("serena.tools.research_tools._read_api_key", return_value="fc-test-key"),
            patch("serena.tools.research_tools._firecrawl_base_url", return_value="http://localhost:3002"),
            patch("requests.post", return_value=mock_response) as mock_post,
        ):
            result = tool.apply(url="https://example.com")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["url"] == "https://example.com"
        assert "Test Page" in result

    def test_scrape_missing_api_key(self):
        from serena.tools.research_tools import WebScrapeTool

        tool = _make_tool(WebScrapeTool)

        with patch("serena.tools.research_tools._read_api_key", return_value=None):
            result = tool.apply(url="https://example.com")

        assert "API key" in result.lower() or "error" in result.lower()


class TestWebSearchTool:
    def test_search_success(self):
        from serena.tools.research_tools import WebSearchTool

        tool = _make_tool(WebSearchTool)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "web": [
                    {"url": "https://example.com/1", "title": "Result 1", "description": "Desc 1", "position": 1},
                    {"url": "https://example.com/2", "title": "Result 2", "description": "Desc 2", "position": 2},
                ],
            },
        }
        mock_response.raise_for_status = MagicMock()

        with (
            patch("serena.tools.research_tools._read_api_key", return_value="fc-test-key"),
            patch("serena.tools.research_tools._firecrawl_base_url", return_value="http://localhost:3002"),
            patch("requests.post", return_value=mock_response) as mock_post,
        ):
            result = tool.apply(query="test query")

        mock_post.assert_called_once()
        assert "Result 1" in result


class TestWebMapTool:
    def test_map_success(self):
        from serena.tools.research_tools import WebMapTool

        tool = _make_tool(WebMapTool)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "links": [
                {"url": "https://example.com/page1", "title": "Page 1"},
                {"url": "https://example.com/page2", "title": "Page 2"},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with (
            patch("serena.tools.research_tools._read_api_key", return_value="fc-test-key"),
            patch("serena.tools.research_tools._firecrawl_base_url", return_value="http://localhost:3002"),
            patch("requests.post", return_value=mock_response) as mock_post,
        ):
            result = tool.apply(url="https://example.com")

        mock_post.assert_called_once()
        assert "page1" in result


class TestWebCrawlTool:
    def test_crawl_start_and_poll(self):
        from serena.tools.research_tools import WebCrawlTool

        tool = _make_tool(WebCrawlTool)

        start_response = MagicMock()
        start_response.status_code = 200
        start_response.json.return_value = {
            "success": True,
            "id": "crawl-123",
            "url": "http://localhost:3002/v2/crawl/crawl-123",
        }
        start_response.raise_for_status = MagicMock()

        status_response = MagicMock()
        status_response.status_code = 200
        status_response.json.return_value = {
            "success": True,
            "status": "completed",
            "completed": 2,
            "total": 2,
            "data": [
                {"markdown": "# Page 1\nContent", "metadata": {"sourceURL": "https://example.com/1"}},
                {"markdown": "# Page 2\nContent", "metadata": {"sourceURL": "https://example.com/2"}},
            ],
        }
        status_response.raise_for_status = MagicMock()

        with (
            patch("serena.tools.research_tools._read_api_key", return_value="fc-test-key"),
            patch("serena.tools.research_tools._firecrawl_base_url", return_value="http://localhost:3002"),
            patch("requests.post", return_value=start_response),
            patch("requests.get", return_value=status_response),
            patch("time.sleep"),
        ):
            result = tool.apply(url="https://example.com", limit=2)

        assert "Page 1" in result
        assert "Page 2" in result
