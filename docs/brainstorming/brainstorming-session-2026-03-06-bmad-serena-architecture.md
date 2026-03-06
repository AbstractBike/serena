---
stepsCompleted: [1, 2]
inputDocuments: []
session_topic: 'BMAD + Serena architecture — merge, decouple, or hybrid as MCP/Claude plugin'
session_goals: 'Determine optimal integration strategy evaluating maintainability, portability, and synchronization trade-offs'
selected_approach: 'ai-recommended'
techniques_used: ['First Principles Thinking', 'Morphological Analysis', 'Constraint Mapping + Chaos Engineering']
ideas_generated: []
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** Serena
**Date:** 2026-03-06

## Session Overview

**Topic:** BMAD + Serena architecture — merge, decouple, or hybrid as MCP/Claude plugin
**Goals:** Determine if BMAD and Serena should be fused into a single MCP/Claude plugin, kept as separate decoupled components, or maintained with the current hybrid approach — evaluating trade-offs of maintainability, portability, and synchronization.

### Context Guidance

Current state: Serena-vanguard is a Python MCP server (LSP + TreeSitter, 49 tools). BMAD is a markdown-based agent/workflow framework installed as `_bmad/` directories. Both coexist in the serena-vanguard repo with a single `.claude-plugin/plugin.json`. BMAD agents are exposed as Serena MCP tools and reference Serena tools via `<mcp-tools>` blocks.

### Session Setup

Exploring architectural integration patterns for two fundamentally different systems: a Python LSP server and a markdown agent framework. Key tensions include upstream sync with Serena, BMAD portability across repos, and unified developer experience.
