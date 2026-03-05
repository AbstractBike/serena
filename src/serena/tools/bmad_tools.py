"""BMAD agent invocation tools.

Expose BMAD agents as Serena tools through MCP.
"""

from pathlib import Path

from serena.tools.tools_base import Tool, ToolMarkerOptional


class InvokeBmadAgentTool(Tool, ToolMarkerOptional):
    """Invoke a BMAD agent workflow."""

    def apply(self, agent_name: str, prompt: str) -> str:
        """
        Invoke a BMAD agent with a prompt.

        :param agent_name: Name of the BMAD agent (e.g., "dev", "architect", "qa")
        :param prompt: The prompt to send to the agent
        :return: Agent output/result
        """
        project_root = self.get_project_root()
        bmad_dir = Path(project_root) / "_bmad"

        if not bmad_dir.exists():
            return f"BMAD not found: {bmad_dir} does not exist"

        # Find agent by name across all BMAD modules
        agent_file = self._find_agent_file(bmad_dir, agent_name)
        if not agent_file:
            return f"BMAD agent '{agent_name}' not found in {bmad_dir}"

        # Invoke agent via bmad CLI or Python API
        try:
            result = self._invoke_agent(agent_file, prompt)
            return result
        except Exception as e:
            return f"Error invoking BMAD agent '{agent_name}': {e!s}"

    @staticmethod
    def _find_agent_file(bmad_dir: Path, agent_name: str) -> Path | None:
        """Find agent markdown file by name."""
        # Search in all BMAD modules
        for agent_file in bmad_dir.rglob(f"{agent_name}.md"):
            if "agents" in agent_file.parts:
                return agent_file
        return None

    @staticmethod
    def _invoke_agent(agent_file: Path, prompt: str) -> str:
        """Invoke agent and return output.

        This is a placeholder that needs actual BMAD integration.
        For now, it returns the agent path and prompt for demonstration.
        """
        # TODO: Integrate with actual BMAD agent executor
        # This would invoke the agent via BMAD's CLI or Python API
        # and return the result.

        return (
            f"BMAD Agent: {agent_file.stem}\n"
            f"Agent File: {agent_file}\n"
            f"Prompt: {prompt}\n\n"
            f"[Agent would be executed here via BMAD executor]\n"
            f"To fully integrate, connect to BMAD agent runner."
        )


class ListBmadAgentsTool(Tool, ToolMarkerOptional):
    """List available BMAD agents."""

    def apply(self) -> str:
        """
        List all available BMAD agents in the project.

        :return: Formatted list of available agents
        """
        project_root = self.get_project_root()
        bmad_dir = Path(project_root) / "_bmad"

        if not bmad_dir.exists():
            return f"BMAD not found: {bmad_dir} does not exist"

        agents = self._collect_agents(bmad_dir)
        if not agents:
            return "No BMAD agents found"

        # Group by module
        by_module: dict[str, list[str]] = {}
        for agent_path in sorted(agents):
            module = agent_path.parts[0]  # e.g., "bmm", "gds", "tea"
            if module not in by_module:
                by_module[module] = []
            by_module[module].append(agent_path.stem)

        # Format output
        result = "Available BMAD Agents:\n\n"
        for module in sorted(by_module.keys()):
            result += f"**{module.upper()}** ({len(by_module[module])} agents)\n"
            for agent_name in sorted(by_module[module]):
                result += f"  - {agent_name}\n"
            result += "\n"

        return result

    @staticmethod
    def _collect_agents(bmad_dir: Path) -> list[Path]:
        """Collect all agent markdown files."""
        agents = []
        for agent_file in bmad_dir.rglob("*.md"):
            if "agents" in agent_file.parts:
                agents.append(agent_file)
        return agents


class BmadAgentInfoTool(Tool, ToolMarkerOptional):
    """Get information about a BMAD agent."""

    def apply(self, agent_name: str) -> str:
        """
        Get information about a specific BMAD agent.

        :param agent_name: Name of the BMAD agent
        :return: Agent information (description, capabilities, etc.)
        """
        project_root = self.get_project_root()
        bmad_dir = Path(project_root) / "_bmad"

        agent_file = InvokeBmadAgentTool._find_agent_file(bmad_dir, agent_name)
        if not agent_file:
            return f"BMAD agent '{agent_name}' not found"

        try:
            content = agent_file.read_text()
            # Extract description and <mcp-tools> info
            lines = content.split("\n")

            result = f"**BMAD Agent: {agent_name}**\n"
            result += f"File: {agent_file.relative_to(bmad_dir)}\n\n"

            # Extract description (first few lines after title)
            in_description = False
            description_lines = []
            for line in lines:
                if line.startswith("# "):
                    in_description = True
                    continue
                if in_description:
                    if line.startswith("<") or not line.strip():
                        break
                    description_lines.append(line)

            if description_lines:
                result += "**Description:**\n"
                result += "\n".join(description_lines[:5]).strip() + "\n\n"

            # Extract MCP tools info
            if "<mcp-tools" in content:
                result += "**MCP Tools:** Available\n"
                if 'tier="full"' in content:
                    result += "  - Tier: Full Access\n"
                elif 'tier="read-only"' in content:
                    result += "  - Tier: Read-Only\n"

            return result
        except Exception as e:
            return f"Error reading agent info: {e!s}"
