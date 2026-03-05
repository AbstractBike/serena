# BMAD-Serena Integration Architecture

## Overview

Serena-Vanguard v0.0.0 exposes BMAD agents through the MCP (Model Context Protocol) server, enabling seamless bidirectional integration:

- **Serena Tools** ← available to BMAD agents via `<mcp-tools>` blocks
- **BMAD Agents** → available to Serena clients via MCP tools

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│           MCP Client (Claude Code/Desktop)              │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ↓
       ┌────────────────────────────┐
       │  Serena MCP Server         │
       ├────────────────────────────┤
       │  Symbol Tools              │ → find_symbol
       │  File Tools                │ → read_file, replace_content
       │  Memory Tools              │ → read_memory, write_memory
       │  Edit Tools                │ → validate_syntax, search_structural
       │  BMAD Tools (NEW)          │ → invoke_bmad_agent, list_bmad_agents
       └────────────────────────────┘
                    ↑
         ┌──────────┴──────────┐
         ↓                     ↓
    ┌─────────┐          ┌──────────┐
    │ Serena  │          │ BMAD     │
    │ Agent   │          │ Agents   │
    └─────────┘          │ (27)     │
                         └──────────┘
```

## Components

### 1. Serena Tools (Existing)
- **Symbol Tools**: find_symbol, get_symbols_overview, find_referencing_symbols, replace_symbol_body, etc.
- **File Tools**: read_file, create_text_file, replace_content, list_dir, find_file, search_for_pattern
- **Memory Tools**: read_memory, write_memory, edit_memory, list_memories
- **Edit Tools**: validate_syntax, search_structural
- **Syntax Validation**: Tree-sitter based error detection
- **Fuzzy Matching**: Levenshtein + CamelCase symbol matching

### 2. BMAD Tools (New)
Located in `src/serena/tools/bmad_tools.py`:

#### `InvokeBmadAgentTool`
```python
def apply(self, agent_name: str, prompt: str) -> str:
    """Invoke a BMAD agent with a prompt"""
```

**Capabilities:**
- Discover BMAD agents by name across all modules
- Invoke agent with user prompt
- Return agent output/result

**Currently:** Placeholder that returns agent path and prompt
**TODO:** Integration with actual BMAD agent executor

#### `ListBmadAgentsTool`
```python
def apply(self) -> str:
    """List all available BMAD agents grouped by module"""
```

**Output:**
```
Available BMAD Agents:

**BMM** (9 agents)
  - dev
  - architect
  - qa
  - analyst
  - pm
  - sm
  - ux-designer
  - tech-writer
  - quick-flow-solo-dev

**GDS** (8 agents)
  - game-dev
  - game-architect
  - game-qa
  - game-designer
  - game-scrum-master
  - game-solo-dev
  - tech-writer
  - (game-solo-dev)

**TEA** (1 agent)
  - tea

**CIS** (5 agents)
  - brainstorming-coach
  - creative-problem-solver
  - design-thinking-coach
  - innovation-strategist
  - presentation-master

**BMB** (3 agents)
  - agent-builder
  - module-builder
  - workflow-builder

**CORE** (1 agent)
  - bmad-master
```

#### `BmadAgentInfoTool`
```python
def apply(self, agent_name: str) -> str:
    """Get information about a BMAD agent"""
```

**Returns:**
- Agent description (from markdown)
- File location
- MCP tools tier (full access / read-only)

## Data Flow

### Scenario 1: Serena Agent Invokes BMAD Agent

```
Claude Code
    ↓
Serena Agent
    ↓
invoke_bmad_agent("dev", "Implement feature X")
    ↓
BMAD Agent: dev executes
    ↓
Returns result to Serena Agent
    ↓
Serena can use Serena tools to process result
```

### Scenario 2: BMAD Agent Uses Serena Tools

```
BMAD Agent (e.g., architect)
    ↓
<mcp-tools> block specifies available Serena tools
    ↓
Calls find_symbol, replace_symbol_body, etc.
    ↓
Serena MCP server executes tools
    ↓
Returns results to BMAD Agent
```

## BMAD Agent Access Control

### Tier 1: Full Access (9 agents)
- dev, quick-flow-solo-dev, architect, qa
- game-dev, game-solo-dev, game-architect, game-qa
- tea

**Available Tools:** All symbol, file, memory, edit tools
**Capabilities:** Read, write, modify code

### Tier 2: Read-Only (9 agents)
- analyst, pm, sm, ux-designer, tech-writer
- game-designer, game-scrum-master, bmad-master

**Available Tools:** find_symbol, get_symbols_overview, find_referencing_symbols, read_file, list_dir, find_file, search_for_pattern
**Capabilities:** Code exploration, analysis, dependency tracing

## MCP Tool Usage Pattern

In Claude Code / Claude Desktop with Serena MCP connected:

```python
# List available BMAD agents
tools.list_bmad_agents()
# → Returns 27 agents across 6 modules

# Get info about an agent
tools.bmad_agent_info("dev")
# → Returns: description, MCP tools tier, capabilities

# Invoke an agent
tools.invoke_bmad_agent("architect", "Design system for handling 10k concurrent users")
# → Invokes BMAD architect agent
# → Returns: architecture recommendations, code patterns, design decisions

# Then use Serena tools to implement the design
tools.find_symbol("main", "service.ts")  # Find where to add code
tools.replace_symbol_body("main", "service.ts", "new code")  # Make changes
tools.validate_syntax("service.ts")  # Verify
```

## Implementation Status

### ✅ Implemented
- Tool classes: InvokeBmadAgentTool, ListBmadAgentsTool, BmadAgentInfoTool
- Agent discovery mechanism (scans _bmad/**/*.md)
- MCP tool registration
- Tests (3/3 passing)
- Documentation

### 🚧 TODO
- **BMAD Agent Executor Integration**
  - Connect to actual BMAD agent runtime
  - Capture agent output and return through MCP
  - Handle async execution
  - Error handling and timeouts

- **Agent Chaining**
  - Allow BMAD agents to invoke other BMAD agents
  - Pass context between agents
  - Manage execution history

- **Advanced Features**
  - Agent versioning
  - Output caching
  - Execution tracing/telemetry
  - Rate limiting
  - Cost estimation

## Endpoints

### MCP Server Endpoints
- `invoke_bmad_agent(agent_name, prompt)` → Invokes agent
- `list_bmad_agents()` → Lists all agents
- `bmad_agent_info(agent_name)` → Gets agent details

### Serena Endpoints (Existing)
- Symbol tools: find_symbol, replace_symbol_body, insert_before_symbol, etc.
- File tools: read_file, replace_content, create_text_file, etc.
- Memory tools: read_memory, write_memory, edit_memory, etc.

## Performance Considerations

- **Agent Discovery:** O(n) filesystem scan where n = number of _bmad markdown files (~27)
  - Cached on first call
  - Refresh available via list_bmad_agents()

- **Agent Invocation:** Depends on executor implementation
  - Currently: O(1) placeholder (returns metadata)
  - With executor: Async, timeout-protected, configurable

## Security

- **BMAD Agents:** Have their own Tier-based access control via `<mcp-tools>` blocks
- **Serena Tools:** Follow LSP/Symbol-level safety (code is already in repo)
- **Bidirectional:** Both can invoke each other with validated inputs

## Testing

Location: `test/serena/test_bmad_tools.py`

Tests cover:
- Agent discovery across _bmad modules
- Agent file finding by name
- Agent info extraction from markdown
- Error handling (missing agents, invalid paths)

## Future Directions

1. **Event-Driven Architecture**
   - Agents emit events (code_written, error_occurred, etc.)
   - Other agents can subscribe and react

2. **Knowledge Base**
   - Persistent memory of agent decisions
   - Learning from past executions
   - Pattern recognition

3. **Agent Composition**
   - Combine multiple agents for complex workflows
   - Automatic coordination and handoff

4. **Observability**
   - Trace BMAD agent calls through Serena
   - Metrics: execution time, success rate, token usage
   - Integration with SkyWalking/monitoring stack

---

**serena-vanguard v0.0.0: Serena tools in BMAD, BMAD agents in Serena, bidirectional MCP integration.** 🚀
