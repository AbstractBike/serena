# BMAD + Serena-Vanguard Integration — Design Document

**Date:** 2026-03-05
**Status:** Approved

## Goal

Give BMAD agents access to Serena-Vanguard MCP tools by modifying existing agent definitions. No new agents or workflows created.

## Approach: Sidecar + Inline Tailored (Option 5)

1. **Sidecar file** — `_bmad/_memory/serena-tools-reference.md` with complete tool catalog (single source of truth)
2. **Inline `<mcp-tools>` block** — added to each agent XML with role-appropriate tool subset and usage strategy

## Agent Tiers

### Tier 1 — Full Access (all tools)

Agents that write/modify code directly:

| Agent | Module |
|-------|--------|
| dev (Amelia) | bmm |
| quick-flow-solo-dev (Barry) | bmm |
| architect (Winston) | bmm |
| qa (Quinn) | bmm |
| game-dev (Link Freeman) | gds |
| game-solo-dev (Indie) | gds |
| game-architect (Cloud Dragonborn) | gds |
| game-qa (GLaDOS) | gds |
| tea (Murat) | tea |

### Tier 2 — Read Only (search + navigation)

Strategic/creative agents that explore code but don't modify it:

| Agent | Module |
|-------|--------|
| analyst (Mary) | bmm |
| pm (John) | bmm |
| sm (Bob) | bmm |
| ux-designer (Sally) | bmm |
| tech-writer (Paige) | bmm + gds |
| game-designer (Samus) | gds |
| game-scrum-master (Max) | gds |
| bmad-master | core |

### Not Modified (no Serena tools)

Pure creative agents with no code interaction:

- cis module: brainstorming-coach, creative-problem-solver, design-thinking-coach, innovation-strategist, presentation-master, storyteller
- bmb module: agent-builder, module-builder, workflow-builder

## Sidecar Structure

File: `_bmad/_memory/serena-tools-reference.md`

Complete catalog organized by category:
- **Symbol Tools** — find_symbol, get_symbols_overview, find_referencing_symbols, replace_symbol_body, insert_before_symbol, insert_after_symbol, rename_symbol
- **Line-Level Edit Tools** — replace_lines, delete_lines, insert_at_line, validate_syntax, search_structural
- **File Tools** — read_file, create_text_file, replace_content, list_dir, find_file, search_for_pattern
- **Memory Tools** — read_memory, write_memory, edit_memory, list_memories
- **Workflow Tools** — onboarding

Each tool entry includes: name, purpose, key parameters.

## Inline Block Format

Location in agent XML: after `<persona>`, before `<menu>`.

### Tier 1 Template

```xml
<mcp-tools tier="full" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
  <usage-strategy>
    [Role-specific strategy text]
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

### Tier 2 Template

```xml
<mcp-tools tier="read-only" reference="{project-root}/_bmad/_memory/serena-tools-reference.md">
  <usage-strategy>
    [Role-specific strategy text]
  </usage-strategy>
  <available-tools>
    find_symbol, get_symbols_overview, find_referencing_symbols,
    read_file, list_dir, find_file, search_for_pattern, search_structural,
    read_memory, write_memory, edit_memory, list_memories
  </available-tools>
</mcp-tools>
```

## Usage Strategies by Agent

| Agent | Strategy Focus |
|-------|---------------|
| dev, quick-flow-solo-dev | TDD: validate_syntax + tests after every edit |
| architect | Impact analysis: find_referencing_symbols before proposing changes |
| qa, tea | Coverage: get_symbols_overview to find untested symbols |
| game-dev, game-solo-dev | Performance: validate_syntax on hot-path, TDD |
| game-architect | System analysis: symbol navigation + reference mapping |
| game-qa | Test automation: symbol search + validation |
| analyst, pm | Requirements tracing: search_for_pattern + symbol overview |
| sm, game-scrum-master | Story tracking: search_for_pattern + read_file |
| ux-designer | UI component exploration: find_symbol + read_file |
| tech-writer | Documentation: get_symbols_overview + read_file for docstrings |
| bmad-master | Orchestration: search + read for context gathering |

## What Does NOT Change

- No new agents or workflows created
- No BMAD config files modified
- No existing workflows modified
- cis and bmb module agents untouched
