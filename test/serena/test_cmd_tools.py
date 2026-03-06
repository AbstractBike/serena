"""P0 tests for ExecuteShellCommandTool and shell utilities."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from serena.tools.cmd_tools import ExecuteShellCommandTool
from serena.util.shell import ShellCommandResult, execute_shell_command


def _make_cmd_tool(project_root: str) -> ExecuteShellCommandTool:
    """Create an ExecuteShellCommandTool with mocked agent."""
    tool = object.__new__(ExecuteShellCommandTool)
    tool.agent = MagicMock()
    tool.agent.serena_config.default_max_tool_answer_chars = 50000
    tool.get_project_root = lambda: project_root  # type: ignore
    return tool


class TestShellCommandResult:
    def test_successful_command(self):
        result = execute_shell_command("echo hello", cwd="/tmp")
        assert result.return_code == 0
        assert "hello" in result.stdout

    def test_failed_command(self):
        result = execute_shell_command("false", cwd="/tmp")
        assert result.return_code != 0

    def test_stderr_capture(self):
        result = execute_shell_command("echo err >&2", cwd="/tmp", capture_stderr=True)
        assert result.stderr is not None
        assert "err" in result.stderr

    def test_result_json_serialization(self):
        result = ShellCommandResult(stdout="out", return_code=0, cwd="/tmp", stderr="err")
        parsed = json.loads(result.json())
        assert parsed["stdout"] == "out"
        assert parsed["return_code"] == 0
        assert parsed["stderr"] == "err"


class TestExecuteShellCommandTool:
    def test_default_cwd_is_project_root(self, tmp_path: Path):
        tool = _make_cmd_tool(str(tmp_path))
        result = tool.apply("pwd")
        parsed = json.loads(result)
        assert parsed["cwd"] == str(tmp_path)

    def test_absolute_cwd(self, tmp_path: Path):
        subdir = tmp_path / "sub"
        subdir.mkdir()
        tool = _make_cmd_tool(str(tmp_path))
        result = tool.apply("pwd", cwd=str(subdir))
        parsed = json.loads(result)
        assert parsed["cwd"] == str(subdir)

    def test_relative_cwd(self, tmp_path: Path):
        subdir = tmp_path / "mydir"
        subdir.mkdir()
        tool = _make_cmd_tool(str(tmp_path))
        result = tool.apply("pwd", cwd="mydir")
        parsed = json.loads(result)
        assert str(subdir) in parsed["cwd"]

    def test_relative_cwd_not_found_raises(self, tmp_path: Path):
        tool = _make_cmd_tool(str(tmp_path))
        with pytest.raises(FileNotFoundError):
            tool.apply("pwd", cwd="nonexistent_dir")

    def test_command_output_in_json(self, tmp_path: Path):
        tool = _make_cmd_tool(str(tmp_path))
        result = tool.apply("echo test_output_42")
        parsed = json.loads(result)
        assert "test_output_42" in parsed["stdout"]
        assert parsed["return_code"] == 0
