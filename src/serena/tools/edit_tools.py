"""Line-level file editing tools and syntax validation.

These tools are available with both LSP and TreeSitter backends.
"""

import os
import subprocess

from serena.tools.tools_base import SUCCESS_RESULT, Tool, ToolMarkerCanEdit, ToolMarkerOptional


def replace_lines_in_file(path: str, start_line: int, end_line: int, new_content: str) -> None:
    """Replace lines start_line..end_line (1-based, inclusive) with new_content."""
    with open(path) as f:
        lines = f.readlines()
    before = lines[: start_line - 1]
    after = lines[end_line:]
    new_lines = new_content.splitlines(keepends=True)
    if new_content and not new_content.endswith("\n"):
        new_lines[-1] += "\n"
    with open(path, "w") as f:
        f.writelines(before + new_lines + after)


def delete_lines_in_file(path: str, start_line: int, end_line: int) -> None:
    """Delete lines start_line..end_line (1-based, inclusive)."""
    with open(path) as f:
        lines = f.readlines()
    before = lines[: start_line - 1]
    after = lines[end_line:]
    with open(path, "w") as f:
        f.writelines(before + after)


def insert_at_line_in_file(path: str, line: int, content: str) -> None:
    """Insert content before the given line (1-based)."""
    with open(path) as f:
        lines = f.readlines()
    new_lines = content.splitlines(keepends=True)
    if content and not content.endswith("\n"):
        new_lines[-1] += "\n"
    lines[line - 1 : line - 1] = new_lines
    with open(path, "w") as f:
        f.writelines(lines)


class ReplaceLinesTool(Tool, ToolMarkerCanEdit):
    """Replace a range of lines in a file."""

    def apply(self, relative_path: str, start_line: int, end_line: int, new_content: str) -> str:
        """
        Replace lines start_line through end_line (1-based, inclusive) with new_content.

        :param relative_path: relative path to the file
        :param start_line: first line to replace (1-based)
        :param end_line: last line to replace (1-based, inclusive)
        :param new_content: replacement text
        """
        abs_path = os.path.join(self.get_project_root(), relative_path)
        replace_lines_in_file(abs_path, start_line, end_line, new_content)
        return SUCCESS_RESULT


class DeleteLinesTool(Tool, ToolMarkerCanEdit):
    """Delete a range of lines from a file."""

    def apply(self, relative_path: str, start_line: int, end_line: int) -> str:
        """
        Delete lines start_line through end_line (1-based, inclusive).

        :param relative_path: relative path to the file
        :param start_line: first line to delete (1-based)
        :param end_line: last line to delete (1-based, inclusive)
        """
        abs_path = os.path.join(self.get_project_root(), relative_path)
        delete_lines_in_file(abs_path, start_line, end_line)
        return SUCCESS_RESULT


class InsertAtLineTool(Tool, ToolMarkerCanEdit):
    """Insert text at a specific line in a file."""

    def apply(self, relative_path: str, line: int, content: str) -> str:
        """
        Insert content before the given line number (1-based).

        :param relative_path: relative path to the file
        :param line: line number before which to insert (1-based)
        :param content: text to insert
        """
        abs_path = os.path.join(self.get_project_root(), relative_path)
        insert_at_line_in_file(abs_path, line, content)
        return SUCCESS_RESULT


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
