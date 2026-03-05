"""Tree-sitter based symbol extraction engine.

Port of codegate src/symbols/engine.rs — uses tree-sitter queries to extract
top-level symbol definitions (classes, functions, etc.) from source code.
"""

from dataclasses import dataclass
from pathlib import Path

import tree_sitter

_QUERIES_DIR = Path(__file__).parent / "queries"

# Language registry: extension -> (module_name, query_file)
# Languages are lazily loaded to avoid import errors for missing grammars.
_LANGUAGE_MAP: dict[str, tuple[str, str]] = {
    "py": ("tree_sitter_python", "python.scm"),
    "rs": ("tree_sitter_rust", "rust.scm"),
    "go": ("tree_sitter_go", "go.scm"),
    "java": ("tree_sitter_java", "java.scm"),
    "kt": ("tree_sitter_kotlin", "kotlin.scm"),
    "kts": ("tree_sitter_kotlin", "kotlin.scm"),
    "ts": ("tree_sitter_typescript", "typescript.scm"),
    "tsx": ("tree_sitter_typescript", "typescript.scm"),
    "js": ("tree_sitter_javascript", "typescript.scm"),
    "jsx": ("tree_sitter_javascript", "typescript.scm"),
}


@dataclass
class SymbolBounds:
    name: str
    kind: str  # "class" | "function" | "variable"
    line: int  # 1-based
    end_line: int  # 1-based


def _get_language(module_name: str) -> tree_sitter.Language:
    """Dynamically load a tree-sitter language from its Python package."""
    import importlib

    mod = importlib.import_module(module_name)
    # tree-sitter-python>=0.23 exposes language() function
    if hasattr(mod, "language"):
        return tree_sitter.Language(mod.language())
    raise ImportError(f"Cannot load tree-sitter language from {module_name}")


def _kind_for_node_kind(node_kind: str) -> str:
    if any(kw in node_kind for kw in ("class", "interface", "struct", "enum", "trait", "object")):
        return "class"
    if any(kw in node_kind for kw in ("function", "method", "fun")):
        return "function"
    return "variable"


class SymbolEngine:
    """Stateless tree-sitter symbol parser."""

    def __init__(self) -> None:
        self._parsers: dict[str, tree_sitter.Parser] = {}
        self._queries: dict[str, tuple[tree_sitter.Language, tree_sitter.Query]] = {}

    def _get_parser_and_query(
        self, ext: str
    ) -> tuple[tree_sitter.Parser, tree_sitter.Language, tree_sitter.Query] | None:
        entry = _LANGUAGE_MAP.get(ext)
        if entry is None:
            return None
        module_name, query_file = entry

        if ext not in self._parsers:
            try:
                lang = _get_language(module_name)
            except (ImportError, OSError):
                return None
            parser = tree_sitter.Parser(lang)
            query_src = (_QUERIES_DIR / query_file).read_text()
            query = tree_sitter.Query(lang, query_src)
            self._parsers[ext] = parser
            self._queries[ext] = (lang, query)

        parser = self._parsers[ext]
        lang, query = self._queries[ext]
        return parser, lang, query

    def parse(self, source: str, ext: str) -> list[SymbolBounds]:
        """Parse source code and return top-level symbol definitions."""
        result = self._get_parser_and_query(ext)
        if result is None:
            return []

        parser, _lang, query = result
        tree = parser.parse(source.encode())
        cursor = tree_sitter.QueryCursor(query)

        symbols: list[SymbolBounds] = []
        for match in cursor.matches(tree.root_node):
            captures = {
                name: node
                for name, nodes in match[1].items()
                for node in (nodes if isinstance(nodes, list) else [nodes])
            }

            name_node = captures.get("name")
            def_node = captures.get("def", name_node)

            if name_node is not None and def_node is not None:
                name = name_node.text.decode()
                kind = _kind_for_node_kind(def_node.type)
                line = def_node.start_point[0] + 1
                end_line = def_node.end_point[0] + 1
                symbols.append(SymbolBounds(name=name, kind=kind, line=line, end_line=end_line))

        return symbols

    def find_symbol(self, source: str, ext: str, name: str) -> SymbolBounds | None:
        """Find a symbol by exact name in source code."""
        symbols = self.parse(source, ext)
        return next((s for s in symbols if s.name == name), None)
