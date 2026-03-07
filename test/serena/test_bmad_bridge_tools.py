import tempfile
from pathlib import Path

from serena.tools.bmad_bridge_tools import GetBmadWorkflowInfoTool, ListBmadWorkflowsTool, LoadBmadWorkflowTool


def test_list_bmad_workflows():
    """Test listing available BMAD workflows."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock BMAD structure
        bmad_dir = Path(tmpdir) / "_bmad"
        bmm_workflows_dir = bmad_dir / "bmm" / "workflows"
        dev_story_dir = bmm_workflows_dir / "dev-story"
        dev_story_dir.mkdir(parents=True)

        # Create sample workflow file
        workflow_file = dev_story_dir / "workflow.md"
        workflow_file.write_text(
            """---
name: 'Dev Story'
description: 'Execute user stories'
steps:
  - 'steps/step-01-load-story.md'
  - 'steps/step-02-implement.md'
---
This workflow executes user stories with TDD.
"""
        )

        # Create another workflow
        code_review_dir = bmm_workflows_dir / "code-review"
        code_review_dir.mkdir(parents=True)
        (code_review_dir / "workflow.yaml").write_text(
            """---
name: 'Code Review'
description: 'Review code quality'
steps:
  - 'steps/step-01-analyze.md'
  - 'steps/step-02-report.md'
---
"""
        )

        # Mock tool context
        tool = ListBmadWorkflowsTool(agent=None)  # type: ignore
        tool._agent_project_root = tmpdir

        # Mock get_project_root
        tool.get_project_root = lambda: tmpdir  # type: ignore

        result = tool.apply()
        assert "dev story" in result.lower()
        assert "code review" in result.lower()
        assert "bmm" in result.lower()
        assert "workflows" in result.lower()


def test_load_bmad_workflow():
    """Test loading and analyzing a BMAD workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock BMAD structure
        bmad_dir = Path(tmpdir) / "_bmad"
        gds_workflows_dir = bmad_dir / "gds" / "workflows"
        game_design_dir = gds_workflows_dir / "game-design"
        game_design_dir.mkdir(parents=True)

        # Create workflow file
        workflow_file = game_design_dir / "workflow.md"
        workflow_file.write_text(
            """---
name: 'Game Design'
description: 'Design game mechanics'
steps:
  - 'steps/step-01-concept.md'
  - 'steps/step-02-mechanics.md'
---
This workflow designs game systems and mechanics.
"""
        )

        # Mock tool context
        tool = LoadBmadWorkflowTool(agent=None)  # type: ignore
        tool._agent_project_root = tmpdir
        tool.get_project_root = lambda: tmpdir  # type: ignore

        result = tool.apply("_bmad/gds/workflows/game-design/workflow.md")
        assert "game design" in result.lower()
        assert "2 step files" in result
        assert "step-01-concept.md" in result
        assert "step-02-mechanics.md" in result
        assert "load_bmad_workflow" in result


def test_get_bmad_workflow_info():
    """Test getting information about a BMAD workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock BMAD structure
        bmad_dir = Path(tmpdir) / "_bmad"
        tea_workflows_dir = bmad_dir / "tea" / "workflows"
        testarch_dir = tea_workflows_dir / "testarch"
        testarch_dir.mkdir(parents=True)

        # Create workflow file
        workflow_file = testarch_dir / "workflow.yaml"
        workflow_file.write_text(
            """---
name: 'Test Architecture'
description: 'Design testing architecture'
steps:
  - 'steps/step-01-strategy.md'
  - 'steps/step-02-tools.md'
---
This workflow designs test architecture.
"""
        )

        # Mock tool context
        tool = GetBmadWorkflowInfoTool(agent=None)  # type: ignore
        tool._agent_project_root = tmpdir
        tool.get_project_root = lambda: tmpdir  # type: ignore

        result = tool.apply("_bmad/tea/workflows/testarch/workflow.yaml")
        assert "test architecture" in result.lower()
        assert "design testing architecture" in result
        assert "2 step files" in result
        assert "step-01-strategy.md" in result
        assert "step-02-tools.md" in result


def test_bmad_workflow_not_found():
    """Test handling of non-existent BMAD workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create empty BMAD directory
        bmad_dir = Path(tmpdir) / "_bmad"
        bmad_dir.mkdir(parents=True)

        # Mock tool context
        tool = LoadBmadWorkflowTool(agent=None)  # type: ignore
        tool._agent_project_root = tmpdir
        tool.get_project_root = lambda: tmpdir  # type: ignore

        result = tool.apply("_bmad/nonexistent/workflow.md")
        assert "not found" in result.lower()
