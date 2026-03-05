"""Fuzzy symbol matching: Exact > CaseInsensitive > CamelCase > Levenshtein.

Port of codegate src/symbols/fuzzy.rs.
"""

from dataclasses import dataclass
from enum import IntEnum

from serena.backends.treesitter.engine import SymbolBounds


class MatchType(IntEnum):
    EXACT = 0
    CASE_INSENSITIVE = 1
    CAMEL_CASE = 2
    FUZZY = 3


@dataclass
class FuzzyMatch:
    symbol: SymbolBounds
    distance: int
    match_type: MatchType


def levenshtein(a: str, b: str) -> int:
    """Standard Levenshtein edit distance."""
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    curr = [0] * (len(b) + 1)

    for i, ca in enumerate(a):
        curr[0] = i + 1
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr[j + 1] = min(prev[j] + cost, prev[j + 1] + 1, curr[j] + 1)
        prev, curr = curr, prev

    return prev[len(b)]


def _extract_initials(name: str) -> str:
    if "_" in name:
        return "".join(part[0] for part in name.split("_") if part)
    initials = []
    for i, c in enumerate(name):
        if i == 0 or c.isupper():
            initials.append(c)
    return "".join(initials)


def camel_case_matches(query: str, candidate: str) -> bool:
    """Check if query matches CamelCase or snake_case initials of candidate."""
    if not query:
        return False
    initials = _extract_initials(candidate)
    return initials.lower().startswith(query.lower())


def find_fuzzy_matches(
    query: str,
    symbols: list[SymbolBounds],
    max_distance: int,
) -> list[FuzzyMatch]:
    """Find fuzzy matches sorted by relevance."""
    query_lower = query.lower()
    matches: list[FuzzyMatch] = []

    for symbol in symbols:
        name = symbol.name
        if name == query:
            matches.append(FuzzyMatch(symbol=symbol, distance=0, match_type=MatchType.EXACT))
        elif name.lower() == query_lower:
            matches.append(FuzzyMatch(symbol=symbol, distance=0, match_type=MatchType.CASE_INSENSITIVE))
        elif camel_case_matches(query, name):
            matches.append(FuzzyMatch(symbol=symbol, distance=0, match_type=MatchType.CAMEL_CASE))
        else:
            dist = levenshtein(query, name)
            if dist <= max_distance:
                matches.append(FuzzyMatch(symbol=symbol, distance=dist, match_type=MatchType.FUZZY))

    matches.sort(key=lambda m: (m.match_type, m.distance, m.symbol.name))
    return matches
