import os
import tempfile


def _replace_lines(path: str, start_line: int, end_line: int, new_content: str) -> None:
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


def _delete_lines(path: str, start_line: int, end_line: int) -> None:
    """Delete lines start_line..end_line (1-based, inclusive)."""
    with open(path) as f:
        lines = f.readlines()
    before = lines[: start_line - 1]
    after = lines[end_line:]
    with open(path, "w") as f:
        f.writelines(before + after)


def _insert_at_line(path: str, line: int, content: str) -> None:
    """Insert content before the given line (1-based)."""
    with open(path) as f:
        lines = f.readlines()
    new_lines = content.splitlines(keepends=True)
    if content and not content.endswith("\n"):
        new_lines[-1] += "\n"
    lines[line - 1 : line - 1] = new_lines
    with open(path, "w") as f:
        f.writelines(lines)


def test_replace_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("line1\nline2\nline3\nline4\n")
        path = f.name
    try:
        _replace_lines(path, 2, 3, "replaced2\nreplaced3\n")
        with open(path) as fh:
            result = fh.read()
        assert result == "line1\nreplaced2\nreplaced3\nline4\n"
    finally:
        os.unlink(path)


def test_delete_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("line1\nline2\nline3\nline4\n")
        path = f.name
    try:
        _delete_lines(path, 2, 3)
        with open(path) as fh:
            result = fh.read()
        assert result == "line1\nline4\n"
    finally:
        os.unlink(path)


def test_insert_at_line():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("line1\nline2\n")
        path = f.name
    try:
        _insert_at_line(path, 2, "inserted\n")
        with open(path) as fh:
            result = fh.read()
        assert result == "line1\ninserted\nline2\n"
    finally:
        os.unlink(path)
