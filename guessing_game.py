"""
Number guessing game.

The computer picks a secret number in a range and you narrow it down with
higher/lower feedback. The game logic lives in `GuessingGame` so it can be
tested without any I/O; `main()` wraps it in an interactive CLI.

Pure standard library.

Usage:
    python guessing_game.py
    python guessing_game.py --difficulty hard
    python guessing_game.py --low 1 --high 1000 --attempts 12
    python guessing_game.py --secret 42          # fixed number (practice/demo)
"""

import argparse
import random
import sys

# name -> (low, high, max_attempts)
DIFFICULTIES = {
    "easy": (1, 10, 5),
    "normal": (1, 100, 7),
    "hard": (1, 1000, 10),
}

TOO_LOW = "too_low"
TOO_HIGH = "too_high"
CORRECT = "correct"


class GameOver(Exception):
    """Raised when a guess is made after the game has already finished."""


class GuessingGame:
    """A single round of the guessing game.

    The secret is drawn from `[low, high]` unless one is supplied. A round
    ends when the secret is guessed or `max_attempts` guesses are used up;
    `max_attempts=None` means unlimited guesses.
    """

    def __init__(self, low=1, high=100, max_attempts=7, secret=None, rng=None):
        if low > high:
            raise ValueError("low must not be greater than high")
        if max_attempts is not None and max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if secret is not None and not low <= secret <= high:
            raise ValueError("secret must be within [low, high]")

        self.low = low
        self.high = high
        self.max_attempts = max_attempts
        self.secret = secret if secret is not None else (rng or random).randint(low, high)
        self.history = []
        self.won = False

    @classmethod
    def from_difficulty(cls, name, **kwargs):
        try:
            low, high, attempts = DIFFICULTIES[name]
        except KeyError:
            raise ValueError("unknown difficulty: %s" % name)
        return cls(low=low, high=high, max_attempts=attempts, **kwargs)

    @property
    def attempts(self):
        return len(self.history)

    @property
    def attempts_left(self):
        """Guesses remaining, or None when the game is unlimited."""
        if self.max_attempts is None:
            return None
        return max(0, self.max_attempts - self.attempts)

    @property
    def over(self):
        return self.won or self.attempts_left == 0

    def guess(self, number):
        """Score one guess and return TOO_LOW, TOO_HIGH, or CORRECT."""
        if self.over:
            raise GameOver("the game is already finished")
        if not self.low <= number <= self.high:
            raise ValueError(
                "guess must be between %d and %d" % (self.low, self.high)
            )

        if number < self.secret:
            verdict = TOO_LOW
        elif number > self.secret:
            verdict = TOO_HIGH
        else:
            verdict = CORRECT
            self.won = True

        self.history.append((number, verdict))
        return verdict

    def hint(self, verdict):
        """A short human-readable reaction to a verdict."""
        if verdict == CORRECT:
            return "Correct! You got it in %d %s." % (
                self.attempts,
                "guess" if self.attempts == 1 else "guesses",
            )
        direction = "Too low" if verdict == TOO_LOW else "Too high"
        if self.attempts_left is None:
            return "%s — try again." % direction
        if self.attempts_left == 0:
            return "%s. Out of guesses — the number was %d." % (direction, self.secret)
        return "%s. %d %s left." % (
            direction,
            self.attempts_left,
            "guess" if self.attempts_left == 1 else "guesses",
        )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Guess the secret number.",
        epilog="Ranges given with --low/--high/--attempts override --difficulty.",
    )
    parser.add_argument(
        "-d",
        "--difficulty",
        choices=sorted(DIFFICULTIES),
        default="normal",
        help="preset range and guess budget (default: normal, 1-100 in 7 guesses)",
    )
    parser.add_argument("--low", type=int, help="lowest possible number")
    parser.add_argument("--high", type=int, help="highest possible number")
    parser.add_argument(
        "--attempts",
        type=int,
        help="maximum number of guesses (0 for unlimited)",
    )
    parser.add_argument(
        "--secret",
        type=int,
        help="fix the secret number instead of drawing one at random",
    )
    parser.add_argument(
        "--seed", type=int, help="seed the random number generator (reproducible games)"
    )
    return parser.parse_args(argv)


def build_game(args):
    """Turn parsed arguments into a GuessingGame."""
    low, high, attempts = DIFFICULTIES[args.difficulty]
    if args.low is not None:
        low = args.low
    if args.high is not None:
        high = args.high
    if args.attempts is not None:
        attempts = args.attempts if args.attempts > 0 else None

    rng = random.Random(args.seed) if args.seed is not None else random
    return GuessingGame(
        low=low, high=high, max_attempts=attempts, secret=args.secret, rng=rng
    )


def read_guess(game, stream=None):
    """Prompt until a valid guess is entered.

    Returns the guess, or None if the input stream ends (EOF / Ctrl-D).
    """
    stream = stream if stream is not None else sys.stdin
    while True:
        left = game.attempts_left
        budget = "" if left is None else " (%d left)" % left
        print("Guess a number between %d and %d%s: " % (game.low, game.high, budget), end="")
        sys.stdout.flush()
        line = stream.readline()
        if not line:
            print()
            return None
        line = line.strip()
        if line.lower() in ("q", "quit", "exit"):
            return None
        try:
            number = int(line)
        except ValueError:
            print("  That is not a whole number.")
            continue
        if not game.low <= number <= game.high:
            print("  Out of range — stay between %d and %d." % (game.low, game.high))
            continue
        return number


def play(game, stream=None):
    """Run one round interactively. Returns True if the player won."""
    print("I picked a number between %d and %d." % (game.low, game.high))
    if game.max_attempts is not None:
        print(
            "You have %d %s. Type q to give up."
            % (game.max_attempts, "guess" if game.max_attempts == 1 else "guesses")
        )
    else:
        print("Guess as often as you like. Type q to give up.")

    while not game.over:
        number = read_guess(game, stream)
        if number is None:
            print("Giving up — the number was %d." % game.secret)
            return False
        print("  " + game.hint(game.guess(number)))

    return game.won


def main(argv=None, stream=None):
    try:
        args = parse_args(argv)
        game = build_game(args)
    except ValueError as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 2

    return 0 if play(game, stream) else 1


if __name__ == "__main__":
    sys.exit(main())
