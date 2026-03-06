from serena.backends.treesitter.engine import SymbolEngine


def test_parse_python_function():
    engine = SymbolEngine()
    source = "def hello():\n    pass\n"
    symbols = engine.parse(source, "py")
    assert len(symbols) == 1
    assert symbols[0].name == "hello"
    assert symbols[0].kind == "function"
    assert symbols[0].line == 1
    assert symbols[0].end_line == 2


def test_parse_python_class():
    engine = SymbolEngine()
    source = "class Foo:\n    def bar(self):\n        pass\n"
    symbols = engine.parse(source, "py")
    assert len(symbols) == 2
    assert symbols[0].name == "Foo"
    assert symbols[0].kind == "class"
    assert symbols[1].name == "bar"
    assert symbols[1].kind == "function"


def test_parse_rust_struct_and_fn():
    engine = SymbolEngine()
    source = "struct Cfg {}\nfn main() {}\n"
    symbols = engine.parse(source, "rs")
    assert len(symbols) == 2
    names = [s.name for s in symbols]
    assert "Cfg" in names
    assert "main" in names


def test_unsupported_extension():
    engine = SymbolEngine()
    symbols = engine.parse("content", "xyz")
    assert symbols == []


def test_find_symbol():
    engine = SymbolEngine()
    source = "def alpha():\n    pass\ndef beta():\n    pass\n"
    result = engine.find_symbol(source, "py", "beta")
    assert result is not None
    assert result.name == "beta"


def test_find_symbol_not_found():
    engine = SymbolEngine()
    source = "def alpha():\n    pass\n"
    result = engine.find_symbol(source, "py", "nope")
    assert result is None
