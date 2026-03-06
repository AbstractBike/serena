---
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
lastSaved: '2026-03-06'
inputDocuments:
  - src/serena/tools/file_tools.py
  - src/serena/tools/symbol_tools.py
  - src/serena/tools/memory_tools.py
  - src/serena/tools/config_tools.py
  - src/serena/tools/workflow_tools.py
  - src/serena/tools/cmd_tools.py
  - src/serena/tools/jetbrains_tools.py
  - src/serena/tools/bmad_tools.py
  - src/serena/tools/research_tools.py
  - src/serena/tools/edit_tools.py
  - src/serena/tools/query_project_tools.py
  - src/serena/mcp.py
  - test/serena/test_mcp.py
  - test/serena/test_serena_agent.py
  - test/serena/test_bmad_tools.py
  - test/serena/test_research_tools.py
---

# Test Design: MCP Server Tools - Full Coverage

**Date:** 2026-03-06
**Author:** Serena (TEA)
**Status:** Draft

---

## Executive Summary

**Scope:** Full test design for all 50 MCP tools exposed by the Serena MCP server.

**Risk Summary:**

- Total risks identified: 12
- High-priority risks (>=6): 3
- Critical categories: TECH, SEC, DATA

**Coverage Summary:**

- P0 scenarios: 18 (~25-35 hours)
- P1 scenarios: 24 (~20-30 hours)
- P2/P3 scenarios: 22 (~8-15 hours)
- **Total effort**: ~53-80 hours (~7-10 days)

**Current State:** 20/50 tools have tests. 30 tools (60%) have zero test coverage. MCP protocol layer has solid tests (`test_mcp.py` validates all tool schemas). Integration gaps are primarily in memory, workflow, config, edit, and query-project categories.

---

## Not in Scope

| Item | Reasoning | Mitigation |
|------|-----------|------------|
| **JetBrains tools (4)** | Require running JetBrains IDE with Serena plugin | Manual testing by contributors with JetBrains; covered by upstream CI |
| **Language-specific LSP tests** | Already covered by 585+ tests in `test/solidlsp/` | Existing parametrized test suite across 37 languages |
| **MCP protocol wire format** | Covered by `test_mcp.py::test_make_tool_all_tools` | Schema validation tests exist for all 61 tool classes |
| **Firecrawl live API** | External service; unit tests mock the API | Mocked tests in `test_research_tools.py` cover all paths |

---

## Risk Assessment

### High-Priority Risks (Score >=6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
|---------|----------|-------------|-------------|--------|-------|------------|-------|----------|
| R-001 | DATA | Memory tools (6 tools) have zero tests; write/delete/rename could corrupt persistent project knowledge | 3 | 3 | 9 | Add unit tests with temp directories; test CRUD lifecycle | DEV | Sprint 1 |
| R-002 | TECH | Shell command execution tool untested; could pass through dangerous commands or fail silently | 2 | 3 | 6 | Add tests with safe commands; verify output capture and error handling | DEV | Sprint 1 |
| R-003 | SEC | `replace_content` regex injection — malformed regex could cause ReDoS or unintended file mutations | 2 | 3 | 6 | Add tests with adversarial regex patterns; verify error handling | DEV | Sprint 1 |

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
|---------|----------|-------------|-------------|--------|-------|------------|-------|
| R-004 | TECH | File tools (create, delete_lines, replace_lines, insert_at_line) untested — silent data loss on edge cases | 2 | 2 | 4 | Add boundary tests (empty files, large files, unicode) | DEV |
| R-005 | TECH | Config tools (switch_modes, remove_project) could leave agent in inconsistent state | 2 | 2 | 4 | Add state transition tests with assertions on tool visibility | DEV |
| R-006 | OPS | Workflow tools (onboarding, prepare_for_new_conversation) untested — broken onboarding blocks new users | 1 | 3 | 3 | Add basic smoke tests verifying output format | DEV |
| R-007 | TECH | Edit tools (validate_syntax, search_structural) depend on external binaries (tree-sitter, ast-grep) | 2 | 2 | 4 | Add tests with fallback behavior when binaries missing | DEV |
| R-008 | TECH | Query project tools untested — cross-project queries could leak data or fail silently | 1 | 3 | 3 | Add tests with mock project configurations | DEV |
| R-009 | TECH | .NET 10 runtime compatibility — OmniSharp may crash with newer .NET versions beyond 10 | 1 | 3 | 3 | Add parametrized DotnetVersion detection test | DEV |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
|---------|----------|-------------|-------------|--------|-------|--------|
| R-010 | OPS | Thinking tools (3 tools) are no-ops that return prompts — low risk of failure | 1 | 1 | 1 | Monitor |
| R-011 | OPS | open_dashboard depends on webbrowser module — environment-specific | 1 | 1 | 1 | Monitor |
| R-012 | TECH | restart_language_server could leave LSP in broken state if called during operation | 1 | 2 | 2 | Monitor; existing LSP restart logic has recovery |

---

## Entry Criteria

- [x] Source code for all 50 tools available in `src/serena/tools/`
- [x] Test infrastructure (conftest.py, fixtures) available
- [x] Existing test patterns established (mocking, temp directories)
- [x] `uv run poe test` executes successfully
- [ ] Test environment provisioned (Python 3.11+, uv installed)

## Exit Criteria

- [ ] All P0 tests passing
- [ ] All P1 tests passing (or failures triaged)
- [ ] No open high-priority bugs in MCP tool behavior
- [ ] Coverage for all 50 tools (at minimum smoke-level)
- [ ] `uv run poe test` green, `uv run poe type-check` green

---

## Test Coverage Plan

### P0 (Critical) - Run on every commit

**Criteria**: Core MCP functionality + High risk (>=6) + No workaround

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
|-------------|-----------|-----------|------------|-------|-------|
| Memory CRUD lifecycle (write, read, list, edit, rename, delete) | Unit | R-001 | 8 | DEV | Temp directory; full lifecycle test |
| Memory concurrent access safety | Unit | R-001 | 2 | DEV | Parallel read/write to same memory |
| ExecuteShellCommand output capture | Unit | R-002 | 3 | DEV | Success, failure, timeout cases |
| ExecuteShellCommand safe boundaries | Unit | R-002 | 2 | DEV | Verify working directory containment |
| ReplaceContent adversarial regex | Unit | R-003 | 3 | DEV | ReDoS patterns, invalid regex, backslash escapes |

**Total P0**: 18 tests, ~25-35 hours

### P1 (High) - Run on PR to main

**Criteria**: Important tool functionality + Medium risk (3-4) + Common workflows

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
|-------------|-----------|-----------|------------|-------|-------|
| CreateTextFileTool (create, overwrite, unicode) | Unit | R-004 | 3 | DEV | Temp directory |
| DeleteLinesTool (boundary, empty file, out of range) | Unit | R-004 | 3 | DEV | Edge cases |
| ReplaceLinesTool (single, multi, boundary) | Unit | R-004 | 3 | DEV | Edge cases |
| InsertAtLineTool (beginning, middle, end, beyond) | Unit | R-004 | 3 | DEV | Edge cases |
| SearchForPatternTool (regex, literal, no match) | Unit | - | 2 | DEV | Verify output format |
| SwitchModesTool state transitions | Unit | R-005 | 3 | DEV | Mode activation, tool visibility |
| RemoveProjectTool (valid, non-existent) | Unit | R-005 | 2 | DEV | State cleanup verification |
| ValidateSyntaxTool (valid, invalid, unsupported lang) | Unit | R-007 | 3 | DEV | Tree-sitter integration |
| SearchStructuralTool (pattern match, no match) | Unit | R-007 | 2 | DEV | ast-grep integration |

**Total P1**: 24 tests, ~20-30 hours

### P2 (Medium) - Run nightly/weekly

**Criteria**: Secondary tools + Low risk + Edge cases

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
|-------------|-----------|-----------|------------|-------|-------|
| OnboardingWorkflowTool output format | Unit | R-006 | 2 | DEV | Verify structured output |
| CheckOnboardingPerformed (yes/no states) | Unit | R-006 | 2 | DEV | File presence check |
| PrepareForNewConversation output | Unit | R-006 | 1 | DEV | Smoke test |
| InitialInstructions output | Unit | - | 1 | DEV | Smoke test |
| SummarizeChanges output | Unit | - | 1 | DEV | Smoke test |
| ListQueryableProjectsTool (with/without projects) | Unit | R-008 | 2 | DEV | Mock config |
| QueryProjectTool (valid query, missing project) | Unit | R-008 | 2 | DEV | Mock config |
| GetCurrentConfigTool output completeness | Unit | - | 1 | DEV | Verify all sections present |
| ActivateProjectTool (valid, invalid path) | Unit | - | 2 | DEV | Already partial coverage |
| DotnetVersion V10 detection | Unit | R-009 | 2 | DEV | Parametrized version strings |

**Total P2**: 16 tests, ~6-10 hours

### P3 (Low) - Run on-demand

**Criteria**: Nice-to-have + Exploratory + Low risk

| Requirement | Test Level | Test Count | Owner | Notes |
|-------------|-----------|------------|-------|-------|
| ThinkAboutCollectedInformation output | Unit | 1 | DEV | Verify returns string |
| ThinkAboutTaskAdherence output | Unit | 1 | DEV | Verify returns string |
| ThinkAboutWhetherYouAreDone output | Unit | 1 | DEV | Verify returns string |
| OpenDashboardTool (mock webbrowser) | Unit | 1 | DEV | Mock webbrowser.open |
| RestartLanguageServerTool (mock LSP) | Unit | 1 | DEV | Verify restart call |
| MCP tool annotation correctness | Integration | 1 | DEV | Verify destructiveHint flags |

**Total P3**: 6 tests, ~2-5 hours

---

## Execution Order

### Smoke Tests (<2 min)

**Purpose**: Fast feedback, catch import/registration issues

- [ ] All tools importable from `serena.tools` (existing: `test_make_tool_all_tools`)
- [ ] MCP server starts without error
- [ ] Tool registry contains expected count

**Total**: 3 scenarios

### P0 Tests (<5 min)

**Purpose**: Critical path validation — memory and command tools

- [ ] Memory write -> read -> edit -> rename -> delete lifecycle
- [ ] Memory list returns written memories
- [ ] Shell command captures stdout and stderr
- [ ] Shell command respects timeout
- [ ] ReplaceContent with valid regex
- [ ] ReplaceContent rejects catastrophic regex

**Total**: 18 scenarios

### P1 Tests (<10 min)

**Purpose**: File manipulation and config tool coverage

- [ ] File creation and overwrite
- [ ] Line deletion boundaries
- [ ] Line replacement
- [ ] Line insertion at all positions
- [ ] Pattern search with regex
- [ ] Mode switching
- [ ] Syntax validation
- [ ] Structural search

**Total**: 24 scenarios

### P2/P3 Tests (<15 min)

**Purpose**: Workflow and auxiliary tool coverage

- [ ] Onboarding output
- [ ] Config query
- [ ] Cross-project query
- [ ] Thinking tools
- [ ] Dashboard launch (mocked)

**Total**: 22 scenarios

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
|----------|-------|------------|-------------|-------|
| P0 | 18 | 1.5 | ~25-35 | Complex setup (memory lifecycle, regex edge cases) |
| P1 | 24 | 1.0 | ~20-30 | Standard file operation tests |
| P2 | 16 | 0.5 | ~6-10 | Simple smoke tests |
| P3 | 6 | 0.25 | ~2-5 | Trivial output checks |
| **Total** | **64** | **-** | **~53-80** | **~7-10 days** |

### Prerequisites

**Test Data:**

- Temporary directory fixtures (existing pattern in conftest.py)
- Mock agent instances (existing pattern in test_research_tools.py)
- Sample project configs for cross-project testing

**Tooling:**

- `pytest` with `syrupy` for snapshot tests
- `unittest.mock` for external service mocking
- `tempfile` for isolated file system tests

**Environment:**

- Python 3.11+ with uv
- tree-sitter and ast-grep for edit tool tests
- No external services required (all mocked)

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: >=95% (waivers required for failures)
- **P2/P3 pass rate**: >=90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **MCP tool coverage**: 100% (all 50 tools have at least one test)
- **Critical paths (memory, command, file mutation)**: >=80% branch coverage
- **Error handling paths**: >=70%
- **Edge cases (empty files, unicode, large inputs)**: >=50%

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (>=6) items unmitigated
- [ ] Memory tool CRUD fully tested
- [ ] Shell command execution boundaries tested
- [ ] Regex injection patterns tested

---

## Mitigation Plans

### R-001: Memory Tools Zero Coverage (Score: 9)

**Mitigation Strategy:** Create `test/serena/test_memory_tools.py` with full CRUD lifecycle tests using temporary directories. Test write, read, list, edit (regex), rename (including scope change), and delete. Include concurrent access test.
**Owner:** DEV
**Timeline:** Sprint 1
**Status:** Planned
**Verification:** `uv run poe test test/serena/test_memory_tools.py` passes with 10 tests

### R-002: Shell Command Execution Untested (Score: 6)

**Mitigation Strategy:** Create `test/serena/test_cmd_tools.py` with tests for: successful command, failed command, timeout, output capture (stdout/stderr), and working directory containment.
**Owner:** DEV
**Timeline:** Sprint 1
**Status:** Planned
**Verification:** `uv run poe test test/serena/test_cmd_tools.py` passes with 5 tests

### R-003: Regex Injection in ReplaceContent (Score: 6)

**Mitigation Strategy:** Add test cases to existing `test_serena_agent.py` or create `test/serena/test_file_tools.py` for: catastrophic backtracking patterns, invalid regex error handling, backslash escaping in replacement strings.
**Owner:** DEV
**Timeline:** Sprint 1
**Status:** Planned
**Verification:** Tests cover invalid regex rejection and safe handling

---

## Assumptions and Dependencies

### Assumptions

1. All tools can be tested in isolation with mocked agent/config instances
2. File system tests use temporary directories (no real project mutation)
3. External services (Firecrawl, JetBrains) are mocked in unit tests
4. Tree-sitter and ast-grep are available in the test environment
5. Existing test patterns (conftest.py fixtures) are reusable

### Dependencies

1. `uv` and Python 3.11+ installed — Required immediately
2. `tree-sitter` Python bindings — Required for edit tool tests
3. `ast-grep` (sg) binary — Required for structural search tests

### Risks to Plan

- **Risk**: tree-sitter or ast-grep not available in CI
  - **Impact**: Edit tool tests would be skipped
  - **Contingency**: Mark as `xfail` or skip with environment detection

---

## Interworking & Regression

| Service/Component | Impact | Regression Scope |
|-------------------|--------|------------------|
| **SolidLanguageServer** | Symbol tools depend on LSP | Existing 585+ tests in `test/solidlsp/` |
| **MCP Protocol Layer** | All tools exposed via MCP | `test_mcp.py::test_make_tool_all_tools` validates schema |
| **SerenaAgent** | Tool registration and lifecycle | `test_serena_agent.py` integration tests |
| **Firecrawl API** | Research tools use HTTP | Mocked in `test_research_tools.py` |
| **BMAD Framework** | BMAD tools read agent files | Mocked in `test_bmad_tools.py` |

---

## Suggested Test File Structure

```
test/serena/
  test_memory_tools.py      # NEW - P0: 10 tests (CRUD lifecycle)
  test_cmd_tools.py         # NEW - P0: 5 tests (shell execution)
  test_file_tools.py        # NEW - P1: 12 tests (create, delete, replace, insert lines)
  test_config_tools.py      # NEW - P1: 5 tests (switch modes, remove project)
  test_edit_tools.py        # EXISTS - extend with P1: 5 tests (syntax, structural)
  test_workflow_tools.py    # NEW - P2: 7 tests (onboarding, instructions, thinking)
  test_query_project_tools.py # NEW - P2: 4 tests (list, query)
  test_dotnet_version.py    # NEW - P2: 2 tests (.NET 10 detection)
  test_bmad_tools.py        # EXISTS - 3 tests (complete)
  test_research_tools.py    # EXISTS - 5 tests (complete)
  test_mcp.py               # EXISTS - 10 tests (schema validation)
  test_serena_agent.py      # EXISTS - 19 tests (integration)
```

---

## Follow-on Workflows (Manual)

- Run `*atdd` to generate failing P0 tests (separate workflow; not auto-run).
- Run `*automate` for broader coverage once implementation exists.

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: ____________ Date: ____________
- [ ] Tech Lead: ____________ Date: ____________
- [ ] QA Lead: ____________ Date: ____________

**Comments:**

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework (TECH/SEC/PERF/DATA/BUS/OPS)
- `test-levels-framework.md` - Test level selection (Unit/Component/API/E2E)
- `test-priorities-matrix.md` - P0-P3 prioritization criteria

### Related Documents

- Architecture: `CLAUDE.md` (project architecture overview)
- Integration: `docs/BMAD_SERENA_INTEGRATION.md`
- Tool source: `src/serena/tools/`
- MCP server: `src/serena/mcp.py`

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `_bmad/tea/testarch/test-design`
**Mode**: Epic-Level (MCP Server Tools)
**Version**: 5.0 (BMad v6)
