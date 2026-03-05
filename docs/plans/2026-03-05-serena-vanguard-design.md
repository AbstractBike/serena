# serena-vanguard — Design Document

**Date:** 2026-03-05
**Status:** Approved

## Goal

Fork Serena Python into a standalone distribution (`serena-vanguard`) that integrates all capabilities of `serena-rs` directly, eliminating the need for a separate Rust MCP server process.

## Problem

Currently two MCP servers coexist:

- **Serena Python** — full MCP server with LSP-based symbol tools, file/memory/shell tools
- **serena-rs** (codegate) — Rust MCP server with tree-sitter symbols, REST compat layer

Serena Python delegates to serena-rs via the JetBrains backend for symbol operations when no LSP is available. This creates operational overhead (two processes, two configs, port management).

## Solution

A single Python MCP server (`serena-vanguard`) that:

1. Keeps the existing LSP backend (solidlsp) unchanged
2. Adds a **tree-sitter backend** as offline fallback (port of serena-rs `symbols/` module)
3. Adds **missing tools** from serena-rs (`replace_lines`, `delete_lines`, `insert_at_line`, `validate_syntax`, `search_structural`)
4. **Removes the JetBrains backend** entirely

## Architecture

### Repository

- New repo: `~/git/serena-vanguard`
- Fork of `serena/` (current upstream)
- Package name: `serena-vanguard`

### Backends

| Backend | When Active | Symbol Source |
|---------|-------------|--------------|
| **LSP** | Language server available | solidlsp (unchanged) |
| **TreeSitter** | No LSP, or explicit in config | `py-tree-sitter` (new) |

`LanguageBackend.JETBRAINS` is removed. Config: `language_backend: TreeSitter` or `language_backend: LSP`.

### New Modules

```
src/serena/backends/treesitter/
├── __init__.py
├── engine.py        # SymbolEngine — port of codegate src/symbols/engine.rs
├── cache.py         # AstCache — mtime-based dict cache
├── fuzzy.py         # Levenshtein + CamelCase/snake_case matching
└── queries/         # tree-sitter .scm query files (copied from codegate)
    ├── python.scm
    ├── rust.scm
    ├── go.scm
    ├── java.scm
    ├── kotlin.scm
    └── typescript.scm

src/serena/tools/
└── edit_tools.py    # replace_lines, delete_lines, insert_at_line, validate_syntax, search_structural
```

### SymbolBounds (dataclass)

```python
@dataclass
class SymbolBounds:
    name: str
    kind: str       # "class" | "function" | "variable"
    line: int       # 1-based
    end_line: int   # 1-based
```

### SymbolEngine

Port of `engine.rs`. Selects grammar + `.scm` query by file extension, runs tree-sitter, maps `@name`/`@def` captures to `SymbolBounds`.

Supported: `.py`, `.rs`, `.go`, `.java`, `.kt`/`.kts`, `.ts`/`.tsx`, `.js`/`.jsx`

### AstCache

Thread-safe dict `path → (mtime, content, symbols)`. Returns cached entry if mtime matches, otherwise re-reads and re-parses. Same semantics as `cache.rs`.

### Fuzzy Matching

Port of `fuzzy.rs`. Priority: Exact > CaseInsensitive > CamelCase > Levenshtein (within max_distance).

### TreeSitter Symbol Tools (same interface as LSP tools)

| Tool | Implementation |
|------|---------------|
| `get_symbols_overview` | `AstCache.get_symbols(file)` → format as Serena output |
| `find_symbol` | `fuzzy.find_fuzzy_matches()` over parsed symbols |
| `find_referencing_symbols` | `rg --word-regexp <name>` + tree-sitter to exclude definitions |

Same tool names and signatures — the agent is backend-agnostic.

### New Edit Tools

| Tool | Description |
|------|-------------|
| `replace_lines` | Replace lines N-M in a file |
| `delete_lines` | Delete lines N-M from a file |
| `insert_at_line` | Insert text at line N |
| `validate_syntax` | tree-sitter parse → report syntax errors |
| `search_structural` | Subprocess `sg` (ast-grep) if in PATH |

Available with both backends.

### Integration Points in agent.py

```python
# Backend selection (replaces current JETBRAINS check at line 321)
if backend == LanguageBackend.TREE_SITTER:
    # register TreeSitter symbol tools, no LS manager
elif backend == LanguageBackend.LSP:
    # existing logic, unchanged
```

`is_lsp()` returns `False` for TreeSitter (no daemon).

### Dependencies Added (pyproject.toml)

```toml
"tree-sitter>=0.21",
"tree-sitter-python>=0.21",
"tree-sitter-javascript>=0.21",
"tree-sitter-typescript>=0.21",
"tree-sitter-rust>=0.21",
"tree-sitter-go>=0.21",
"tree-sitter-java>=0.21",
"tree-sitter-kotlin>=0.0",
```

### Files Removed (JetBrains cleanup)

- `src/serena/tools/jetbrains_tools.py`
- `src/serena/jetbrains/` (entire directory)
- `LanguageBackend.JETBRAINS` from `serena_config.py`
- All JetBrains references in `agent.py`, `dashboard.py`, `tools/__init__.py`

## What Does NOT Change

- solidlsp module (LSP backend) — untouched
- Existing MCP protocol / transport layer
- Memory tools, file tools, shell tools, project tools
- Config tools, workflow tools
- Dashboard, CLI

## Testing Strategy

- Unit tests for `engine.py`, `cache.py`, `fuzzy.py` (port existing Rust tests)
- Integration test: parse real source files with tree-sitter, verify symbol extraction
- Integration test: `find_referencing_symbols` with rg
- Edit tools: unit tests for line operations on temp files
- `validate_syntax`: test with valid/invalid source files
