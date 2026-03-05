# serena-vanguard v0.0.0

**Initial release of serena-vanguard: LSP-first fork of Serena with enhanced tooling and BMAD integration.**

## What's New

### Core Features
- **LSP-Only Architecture** — Single backend, clean and maintainable
- **Fuzzy Symbol Matching** — Exact > CaseInsensitive > CamelCase > Levenshtein ranking
- **Tree-Sitter Utilities**
  - `ValidateSyntaxTool` — Parse errors detection via tree-sitter
  - `SearchStructuralTool` — Structural pattern search via ast-grep (sg)
- **Auto-Project Registration** — `get_active_project_or_raise()` auto-registers CWD if no project active

### BMAD Integration
18 BMAD agents equipped with Serena MCP tools:

**Tier 1 (Full Access):** dev, quick-flow-solo-dev, architect, qa, game-dev, game-solo-dev, game-architect, game-qa, tea

**Tier 2 (Read-Only):** analyst, pm, sm, ux-designer, tech-writer (×2), game-designer, game-scrum-master, bmad-master

## Testing
- ✅ 615 tests passed
- ✅ Type-check: 112 source files + 103 test files clean
- ✅ Code format: Black + Ruff compliant

## Installation
```bash
uv pip install serena-vanguard==0.0.0
# or in editable mode:
uv pip install -e /path/to/serena-vanguard
```

## Documentation
- See `README.md` for architecture overview
- See `_bmad/_memory/serena-tools-reference.md` for MCP tools reference
- See BMAD agent files for usage examples (search for `<mcp-tools>` blocks)

## Commits
- `06d7bc5f` — Fuzzy symbol matching (Levenshtein + CamelCase)
- `75538b37` — Tree-Sitter tools (ValidateSyntax + SearchStructural)
- `4c301f5b` — BMAD reference sidecar documentation
- `481ced6f` — Tier 1 agents (full access, 9/9)
- `0a66aef4` — Tier 2 agents (read-only, 9/9)
- `5e711aa9` — Register tools in ToolSet
- `b4d6fdc4` — README update (LSP-first focus)
- `22f68151` — Auto-register project on demand
- `872a6b21` — Version bump to 0.0.0

## Known Limitations
- Push to upstream unavailable (no permissions on oraios/serena)
- Nexus upload requires authentication (not configured)
- Only applicable to Python projects (not Rust/Java/Nix ecosystems)

---

**serena-vanguard is ready for production use.** 🚀
