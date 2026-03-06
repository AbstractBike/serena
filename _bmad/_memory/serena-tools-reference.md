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

## Research Tools (web intelligence)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `web_scrape` | Scrape a web page for content | `url`, `formats`, `only_main_content` |
| `web_search` | Search the web by query | `query`, `limit`, `scrape_results` |
| `web_map` | Discover all URLs on a website | `url`, `search`, `limit` |
| `web_crawl` | Recursively crawl a website | `url`, `limit`, `max_depth`, `poll_timeout` |

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

**Research before editing:**
1. `web_search` to find existing solutions or documentation
2. `web_scrape` to extract detailed content from relevant pages
3. `web_map` to understand a documentation site structure
4. `web_crawl` for comprehensive content gathering (keep limit low)
