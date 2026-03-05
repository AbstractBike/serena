import tempfile
from pathlib import Path

from serena.tools.bmad_tools import BmadAgentInfoTool, InvokeBmadAgentTool, ListBmadAgentsTool


def test_list_bmad_agents():
    """Test listing available BMAD agents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock BMAD structure
        bmad_dir = Path(tmpdir) / "_bmad"
        agents_dir = bmad_dir / "bmm" / "agents"
        agents_dir.mkdir(parents=True)

        # Create sample agent files
        (agents_dir / "dev.md").write_text("# Dev Agent\nDeveloper workflow")
        (agents_dir / "qa.md").write_text("# QA Agent\nQuality assurance")

        # Mock tool context
        tool = ListBmadAgentsTool(agent=None)  # type: ignore
        tool._agent_project_root = tmpdir

        # Mock get_project_root
        tool.get_project_root = lambda: tmpdir  # type: ignore

        result = tool.apply()
        assert "dev" in result.lower()
        assert "qa" in result.lower()
        assert "agents" in result.lower()


def test_find_agent_file():
    """Test finding agent file by name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bmad_dir = Path(tmpdir) / "_bmad"
        agents_dir = bmad_dir / "gds" / "agents"
        agents_dir.mkdir(parents=True)

        agent_file = agents_dir / "game-dev.md"
        agent_file.write_text("# Game Dev")

        found = InvokeBmadAgentTool._find_agent_file(bmad_dir, "game-dev")
        assert found is not None
        assert found.name == "game-dev.md"


def test_agent_info():
    """Test getting agent information."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bmad_dir = Path(tmpdir) / "_bmad"
        agents_dir = bmad_dir / "tea" / "agents"
        agents_dir.mkdir(parents=True)

        agent_file = agents_dir / "tea.md"
        agent_file.write_text(
            """# Tea Agent
Test architecture and execution planning

This agent specializes in test design.

<mcp-tools tier="full">
  Tools available here
</mcp-tools>
"""
        )

        tool = BmadAgentInfoTool(agent=None)  # type: ignore
        tool.get_project_root = lambda: tmpdir  # type: ignore

        result = tool.apply("tea")
        assert "tea" in result.lower()
        assert "Test architecture" in result
        assert "MCP Tools" in result
