"""Syntax validation and structural search tools.

These tools complement the existing line-level edit tools in file_tools.py.
"""

import os
import subprocess

from serena.tools.tools_base import Tool, ToolMarkerOptional


class ValidateSyntaxTool(Tool, ToolMarkerOptional):
    """Validate syntax of a source file using tree-sitter."""

    def apply(self, relative_path: str) -> str:
        """
        Parse the file with tree-sitter and report any syntax errors.

        :param relative_path: relative path to the file to validate
        """
        from serena.backends.treesitter.engine import SymbolEngine

        abs_path = os.path.join(self.get_project_root(), relative_path)
        ext = os.path.splitext(abs_path)[1].lstrip(".")

        with open(abs_path) as f:
            source = f.read()

        engine = SymbolEngine()
        result = engine._get_parser_and_query(ext)
        if result is None:
            return f"Unsupported file extension: {ext}"

        parser, _lang, _query = result
        tree = parser.parse(source.encode())

        errors: list[str] = []

        def _collect_errors(node) -> None:  # type: ignore[no-untyped-def]
            if node.type == "ERROR" or node.is_missing:
                errors.append(f"line {node.start_point[0] + 1}: syntax error at '{node.text.decode()[:50]}'")
            for child in node.children:
                _collect_errors(child)

        _collect_errors(tree.root_node)

        if not errors:
            return "Syntax OK"
        return "Syntax errors found:\n" + "\n".join(errors)


class SearchStructuralTool(Tool, ToolMarkerOptional):
    """Structural code search using ast-grep (sg)."""

    def apply(self, pattern: str, relative_path: str = ".") -> str:
        """
        Search for structural code patterns using ast-grep.
        Requires `sg` binary in PATH.

        :param pattern: ast-grep pattern to search for
        :param relative_path: directory or file to search in (relative to project root)
        """
        search_path = os.path.join(self.get_project_root(), relative_path)
        try:
            result = subprocess.run(
                ["sg", "--pattern", pattern, search_path],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0 and result.stderr:
                return f"ast-grep error: {result.stderr.strip()}"
            return result.stdout if result.stdout else "No matches found."
        except FileNotFoundError:
            return "ast-grep (sg) not found in PATH. Install it to use structural search."
