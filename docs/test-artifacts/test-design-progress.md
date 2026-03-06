---
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
lastSaved: '2026-03-06'
mode: epic-level
scope: MCP Server Tools (50 tools)
---

# Test Design Progress: MCP Server Tools

## Step 1: Mode Detection
- **Mode**: Epic-Level
- **Scope**: All 50 MCP tools
- **Rationale**: No formal PRD/ADR; operational test plan for existing tools

## Step 2: Context Loading
- **Stack**: Backend (Python, pyproject.toml)
- **Tools explored**: 50 tools across 11 source files
- **Existing coverage**: 20/50 tools (40%)
- **Test infrastructure**: conftest.py fixtures, syrupy snapshots, unittest.mock

## Step 3: Risk Assessment
- **High risks (>=6)**: 3 (memory CRUD, shell command, regex injection)
- **Medium risks (3-4)**: 6 (file tools, config, workflow, edit tools, query project, .NET 10)
- **Low risks (1-2)**: 3 (thinking tools, dashboard, LSP restart)

## Step 4: Coverage Plan
- **P0**: 18 tests (~25-35 hours) - Memory, command, regex safety
- **P1**: 24 tests (~20-30 hours) - File manipulation, config, edit tools
- **P2**: 16 tests (~6-10 hours) - Workflow, query project, .NET detection
- **P3**: 6 tests (~2-5 hours) - Thinking tools, dashboard, LSP restart
- **Total**: 64 tests, ~53-80 hours, ~7-10 days

## Step 5: Output Generation
- **Output**: `docs/test-artifacts/test-design-epic-mcp.md`
- **Mode**: Sequential (single document)
- **Status**: Complete
