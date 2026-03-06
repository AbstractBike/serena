"""JETBrains intelligent routing layer.

Provides smart context-aware tool selection and routing for Serena.
"""

from typing import TYPE_CHECKING


def get_intelligent_mode(active_modes: list[str] | None) -> str:
    """
    Determine if JETBrains intelligent mode is active.

    :param active_modes: List of active mode names
    :return: Mode name or 'standard'
    """
    if not active_modes:
        return 'standard'

    # Check for JETBrains mode presence
    for mode in active_modes:
        if hasattr(mode, 'name') and getattr(mode, 'name', '').lower() == 'jetbrains':
            return 'jetbrains'

    return 'standard'


def get_tool_selection(active_modes: list[str] | None, jetbrains_mode: bool = False) -> set[str]:
    """
    Determine which tools should be exposed based on mode.

    :param active_modes: List of active mode names
    :param jetbrains_mode: Whether JETBrains intelligent mode is active
    :return: Set of tool names to include/exclude
    """
    excluded_tools = set()
    included_tools = set()

    if jetbrains_mode:
        # In JETBrains mode, exclude standard BMAD agents
        excluded_tools.update({
            'invoke_bmad_agent',
            'list_bmad_agents',
            'bmad_agent_info',
        })

        # Include JETBrains BMAD-integrated tools
        included_tools.update({
            'quick_spec',       # JETBrains: quick-spec
            'quick_dev',        # JETBrains: quick-dev
            'brainstorming',    # JETBrains: brainstorming
            'smart_code_review', # JETBrains: intelligent review
            'task_analyzer',     # JETBrains: task analysis
            'explain_concept',   # JETBrains: concept explanation
        })

    # Always include standard tools (unless explicitly excluded)
    always_include = set()

    return {
        'excluded': excluded_tools,
        'included': included_tools | always_include,
    }


# Export public functions
__all__ = [
    get_intelligent_mode,
    get_tool_selection,
]
