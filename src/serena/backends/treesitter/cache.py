"""Mtime-based AST cache for tree-sitter parsed symbols."""

import os
import threading
from pathlib import Path

from serena.backends.treesitter.engine import SymbolBounds, SymbolEngine


class AstCache:
    """Thread-safe mtime-based cache keyed by absolute file path."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: dict[str, tuple[float, str, list[SymbolBounds]]] = {}

    def get_or_parse(self, path: str, engine: SymbolEngine) -> tuple[str, list[SymbolBounds]]:
        """Return (content, symbols), using cache if mtime matches."""
        abs_path = os.path.abspath(path)
        mtime = os.path.getmtime(abs_path)

        with self._lock:
            entry = self._entries.get(abs_path)
            if entry is not None and entry[0] == mtime:
                return entry[1], entry[2]

        content = Path(abs_path).read_text()
        ext = Path(abs_path).suffix.lstrip(".")
        symbols = engine.parse(content, ext)

        with self._lock:
            self._entries[abs_path] = (mtime, content, symbols)

        return content, symbols

    def get_symbols(self, path: str, engine: SymbolEngine) -> list[SymbolBounds]:
        """Convenience: return only symbols for a path."""
        _, symbols = self.get_or_parse(path, engine)
        return symbols
