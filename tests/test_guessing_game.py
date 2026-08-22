"""Unit tests for guessing_game.

Stdlib-only: run with `python -m unittest discover -s tests`.
"""

import io
import random
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import guessing_game
from guessing_game import CORRECT, TOO_HIGH, TOO_LOW, GameOver, GuessingGame

SCRIPT = Path(__file__).resolve().parent.parent / "guessing_game.py"


class ConstructionTests(unittest.TestCase):
    def test_secret_is_drawn_from_range(self):
        for _ in range(50):
            game = GuessingGame(low=3, high=6)
            self.assertGreaterEqual(game.secret, 3)
            self.assertLessEqual(game.secret, 6)

    def test_single_value_range_is_allowed(self):
        game = GuessingGame(low=7, high=7)
        self.assertEqual(game.secret, 7)

    def test_seeded_rng_is_reproducible(self):
        first = GuessingGame(low=1, high=1000, rng=random.Random(1234)).secret
        second = GuessingGame(low=1, high=1000, rng=random.Random(1234)).secret
        self.assertEqual(first, second)

    def test_inverted_range_rejected(self):
        with self.assertRaises(ValueError):
            GuessingGame(low=10, high=1)

    def test_zero_attempts_rejected(self):
        with self.assertRaises(ValueError):
            GuessingGame(max_attempts=0)

    def test_secret_outside_range_rejected(self):
        with self.assertRaises(ValueError):
            GuessingGame(low=1, high=10, secret=99)

    def test_from_difficulty_applies_preset(self):
        game = GuessingGame.from_difficulty("hard")
        self.assertEqual((game.low, game.high, game.max_attempts), (1, 1000, 10))

    def test_from_difficulty_rejects_unknown_name(self):
        with self.assertRaises(ValueError):
            GuessingGame.from_difficulty("impossible")


class GuessTests(unittest.TestCase):
    def setUp(self):
        self.game = GuessingGame(low=1, high=100, max_attempts=3, secret=42)

    def test_verdicts(self):
        self.assertEqual(self.game.guess(10), TOO_LOW)
        self.assertEqual(self.game.guess(90), TOO_HIGH)
        self.assertEqual(self.game.guess(42), CORRECT)

    def test_correct_guess_wins_and_ends_game(self):
        self.game.guess(42)
        self.assertTrue(self.game.won)
        self.assertTrue(self.game.over)

    def test_history_records_every_guess(self):
        self.game.guess(10)
        self.game.guess(90)
        self.assertEqual(self.game.history, [(10, TOO_LOW), (90, TOO_HIGH)])
        self.assertEqual(self.game.attempts, 2)

    def test_attempts_left_counts_down(self):
        self.assertEqual(self.game.attempts_left, 3)
        self.game.guess(1)
        self.assertEqual(self.game.attempts_left, 2)

    def test_running_out_of_attempts_ends_game_without_a_win(self):
        for number in (1, 2, 3):
            self.game.guess(number)
        self.assertTrue(self.game.over)
        self.assertFalse(self.game.won)

    def test_guessing_after_game_over_raises(self):
        self.game.guess(42)
        with self.assertRaises(GameOver):
            self.game.guess(42)

    def test_out_of_range_guess_raises_and_is_not_recorded(self):
        with self.assertRaises(ValueError):
            self.game.guess(101)
        self.assertEqual(self.game.history, [])
        self.assertEqual(self.game.attempts_left, 3)

    def test_unlimited_game_never_runs_out(self):
        game = GuessingGame(low=1, high=10, max_attempts=None, secret=5)
        self.assertIsNone(game.attempts_left)
        for _ in range(20):
            game.guess(1)
        self.assertFalse(game.over)


class HintTests(unittest.TestCase):
    def test_win_hint_reports_attempt_count(self):
        game = GuessingGame(secret=42, max_attempts=5)
        hint = game.hint(game.guess(42))
        self.assertIn("Correct", hint)
        self.assertIn("1 guess.", hint)

    def test_last_attempt_hint_reveals_secret(self):
        game = GuessingGame(low=1, high=10, max_attempts=1, secret=9)
        self.assertIn("Out of guesses", game.hint(game.guess(1)))

    def test_direction_hints(self):
        game = GuessingGame(low=1, high=10, max_attempts=5, secret=5)
        self.assertIn("Too low", game.hint(game.guess(1)))
        self.assertIn("Too high", game.hint(game.guess(9)))

    def test_unlimited_hint_omits_budget(self):
        game = GuessingGame(low=1, high=10, max_attempts=None, secret=5)
        self.assertEqual(game.hint(game.guess(1)), "Too low — try again.")

    def test_singular_guess_left(self):
        game = GuessingGame(low=1, high=10, max_attempts=2, secret=5)
        self.assertIn("1 guess left", game.hint(game.guess(1)))


class BuildGameTests(unittest.TestCase):
    def _build(self, argv):
        return guessing_game.build_game(guessing_game.parse_args(argv))

    def test_difficulty_default_is_normal(self):
        game = self._build([])
        self.assertEqual((game.low, game.high, game.max_attempts), (1, 100, 7))

    def test_explicit_bounds_override_difficulty(self):
        game = self._build(["-d", "easy", "--low", "5", "--high", "50"])
        self.assertEqual((game.low, game.high), (5, 50))
        self.assertEqual(game.max_attempts, 5)

    def test_zero_attempts_means_unlimited(self):
        self.assertIsNone(self._build(["--attempts", "0"]).max_attempts)

    def test_secret_flag_is_honoured(self):
        self.assertEqual(self._build(["--secret", "13"]).secret, 13)

    def test_seed_makes_the_secret_reproducible(self):
        first = self._build(["--seed", "7", "-d", "hard"]).secret
        second = self._build(["--seed", "7", "-d", "hard"]).secret
        self.assertEqual(first, second)


class ReadGuessTests(unittest.TestCase):
    def _read(self, text, game=None):
        game = game or GuessingGame(low=1, high=10, max_attempts=5, secret=5)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            value = guessing_game.read_guess(game, io.StringIO(text))
        return value, buffer.getvalue()

    def test_valid_number_is_returned(self):
        value, _ = self._read("4\n")
        self.assertEqual(value, 4)

    def test_surrounding_whitespace_is_ignored(self):
        value, _ = self._read("  4  \n")
        self.assertEqual(value, 4)

    def test_non_numeric_input_reprompts(self):
        value, output = self._read("four\n4\n")
        self.assertEqual(value, 4)
        self.assertIn("not a whole number", output)

    def test_out_of_range_input_reprompts(self):
        value, output = self._read("99\n4\n")
        self.assertEqual(value, 4)
        self.assertIn("Out of range", output)

    def test_quit_words_return_none(self):
        for word in ("q", "quit", "EXIT"):
            value, _ = self._read(word + "\n")
            self.assertIsNone(value)

    def test_eof_returns_none(self):
        value, _ = self._read("")
        self.assertIsNone(value)

    def test_prompt_shows_remaining_guesses(self):
        _, output = self._read("4\n")
        self.assertIn("(5 left)", output)

    def test_unlimited_prompt_hides_budget(self):
        game = GuessingGame(low=1, high=10, max_attempts=None, secret=5)
        _, output = self._read("4\n", game)
        self.assertNotIn("left", output)


class PlayTests(unittest.TestCase):
    def _play(self, text, **kwargs):
        kwargs.setdefault("low", 1)
        kwargs.setdefault("high", 100)
        kwargs.setdefault("max_attempts", 3)
        kwargs.setdefault("secret", 42)
        game = GuessingGame(**kwargs)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            won = guessing_game.play(game, io.StringIO(text))
        return won, buffer.getvalue(), game

    def test_winning_round(self):
        won, output, game = self._play("10\n42\n")
        self.assertTrue(won)
        self.assertIn("Correct", output)
        self.assertEqual(game.attempts, 2)

    def test_losing_round_reveals_secret(self):
        won, output, _ = self._play("1\n2\n3\n")
        self.assertFalse(won)
        self.assertIn("Out of guesses", output)
        self.assertIn("42", output)

    def test_quitting_reveals_secret(self):
        won, output, game = self._play("q\n")
        self.assertFalse(won)
        self.assertIn("Giving up", output)
        self.assertEqual(game.attempts, 0)

    def test_extra_input_after_a_win_is_ignored(self):
        won, _, game = self._play("42\n7\n7\n")
        self.assertTrue(won)
        self.assertEqual(game.attempts, 1)

    def test_intro_mentions_range_and_budget(self):
        _, output, _ = self._play("42\n")
        self.assertIn("between 1 and 100", output)
        self.assertIn("3 guesses", output)


class CliTests(unittest.TestCase):
    """End-to-end runs of the script, driven through stdin."""

    def _run(self, args, stdin=""):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_win_exits_zero(self):
        result = self._run(["--secret", "42"], "42\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Correct", result.stdout)

    def test_loss_exits_one(self):
        result = self._run(["-d", "easy", "--secret", "9"], "1\n2\n3\n4\n5\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Out of guesses", result.stdout)

    def test_invalid_range_exits_two(self):
        result = self._run(["--low", "10", "--high", "1"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("low must not be greater than high", result.stderr)

    def test_secret_outside_range_exits_two(self):
        result = self._run(["-d", "easy", "--secret", "500"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("secret must be within", result.stderr)

    def test_help_lists_difficulties(self):
        result = self._run(["--help"])
        self.assertEqual(result.returncode, 0)
        for name in ("easy", "normal", "hard"):
            self.assertIn(name, result.stdout)

    def test_unknown_difficulty_rejected_by_argparse(self):
        result = self._run(["-d", "impossible"])
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
