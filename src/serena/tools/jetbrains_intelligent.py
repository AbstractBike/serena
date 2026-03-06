"""JETBrains intelligent tools - standalone smart code operations.

These tools operate independently without BMAD context, providing intelligent
code analysis and suggestions.
"""

from pathlib import Path
from typing import Any

from serena.tools.tools_base import Tool, ToolMarkerOptional
from serena.util.logging import log


class AnalyzeTaskTool(Tool, ToolMarkerOptional):
    """Analyze the current codebase and suggest next actions."""

    def apply(self, description: str = "") -> str:
        """
        Analyze the current state and suggest intelligent next steps.

        :param description: Description of what was just done or the current task
        :return: Intelligent analysis and suggestions
        """
        project_root = self.get_project_root()

        # Check for BMAD workflows availability
        bmad_available = (project_root / "_bmad").exists()

        result = f"""Task Analysis: {description}

Context-Aware Assessment:
1. Project Structure: {'self._scan_codebase() if callable else 'not available'}'}
2. BMAD Available: {'Yes' if bmad_available else 'No'}
3. Git Status: {'subprocess.check_output(['git', 'status', '--short']).strip()[:100]' if callable else 'not available'}

Intelligent Suggestions:
1. Consider using BMAD workflows for:
   - quick-spec: If this is a new feature requiring technical specs
   - quick-dev: If implementing a tech spec or direct task
   - brainstorming: If ideation is needed

2. Code Quality Check:
   - Review recent changes for patterns
   - Check test coverage
   - Verify documentation exists for new code

3. Next Steps Based on Context:
"""
        if bmad_available:
            result += "   - Available BMAD workflows: quick-spec, quick-dev, brainstorming\n"
            result += "   - Consider using /bmad-help for workflow guidance\n"
        else:
            result += "   - BMAD not available in this project\n"

        result += "\nFor detailed analysis, use:\n"
        result += "  /bmad-core-serena    # Access Serena with BMAD capabilities\n"
        result += "  /bmad-brainstorming   # Or: /bmad-help for brainstorming guidance\n"

        return result


class SmartSuggestTool(Tool, ToolMarkerOptional):
    """Provide context-aware suggestions based on current work."""

    def apply(self, context: str = "") -> str:
        """
        Provide intelligent suggestions based on the current context.

        :param context: The current work context or question
        :return: Context-aware suggestions
        """
        result = f"""Context-Aware Suggestions for: {context}

Available Intelligent Tools:
1. quick-spec - Rapid technical specification (requires BMAD)
2. quick-dev - Efficient implementation (requires BMAD)
3. brainstorming - Creative ideation (requires BMAD)
4. smart_code_review - Intelligent code analysis
5. task_analyzer - Task breakdown and analysis

Based on the context, I recommend:
{self._recommend_based_on_context(context)}

For detailed workflow execution, use: /bmad-core-serena with --mode jetbrains
"""
        return result

    @staticmethod
    def _recommend_based_on_context(context: str) -> str:
        """Recommend the most appropriate action based on context."""
        context_lower = context.lower()

        if any(word in context_lower for word in ['feature', 'implement', 'add', 'create', 'spec']):
            return "Use /bmad-core-serena quick-spec to create a technical specification for this feature."

        if any(word in context_lower for word in ['fix', 'bug', 'error', 'debug', 'test']):
            return "Use code analysis tools like smart_code_review to diagnose the issue."

        if any(word in context_lower for word in ['help', 'how', 'what', 'why', 'explain', 'documentation']):
            return "Use explain_concept tool to explain technical concepts in project context."

        if any(word in context_lower for word in ['brainstorm', 'idea', 'design', 'creative', 'prototype']):
            return "Use brainstorming tool for creative ideation sessions."

        if any(word in context_lower for word in ['task', 'next', 'continue', 'finish', 'done', 'complete']):
            return "Use task_analyzer tool to get intelligent breakdown of remaining work."

        return "I need more context to provide specific recommendations. Try asking: 'What would you like me to analyze?' or specify the feature/work you're focusing on."


# Export all tools
__all_tools__ = [
    AnalyzeTaskTool,
    SmartSuggestTool,
]
