#!/usr/bin/env python3
"""Create two text files, pausing for about 10 seconds during the run."""

import time


def create_file(filename, content):
    """Write content to a text file."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created {filename}")


def main():
    print("Starting...")

    # Create the first text file.
    create_file(
        "file_one.txt",
        "This is the first text file.\nIt was created by create_files.py.\n",
    )

    # Pause for about 10 seconds to simulate work.
    print("Working (sleeping for 10 seconds)...")
    time.sleep(10)

    # Create the second text file.
    create_file(
        "file_two.txt",
        "This is the second text file.\nIt was created after a 10 second pause.\n",
    )

    print("Done. Both files created.")


if __name__ == "__main__":
    main()
