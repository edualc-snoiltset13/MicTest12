"""
Sudoku solver using constraint propagation and MRV backtracking.

Cells are indexed 0..80 row-major. Candidates per cell are 9-bit bitmasks
where bit (d-1) is set iff digit d is still possible. Propagation applies
naked singles (cell down to one candidate -> eliminate from peers) and
hidden singles (digit has one remaining slot in a unit -> assign).
Search uses minimum-remaining-values to pick the next branching cell.
"""

from typing import List, Optional

ALL_DIGITS = 0x1FF  # bits 0..8 set = digits 1..9 all candidate


def _build_units():
    rows = [[r * 9 + c for c in range(9)] for r in range(9)]
    cols = [[r * 9 + c for r in range(9)] for c in range(9)]
    boxes = [
        [(br * 3 + dr) * 9 + (bc * 3 + dc) for dr in range(3) for dc in range(3)]
        for br in range(3) for bc in range(3)
    ]
    return rows + cols + boxes


UNITS = _build_units()
UNITS_OF: List[List[List[int]]] = [[] for _ in range(81)]
for _u in UNITS:
    for _cell in _u:
        UNITS_OF[_cell].append(_u)

PEERS: List[frozenset] = []
for _cell in range(81):
    _p = set()
    for _u in UNITS_OF[_cell]:
        _p.update(_u)
    _p.discard(_cell)
    PEERS.append(frozenset(_p))


class _Contradiction(Exception):
    pass


def _bits(b: int):
    while b:
        lsb = b & -b
        yield lsb
        b ^= lsb


def _assign(cands: List[int], cell: int, digit_bit: int) -> None:
    if not (cands[cell] & digit_bit):
        raise _Contradiction
    other = cands[cell] ^ digit_bit
    for bit in _bits(other):
        _eliminate(cands, cell, bit)


def _eliminate(cands: List[int], cell: int, digit_bit: int) -> None:
    if not (cands[cell] & digit_bit):
        return
    cands[cell] ^= digit_bit
    remaining = cands[cell]
    if remaining == 0:
        raise _Contradiction
    if remaining & (remaining - 1) == 0:
        # naked single: propagate to peers
        for p in PEERS[cell]:
            _eliminate(cands, p, remaining)
    # hidden single: in each unit, digit_bit must land somewhere
    for unit in UNITS_OF[cell]:
        places = [c for c in unit if cands[c] & digit_bit]
        if not places:
            raise _Contradiction
        if len(places) == 1:
            target = places[0]
            if cands[target] != digit_bit:
                _assign(cands, target, digit_bit)


def parse(puzzle: str) -> List[int]:
    digits = [c for c in puzzle if c in "0123456789."]
    if len(digits) != 81:
        raise ValueError(f"expected 81 cells, got {len(digits)}")
    return [0 if c in "0." else int(c) for c in digits]


def _initial_candidates(grid: List[int]) -> List[int]:
    cands = [ALL_DIGITS] * 81
    for cell, d in enumerate(grid):
        if d:
            _assign(cands, cell, 1 << (d - 1))
    return cands


def _search(cands: List[int]) -> Optional[List[int]]:
    target = -1
    best = 10
    for c in range(81):
        v = cands[c]
        if v & (v - 1):  # more than one bit set
            n = bin(v).count("1")
            if n < best:
                best = n
                target = c
                if n == 2:
                    break
    if target == -1:
        return cands
    for bit in _bits(cands[target]):
        trial = cands[:]
        try:
            _assign(trial, target, bit)
        except _Contradiction:
            continue
        result = _search(trial)
        if result is not None:
            return result
    return None


def solve(puzzle: str) -> Optional[str]:
    """Solve an 81-char puzzle string. Returns the 81-digit solution or None."""
    grid = parse(puzzle)
    try:
        cands = _initial_candidates(grid)
    except _Contradiction:
        return None
    result = _search(cands)
    if result is None:
        return None
    return "".join(str(b.bit_length()) for b in result)


if __name__ == "__main__":
    import sys
    puzzle = sys.stdin.read().strip() if not sys.stdin.isatty() else (
        "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
    )
    sol = solve(puzzle)
    if sol is None:
        print("no solution")
        sys.exit(1)
    for r in range(9):
        print(" ".join(sol[r * 9:(r + 1) * 9]))
