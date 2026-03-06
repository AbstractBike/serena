# serena-vanguard Remaining Tasks — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete serena-vanguard fork: add fuzzy matching, line-level edit tools, remove JetBrains backend, integrate TreeSitter into agent, register tools, and add Serena MCP tools to all BMAD agents.

**Architecture:** Two-backend Serena (LSP primary + TreeSitter offline fallback). New `edit_tools.py` with line-level operations. JetBrains backend fully removed. BMAD agents receive `<mcp-tools>` blocks tailored to their role tier.

**Tech Stack:** Python 3.11, py-tree-sitter, mcp, solidlsp (existing), BMAD 6.0.4 (markdown agent definitions)

---

### Task 4: Port fuzzy matching

**Files:**
- Create: `src/serena/backends/treesitter/fuzzy.py`
- Test: `test/serena/backends/test_fuzzy.py`

**Step 1: Write the failing test**

Create `test/serena/backends/test_fuzzy.py`:

```python
from serena.backends.treesitter.engine import SymbolBounds
from serena.backends.treesitter.fuzzy import MatchType, find_fuzzy_matches, levenshtein, camel_case_matches


def _sym(name: str) -> SymbolBounds:
    return SymbolBounds(name=name, kind="function", line=1, end_line=5)


def test_exact_match_first():
    symbols = [_sym("connect"), _sym("Connect"), _sym("conn")]
    results = find_fuzzy_matches("connect", symbols, max_distance=3)
    assert results[0].match_type == MatchType.EXACT
    assert results[0].symbol.name == "connect"
    assert results[1].match_type == MatchType.CASE_INSENSITIVE
    assert results[1].symbol.name == "Connect"


def test_camel_case_matching():
    symbols = [_sym("GetSymbol"), _sym("GlobalState"), _sym("get_symbols_overview")]
    results = find_fuzzy_matches("GS", symbols, max_distance=5)
    camel_names = [r.symbol.name for r in results if r.match_type == MatchType.CAMEL_CASE]
    assert "GetSymbol" in camel_names
    assert "GlobalState" in camel_names

    results = find_fuzzy_matches("gso", symbols, max_distance=5)
    camel_names = [r.symbol.name for r in results if r.match_type == MatchType.CAMEL_CASE]
    assert "get_symbols_overview" in camel_names


def test_levenshtein():
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein("", "abc") == 3
    assert levenshtein("abc", "abc") == 0


def test_levenshtein_fuzzy():
    symbols = [_sym("process"), _sym("progres"), _sym("unrelated")]
    results = find_fuzzy_matches("progress", symbols, max_distance=3)
    fuzzy = [(r.symbol.name, r.distance) for r in results if r.match_type == MatchType.FUZZY]
    assert any(n == "progres" and d == 1 for n, d in fuzzy)
    assert any(n == "process" and d == 2 for n, d in fuzzy)
    assert not any(n == "unrelated" for n, _ in fuzzy)


def test_camel_case_snake():
    assert camel_case_matches("gso", "get_symbols_overview")
    assert not camel_case_matches("xyz", "get_symbols_overview")


def test_camel_case_upper():
    assert camel_case_matches("GS", "GetSymbol")
    assert camel_case_matches("gs", "GetSymbol")
```

**Step 2: Run test to verify it fails**

Run: `cd ~/git/serena-vanguard && uv run python -m pytest test/serena/backends/test_fuzzy.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'serena.backends.treesitter.fuzzy'`

**Step 3: Write implementation**

Create `src/serena/backends/treesitter/fuzzy.py`:

```python
"""Fuzzy symbol matching: Exact > CaseInsensitive > CamelCase > Levenshtein.

Port of codegate src/symbols/fuzzy.rs.
"""

from dataclasses import dataclass
from enum import IntEnum

from serena.backends.treesitter.engine import SymbolBounds


class MatchType(IntEnum):
    EXACT = 0
    CASE_INSENSITIVE = 1
    CAMEL_CASE = 2
    FUZZY = 3


@dataclass
class FuzzyMatch:
    symbol: SymbolBounds
    distance: int
    match_type: MatchType


def levenshtein(a: str, b: str) -> int:
    """Standard Levenshtein edit distance."""
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    curr = [0] * (len(b) + 1)

    for i, ca in enumerate(a):
        curr[0] = i + 1
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr[j + 1] = min(prev[j] + cost, prev[j + 1] + 1, curr[j] + 1)
        prev, curr = curr, prev

    return prev[len(b)]


def _extract_initials(name: str) -> str:
    if "_" in name:
        return "".join(part[0] for part in name.split("_") if part)
    initials = []
    for i, c in enumerate(name):
        if i == 0 or c.isupper():
            initials.append(c)
    return "".join(initials)


def camel_case_matches(query: str, candidate: str) -> bool:
    """Check if query matches CamelCase or snake_case initials of candidate."""
    if not query:
        return False
    initials = _extract_initials(candidate)
    return initials.lower().startswith(query.lower())


def find_fuzzy_matches(
    query: str,
    symbols: list[SymbolBounds],
    max_distance: int,
) -> list[FuzzyMatch]:
    """Find fuzzy matches sorted by relevance."""
    query_lower = query.lower()
    matches: list[FuzzyMatch] = []

    for symbol in symbols:
        name = symbol.name
        if name == query:
            matches.append(FuzzyMatch(symbol=symbol, distance=0, match_type=MatchType.EXACT))
        elif name.lower() == query_lower:
            matches.append(FuzzyMatch(symbol=symbol, distance=0, match_type=MatchType.CASE_INSENSITIVE))
        elif camel_case_matches(query, name):
            matches.append(FuzzyMatch(symbol=symbol, distance=0, match_type=MatchType.CAMEL_CASE))
        else:
            dist = levenshtein(query, name)
            if dist <= max_distance:
                matches.append(FuzzyMatch(symbol=symbol, distance=dist, match_type=MatchType.FUZZY))

    matches.sort(key=lambda m: (m.match_type, m.distance, m.symbol.name))
    return matches
```

**Step 4: Run test to verify it passes**

Run: `cd ~/git/serena-vanguard && uv run python -m pytest test/serena/backends/test_fuzzy.py -v`
Expected: PASS

**Step 5: Format and type-check**

Run: `cd ~/git/serena-vanguard && uv run poe format && uv run poe type-check`

**Step 6: Commit**

```bash
git add src/serena/backends/treesitter/fuzzy.py test/serena/backends/test_fuzzy.py
git commit -m "feat: add fuzzy symbol matching (Levenshtein + CamelCase)"
```

---

### Task 5: Add edit_tools.py (replace_lines, delete_lines, insert_at_line)

**Files:**
- Create: `src/serena/tools/edit_tools.py`
- Test: `test/serena/test_edit_tools.py`

**Step 1: Write the failing test**

Create `test/serena/test_edit_tools.py`:

```python
import os
import tempfile

from serena.tools.edit_tools import replace_lines_in_file, delete_lines_in_file, insert_at_line_in_file


def test_replace_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("line1\nline2\nline3\nline4\n")
        path = f.name
    try:
        replace_lines_in_file(path, 2, 3, "replaced2\nreplaced3\n")
        result = open(path).read()
        assert result == "line1\nreplaced2\nreplaced3\nline4\n"
    finally:
        os.unlink(path)


def test_delete_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("line1\nline2\nline3\nline4\n")
        path = f.name
    try:
        delete_lines_in_file(path, 2, 3)
        result = open(path).read()
        assert result == "line1\nline4\n"
    finally:
        os.unlink(path)


def test_insert_at_line():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("line1\nline2\n")
        path = f.name
    try:
        insert_at_line_in_file(path, 2, "inserted\n")
        result = open(path).read()
        assert result == "line1\ninserted\nline2\n"
    finally:
        os.unlink(path)
```

**Step 2: Run test to verify it fails**

Run: `cd ~/git/serena-vanguard && uv run python -m pytest test/serena/test_edit_tools.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write implementation**

Create `src/serena/tools/edit_tools.py`:

```python
"""Line-level file editing tools and syntax validation.

These tools are available with both LSP and TreeSitter backends.
"""

import os
import subprocess

from serena.tools import SUCCESS_RESULT, Tool, ToolMarkerCanEdit, ToolMarkerOptional


def replace_lines_in_file(path: str, start_line: int, end_line: int, new_content: str) -> None:
    """Replace lines start_line..end_line (1-based, inclusive) with new_content."""
    with open(path) as f:
        lines = f.readlines()
    before = lines[: start_line - 1]
    after = lines[end_line:]
    new_lines = new_content.splitlines(keepends=True)
    if new_content and not new_content.endswith("\n"):
        new_lines[-1] += "\n"
    with open(path, "w") as f:
        f.writelines(before + new_lines + after)


def delete_lines_in_file(path: str, start_line: int, end_line: int) -> None:
    """Delete lines start_line..end_line (1-based, inclusive)."""
    with open(path) as f:
        lines = f.readlines()
    before = lines[: start_line - 1]
    after = lines[end_line:]
    with open(path, "w") as f:
        f.writelines(before + after)


def insert_at_line_in_file(path: str, line: int, content: str) -> None:
    """Insert content before the given line (1-based)."""
    with open(path) as f:
        lines = f.readlines()
    new_lines = content.splitlines(keepends=True)
    if content and not content.endswith("\n"):
        new_lines[-1] += "\n"
    lines[line - 1 : line - 1] = new_lines
    with open(path, "w") as f:
        f.writelines(lines)


class ReplaceLinesTool(Tool, ToolMarkerCanEdit):
    """Replace a range of lines in a file."""

    def apply(self, relative_path: str, start_line: int, end_line: int, new_content: str) -> str:
        """
        Replace lines start_line through end_line (1-based, inclusive) with new_content.

        :param relative_path: relative path to the file
        :param start_line: first line to replace (1-based)
        :param end_line: last line to replace (1-based, inclusive)
        :param new_content: replacement text
        """
        abs_path = os.path.join(self.get_project_root(), relative_path)
        replace_lines_in_file(abs_path, start_line, end_line, new_content)
        return SUCCESS_RESULT


class DeleteLinesTool(Tool, ToolMarkerCanEdit):
    """Delete a range of lines from a file."""

    def apply(self, relative_path: str, start_line: int, end_line: int) -> str:
        """
        Delete lines start_line through end_line (1-based, inclusive).

        :param relative_path: relative path to the file
        :param start_line: first line to delete (1-based)
        :param end_line: last line to delete (1-based, inclusive)
        """
        abs_path = os.path.join(self.get_project_root(), relative_path)
        delete_lines_in_file(abs_path, start_line, end_line)
        return SUCCESS_RESULT


class InsertAtLineTool(Tool, ToolMarkerCanEdit):
    """Insert text at a specific line in a file."""

    def apply(self, relative_path: str, line: int, content: str) -> str:
        """
        Insert content before the given line number (1-based).

        :param relative_path: relative path to the file
        :param line: line number before which to insert (1-based)
        :param content: text to insert
        """
        abs_path = os.path.join(self.get_project_root(), relative_path)
        insert_at_line_in_file(abs_path, line, content)
        return SUCCESS_RESULT


class ValidateSyntaxTool(Tool, ToolMarkerOptional):
    """Validate syntax of a source file using tree-sitter."""

    def apply(self, relative_path: str) -> str:
        """
        Parse the file with tree-sitter and report any syntax errors.

        :param relative_path: relative path to the file to validate
        """
        from serena.backends.treesitter.engine import SymbolEngine

        abs_path = os.path.join(self.get_project_root(), relative_path)
        ext = os.path.splitext(abs_path)[1].lstrip(".")

        with open(abs_path) as f:
            source = f.read()

        engine = SymbolEngine()
        result = engine._get_parser_and_query(ext)
        if result is None:
            return f"Unsupported file extension: {ext}"

        parser, _lang, _query = result
        tree = parser.parse(source.encode())

        errors: list[str] = []

        def _collect_errors(node) -> None:  # type: ignore[no-untyped-def]
            if node.type == "ERROR" or node.is_missing:
                errors.append(f"line {node.start_point[0] + 1}: syntax error at '{node.text.decode()[:50]}'")
            for child in node.children:
                _collect_errors(child)

        _collect_errors(tree.root_node)

        if not errors:
            return "Syntax OK"
        return "Syntax errors found:\n" + "\n".join(errors)


class SearchStructuralTool(Tool, ToolMarkerOptional):
    """Structural code search using ast-grep (sg)."""

    def apply(self, pattern: str, relative_path: str = ".") -> str:
        """
        Search for structural code patterns using ast-grep.
        Requires `sg` binary in PATH.

        :param pattern: ast-grep pattern to search for
        :param relative_path: directory or file to search in (relative to project root)
        """
        search_path = os.path.join(self.get_project_root(), relative_path)
        try:
            result = subprocess.run(
                ["sg", "--pattern", pattern, search_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0 and result.stderr:
                return f"ast-grep error: {result.stderr.strip()}"
            return result.stdout if result.stdout else "No matches found."
        except FileNotFoundError:
            return "ast-grep (sg) not found in PATH. Install it to use structural search."
```

**Step 4: Run test to verify it passes**

Run: `cd ~/git/serena-vanguard && uv run python -m pytest test/serena/test_edit_tools.py -v`
Expected: PASS

**Step 5: Format and type-check**

Run: `cd ~/git/serena-vanguard && uv run poe format && uv run poe type-check`

**Step 6: Commit**

```bash
git add src/serena/tools/edit_tools.py test/serena/test_edit_tools.py
git commit -m "feat: add line-level edit tools, validate_syntax, search_structural"
```

---

### Task 6: Remove JetBrains backend, add TreeSitter to LanguageBackend

**Files:**
- Modify: `src/serena/config/serena_config.py`
- Modify: `src/serena/tools/__init__.py`
- Modify: `src/serena/code_editor.py`
- Modify: `src/serena/agent.py`
- Modify: `src/serena/dashboard.py`
- Modify: `src/serena/tools/tools_base.py`
- Delete: `src/serena/tools/jetbrains_tools.py`
- Delete: `src/serena/jetbrains/` (entire directory)
- Delete: `test/serena/test_jetbrains_plugin_client.py` (if exists)

**Step 1: Read all files that reference JetBrains**

Run: `cd ~/git/serena-vanguard && grep -rl "jetbrains\|JetBrains\|JETBRAINS" src/ test/ --include="*.py"`

Use this output to identify every file that needs modification. The list above is the expected result — verify before proceeding.

**Step 2: Update LanguageBackend enum in serena_config.py**

In `src/serena/config/serena_config.py`, replace:
```python
    JETBRAINS = "JetBrains"
```
with:
```python
    TREE_SITTER = "TreeSitter"
```

Remove any docstring about JetBrains IDE plugin. Add:
```python
    """
    Use tree-sitter for offline symbol extraction (no language server daemon needed).
    """
```

Also remove any auto-detection logic that sets `language_backend = LanguageBackend.JETBRAINS`.

**Step 3: Update tools/__init__.py**

In `src/serena/tools/__init__.py`, replace:
```python
from .jetbrains_tools import *
```
with:
```python
from .edit_tools import *
```

**Step 4: Remove JetBrains files**

```bash
rm -rf src/serena/jetbrains/
rm -f src/serena/tools/jetbrains_tools.py
rm -f test/serena/test_jetbrains_plugin_client.py
```

**Step 5: Fix code_editor.py**

In `src/serena/code_editor.py`:
- Remove `from serena.jetbrains.jetbrains_plugin_client import JetBrainsPluginClient` (if present)
- Remove `JetBrainsCodeEditor` class entirely (if present)
- Keep `LanguageServerCodeEditor` and `CodeEditor` base class

**Step 6: Fix agent.py references**

In `src/serena/agent.py`:
- Remove the `if self.serena_config.language_backend == LanguageBackend.JETBRAINS:` block
- Update imports — remove any `JetBrains` imports
- Verify `is_using_language_server()` returns `self.serena_config.language_backend == LanguageBackend.LSP`

**Step 7: Fix dashboard.py references**

In `src/serena/dashboard.py`, remove or replace any `jetbrains_mode` references.

**Step 8: Fix tools_base.py**

In `src/serena/tools/tools_base.py`:
- Remove any JetBrains branch from `create_code_editor()`
- Remove JetBrains imports

**Step 9: Verify no remaining JetBrains references**

Run: `cd ~/git/serena-vanguard && grep -rl "jetbrains\|JetBrains\|JETBRAINS" src/ test/ --include="*.py"`
Expected: No output (no remaining references)

**Step 10: Run tests**

Run: `cd ~/git/serena-vanguard && uv run poe format && uv run poe type-check && uv run poe test`
Expected: PASS (JetBrains tests deleted, no import errors)

**Step 11: Commit**

```bash
git add -A
git commit -m "refactor: remove JetBrains backend, add TreeSitter to LanguageBackend enum"
```

---

### Task 7: Integrate TreeSitter tools into agent

**Files:**
- Modify: `src/serena/tools/tools_base.py`
- Modify: `src/serena/code_editor.py`
- Modify: `src/serena/agent.py`

**Step 1: Read current code_editor.py, tools_base.py, agent.py**

Read these files fully to understand current `CodeEditor` interface, `Component.create_code_editor()`, and backend selection logic.

**Step 2: Add TreeSitterCodeEditor to code_editor.py**

Add a `TreeSitterCodeEditor` class that uses `SymbolEngine` + `AstCache` for symbol resolution. It must implement the same `CodeEditor` interface as `LanguageServerCodeEditor` — the key method is resolving symbol names to line ranges using `SymbolEngine.find_symbol()`.

**Step 3: Update create_code_editor() in tools_base.py**

Add a TreeSitter branch:
```python
def create_code_editor(self) -> "CodeEditor":
    from ..code_editor import LanguageServerCodeEditor, TreeSitterCodeEditor
    if self.agent.is_using_language_server():
        return LanguageServerCodeEditor(self.create_language_server_symbol_retriever(), agent=self.agent)
    else:
        return TreeSitterCodeEditor(project=self.project, agent=self.agent)
```

**Step 4: Update agent.py backend selection**

Add TreeSitter branch to replace the deleted JetBrains block:
```python
if backend == LanguageBackend.TREE_SITTER:
    # Register TreeSitter symbol tools, no language server manager needed
```

**Step 5: Run tests**

Run: `cd ~/git/serena-vanguard && uv run poe format && uv run poe type-check && uv run poe test`
Expected: PASS

**Step 6: Commit**

```bash
git add src/serena/agent.py src/serena/tools/tools_base.py src/serena/code_editor.py
git commit -m "feat: integrate TreeSitter backend into agent and code editor"
```

---

### Task 8: Register edit_tools in ToolSet and verify

**Files:**
- Verify: `src/serena/tools/__init__.py` (already updated in Task 6)

**Step 1: Verify edit_tools are importable**

Run: `cd ~/git/serena-vanguard && uv run python -c "from serena.tools.edit_tools import ReplaceLinesTool, DeleteLinesTool, InsertAtLineTool, ValidateSyntaxTool, SearchStructuralTool; print('OK')"`
Expected: `OK`

**Step 2: Run full test suite**

Run: `cd ~/git/serena-vanguard && uv run poe format && uv run poe type-check && uv run poe test`
Expected: PASS

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: verify edit_tools registration in ToolSet"
```

---

### Task 9: Create Serena tools reference sidecar for BMAD

**Files:**
- Create: `_bmad/_memory/serena-tools-reference.md`

**Step 1: Create the sidecar file**

Create `_bmad/_memory/serena-tools-reference.md`:

```markdown
# Serena-Vanguard MCP Tools Reference

Use these tools via MCP when the Serena-Vanguard server is connected.
For full parameter details, invoke the tool with no arguments to see its schema.

## Symbol Tools (code intelligence)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `find_symbol` | Find symbol by name (supports fuzzy matching) | `name_path`, `relative_path`, `include_body`, `depth` |
| `get_symbols_overview` | List all symbols in a file | `relative_path` |
| `find_referencing_symbols` | Find all references to a symbol | `name_path`, `relative_path` |
| `replace_symbol_body` | Replace entire symbol definition | `name_path`, `relative_path`, `new_body` |
| `insert_before_symbol` | Insert code before a symbol | `name_path`, `relative_path`, `content` |
| `insert_after_symbol` | Insert code after a symbol | `name_path`, `relative_path`, `content` |
| `rename_symbol` | Rename symbol and update all references | `name_path`, `relative_path`, `new_name` |

## Line-Level Edit Tools

| Tool | Purpose | Key Params |
|------|---------|------------|
| `replace_lines` | Replace line range N-M | `relative_path`, `start_line`, `end_line`, `new_content` |
| `delete_lines` | Delete line range N-M | `relative_path`, `start_line`, `end_line` |
| `insert_at_line` | Insert text before line N | `relative_path`, `line`, `content` |
| `validate_syntax` | Check syntax via tree-sitter | `relative_path` |
| `search_structural` | Structural search via ast-grep | `pattern`, `relative_path` |

## File Tools

| Tool | Purpose | Key Params |
|------|---------|------------|
| `read_file` | Read file or line range | `relative_path`, `start_line`, `end_line` |
| `create_text_file` | Create new file | `relative_path`, `content` |
| `replace_content` | Regex or string replacement in file | `relative_path`, `pattern`, `replacement` |
| `list_dir` | List directory contents | `relative_path`, `recursive` |
| `find_file` | Find files by glob mask | `file_mask`, `relative_path` |
| `search_for_pattern` | Search text patterns in codebase | `pattern`, `relative_path` |

## Memory Tools

| Tool | Purpose | Key Params |
|------|---------|------------|
| `read_memory` | Read a project memory | `memory_name` |
| `write_memory` | Create or overwrite memory | `memory_name`, `content` |
| `edit_memory` | Edit existing memory | `memory_name`, `edits` |
| `list_memories` | List all project memories | — |

## Workflow Tools

| Tool | Purpose | Key Params |
|------|---------|------------|
| `onboarding` | Analyze and document a new project | — |

## Usage Patterns

**Navigate before editing:**
1. `get_symbols_overview` to see file structure
2. `find_symbol` with `include_body=False` to locate candidates
3. `find_symbol` with `include_body=True` to read specific symbol

**Choose the right edit tool:**
- `replace_symbol_body` — replacing an entire function/class/method
- `replace_lines` — surgical change to a few lines within a symbol
- `insert_at_line` — adding new code at a specific position
- `delete_lines` — removing a block of code

**After every edit:**
- `validate_syntax` to catch syntax errors immediately
- Run project tests

**Impact analysis before refactoring:**
- `find_referencing_symbols` to find all callers/users
- `search_for_pattern` for text-based search (comments, strings, config)
```

**Step 2: Commit**

```bash
git add _bmad/_memory/serena-tools-reference.md
git commit -m "docs: add Serena tools reference sidecar for BMAD agents"
```

---

### Task 10: Add `<mcp-tools>` to Tier 1 BMAD agents (full access)

**Files:**
- Modify: `_bmad/bmm/agents/dev.md`
- Modify: `_bmad/bmm/agents/quick-flow-solo-dev.md`
- Modify: `_bmad/bmm/agents/architect.md`
- Modify: `_bmad/bmm/agents/qa.md`
- Modify: `_bmad/gds/agents/game-dev.md`
- Modify: `_bmad/gds/agents/game-solo-dev.md`
- Modify: `_bmad/gds/agents/game-architect.md`
- Modify: `_bmad/gds/agents/game-qa.md`
- Modify: `_bmad/tea/agents/tea.md`

**Step 1: Add `<mcp-tools>` block to `_bmad/bmm/agents/dev.md`**

Insert the following block after `</persona>` and before `<prompts>` (or `<menu>` if no prompts):

```xml
  <mcp-tools tier="full" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
    <usage-strategy>
      Use Serena-Vanguard MCP tools for all code operations. Never edit files by raw text manipulation when symbolic tools are available.
      1. Navigate: get_symbols_overview then find_symbol(include_body=False) then find_symbol(include_body=True)
      2. Edit: replace_symbol_body for whole functions, replace_lines for surgical changes
      3. Verify: validate_syntax after every edit, run tests after every task
      4. Search: search_for_pattern for text, find_referencing_symbols for impact analysis
    </usage-strategy>
    <available-tools>
      find_symbol, get_symbols_overview, find_referencing_symbols,
      replace_symbol_body, insert_before_symbol, insert_after_symbol, rename_symbol,
      replace_lines, delete_lines, insert_at_line, validate_syntax, search_structural,
      read_file, create_text_file, replace_content, list_dir, find_file, search_for_pattern,
      read_memory, write_memory, edit_memory, list_memories, onboarding
    </available-tools>
  </mcp-tools>
```

**Step 2: Add `<mcp-tools>` block to `_bmad/bmm/agents/quick-flow-solo-dev.md`**

Same block as dev.md. Insert after `</persona>` before `<menu>`.

**Step 3: Add `<mcp-tools>` block to `_bmad/bmm/agents/architect.md`**

Insert after `</persona>` before `<menu>`:

```xml
  <mcp-tools tier="full" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
    <usage-strategy>
      Use Serena-Vanguard MCP tools for architecture analysis and validation.
      1. Navigate: get_symbols_overview for structural understanding, find_symbol for specific components
      2. Analyze: find_referencing_symbols for dependency mapping before proposing changes
      3. Edit: replace_symbol_body for interface changes, replace_lines for config adjustments
      4. Verify: validate_syntax after edits, search_for_pattern for convention compliance
    </usage-strategy>
    <available-tools>
      find_symbol, get_symbols_overview, find_referencing_symbols,
      replace_symbol_body, insert_before_symbol, insert_after_symbol, rename_symbol,
      replace_lines, delete_lines, insert_at_line, validate_syntax, search_structural,
      read_file, create_text_file, replace_content, list_dir, find_file, search_for_pattern,
      read_memory, write_memory, edit_memory, list_memories, onboarding
    </available-tools>
  </mcp-tools>
```

**Step 4: Add `<mcp-tools>` block to `_bmad/bmm/agents/qa.md`**

Insert after `</persona>` before `<prompts>`:

```xml
  <mcp-tools tier="full" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
    <usage-strategy>
      Use Serena-Vanguard MCP tools for test generation and code analysis.
      1. Discover: get_symbols_overview to identify untested symbols and public API surface
      2. Analyze: find_referencing_symbols to understand usage patterns for test scenarios
      3. Generate: create_text_file for new test files, insert_after_symbol for adding test methods
      4. Validate: validate_syntax on generated tests, search_for_pattern for coverage gaps
    </usage-strategy>
    <available-tools>
      find_symbol, get_symbols_overview, find_referencing_symbols,
      replace_symbol_body, insert_before_symbol, insert_after_symbol, rename_symbol,
      replace_lines, delete_lines, insert_at_line, validate_syntax, search_structural,
      read_file, create_text_file, replace_content, list_dir, find_file, search_for_pattern,
      read_memory, write_memory, edit_memory, list_memories, onboarding
    </available-tools>
  </mcp-tools>
```

**Step 5: Add `<mcp-tools>` block to `_bmad/gds/agents/game-dev.md`**

Insert after `</persona>` before `<menu>`:

```xml
  <mcp-tools tier="full" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
    <usage-strategy>
      Use Serena-Vanguard MCP tools for all code operations. Validate performance on hot-path files.
      1. Navigate: get_symbols_overview then find_symbol to locate game systems
      2. Edit: replace_symbol_body for whole functions, replace_lines for surgical changes
      3. Verify: validate_syntax after every edit, run tests after every task
      4. Performance: search_structural to find patterns that may impact game loop
    </usage-strategy>
    <available-tools>
      find_symbol, get_symbols_overview, find_referencing_symbols,
      replace_symbol_body, insert_before_symbol, insert_after_symbol, rename_symbol,
      replace_lines, delete_lines, insert_at_line, validate_syntax, search_structural,
      read_file, create_text_file, replace_content, list_dir, find_file, search_for_pattern,
      read_memory, write_memory, edit_memory, list_memories, onboarding
    </available-tools>
  </mcp-tools>
```

**Step 6: Add `<mcp-tools>` block to `_bmad/gds/agents/game-solo-dev.md`**

Same block as game-dev.md. Insert after `</persona>` before `<menu>`.

**Step 7: Add `<mcp-tools>` block to `_bmad/gds/agents/game-architect.md`**

Insert after `</persona>` before `<menu>`:

```xml
  <mcp-tools tier="full" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
    <usage-strategy>
      Use Serena-Vanguard MCP tools for system analysis and architecture validation.
      1. Navigate: get_symbols_overview for system component mapping
      2. Analyze: find_referencing_symbols for dependency and coupling analysis
      3. Edit: replace_symbol_body for interface refactoring, rename_symbol for API changes
      4. Document: search_for_pattern for convention verification, validate_syntax after changes
    </usage-strategy>
    <available-tools>
      find_symbol, get_symbols_overview, find_referencing_symbols,
      replace_symbol_body, insert_before_symbol, insert_after_symbol, rename_symbol,
      replace_lines, delete_lines, insert_at_line, validate_syntax, search_structural,
      read_file, create_text_file, replace_content, list_dir, find_file, search_for_pattern,
      read_memory, write_memory, edit_memory, list_memories, onboarding
    </available-tools>
  </mcp-tools>
```

**Step 8: Add `<mcp-tools>` block to `_bmad/gds/agents/game-qa.md`**

Insert after `</persona>` before `<menu>`:

```xml
  <mcp-tools tier="full" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
    <usage-strategy>
      Use Serena-Vanguard MCP tools for test automation and code validation.
      1. Discover: get_symbols_overview to map testable game systems
      2. Analyze: find_referencing_symbols for usage patterns and test scenario generation
      3. Generate: create_text_file for test files, replace_symbol_body for test updates
      4. Validate: validate_syntax on tests, search_structural for anti-patterns
    </usage-strategy>
    <available-tools>
      find_symbol, get_symbols_overview, find_referencing_symbols,
      replace_symbol_body, insert_before_symbol, insert_after_symbol, rename_symbol,
      replace_lines, delete_lines, insert_at_line, validate_syntax, search_structural,
      read_file, create_text_file, replace_content, list_dir, find_file, search_for_pattern,
      read_memory, write_memory, edit_memory, list_memories, onboarding
    </available-tools>
  </mcp-tools>
```

**Step 9: Add `<mcp-tools>` block to `_bmad/tea/agents/tea.md`**

Insert after `</persona>` before `<menu>`:

```xml
  <mcp-tools tier="full" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
    <usage-strategy>
      Use Serena-Vanguard MCP tools for test architecture and coverage analysis.
      1. Discover: get_symbols_overview to identify untested public API surface
      2. Trace: find_referencing_symbols for call chain analysis and risk-based test prioritization
      3. Generate: create_text_file for test scaffolds, insert_after_symbol for test methods
      4. Validate: validate_syntax on generated tests, search_for_pattern for assertion coverage
    </usage-strategy>
    <available-tools>
      find_symbol, get_symbols_overview, find_referencing_symbols,
      replace_symbol_body, insert_before_symbol, insert_after_symbol, rename_symbol,
      replace_lines, delete_lines, insert_at_line, validate_syntax, search_structural,
      read_file, create_text_file, replace_content, list_dir, find_file, search_for_pattern,
      read_memory, write_memory, edit_memory, list_memories, onboarding
    </available-tools>
  </mcp-tools>
```

**Step 10: Commit**

```bash
git add _bmad/bmm/agents/dev.md _bmad/bmm/agents/quick-flow-solo-dev.md _bmad/bmm/agents/architect.md _bmad/bmm/agents/qa.md _bmad/gds/agents/game-dev.md _bmad/gds/agents/game-solo-dev.md _bmad/gds/agents/game-architect.md _bmad/gds/agents/game-qa.md _bmad/tea/agents/tea.md
git commit -m "feat: add full-access Serena MCP tools to Tier 1 BMAD agents"
```

---

### Task 11: Add `<mcp-tools>` to Tier 2 BMAD agents (read-only)

**Files:**
- Modify: `_bmad/bmm/agents/analyst.md`
- Modify: `_bmad/bmm/agents/pm.md`
- Modify: `_bmad/bmm/agents/sm.md`
- Modify: `_bmad/bmm/agents/ux-designer.md`
- Modify: `_bmad/bmm/agents/tech-writer/tech-writer.md`
- Modify: `_bmad/gds/agents/game-designer.md`
- Modify: `_bmad/gds/agents/game-scrum-master.md`
- Modify: `_bmad/gds/agents/tech-writer/tech-writer.md`
- Modify: `_bmad/core/agents/bmad-master.md`

**Step 1: Add `<mcp-tools>` block to `_bmad/bmm/agents/analyst.md`**

Insert after `</persona>` before `<menu>`:

```xml
  <mcp-tools tier="read-only" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
    <usage-strategy>
      Use Serena-Vanguard MCP tools to explore and understand code. Do NOT modify files directly.
      1. Explore: get_symbols_overview to understand module structure
      2. Trace: find_referencing_symbols for dependency and requirements tracing
      3. Search: search_for_pattern to find implementations matching business requirements
    </usage-strategy>
    <available-tools>
      find_symbol, get_symbols_overview, find_referencing_symbols,
      read_file, list_dir, find_file, search_for_pattern, search_structural,
      read_memory, write_memory, edit_memory, list_memories
    </available-tools>
  </mcp-tools>
```

**Step 2: Add `<mcp-tools>` block to `_bmad/bmm/agents/pm.md`**

Insert after `</persona>` before `<menu>`. Same block as analyst.md (requirements tracing strategy).

**Step 3: Add `<mcp-tools>` block to `_bmad/bmm/agents/sm.md`**

Insert after `</persona>` before `<menu>`:

```xml
  <mcp-tools tier="read-only" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
    <usage-strategy>
      Use Serena-Vanguard MCP tools to understand codebase for story preparation. Do NOT modify files directly.
      1. Explore: list_dir and find_file to map project structure for story scoping
      2. Read: read_file and get_symbols_overview to understand complexity for estimation
      3. Search: search_for_pattern to find relevant code for story context
    </usage-strategy>
    <available-tools>
      find_symbol, get_symbols_overview, find_referencing_symbols,
      read_file, list_dir, find_file, search_for_pattern, search_structural,
      read_memory, write_memory, edit_memory, list_memories
    </available-tools>
  </mcp-tools>
```

**Step 4: Add `<mcp-tools>` block to `_bmad/bmm/agents/ux-designer.md`**

Insert after `</persona>` before `<menu>`:

```xml
  <mcp-tools tier="read-only" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
    <usage-strategy>
      Use Serena-Vanguard MCP tools to explore UI components and patterns. Do NOT modify files directly.
      1. Discover: find_symbol to locate UI component definitions
      2. Read: read_file to understand component structure and props
      3. Search: search_for_pattern to find existing UI patterns for consistency
    </usage-strategy>
    <available-tools>
      find_symbol, get_symbols_overview, find_referencing_symbols,
      read_file, list_dir, find_file, search_for_pattern, search_structural,
      read_memory, write_memory, edit_memory, list_memories
    </available-tools>
  </mcp-tools>
```

**Step 5: Add `<mcp-tools>` block to `_bmad/bmm/agents/tech-writer/tech-writer.md`**

Insert after `</persona>` before `<menu>`:

```xml
  <mcp-tools tier="read-only" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
    <usage-strategy>
      Use Serena-Vanguard MCP tools to understand code for documentation. Do NOT modify source files directly.
      1. Map: get_symbols_overview to document module APIs and public interfaces
      2. Read: find_symbol with include_body=True to extract docstrings and signatures
      3. Trace: find_referencing_symbols to document usage examples
    </usage-strategy>
    <available-tools>
      find_symbol, get_symbols_overview, find_referencing_symbols,
      read_file, list_dir, find_file, search_for_pattern, search_structural,
      read_memory, write_memory, edit_memory, list_memories
    </available-tools>
  </mcp-tools>
```

**Step 6: Add `<mcp-tools>` block to `_bmad/gds/agents/game-designer.md`**

Insert after `</persona>` before `<menu>`. Same block as analyst.md.

**Step 7: Add `<mcp-tools>` block to `_bmad/gds/agents/game-scrum-master.md`**

Insert after `</persona>` before `<menu>`. Same block as sm.md.

**Step 8: Add `<mcp-tools>` block to `_bmad/gds/agents/tech-writer/tech-writer.md`**

Insert after `</persona>` before `<menu>`. Same block as bmm tech-writer.

**Step 9: Add `<mcp-tools>` block to `_bmad/core/agents/bmad-master.md`**

Insert after `</persona>` before `<menu>`:

```xml
  <mcp-tools tier="read-only" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
    <usage-strategy>
      Use Serena-Vanguard MCP tools for codebase context gathering during orchestration. Do NOT modify files directly.
      1. Explore: list_dir and find_file for project structure awareness
      2. Search: search_for_pattern to find relevant code context for workflow decisions
      3. Memory: read_memory and list_memories for project knowledge retrieval
    </usage-strategy>
    <available-tools>
      find_symbol, get_symbols_overview, find_referencing_symbols,
      read_file, list_dir, find_file, search_for_pattern, search_structural,
      read_memory, write_memory, edit_memory, list_memories
    </available-tools>
  </mcp-tools>
```

**Step 10: Commit**

```bash
git add _bmad/bmm/agents/analyst.md _bmad/bmm/agents/pm.md _bmad/bmm/agents/sm.md _bmad/bmm/agents/ux-designer.md _bmad/bmm/agents/tech-writer/tech-writer.md _bmad/gds/agents/game-designer.md _bmad/gds/agents/game-scrum-master.md _bmad/gds/agents/tech-writer/tech-writer.md _bmad/core/agents/bmad-master.md
git commit -m "feat: add read-only Serena MCP tools to Tier 2 BMAD agents"
```

---

### Task 12: Final cleanup — README and verification

**Files:**
- Modify: `README.md`
- Verify: all tests pass

**Step 1: Update README.md**

Add a section explaining serena-vanguard vs upstream Serena:
- Tree-sitter offline backend
- Line-level edit tools
- No JetBrains dependency
- BMAD agent integration with Serena tools

**Step 2: Run full test suite**

Run: `cd ~/git/serena-vanguard && uv run poe format && uv run poe type-check && uv run poe test`
Expected: PASS

**Step 3: Commit**

```bash
git add -A
git commit -m "docs: update README for serena-vanguard fork with BMAD integration"
```

---

## Task Dependency Graph

```
Task 4 (fuzzy)  ──────────────────────────────┐
                                               ↓
Task 5 (edit_tools) ────────────→ Task 6 (remove JetBrains)
                                               ↓
                                  Task 7 (agent integration)
                                               ↓
                                  Task 8 (tool registration)
                                               ↓
                                  Task 9 (sidecar reference)
                                               ↓
                                  Task 10 (Tier 1 agents)
                                               ↓
                                  Task 11 (Tier 2 agents)
                                               ↓
                                  Task 12 (cleanup + docs)
```

Tasks 4 and 5 are independent and can run in parallel.
Tasks 6-12 are sequential.
Tasks 9-11 are pure markdown edits (no Python code).
