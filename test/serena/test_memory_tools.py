"""P0 tests for MemoriesManager — full CRUD lifecycle and edge cases."""

from pathlib import Path

import pytest

from serena.project import MemoriesManager


@pytest.fixture()
def mem_manager(tmp_path: Path) -> MemoriesManager:
    """Create a MemoriesManager backed by a temporary directory."""
    serena_data = tmp_path / ".serena"
    serena_data.mkdir()
    return MemoriesManager(serena_data_folder=str(serena_data))


class TestMemoryWriteAndRead:
    def test_write_then_read(self, mem_manager: MemoriesManager):
        result = mem_manager.save_memory("notes", "hello world", is_tool_context=False)
        assert "written" in result.lower()
        content = mem_manager.load_memory("notes")
        assert content == "hello world"

    def test_read_nonexistent_returns_hint(self, mem_manager: MemoriesManager):
        result = mem_manager.load_memory("does_not_exist")
        assert "not found" in result.lower()

    def test_overwrite_existing_memory(self, mem_manager: MemoriesManager):
        mem_manager.save_memory("notes", "v1", is_tool_context=False)
        mem_manager.save_memory("notes", "v2", is_tool_context=False)
        assert mem_manager.load_memory("notes") == "v2"


class TestMemoryList:
    def test_list_empty(self, mem_manager: MemoriesManager):
        assert mem_manager.list_project_memories() == []

    def test_list_after_writes(self, mem_manager: MemoriesManager):
        mem_manager.save_memory("alpha", "a", is_tool_context=False)
        mem_manager.save_memory("beta", "b", is_tool_context=False)
        memories = mem_manager.list_memories()
        assert "alpha" in memories
        assert "beta" in memories

    def test_list_with_topic_filter(self, mem_manager: MemoriesManager):
        mem_manager.save_memory("auth/login", "login logic", is_tool_context=False)
        mem_manager.save_memory("auth/session", "session logic", is_tool_context=False)
        mem_manager.save_memory("other", "other stuff", is_tool_context=False)
        filtered = mem_manager.list_memories(topic="auth")
        assert len(filtered) == 2
        assert all("auth/" in m for m in filtered)


class TestMemoryDelete:
    def test_delete_existing(self, mem_manager: MemoriesManager):
        mem_manager.save_memory("temp", "data", is_tool_context=False)
        result = mem_manager.delete_memory("temp", is_tool_context=False)
        assert "deleted" in result.lower()
        assert "not found" in mem_manager.load_memory("temp").lower()

    def test_delete_nonexistent(self, mem_manager: MemoriesManager):
        result = mem_manager.delete_memory("ghost", is_tool_context=False)
        assert "not found" in result.lower()


class TestMemoryRename:
    def test_rename_success(self, mem_manager: MemoriesManager):
        mem_manager.save_memory("old_name", "content", is_tool_context=False)
        result = mem_manager.move_memory("old_name", "new_name", is_tool_context=False)
        assert "renamed" in result.lower()
        assert mem_manager.load_memory("new_name") == "content"
        assert "not found" in mem_manager.load_memory("old_name").lower()

    def test_rename_to_existing_raises(self, mem_manager: MemoriesManager):
        mem_manager.save_memory("a", "1", is_tool_context=False)
        mem_manager.save_memory("b", "2", is_tool_context=False)
        with pytest.raises(FileExistsError):
            mem_manager.move_memory("a", "b", is_tool_context=False)

    def test_rename_nonexistent_raises(self, mem_manager: MemoriesManager):
        with pytest.raises(FileNotFoundError):
            mem_manager.move_memory("ghost", "new", is_tool_context=False)


class TestMemoryEditLiteral:
    def test_literal_replace(self, mem_manager: MemoriesManager):
        mem_manager.save_memory("doc", "Hello World", is_tool_context=False)
        result = mem_manager.edit_memory("doc", "World", "Python", mode="literal", allow_multiple_occurrences=False, is_tool_context=False)
        assert "edited" in result.lower()
        assert mem_manager.load_memory("doc") == "Hello Python"

    def test_literal_no_match_raises(self, mem_manager: MemoriesManager):
        mem_manager.save_memory("doc", "Hello World", is_tool_context=False)
        with pytest.raises(ValueError, match="No matches"):
            mem_manager.edit_memory("doc", "MISSING", "repl", mode="literal", allow_multiple_occurrences=False, is_tool_context=False)


class TestMemoryEditRegex:
    def test_regex_replace(self, mem_manager: MemoriesManager):
        mem_manager.save_memory("doc", "version: 1.0.0", is_tool_context=False)
        mem_manager.edit_memory(
            "doc", r"version: \d+\.\d+\.\d+", "version: 2.0.0", mode="regex", allow_multiple_occurrences=False, is_tool_context=False
        )
        assert mem_manager.load_memory("doc") == "version: 2.0.0"

    def test_regex_multiple_disallowed_raises(self, mem_manager: MemoriesManager):
        mem_manager.save_memory("doc", "foo bar foo", is_tool_context=False)
        with pytest.raises(ValueError, match="occurrences"):
            mem_manager.edit_memory("doc", "foo", "baz", mode="regex", allow_multiple_occurrences=False, is_tool_context=False)

    def test_regex_multiple_allowed(self, mem_manager: MemoriesManager):
        mem_manager.save_memory("doc", "foo bar foo", is_tool_context=False)
        mem_manager.edit_memory("doc", "foo", "baz", mode="regex", allow_multiple_occurrences=True, is_tool_context=False)
        assert mem_manager.load_memory("doc") == "baz bar baz"

    def test_edit_nonexistent_raises(self, mem_manager: MemoriesManager):
        with pytest.raises(FileNotFoundError):
            mem_manager.edit_memory("ghost", "a", "b", mode="literal", allow_multiple_occurrences=False, is_tool_context=False)


class TestMemoryMaxCharsAndGlobal:
    def test_global_write_blocked_in_tool_context(self, mem_manager: MemoriesManager):
        with pytest.raises(PermissionError):
            mem_manager.save_memory("global/shared", "data", is_tool_context=True)

    def test_global_write_allowed_when_configured(self, tmp_path: Path):
        serena_data = tmp_path / ".serena"
        serena_data.mkdir()
        mgr = MemoriesManager(serena_data_folder=str(serena_data), global_memory_tool_write_access=True)
        result = mgr.save_memory("global/shared", "data", is_tool_context=True)
        assert "written" in result.lower()

    def test_bare_global_raises(self, mem_manager: MemoriesManager):
        with pytest.raises(ValueError, match="not a valid memory name"):
            mem_manager.get_memory_file_path("global")
