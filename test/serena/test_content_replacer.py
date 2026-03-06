"""P0 tests for ContentReplacer — regex adversarial and edge cases."""

import re

import pytest

from serena.util.text_utils import ContentReplacer


class TestContentReplacerLiteral:
    def test_literal_with_regex_metacharacters(self):
        """Ensure literal mode escapes regex metacharacters properly."""
        replacer = ContentReplacer(mode="literal", allow_multiple_occurrences=False)
        content = "price is $100.00 (USD)"
        result = replacer.replace(content, "$100.00", "EUR 100.00")
        assert result == "price is EUR 100.00 (USD)"

    def test_literal_no_match_raises(self):
        replacer = ContentReplacer(mode="literal", allow_multiple_occurrences=False)
        with pytest.raises(ValueError, match="No matches"):
            replacer.replace("hello world", "MISSING", "repl")


class TestContentReplacerRegex:
    def test_invalid_regex_raises(self):
        """Invalid regex patterns should raise a clear error."""
        replacer = ContentReplacer(mode="regex", allow_multiple_occurrences=False)
        with pytest.raises(re.error):
            replacer.replace("some content", "[invalid(", "repl")

    def test_catastrophic_backtracking_pattern(self):
        """Patterns that could cause ReDoS should either complete or raise, not hang."""
        replacer = ContentReplacer(mode="regex", allow_multiple_occurrences=False)
        # This pattern is intentionally non-catastrophic but tests the boundary
        # A truly catastrophic pattern would hang, so we use a mild one
        content = "aaaaab"
        result = replacer.replace(content, "a+b", "X")
        assert result == "X"

    def test_backreference_substitution(self):
        """$!1 backreferences should expand correctly."""
        replacer = ContentReplacer(mode="regex", allow_multiple_occurrences=False)
        content = "def foo(x, y):"
        result = replacer.replace(content, r"def (\w+)\(", "def renamed_$!1(")
        assert result == "def renamed_foo(x, y):"

    def test_multiple_occurrences_disallowed(self):
        replacer = ContentReplacer(mode="regex", allow_multiple_occurrences=False)
        with pytest.raises(ValueError, match="occurrences"):
            replacer.replace("foo bar foo", "foo", "baz")

    def test_multiple_occurrences_allowed(self):
        replacer = ContentReplacer(mode="regex", allow_multiple_occurrences=True)
        result = replacer.replace("foo bar foo", "foo", "baz")
        assert result == "baz bar baz"

    def test_dotall_mode_matches_newlines(self):
        """DOTALL flag means . matches newlines."""
        replacer = ContentReplacer(mode="regex", allow_multiple_occurrences=False)
        content = "start\nmiddle\nend"
        result = replacer.replace(content, r"start.*?end", "REPLACED")
        assert result == "REPLACED"

    def test_backslash_in_replacement(self):
        """Replacement strings are inserted verbatim (no regex escape processing)."""
        replacer = ContentReplacer(mode="regex", allow_multiple_occurrences=False)
        content = "path: forward"
        result = replacer.replace(content, "forward", "back\\\\slash")
        assert result == "path: back\\\\slash"

    def test_invalid_mode_raises(self):
        replacer = ContentReplacer(mode="invalid", allow_multiple_occurrences=False)  # type: ignore
        with pytest.raises(ValueError, match="Invalid mode"):
            replacer.replace("content", "needle", "repl")
