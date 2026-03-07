# BMAD Integration Architecture

## Overview

BMAD (Business Model And Design) integration with Serena is provided through **workflow-based tools**, not direct agent invocation. This document explains the correct architecture for BMAD integration.

## Architecture

### Layer 1: BMAD Workflows (Source of Truth)

BMAD workflows are YAML files with step-by-step instructions:

```
_bmad/
├── bmm/workflows/
│   ├── dev-story/workflow.yaml
│   └── code-review/workflow.yaml
├── gds/workflows/
│   └── game-design/workflow.yaml
└── core/workflows/
    └── party-mode/workflow.md
```

Each workflow:
- Has a `workflow.yaml` or `workflow.md` main file
- Contains step files in `steps/` directory
- Uses frontmatter for state tracking
- Designed for sequential execution with checkpoints

### Layer 2: Serena Bridge Tools (Integration Point)

Serena provides bridge tools that load and analyze BMAD workflows:

**Location:** `src/serena/tools/bmad_bridge_tools.py`

**Tools:**
1. **LoadBmadWorkflowTool** - Load workflow and provide execution guidance
2. **ListBmadWorkflowsTool** - List all available workflows
3. **GetBmadWorkflowInfoTool** - Get workflow details

These tools:
- Read BMAD workflow files
- Analyze structure and steps
- Provide execution guidance
- Don't execute workflows directly - that's done by the LLM using Serena tools

### Layer 3: Serena Execution (Actual Execution)

The LLM (Claude) uses Serena's existing tools to execute workflows:

- `read_file` - Read step files and configuration
- `search_for_pattern` - Find code for investigation
- `find_file` - Locate relevant files
- `list_dir` - Browse project structure
- `edit_file` - Make code changes
- etc.

## Correct Usage Pattern

### ❌ Wrong Approach (Deprecated)

```python
# Don't try to invoke BMAD agents directly
from serena.tools.bmad_tools import InvokeBmadAgentTool

tool = InvokeBmadAgentTool()
result = tool.apply(agent_name="dev", prompt="Do something")
# This returns a placeholder message
```

### ✅ Correct Approach

```python
# Load and analyze BMAD workflow
from serena.tools.bmad_bridge_tools import LoadBmadWorkflowTool

tool = LoadBmadWorkflowTool()
result = tool.apply(workflow_path="_bmad/bmm/workflows/dev-story/workflow.yaml")

# The LLM then:
# 1. Reads the workflow guidance
# 2. Uses Serena tools to execute each step
# 3. Follows instructions exactly (no skipping, no optimization)
```

## Workflow Execution Model

### BMAD Workflow Structure

```yaml
---
name: "Dev Story"
description: "Execute user stories with TDD"
steps:
  - 'steps/step-01-load-story.md'
  - 'steps/step-02-analyze-requirements.md'
  - 'steps/step-03-implement-tests.md'
  - 'steps/step-04-implement-code.md'
---
```

### Execution Flow

1. **Load Workflow:**
   ```
   User: "Load BMAD workflow dev-story"
   Tool: LoadBmadWorkflowTool.apply("_bmad/bmm/workflows/dev-story/workflow.yaml")
   Result: Workflow analysis and execution guidance
   ```

2. **Read Step:**
   ```
   LLM: "I'll read step 1"
   Tool: read_file("_bmad/bmm/workflows/dev-story/steps/step-01-load-story.md")
   ```

3. **Execute Instructions:**
   ```
   LLM: Reads step completely, follows exact instructions
   Uses Serena tools to complete actions
   Waits for user input at menus
   ```

4. **Update State:**
   ```
   LLM: Updates workflow frontmatter stepsCompleted array
   Tool: edit_file(workflow.yaml)
   ```

5. **Continue to Next Step:**
   ```
   Repeat until all steps complete
   ```

## Key Principles

1. **Sequential Execution:** Steps must be executed in exact order
2. **No Skipping:** Never skip steps or optimize prematurely
3. **User Interaction:** Always wait for user input at menus
4. **State Tracking:** Update `stepsCompleted` in workflow frontmatter
5. **Tool Integration:** Use Serena tools for file operations

## Deprecated Components

### bmad_tools.py (Placeholder Tools)

**Status:** DEPRECATED

The following tools have been removed as non-functional:
- `InvokeBmadAgentTool` - Attempted to invoke agents directly
- `ListBmadAgentsTool` - Attempted to list agents
- `BmadAgentInfoTool` - Attempted to get agent info

**Reason:** These tools tried to invoke BMAD as if it were an API service, but BMAD is designed as workflow files that LLMs interpret and execute.

**Replacement:** Use tools from `bmad_bridge_tools.py` instead.

## Example Workflows

### Dev Story Workflow

```bash
# Load workflow
LoadBmadWorkflowTool.apply("_bmad/bmm/workflows/dev-story/workflow.yaml")

# Execute steps
# 1. Load user story file
# 2. Analyze requirements
# 3. Implement tests (TDD)
# 4. Implement code
# 5. Run tests
# 6. Update story file
```

### Code Review Workflow

```bash
# Load workflow
LoadBmadWorkflowTool.apply("_bmad/bmm/workflows/code-review/workflow.yaml")

# Execute steps
# 1. Prepare review context
# 2. Analyze code quality
# 3. Check test coverage
# 4. Verify documentation
# 5. Generate review report
```

## Benefits of This Architecture

1. **Flexibility:** LLMs can adapt workflow execution to context
2. **Transparency:** Each step is visible and can be reviewed
3. **Integration:** Uses existing Serena tools seamlessly
4. **State Tracking:** Workflows track progress through frontmatter
5. **User Control:** Menus and checkpoints allow user oversight

## Troubleshooting

### "BMAD workflow not found" Error

**Cause:** Incorrect workflow path
**Solution:** Use path relative to project root: `_bmad/bmm/workflows/dev-story/workflow.yaml`

### "No Step Files Defined" Message

**Cause:** Workflow doesn't use step-file architecture
**Solution:** Read main workflow file for inline instructions

### Workflow Not Progressing

**Cause:** Not updating `stepsCompleted` in frontmatter
**Solution:** After each step, update the workflow frontmatter array

## Future Enhancements

Possible improvements:
- Automatic workflow state persistence
- Workflow progress visualization
- Step-level validation
- Automated testing of workflow completions
- Workflow template generation

## References

- **BMAD Architecture:** `_bmad/core/tasks/workflow.xml`
- **Workflow Examples:** `_bmad/bmm/workflows/`, `_bmad/gds/workflows/`, `_bmad/tea/workflows/`
- **Bridge Tools:** `src/serena/tools/bmad_bridge_tools.py`
- **Agent Files:** `_bmad/*/agents/*.md`
## 🚀 Current Status

**Resolution:** CR-BM01 ✅ RESOLVED (2026-03-06)
CR-BM02 ✅ RESOLVED (2026-03-07)
CR-QG01 ✅ RESOLVED (2026-03-07)

The BMAD integration architecture has been corrected:
1. **CR-BM01:** Removed placeholder tools that attempted to invoke BMAD agents as API services
2. **CR-BM02:** Clarified that BMAD is not an API service - it consists of instruction files for LLMs to read and execute
3. **CR-QG01:** Quality Gates workflow created with comprehensive quality checks

All BMAD architectural issues have been resolved. The system now has:
- Proper workflow-based integration through bmad_bridge_tools.py
- Centralized configuration management avoiding duplication
- Comprehensive quality gates system for production readiness
- Correct understanding that BMAD agents are instruction files, not executable services

**Note on CR-QG02:** The `risk-governance.md` file is a complete risk governance system implementation (TypeScript code with automated scoring, mitigation tracking, and audit trails), not a quality gates workflow. This provides examples and patterns for risk governance implementations but is a separate system from the quality gates workflow that BMAD would use. The documentation is not "fragmented" - it's a functional risk management toolkit.


**Note on CR-QG02:** El `risk-governance.md` file is a complete risk governance system implementation (TypeScript code with automated scoring, mitigation tracking, and audit trails), not a quality gates workflow. This provides examples and patterns for risk governance implementations but is a separate system from the quality gates workflow that BMAD would use. The documentation is not "fragmented" - it's a functional risk management toolkit. The workflow quality-gates that was created provides the executable quality checks that BMAD should use.
