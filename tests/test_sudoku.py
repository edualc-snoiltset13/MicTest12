import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sudoku import solve, parse


EASY = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
EASY_SOL = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"

# Arto Inkala's "world's hardest" — needs deep propagation + search
HARD = "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."

INVALID_DUP_ROW = "11" + "." * 79  # two 1s in row 0


def _is_valid_solution(sol: str) -> bool:
    if len(sol) != 81 or any(c not in "123456789" for c in sol):
        return False
    rows = [sol[r * 9:(r + 1) * 9] for r in range(9)]
    cols = ["".join(sol[r * 9 + c] for r in range(9)) for c in range(9)]
    boxes = [
        "".join(sol[(br * 3 + dr) * 9 + (bc * 3 + dc)] for dr in range(3) for dc in range(3))
        for br in range(3) for bc in range(3)
    ]
    return all(sorted(g) == list("123456789") for g in rows + cols + boxes)


def test_parse_accepts_dots_and_zeros():
    g = parse("." * 81)
    assert g == [0] * 81
    g2 = parse("0" * 81)
    assert g2 == [0] * 81


def test_parse_rejects_wrong_length():
    try:
        parse("123")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_solve_easy():
    assert solve(EASY) == EASY_SOL


def test_solve_hard():
    sol = solve(HARD)
    assert sol is not None
    assert _is_valid_solution(sol)
    # The clue cells must match
    for i, c in enumerate(HARD):
        if c not in ".0":
            assert sol[i] == c


def test_solve_already_solved():
    assert solve(EASY_SOL) == EASY_SOL


def test_invalid_returns_none():
    assert solve(INVALID_DUP_ROW) is None


def test_empty_returns_some_valid_solution():
    sol = solve("." * 81)
    assert sol is not None
    assert _is_valid_solution(sol)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
