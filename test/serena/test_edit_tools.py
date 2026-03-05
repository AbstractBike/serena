import os
import tempfile

from serena.tools.edit_tools import delete_lines_in_file, insert_at_line_in_file, replace_lines_in_file


def test_replace_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("line1\nline2\nline3\nline4\n")
        path = f.name
    try:
        replace_lines_in_file(path, 2, 3, "replaced2\nreplaced3\n")
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
        delete_lines_in_file(path, 2, 3)
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
        insert_at_line_in_file(path, 2, "inserted\n")
        with open(path) as fh:
            result = fh.read()
        assert result == "line1\ninserted\nline2\n"
    finally:
        os.unlink(path)
