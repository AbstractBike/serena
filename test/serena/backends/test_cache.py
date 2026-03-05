import os
import tempfile
import time

from serena.backends.treesitter.cache import AstCache
from serena.backends.treesitter.engine import SymbolEngine


def test_cache_hit():
    engine = SymbolEngine()
    cache = AstCache()

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("def hello():\n    pass\n")
        path = f.name

    try:
        symbols1 = cache.get_symbols(path, engine)
        symbols2 = cache.get_symbols(path, engine)
        assert len(symbols1) == 1
        assert symbols1[0].name == "hello"
        # second call should be from cache (same result)
        assert [s.name for s in symbols2] == [s.name for s in symbols1]
    finally:
        os.unlink(path)


def test_cache_invalidation_on_mtime_change():
    engine = SymbolEngine()
    cache = AstCache()

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("def alpha():\n    pass\n")
        path = f.name

    try:
        symbols1 = cache.get_symbols(path, engine)
        assert symbols1[0].name == "alpha"

        # modify the file
        time.sleep(0.05)
        with open(path, "w") as f:
            f.write("def beta():\n    pass\n")

        symbols2 = cache.get_symbols(path, engine)
        assert symbols2[0].name == "beta"
    finally:
        os.unlink(path)
