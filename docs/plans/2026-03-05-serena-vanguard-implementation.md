# serena-vanguard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fork Serena Python into `~/git/serena-vanguard`, integrate tree-sitter offline symbol backend, add missing tools from serena-rs, remove JetBrains backend.

**Architecture:** Two-backend Serena: LSP (primary, unchanged) + TreeSitter (new offline fallback). New `edit_tools.py` with line-level operations and ast-grep. JetBrains backend fully removed.

**Tech Stack:** Python 3.11, py-tree-sitter, mcp, solidlsp (existing), ripgrep (external), ast-grep (external, optional)

---

### Task 1: Create the fork repository

**Step 1: Copy Serena to new repo**

```bash
cp -r ~/git/codegate/serena ~/git/serena-vanguard
cd ~/git/serena-vanguard
rm -rf .git __pycache__ src/**/__pycache__
git init
git add -A
git commit -m "chore: initial fork from serena upstream"
```

**Step 2: Update pyproject.toml metadata**

In `pyproject.toml`, change:
```toml
name = "serena-vanguard"
```

Add tree-sitter dependencies to `dependencies`:
```toml
  "tree-sitter>=0.24",
  "tree-sitter-python>=0.23",
  "tree-sitter-javascript>=0.23",
  "tree-sitter-typescript>=0.23",
  "tree-sitter-rust>=0.23",
  "tree-sitter-go>=0.23",
  "tree-sitter-java>=0.23",
```

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: rename to serena-vanguard, add tree-sitter deps"
```

---

### Task 2: Port SymbolBounds and SymbolEngine

**Files:**
- Create: `src/serena/backends/__init__.py`
- Create: `src/serena/backends/treesitter/__init__.py`
- Create: `src/serena/backends/treesitter/engine.py`
- Create: `src/serena/backends/treesitter/queries/python.scm`
- Create: `src/serena/backends/treesitter/queries/rust.scm`
- Create: `src/serena/backends/treesitter/queries/go.scm`
- Create: `src/serena/backends/treesitter/queries/java.scm`
- Create: `src/serena/backends/treesitter/queries/kotlin.scm`
- Create: `src/serena/backends/treesitter/queries/typescript.scm`
- Test: `test/serena/backends/test_engine.py`

**Step 1: Create query files**

Copy all `.scm` files from `~/git/codegate/src/symbols/queries/` to `src/serena/backends/treesitter/queries/`. These are identical — tree-sitter queries are language-agnostic.

**Step 2: Write the failing test**

Create `test/serena/backends/__init__.py` (empty) and `test/serena/backends/test_engine.py`:

```python
from serena.backends.treesitter.engine import SymbolBounds, SymbolEngine


def test_parse_python_function():
    engine = SymbolEngine()
    source = "def hello():\n    pass\n"
    symbols = engine.parse(source, "py")
    assert len(symbols) == 1
    assert symbols[0].name == "hello"
    assert symbols[0].kind == "function"
    assert symbols[0].line == 1
    assert symbols[0].end_line == 2


def test_parse_python_class():
    engine = SymbolEngine()
    source = "class Foo:\n    def bar(self):\n        pass\n"
    symbols = engine.parse(source, "py")
    assert len(symbols) == 2
    assert symbols[0].name == "Foo"
    assert symbols[0].kind == "class"
    assert symbols[1].name == "bar"
    assert symbols[1].kind == "function"


def test_parse_rust_struct_and_fn():
    engine = SymbolEngine()
    source = "struct Cfg {}\nfn main() {}\n"
    symbols = engine.parse(source, "rs")
    assert len(symbols) == 2
    names = [s.name for s in symbols]
    assert "Cfg" in names
    assert "main" in names


def test_unsupported_extension():
    engine = SymbolEngine()
    symbols = engine.parse("content", "xyz")
    assert symbols == []


def test_find_symbol():
    engine = SymbolEngine()
    source = "def alpha():\n    pass\ndef beta():\n    pass\n"
    result = engine.find_symbol(source, "py", "beta")
    assert result is not None
    assert result.name == "beta"


def test_find_symbol_not_found():
    engine = SymbolEngine()
    source = "def alpha():\n    pass\n"
    result = engine.find_symbol(source, "py", "nope")
    assert result is None
```

**Step 3: Run test to verify it fails**

Run: `cd ~/git/serena-vanguard && python -m pytest test/serena/backends/test_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'serena.backends'`

**Step 4: Write implementation**

Create `src/serena/backends/__init__.py` (empty).

Create `src/serena/backends/treesitter/__init__.py` (empty).

Create `src/serena/backends/treesitter/engine.py`:

```python
"""Tree-sitter based symbol extraction engine.

Port of codegate src/symbols/engine.rs — uses tree-sitter queries to extract
top-level symbol definitions (classes, functions, etc.) from source code.
"""

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

import tree_sitter

_QUERIES_DIR = Path(__file__).parent / "queries"

# Language registry: extension -> (module_name, query_file, callable)
# We lazily load languages to avoid import errors for missing grammars.
_LANGUAGE_MAP: dict[str, tuple[str, str]] = {
    "py": ("tree_sitter_python", "python.scm"),
    "rs": ("tree_sitter_rust", "rust.scm"),
    "go": ("tree_sitter_go", "go.scm"),
    "java": ("tree_sitter_java", "java.scm"),
    "kt": ("tree_sitter_kotlin", "kotlin.scm"),
    "kts": ("tree_sitter_kotlin", "kotlin.scm"),
    "ts": ("tree_sitter_typescript", "typescript.scm"),
    "tsx": ("tree_sitter_typescript", "typescript.scm"),
    "js": ("tree_sitter_javascript", "typescript.scm"),
    "jsx": ("tree_sitter_javascript", "typescript.scm"),
}


@dataclass
class SymbolBounds:
    name: str
    kind: str  # "class" | "function" | "variable"
    line: int  # 1-based
    end_line: int  # 1-based


def _get_language(module_name: str) -> tree_sitter.Language:
    """Dynamically load a tree-sitter language from its Python package."""
    import importlib
    mod = importlib.import_module(module_name)
    # tree-sitter-python>=0.23 exposes language() function
    if hasattr(mod, "language"):
        return tree_sitter.Language(mod.language())
    raise ImportError(f"Cannot load tree-sitter language from {module_name}")


def _kind_for_node_kind(node_kind: str) -> str:
    if any(kw in node_kind for kw in ("class", "interface", "struct", "enum", "trait", "object")):
        return "class"
    if any(kw in node_kind for kw in ("function", "method", "fun")):
        return "function"
    return "variable"


class SymbolEngine:
    """Stateless tree-sitter symbol parser."""

    def __init__(self) -> None:
        self._parsers: dict[str, tree_sitter.Parser] = {}
        self._queries: dict[str, tuple[tree_sitter.Language, str]] = {}

    def _get_parser_and_query(self, ext: str) -> tuple[tree_sitter.Parser, tree_sitter.Language, str] | None:
        entry = _LANGUAGE_MAP.get(ext)
        if entry is None:
            return None
        module_name, query_file = entry

        if ext not in self._parsers:
            try:
                lang = _get_language(module_name)
            except (ImportError, OSError):
                return None
            parser = tree_sitter.Parser(lang)
            query_src = (_QUERIES_DIR / query_file).read_text()
            self._parsers[ext] = parser
            self._queries[ext] = (lang, query_src)

        parser = self._parsers[ext]
        lang, query_src = self._queries[ext]
        return parser, lang, query_src

    def parse(self, source: str, ext: str) -> list[SymbolBounds]:
        """Parse source code and return top-level symbol definitions."""
        result = self._get_parser_and_query(ext)
        if result is None:
            return []

        parser, lang, query_src = result
        tree = parser.parse(source.encode())
        query = lang.query(query_src)

        symbols: list[SymbolBounds] = []
        for match in query.matches(tree.root_node):
            captures = {name: node for name, nodes in match[1].items() for node in (nodes if isinstance(nodes, list) else [nodes])}

            name_node = captures.get("name")
            def_node = captures.get("def", name_node)

            if name_node is not None and def_node is not None:
                name = name_node.text.decode()
                kind = _kind_for_node_kind(def_node.type)
                line = def_node.start_point[0] + 1
                end_line = def_node.end_point[0] + 1
                symbols.append(SymbolBounds(name=name, kind=kind, line=line, end_line=end_line))

        return symbols

    def find_symbol(self, source: str, ext: str, name: str) -> SymbolBounds | None:
        """Find a symbol by exact name in source code."""
        symbols = self.parse(source, ext)
        return next((s for s in symbols if s.name == name), None)
```

**Step 5: Run test to verify it passes**

Run: `cd ~/git/serena-vanguard && python -m pytest test/serena/backends/test_engine.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/serena/backends/ test/serena/backends/
git commit -m "feat: add tree-sitter SymbolEngine with query files

Port of codegate src/symbols/engine.rs to Python using py-tree-sitter.
Supports Python, Rust, Go, Java, Kotlin, TypeScript, JavaScript."
```

---

### Task 3: Port AstCache

**Files:**
- Create: `src/serena/backends/treesitter/cache.py`
- Test: `test/serena/backends/test_cache.py`

**Step 1: Write the failing test**

```python
import os
import tempfile
import time

from serena.backends.treesitter.cache import AstCache
from serena.backends.treesitter.engine import SymbolEngine


def test_cache_hit():
    engine = SymbolEngine()
    cache = AstCache()

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("def hello():\n    pass\n")
        path = f.name

    try:
        symbols1 = cache.get_symbols(path, engine)
        symbols2 = cache.get_symbols(path, engine)
        assert len(symbols1) == 1
        assert symbols1[0].name == "hello"
        # second call should be from cache (same result)
        assert [s.name for s in symbols2] == [s.name for s in symbols1]
    finally:
        os.unlink(path)


def test_cache_invalidation_on_mtime_change():
    engine = SymbolEngine()
    cache = AstCache()

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("def alpha():\n    pass\n")
        path = f.name

    try:
        symbols1 = cache.get_symbols(path, engine)
        assert symbols1[0].name == "alpha"

        # modify the file
        time.sleep(0.05)
        with open(path, "w") as f:
            f.write("def beta():\n    pass\n")

        symbols2 = cache.get_symbols(path, engine)
        assert symbols2[0].name == "beta"
    finally:
        os.unlink(path)
```

**Step 2: Run test to verify it fails**

Run: `cd ~/git/serena-vanguard && python -m pytest test/serena/backends/test_cache.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write implementation**

Create `src/serena/backends/treesitter/cache.py`:

```python
"""Mtime-based AST cache for tree-sitter parsed symbols."""

import os
import threading
from pathlib import Path

from serena.backends.treesitter.engine import SymbolBounds, SymbolEngine


class AstCache:
    """Thread-safe mtime-based cache keyed by absolute file path."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: dict[str, tuple[float, str, list[SymbolBounds]]] = {}

    def get_or_parse(self, path: str, engine: SymbolEngine) -> tuple[str, list[SymbolBounds]]:
        """Return (content, symbols), using cache if mtime matches."""
        abs_path = os.path.abspath(path)
        mtime = os.path.getmtime(abs_path)

        with self._lock:
            entry = self._entries.get(abs_path)
            if entry is not None and entry[0] == mtime:
                return entry[1], entry[2]

        content = Path(abs_path).read_text()
        ext = Path(abs_path).suffix.lstrip(".")
        symbols = engine.parse(content, ext)

        with self._lock:
            self._entries[abs_path] = (mtime, content, symbols)

        return content, symbols

    def get_symbols(self, path: str, engine: SymbolEngine) -> list[SymbolBounds]:
        """Convenience: return only symbols for a path."""
        _, symbols = self.get_or_parse(path, engine)
        return symbols
```

**Step 4: Run test to verify it passes**

Run: `cd ~/git/serena-vanguard && python -m pytest test/serena/backends/test_cache.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/serena/backends/treesitter/cache.py test/serena/backends/test_cache.py
git commit -m "feat: add AstCache with mtime-based invalidation"
```

---

### Task 4: Port fuzzy matching

**Files:**
- Create: `src/serena/backends/treesitter/fuzzy.py`
- Test: `test/serena/backends/test_fuzzy.py`

**Step 1: Write the failing test**

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

Run: `cd ~/git/serena-vanguard && python -m pytest test/serena/backends/test_fuzzy.py -v`
Expected: FAIL

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

Run: `cd ~/git/serena-vanguard && python -m pytest test/serena/backends/test_fuzzy.py -v`
Expected: PASS

**Step 5: Commit**

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

```python
import os
import tempfile

from unittest.mock import MagicMock

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

Run: `cd ~/git/serena-vanguard && python -m pytest test/serena/test_edit_tools.py -v`
Expected: FAIL

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
    lines[line - 1: line - 1] = new_lines
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

        errors = []
        def _collect_errors(node):
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
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0 and result.stderr:
                return f"ast-grep error: {result.stderr.strip()}"
            return result.stdout if result.stdout else "No matches found."
        except FileNotFoundError:
            return "ast-grep (sg) not found in PATH. Install it to use structural search."
```

**Step 4: Run test to verify it passes**

Run: `cd ~/git/serena-vanguard && python -m pytest test/serena/test_edit_tools.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/serena/tools/edit_tools.py test/serena/test_edit_tools.py
git commit -m "feat: add line-level edit tools, validate_syntax, search_structural"
```

---

### Task 6: Add TreeSitter to LanguageBackend enum and remove JetBrains

**Files:**
- Modify: `src/serena/config/serena_config.py`
- Modify: `src/serena/tools/__init__.py`
- Delete: `src/serena/tools/jetbrains_tools.py`
- Delete: `src/serena/jetbrains/` (entire directory)

**Step 1: Modify LanguageBackend enum**

In `src/serena/config/serena_config.py`, replace:
```python
    JETBRAINS = "JetBrains"
    """
    Use the Serena plugin in your JetBrains IDE.
    """
```
with:
```python
    TREE_SITTER = "TreeSitter"
    """
    Use tree-sitter for offline symbol extraction (no language server daemon needed).
    """
```

Also remove the auto-detection block that sets `language_backend = LanguageBackend.JETBRAINS` (around line 653).

**Step 2: Update tools/__init__.py**

Replace:
```python
from .jetbrains_tools import *
```
with:
```python
from .edit_tools import *
```

**Step 3: Delete JetBrains files**

```bash
rm -rf src/serena/jetbrains/
rm src/serena/tools/jetbrains_tools.py
rm test/serena/test_jetbrains_plugin_client.py
```

**Step 4: Fix code_editor.py import**

In `src/serena/code_editor.py`, remove or guard the `JetBrainsCodeEditor` import and class usage.
Remove line: `from serena.jetbrains.jetbrains_plugin_client import JetBrainsPluginClient`
Remove `JetBrainsCodeEditor` class entirely.
Update `Component.create_code_editor()` in `tools_base.py` to remove the JetBrains branch.

**Step 5: Fix agent.py references**

In `src/serena/agent.py`:
- Remove the `if self.serena_config.language_backend == LanguageBackend.JETBRAINS:` block (line 321)
- Update `is_using_language_server()` to also return `False` for `TREE_SITTER`:
```python
    def is_using_language_server(self) -> bool:
        return self.serena_config.language_backend == LanguageBackend.LSP
```
(This is already the implementation — just verify it stays correct after removing JETBRAINS.)

**Step 6: Fix dashboard.py references**

In `src/serena/dashboard.py`, remove or replace `jetbrains_mode=...` reference.

**Step 7: Run tests to verify nothing broke**

Run: `cd ~/git/serena-vanguard && python -m pytest test/ -v --ignore=test/solidlsp/`
Expected: PASS (JetBrains tests deleted, no import errors)

**Step 8: Commit**

```bash
git add -A
git commit -m "refactor: remove JetBrains backend, add TreeSitter to LanguageBackend enum

BREAKING: LanguageBackend.JETBRAINS removed. Use LSP or TreeSitter instead."
```

---

### Task 7: Integrate TreeSitter tools into agent

**Files:**
- Modify: `src/serena/agent.py`
- Modify: `src/serena/tools/tools_base.py`

**Step 1: Update Component.create_code_editor() in tools_base.py**

In `src/serena/tools/tools_base.py`, the `create_code_editor` method needs a TreeSitter branch:

```python
    def create_code_editor(self) -> "CodeEditor":
        from ..code_editor import LanguageServerCodeEditor, TreeSitterCodeEditor

        if self.agent.is_using_language_server():
            return LanguageServerCodeEditor(self.create_language_server_symbol_retriever(), agent=self.agent)
        else:
            return TreeSitterCodeEditor(project=self.project, agent=self.agent)
```

**Step 2: Create TreeSitterCodeEditor in code_editor.py**

Add a `TreeSitterCodeEditor` class to `src/serena/code_editor.py` that uses the tree-sitter engine for symbol resolution instead of JetBrains. This class handles symbol-based file editing (insert_after_symbol, replace_symbol_body, etc.) using `SymbolEngine` + `AstCache` to locate symbols by line number.

```python
class TreeSitterCodeEditor(CodeEditor["TreeSitterSymbol"]):
    """Code editor backed by tree-sitter symbol resolution."""

    def __init__(self, project: Project, agent: Optional["SerenaAgent"] = None):
        super().__init__(project.project_root, agent)
        from serena.backends.treesitter.engine import SymbolEngine
        from serena.backends.treesitter.cache import AstCache
        self._engine = SymbolEngine()
        self._cache = AstCache()
        self._project = project

    # Implementation follows the same pattern as LanguageServerCodeEditor
    # but uses tree-sitter for symbol lookup instead of LSP
```

Note: The exact implementation of `TreeSitterCodeEditor` depends on how deeply the symbol editing tools (`replace_symbol_body`, `insert_after_symbol`, etc.) interact with the `CodeEditor` interface. These tools already work via line-based operations — the CodeEditor just needs to resolve symbol names to line ranges, which is exactly what `SymbolEngine.find_symbol()` provides.

**Step 3: Verify symbol tools work with TreeSitter backend**

Run: `cd ~/git/serena-vanguard && python -m pytest test/serena/ -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/serena/agent.py src/serena/tools/tools_base.py src/serena/code_editor.py
git commit -m "feat: integrate TreeSitter backend into agent and code editor"
```

---

### Task 8: Register edit_tools in ToolSet

**Files:**
- Modify: `src/serena/tools/__init__.py` (already done in Task 6)
- Verify tools appear in `tools/list` MCP response

**Step 1: Verify edit_tools are importable**

```python
from serena.tools.edit_tools import ReplaceLinesTool, DeleteLinesTool, InsertAtLineTool, ValidateSyntaxTool, SearchStructuralTool
```

**Step 2: Run the full test suite**

Run: `cd ~/git/serena-vanguard && python -m pytest test/ -v --ignore=test/solidlsp/`
Expected: PASS

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: verify edit_tools registration in ToolSet"
```

---

### Task 9: Final cleanup and documentation

**Files:**
- Modify: `README.md`
- Modify: `pyproject.toml` (verify final state)

**Step 1: Update README.md**

Add a section explaining serena-vanguard vs upstream Serena:
- Tree-sitter offline backend
- Line-level edit tools
- No JetBrains dependency

**Step 2: Verify full test suite**

Run: `cd ~/git/serena-vanguard && python -m pytest test/ -v`
Expected: PASS

**Step 3: Final commit**

```bash
git add -A
git commit -m "docs: update README for serena-vanguard fork"
```

---

## Task Dependency Graph

```
Task 1 (fork) → Task 2 (engine) → Task 3 (cache) → Task 4 (fuzzy)
                                                          ↓
Task 5 (edit_tools) ─────────────────────────→ Task 6 (remove JetBrains)
                                                          ↓
                                               Task 7 (agent integration)
                                                          ↓
                                               Task 8 (tool registration)
                                                          ↓
                                               Task 9 (cleanup + docs)
```

Tasks 2-4 are sequential (each builds on the previous).
Task 5 is independent and can run in parallel with Tasks 2-4.
Tasks 6-9 are sequential and depend on both tracks.
