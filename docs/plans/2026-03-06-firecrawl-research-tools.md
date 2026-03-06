# Firecrawl Research Tools — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Firecrawl-powered web research tools to Serena MCP and integrate an iterative research loop into the BMAD brainstorming workflow.

**Architecture:** Four new Serena MCP tools wrapping Firecrawl v2 API (scrape, search, map, crawl). A new `research` technique category in the brainstorming CSV. Workflow modifications to step-01 (pre-research option) and step-03 (iterative validation loop). BMAD agent sidecar and agent definitions updated.

**Tech Stack:** Python 3.11, requests (already a dependency), Firecrawl v2 REST API at `http://192.168.0.4:3002`, API key at `~/.config/firecrawl/api_key`

---

### Task 1: Create research_tools.py with WebScrapeTool

**Files:**
- Create: `src/serena/tools/research_tools.py`
- Create: `test/serena/test_research_tools.py`

**Step 1: Write the failing test**

Create `test/serena/test_research_tools.py`:

```python
"""Tests for Firecrawl research tools."""

import json
from unittest.mock import MagicMock, patch

import pytest


def _make_tool(tool_cls):
    """Create a tool instance with mocked agent."""
    tool = object.__new__(tool_cls)
    tool._agent = MagicMock()
    tool._agent.max_response_chars = 50000
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
```

**Step 2: Run test to verify it fails**

Run: `cd ~/git/serena-vanguard && uv run python -m pytest test/serena/test_research_tools.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'serena.tools.research_tools'`

**Step 3: Write implementation**

Create `src/serena/tools/research_tools.py`:

```python
"""Firecrawl-powered web research tools for scraping, searching, mapping, and crawling."""

import json
import os
import time

import requests

from serena.tools import SUCCESS_RESULT, Tool, ToolMarkerOptional


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

            return self._limit_length("\n".join(parts) if parts else json.dumps(result_data, indent=2), max_answer_chars)

        except requests.exceptions.RequestException as e:
            return f"Firecrawl API error: {e}"
```

**Step 4: Run test to verify it passes**

Run: `cd ~/git/serena-vanguard && uv run python -m pytest test/serena/test_research_tools.py -v`
Expected: PASS

**Step 5: Format and type-check**

Run: `cd ~/git/serena-vanguard && uv run poe format && uv run poe type-check`

**Step 6: Commit**

```bash
git add src/serena/tools/research_tools.py test/serena/test_research_tools.py
git commit -m "feat: add WebScrapeTool wrapping Firecrawl v2 scrape API"
```

---

### Task 2: Add WebSearchTool, WebMapTool, WebCrawlTool

**Files:**
- Modify: `src/serena/tools/research_tools.py`
- Modify: `test/serena/test_research_tools.py`

**Step 1: Write failing tests**

Append to `test/serena/test_research_tools.py`:

```python
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
```

**Step 2: Run test to verify failures**

Run: `cd ~/git/serena-vanguard && uv run python -m pytest test/serena/test_research_tools.py -v`
Expected: FAIL with `ImportError` for missing classes

**Step 3: Add implementations to research_tools.py**

Append to `src/serena/tools/research_tools.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `cd ~/git/serena-vanguard && uv run python -m pytest test/serena/test_research_tools.py -v`
Expected: PASS (all 5 tests)

**Step 5: Format and type-check**

Run: `cd ~/git/serena-vanguard && uv run poe format && uv run poe type-check`

**Step 6: Commit**

```bash
git add src/serena/tools/research_tools.py test/serena/test_research_tools.py
git commit -m "feat: add WebSearchTool, WebMapTool, WebCrawlTool for Firecrawl v2"
```

---

### Task 3: Register research tools in __init__.py and project.yml

**Files:**
- Modify: `src/serena/tools/__init__.py`
- Modify: `.serena/project.yml`

**Step 1: Add import to __init__.py**

In `src/serena/tools/__init__.py`, add after the last import:

```python
from .research_tools import *
```

**Step 2: Enable optional tools in project.yml**

In `.serena/project.yml`, add to the `included_optional_tools` list:

```yaml
included_optional_tools:
  - invoke_bmad_agent
  - list_bmad_agents
  - bmad_agent_info
  - web_scrape
  - web_search
  - web_map
  - web_crawl
```

**Step 3: Verify tools are importable**

Run: `cd ~/git/serena-vanguard && uv run python -c "from serena.tools.research_tools import WebScrapeTool, WebSearchTool, WebMapTool, WebCrawlTool; print('OK')"`
Expected: `OK`

**Step 4: Run full test suite**

Run: `cd ~/git/serena-vanguard && uv run poe format && uv run poe type-check && uv run poe test`
Expected: PASS

**Step 5: Commit**

```bash
git add src/serena/tools/__init__.py .serena/project.yml
git commit -m "feat: register Firecrawl research tools as optional MCP tools"
```

---

### Task 4: Add research technique to brainstorming CSV

**Files:**
- Modify: `_bmad/core/workflows/brainstorming/brain-methods.csv`

**Step 1: Append research techniques**

Add these lines at the end of `_bmad/core/workflows/brainstorming/brain-methods.csv`:

```csv
research,Web Research,"Search the web for real data on your brainstorming topic using Firecrawl - validate assumptions with evidence, discover existing solutions, find market data, and ground creative ideas in reality by searching for relevant information and analyzing results"
research,Competitive Analysis,"Scrape and analyze competitor websites and products to understand the landscape - use web_scrape and web_map to systematically explore competitor offerings, pricing, features, and positioning for informed ideation"
research,Literature Review,"Crawl documentation sites, research papers, and technical resources to build a knowledge base before ideating - use web_crawl to gather comprehensive information from authoritative sources"
```

**Step 2: Commit**

```bash
git add _bmad/core/workflows/brainstorming/brain-methods.csv
git commit -m "feat: add research technique category to brainstorming CSV"
```

---

### Task 5: Add pre-research option to step-01-session-setup.md

**Files:**
- Modify: `_bmad/core/workflows/brainstorming/steps/step-01-session-setup.md`

**Step 1: Add research option to approach selection**

In `_bmad/core/workflows/brainstorming/steps/step-01-session-setup.md`, replace the approach selection block:

```markdown
**Ready to explore technique approaches?**
[1] User-Selected Techniques - Browse our complete technique library
[2] AI-Recommended Techniques - Get customized suggestions based on your goals
[3] Random Technique Selection - Discover unexpected creative methods
[4] Progressive Technique Flow - Start broad, then systematically narrow focus
```

With:

```markdown
**Ready to explore technique approaches?**
[1] User-Selected Techniques - Browse our complete technique library
[2] AI-Recommended Techniques - Get customized suggestions based on your goals
[3] Random Technique Selection - Discover unexpected creative methods
[4] Progressive Technique Flow - Start broad, then systematically narrow focus
[5] Research-First - Investigate your topic with web search before ideating

Which approach appeals to you most? (Enter 1-5)
```

**Step 2: Add routing for option 5**

In the "Handle User Selection" section, add:

```markdown
- **If 5:** Load `./step-02e-research-first.md`
```

**Step 3: Commit**

```bash
git add _bmad/core/workflows/brainstorming/steps/step-01-session-setup.md
git commit -m "feat: add research-first approach option to brainstorming setup"
```

---

### Task 6: Create step-02e-research-first.md

**Files:**
- Create: `_bmad/core/workflows/brainstorming/steps/step-02e-research-first.md`

**Step 1: Create the research-first step file**

Create `_bmad/core/workflows/brainstorming/steps/step-02e-research-first.md`:

```markdown
# Step 2e: Research-First Approach

## MANDATORY EXECUTION RULES (READ FIRST):

- ✅ YOU ARE A RESEARCH FACILITATOR guiding evidence-based brainstorming
- 🔍 USE SERENA MCP TOOLS: web_search, web_scrape, web_map for research
- 📋 GATHER REAL DATA before entering creative ideation
- 💬 PRESENT FINDINGS in structured format for user review
- ✅ YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the `communication_language`

## EXECUTION PROTOCOLS:

- 🎯 Use web_search to explore the topic broadly first
- ⚠️ Present [B] back option and [C] continue options
- 💾 Update frontmatter with research findings
- 📖 Route to technique execution after research is complete
- 🚫 FORBIDDEN to skip research phase or generate findings without actual web searches

## YOUR TASK:

Guide the user through a structured web research phase before brainstorming begins.

## RESEARCH SEQUENCE:

### 1. Define Research Questions

"Great choice! Research-first brainstorming grounds your creativity in real-world evidence.

**Let's define what we need to investigate about [session_topic]:**

Based on your goals, I suggest researching:

1. **Landscape:** What already exists in this space?
2. **Evidence:** What data supports or challenges our assumptions?
3. **Gaps:** What problems remain unsolved?

**What specific questions do you want answered before we start ideating?**"

### 2. Execute Research

For each research question:

1. Use `web_search` with targeted queries
2. For promising results, use `web_scrape` to get full content
3. Summarize findings in structured format

**Present each finding:**

"**Research Finding #[N]:**
**Source:** [URL]
**Key Insight:** [2-3 sentence summary]
**Relevance to Session:** [How this informs our brainstorming]
**Implication:** [What this means for ideation direction]"

### 3. Research Synthesis

"**Research Phase Complete!**

**What We Discovered:**
- **[N] sources** analyzed across [topics]
- **Key themes:** [list emerging patterns]
- **Validated assumptions:** [what we confirmed]
- **Challenged assumptions:** [what surprised us]
- **Knowledge gaps:** [what we still don't know]

**Research-Informed Brainstorming Directions:**
1. [Direction based on finding 1]
2. [Direction based on finding 2]
3. [Direction based on gap analysis]

This research will serve as our foundation. All generated ideas can be validated against these findings.

**Ready to start ideating with this evidence base?**
[C] Continue to technique selection (with research context loaded)
[R] Research more — I want to investigate additional questions
[B] Back to approach selection"

### 4. Handle User Response

#### If [C] Continue:
- Update frontmatter with research findings summary
- Append research to document
- Set research as context for technique execution
- Load approach selection (steps [1]-[4]) for technique choice, with research as `context_file`

#### If [R] Research more:
- Return to step 2 for additional research questions

#### If [B] Back:
- Return to step-01-session-setup.md

### 5. Update Frontmatter and Document

**Update frontmatter:**

```yaml
---
selected_approach: 'research-first'
research_findings: [list of key findings]
stepsCompleted: [1, 2]
---
```

**Append to document:**

```markdown
## Pre-Research Phase

**Research Questions:**
- [Question 1]
- [Question 2]

**Findings:**

### Finding 1: [Title]
**Source:** [URL]
**Summary:** [Content]
**Implication:** [What this means]

### Finding 2: [Title]
...

### Research Synthesis
**Themes:** [patterns]
**Validated:** [confirmed assumptions]
**Challenged:** [surprising findings]
**Gaps:** [unknowns]
```

## SUCCESS METRICS:

✅ Research questions defined collaboratively with user
✅ Real web searches executed (not fabricated findings)
✅ Findings presented in structured, actionable format
✅ User reviews and approves research before ideation begins
✅ Research context carried forward into technique execution

## FAILURE MODES:

❌ Generating fake research without actual web searches
❌ Skipping user review of findings
❌ Not connecting findings to brainstorming directions
❌ Losing research context when transitioning to techniques

## NEXT STEP:

After research is complete and user confirms, route back to approach selection [1]-[4] for technique choice, with research loaded as session context.
```

**Step 2: Commit**

```bash
git add _bmad/core/workflows/brainstorming/steps/step-02e-research-first.md
git commit -m "feat: add research-first brainstorming step using Firecrawl"
```

---

### Task 7: Add iterative research loop to step-03

**Files:**
- Modify: `_bmad/core/workflows/brainstorming/steps/step-03-technique-execution.md`

**Step 1: Add [R] option to the technique completion menu**

In `_bmad/core/workflows/brainstorming/steps/step-03-technique-execution.md`, replace the menu:

```markdown
**What would you like to do next?**

[K] **Keep exploring this technique** - We're just getting warmed up!
[T] **Try a different technique** - Fresh perspective on the same topic
[A] **Go deeper on a specific idea** - Develop a promising concept further (Advanced Elicitation)
[B] **Take a quick break** - Pause and return with fresh energy
[C] **Move to organization** - Only when you feel we've thoroughly explored
```

With:

```markdown
**What would you like to do next?**

[K] **Keep exploring this technique** - We're just getting warmed up!
[T] **Try a different technique** - Fresh perspective on the same topic
[R] **Research & validate** - Search the web to validate or challenge current ideas
[A] **Go deeper on a specific idea** - Develop a promising concept further (Advanced Elicitation)
[B] **Take a quick break** - Pause and return with fresh energy
[C] **Move to organization** - Only when you feel we've thoroughly explored
```

**Step 2: Add [R] handler section**

After the existing handler for option [A], add:

```markdown
#### If 'R' (Research & Validate):

**Research Validation Loop:**

"**Let's put our ideas to the test with real-world evidence!**

**Ideas to Validate:**
[List the top 3-5 most promising ideas generated so far]

**For each idea, I'll:**
1. Search the web for existing implementations or evidence
2. Report what I find — supporting evidence, contradictions, or gaps
3. You decide: strengthen the idea, pivot it, or discard it

**Which idea should we investigate first?** (Or tell me a specific question to research)"

**Execute Research:**
1. Use `web_search` with queries derived from the selected idea
2. Optionally `web_scrape` promising results for deeper analysis
3. Present findings using the IDEA FORMAT TEMPLATE:

**[Research Validation #X]**: [Idea Being Validated]
_Finding_: [What the research revealed]
_Impact_: [How this changes/strengthens/challenges the idea]
_Action_: [Strengthen / Pivot / Discard / Needs More Research]

**After each validation:**
"**Validation complete for [idea].** Result: [Strengthened/Pivoted/Discarded]

**What's next?**
- Validate another idea
- Return to ideation with new insights
- Research a new question that emerged"

**Stay in Step 3** after research — return to the facilitation loop with enriched context.
```

**Step 3: Commit**

```bash
git add _bmad/core/workflows/brainstorming/steps/step-03-technique-execution.md
git commit -m "feat: add iterative research validation loop [R] to brainstorming execution"
```

---

### Task 8: Update BMAD agent sidecar and agent definitions

**Files:**
- Modify: `_bmad/_memory/serena-tools-reference.md`
- Modify: All Tier 1 agent `<mcp-tools>` blocks (9 agents)
- Modify: All Tier 2 agent `<mcp-tools>` blocks (9 agents)

**Step 1: Add Research Tools section to sidecar**

In `_bmad/_memory/serena-tools-reference.md`, add a new section after "Workflow Tools":

```markdown
## Research Tools (web intelligence)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `web_scrape` | Scrape a web page for content | `url`, `formats`, `only_main_content` |
| `web_search` | Search the web by query | `query`, `limit`, `scrape_results` |
| `web_map` | Discover all URLs on a website | `url`, `search`, `limit` |
| `web_crawl` | Recursively crawl a website | `url`, `limit`, `max_depth`, `poll_timeout` |
```

Also add to the "Usage Patterns" section:

```markdown
**Research before editing:**
1. `web_search` to find existing solutions or documentation
2. `web_scrape` to extract detailed content from relevant pages
3. `web_map` to understand a documentation site structure
4. `web_crawl` for comprehensive content gathering (keep limit low)
```

**Step 2: Add research tools to Tier 1 agent `<available-tools>` blocks**

In each Tier 1 agent file, add `web_scrape, web_search, web_map, web_crawl` to the `<available-tools>` list.

Files to modify:
- `_bmad/bmm/agents/dev.md`
- `_bmad/bmm/agents/quick-flow-solo-dev.md`
- `_bmad/bmm/agents/architect.md`
- `_bmad/bmm/agents/qa.md`
- `_bmad/gds/agents/game-dev.md`
- `_bmad/gds/agents/game-solo-dev.md`
- `_bmad/gds/agents/game-architect.md`
- `_bmad/gds/agents/game-qa.md`
- `_bmad/tea/agents/tea.md`

**Step 3: Add read-only research tools to Tier 2 agent `<available-tools>` blocks**

In each Tier 2 agent file, add `web_scrape, web_search` to the `<available-tools>` list.

Files to modify:
- `_bmad/bmm/agents/analyst.md`
- `_bmad/bmm/agents/pm.md`
- `_bmad/bmm/agents/sm.md`
- `_bmad/bmm/agents/ux-designer.md`
- `_bmad/bmm/agents/tech-writer/tech-writer.md`
- `_bmad/gds/agents/game-designer.md`
- `_bmad/gds/agents/game-scrum-master.md`
- `_bmad/gds/agents/tech-writer/tech-writer.md`
- `_bmad/core/agents/bmad-master.md`

**Step 4: Commit**

```bash
git add _bmad/_memory/serena-tools-reference.md _bmad/bmm/agents/ _bmad/gds/agents/ _bmad/tea/agents/ _bmad/core/agents/
git commit -m "feat: add Firecrawl research tools to BMAD agent sidecar and all agent tiers"
```

---

### Task 9: Final verification

**Files:**
- Verify: all tests pass
- Verify: MCP server starts

**Step 1: Run full test suite**

Run: `cd ~/git/serena-vanguard && uv run poe format && uv run poe type-check && uv run poe test`
Expected: PASS

**Step 2: Verify MCP server starts with new tools**

Run: `cd ~/git/serena-vanguard && timeout 5 uv run serena-mcp-server 2>&1 | head -20 || true`
Expected: Server starts without import errors

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: verify Firecrawl research tools integration"
```

---

## Task Dependency Graph

```
Task 1 (WebScrapeTool) ──→ Task 2 (Search+Map+Crawl) ──→ Task 3 (registration)
                                                                    ↓
Task 4 (CSV technique) ←── independent ──────────────────── Task 3
Task 5 (step-01 option) ←── independent ─────────────────── Task 3
Task 6 (step-02e research-first) ←── depends on ────────── Task 5
Task 7 (step-03 iterative loop) ←── independent ────────── Task 3
Task 8 (BMAD agents) ←── depends on ────────────────────── Task 3
Task 9 (final verification) ←── depends on all ─────────── Tasks 1-8
```

Tasks 4, 5, 7 are independent markdown-only changes (no Python).
Tasks 1-3 are sequential Python implementation.
Task 6 depends on Task 5.
Task 8 depends on Task 3.
