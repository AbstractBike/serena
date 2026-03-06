---
name: serena
description: Unlock semantic code intelligence (49 LSP tools, 46 languages)
---

Activate Serena for symbol-level code navigation, refactoring, and project memory across 46 programming languages.

## Quick Start

1. **Check setup** — `check_onboarding_performed()`
2. **If needed, onboard** — `onboarding(current_directory)`
3. **Activate for project** — `activate_project(current_directory)`
4. **Done!** — Use symbol tools immediately

## What You Get (49 MCP Tools)

**Symbol Tools** (semantic, not text-based):
- `find_symbol` — Find code by name (fuzzy matching)
- `find_referencing_symbols` — Find all usages
- `replace_symbol_body` — Replace function/class/method bodies
- `rename_symbol` — Refactor rename across entire codebase
- `insert_before_symbol` / `insert_after_symbol`
- `get_symbols_overview` — List all symbols in file

**Search & Structure:**
- `search_structural` — Pattern-based code search via ast-grep
- `validate_syntax` — Check syntax without parsing entire codebase

**File Operations:**
- `read_file`, `create_text_file`, `replace_content`
- `list_dir`, `find_file`, `search_for_pattern`

**Project Memory:**
- `read_memory` / `write_memory` — Persistent project knowledge
- `edit_memory` / `list_memories` — Update and track insights

**Languages Supported:**
Python, JavaScript, TypeScript, Rust, Go, Java, C/C++, C#, Kotlin, PHP, Perl, Ruby, Bash, PowerShell, Haskell, Elixir, Erlang, Scala, Swift, Lua, Nix, YAML, TOML, Markdown, and 20+ more via Language Server Protocol.

## Why Serena vs Plain File Reading

| Task | Plain Files | Serena |
|------|------------|--------|
| Find all uses of function X | Read 10 files, grep | 1 tool call: `find_referencing_symbols` |
| Rename function + all calls | Manual string replace (risky) | 1 tool: `rename_symbol` (safe LSP refactoring) |
| Add method to class | Read file, manual edit | `insert_after_symbol` (precise) |
| Navigate large repo | Read entire files | Symbols only (5-10x faster, fewer tokens) |

## BMAD Agent Integration

Serena includes 27 BMAD agents for multi-role development:
- `dev` — Developer agent (story execution, TDD)
- `architect` — Architecture design
- `qa` — Quality assurance
- `pm` — Project management
- `game-dev`, `game-architect` — Game development workflows
- And 21 more specialized agents

Access via `invoke_bmad_agent(agent_name, prompt)`
