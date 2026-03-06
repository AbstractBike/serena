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
