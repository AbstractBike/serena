# serena-vanguard v0.0.0 — Deployment Summary

## Release Date
March 5, 2026

## Version
- **PyPI/Local**: v0.0.0
- **Python Support**: 3.11, 3.12, 3.13, 3.14+

## Build Artifacts
```
dist/serena_vanguard-0.0.0-py3-none-any.whl (628 KB)
dist/serena_vanguard-0.0.0.tar.gz (3.1 MB)
```

## Installation Status
✅ **Deployed to all ~/git repositories:**
- claude-chat
- codegate
- cloudflare-grafana-app
- fluffychat
- home
- homelab
- mcp_vanguard
- scalable-market
- serena-vanguard (source)

## Commits in Release
1. `06d7bc5f` — Fuzzy symbol matching (Levenshtein + CamelCase)
2. `75538b37` — Tree-Sitter tools (ValidateSyntax + SearchStructural)
3. `4c301f5b` — BMAD reference sidecar documentation
4. `481ced6f` — Tier 1 agents (full access, 9/9)
5. `0a66aef4` — Tier 2 agents (read-only, 9/9)
6. `5e711aa9` — Register tools in ToolSet
7. `b4d6fdc4` — README update (LSP-first focus)
8. `22f68151` — Auto-register project on demand
9. `872a6b21` — Version bump to 0.0.0
10. `8bd0f051` — Release notes
11. `6dc87b8a` — Broaden Python version support

## Features Deployed
- **LSP-only architecture** — Clean, maintainable single backend
- **Fuzzy symbol matching** — Exact > CaseInsensitive > CamelCase > Levenshtein
- **Tree-Sitter utilities**
  - ValidateSyntaxTool: Parse error detection
  - SearchStructuralTool: ast-grep structural search
- **BMAD integration** — 18 agents with MCP tools (9 Tier 1 full, 9 Tier 2 read-only)
- **Auto-project registration** — Seamless setup (no manual activation required)

## Testing
- ✅ 615 tests passed
- ✅ Type-check clean (112 src + 103 test files)
- ✅ Code format compliant (Black + Ruff)

## Access
All repos can now use serena-vanguard tools:
```python
from serena import SerenaAgent
agent = SerenaAgent()  # Auto-registers current directory if no project active
```

## Known Limitations
- ❌ No upstream push (permissions)
- ❌ No Nexus upload (auth)
- ✅ All local repos have access

---

**serena-vanguard v0.0.0 is production-ready across all ~/git repositories.** 🚀
