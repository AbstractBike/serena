"""BMAD Bridge Tools - Real integration with BMAD workflows.

These tools serve as bridges between BMAD workflow files and Serena's capabilities,
providing workflow guidance that users can execute with Serena's existing tools.
"""

import logging
import re
from pathlib import Path

from serena.tools.tools_base import Tool, ToolMarkerOptional

log = logging.getLogger(__name__)


class LoadBmadWorkflowTool(Tool, ToolMarkerOptional):
    """Load and analyze a BMAD workflow file for execution guidance."""

    def apply(self, workflow_path: str, analyze_only: bool = False) -> str:
        """
        Load a BMAD workflow file and provide execution guidance.

        :param workflow_path: Path to BMAD workflow file (relative to _bmad/)
        :param analyze_only: If True, only analyze structure without generating execution steps
        :return: Workflow analysis and execution guidance
        """
        project_root = self.get_project_root()

        # Resolve path relative to _bmad/ or absolute
        workflow_path_obj = Path(workflow_path)
        if not workflow_path.startswith("_bmad/"):
            workflow_file = project_root / workflow_path_obj
        else:
            workflow_file = project_root / workflow_path_obj

        if not workflow_file.exists():
            return f"❌ BMAD workflow not found: {workflow_file}"

        try:
            content = workflow_file.read_text()
            return self._analyze_workflow(content, workflow_file, analyze_only)
        except Exception as e:
            return f"❌ Error reading BMAD workflow: {e}"

    @staticmethod
    def _analyze_workflow(content: str, workflow_file: Path, analyze_only: bool = False) -> str:
        """Analyze workflow content and extract execution guidance."""
        lines = content.split("\n")

        # Extract frontmatter (YAML between --- markers)
        frontmatter_end = -1
        for i, line in enumerate(lines):
            if line.strip() == "---" and i > 0:
                frontmatter_end = i
                break

        # Extract workflow name
        workflow_name = "Unknown"
        for i, line in enumerate(lines):
            if i <= frontmatter_end and line.startswith("name:"):
                workflow_name = line.split(":")[1].strip().strip("'")

        # Extract step files
        step_files = []
        for line in lines:
            if line.startswith("steps/"):
                steps_line = line.split(":")[1].strip()
                # Extract path between quotes
                match = re.search(r"'([^']+)'", steps_line)
                if match:
                    step_files.append(match.group(1))

        # Build analysis
        result = f"""## 📋 BMAD Workflow Analysis: {workflow_name}

**File Location:** `{workflow_file}`

**Structure:**
- {len(step_files)} step files defined
- Uses step-file architecture with sequential execution
- Frontmatter configuration for state tracking

**Execution Model:**
BMAD workflows are designed for sequential execution with state tracking:
1. Read current step file completely before taking action
2. Follow exact instructions (NO skipping, NO optimization)
3. Update `stepsCompleted` array in frontmatter after each step
4. Load next step file only when directed
5. Always halt at menus and wait for user input

**Integration with Serena:**
This workflow requires Serena's capabilities:

**Required Serena Tools:**
- `read_file` - Read step files and configuration
- `search_for_pattern` - Find code for investigation
- `find_file` - Locate relevant files
- `list_dir` - Browse project structure

**Serena's Role:**
You (Claude) act as the workflow executor, interpreting and executing
the step-by-step instructions from BMAD workflow files.

**How to Execute:**
"""

        if analyze_only:
            result += "\n\n**ANALYSIS ONLY - No Execution Guidance**\n\n"
            result += "Use this to understand workflow structure before execution.\n\n"
        else:
            # Generate execution guidance
            result += "\n\n**Execution Guidance**\n\n"

            if step_files:
                result += f"### 📝 Step Files ({len(step_files)}):\n\n"
                result += "Execute in this order:\n\n"
                for i, step_file in enumerate(step_files, 1):
                    relative_path = workflow_file.parent / step_file
                    if relative_path.exists():
                        result += f"{i}. `{step_file}` → Read completely, then follow instructions\n\n"
                    else:
                        result += f"{i}. `{step_file}` → Not found, cannot execute\n\n"

                result += "\n\n**Key Execution Rules:**\n\n"
                result += "1. Read entire step file before taking action\n"
                result += "2. Follow numbered sections in exact order\n"
                result += "3. Wait for user input at menus\n"
                result += "4. Use Serena tools for code investigation\n"
                result += "5. Apply `/reload` after file modifications\n\n"

            else:
                result += "\n\n⚠️  No Step Files Defined\n\n"
                result += "This workflow may not use step-file architecture.\n\n"
                result += "Read the main workflow file for direct instructions.\n\n"

        result += "\n\n**Integration Note:**\n\n"
        result += "BMAD workflows are designed for sequential execution with checkpoints. "
        result += "Use Serena tools to complete each step, then call `/reload` "
        result += "to update Serena's internal state after code changes.\n\n"

        return result


class ListBmadWorkflowsTool(Tool, ToolMarkerOptional):
    """List available BMAD workflows in the project."""

    def apply(self, module_filter: str = "") -> str:
        """
        List all BMAD workflows, optionally filtered by module.

        :param module_filter: Filter by BMAD module (e.g., "bmm", "gds", "tea")
        :return: Formatted list of available workflows
        """
        project_root = self.get_project_root()
        bmad_dir = project_root / Path("_bmad")

        if not bmad_dir.exists():
            return f"❌ BMAD directory not found: {bmad_dir}"

        # Find all workflow.md files
        workflows = []
        for workflow_file in bmad_dir.rglob("**/workflow.md"):
            # Extract module from path
            parts = workflow_file.relative_to(bmad_dir).parts
            if len(parts) >= 2:
                module = parts[0]  # e.g., "bmm", "gds", "tea", "core"
            else:
                module = "root"  # core workflows

            # Apply module filter
            if module_filter and module != module_filter:
                continue

            # Extract name from workflow file
            try:
                with open(workflow_file) as f:
                    first_line = f.readline().strip()
                    name = "Unknown"
                    if first_line.startswith("name:"):
                        name = first_line.split(":")[1].strip().strip("'")

                    workflows.append({"name": name, "module": module, "path": str(workflow_file.relative_to(project_root))})
            except Exception as e:
                log.warning(f"Error reading {workflow_file}: {e}")

        if not workflows:
            return "❌ No BMAD workflows found"

        # Build formatted output
        result = f"""## 📚 Available BMAD Workflows ({len(workflows)} total)

"""

        # Group by module
        modules: dict[str, list[dict[str, str]]] = {}
        for wf in workflows:
            module = wf["module"]
            if module not in modules:
                modules[module] = []
            modules[module].append(wf)

        # Display by module
        for module, module_workflows in sorted(modules.items()):
            result += f"\n### 📦 {module.upper()} ({len(module_workflows)} workflows)\n\n"
            for wf in sorted(module_workflows, key=lambda x: x["name"]):
                result += f"  - **{wf['name']}** - `{wf['path']}`\n"

        result += """
**Workflow Structure:**
- Each workflow has step files in `steps/` directory
- Uses frontmatter for state tracking
- Sequential execution with checkpoints and menus

**Execution Instructions:**
Use: `load_bmad_workflow <path>` - Load and analyze a workflow
Then: Execute steps using Serena tools, call `/reload` after modifications

**Note:** These are real BMAD workflows (not placeholder tools).
They require manual execution following the sequential step-by-step instructions.
"""
        return result


class GetBmadWorkflowInfoTool(Tool, ToolMarkerOptional):
    """Get information about a BMAD workflow."""

    def apply(self, workflow_path: str) -> str:
        """
        Get detailed information about a BMAD workflow.

        :param workflow_path: Path to BMAD workflow file (relative to _bmad/)
        :return: Workflow information including configuration and structure
        """
        project_root = self.get_project_root()

        # Resolve path
        workflow_path_obj = Path(workflow_path)
        if not workflow_path.startswith("_bmad/"):
            workflow_file = project_root / workflow_path_obj
        else:
            workflow_file = project_root / workflow_path_obj

        if not workflow_file.exists():
            return f"❌ BMAD workflow not found: {workflow_file}"

        try:
            content = workflow_file.read_text()

            # Parse frontmatter
            lines = content.split("\n")
            frontmatter = []
            in_frontmatter = False

            for line in lines:
                if line.strip() == "---":
                    if in_frontmatter:
                        in_frontmatter = False
                        break
                    in_frontmatter = True
                elif in_frontmatter:
                    frontmatter.append(line)

            # Extract key information
            info = {}
            for line in frontmatter:
                if ":" in line:
                    key, value = line.split(":", 1)
                    info[key.strip()] = value.strip()

            # Extract step files
            step_files = []
            for line in lines:
                if line.startswith("steps:"):
                    steps_line = line.split(":")[1].strip()
                    match = re.search(r"'([^']+)'", steps_line)
                    if match:
                        step_files.append(match.group(1))

            # Build result
            result = f"""## 📋 BMAD Workflow: {info.get('name', 'Unknown')}

**File:** `{workflow_file}`

**Configuration:**
"""
            for key, value in info.items():
                if key != "name":
                    result += f"{key}: {value}\n"

            if step_files:
                result += f"**Step Files ({len(step_files)}):**\n"
                for step_file in step_files:
                    result += f"  - {step_file}\n"
            else:
                result += "**Step Files:** None (uses inline steps)\n"

            result += f"""
**Structure:**
- Frontmatter-based configuration
- Step-file architecture: {len(step_files)} separate step files
- Sequential execution model
- State tracking via `stepsCompleted` array

**How to Execute:**
1. Use `load_bmad_workflow` to analyze this workflow
2. Read each step file completely using `read_file`
3. Follow instructions in exact order (NO skipping)
4. Execute actions using Serena tools
5. Call `/reload` after any file modifications
6. Update workflow frontmatter state as instructed
"""
            return result
        except Exception as e:
            return f"❌ Error reading BMAD workflow info: {e}"


# Export all tools
__all_tools__ = [
    LoadBmadWorkflowTool,
    ListBmadWorkflowsTool,
    GetBmadWorkflowInfoTool,
]
