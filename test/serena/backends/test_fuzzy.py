from serena.backends.treesitter.engine import SymbolBounds
from serena.backends.treesitter.fuzzy import MatchType, camel_case_matches, find_fuzzy_matches, levenshtein


def _sym(name: str) -> SymbolBounds:
    return SymbolBounds(name=name, kind="function", line=1, end_line=5)


def test_exact_match_first():
    symbols = [_sym("connect"), _sym("Connect"), _sym("conn")]
    results = find_fuzzy_matches("connect", symbols, max_distance=3)
    assert results[0].match_type == MatchType.EXACT
    assert results[0].symbol.name == "connect"
    assert results[1].match_type == MatchType.CASE_INSENSITIVE
    assert results[1].symbol.name == "Connect"


def test_camel_case_matching():
    symbols = [_sym("GetSymbol"), _sym("GlobalState"), _sym("get_symbols_overview")]
    results = find_fuzzy_matches("GS", symbols, max_distance=5)
    camel_names = [r.symbol.name for r in results if r.match_type == MatchType.CAMEL_CASE]
    assert "GetSymbol" in camel_names
    assert "GlobalState" in camel_names

    results = find_fuzzy_matches("gso", symbols, max_distance=5)
    camel_names = [r.symbol.name for r in results if r.match_type == MatchType.CAMEL_CASE]
    assert "get_symbols_overview" in camel_names


def test_levenshtein():
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein("", "abc") == 3
    assert levenshtein("abc", "abc") == 0


def test_levenshtein_fuzzy():
    symbols = [_sym("process"), _sym("progres"), _sym("unrelated")]
    results = find_fuzzy_matches("progress", symbols, max_distance=3)
    fuzzy = [(r.symbol.name, r.distance) for r in results if r.match_type == MatchType.FUZZY]
    assert any(n == "progres" and d == 1 for n, d in fuzzy)
    assert any(n == "process" and d == 2 for n, d in fuzzy)
    assert not any(n == "unrelated" for n, _ in fuzzy)


def test_camel_case_snake():
    assert camel_case_matches("gso", "get_symbols_overview")
    assert not camel_case_matches("xyz", "get_symbols_overview")


def test_camel_case_upper():
    assert camel_case_matches("GS", "GetSymbol")
    assert camel_case_matches("gs", "GetSymbol")
