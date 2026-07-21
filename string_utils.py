"""Small string utility helpers."""


def reverse(text: str) -> str:
    """Return the reversed string."""
    return text[::-1]


def is_palindrome(text: str) -> bool:
    """Check whether the string reads the same forwards and backwards."""
    normalized = "".join(ch.lower() for ch in text if ch.isalnum())
    return normalized == normalized[::-1]


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max_length characters, appending a suffix if cut."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
