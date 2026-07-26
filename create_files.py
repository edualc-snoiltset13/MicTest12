"""Create two different text files, pausing about 10 seconds in between.

Running the script writes two distinct text files to the current directory and
uses time.sleep to make the whole run take roughly ten seconds.
"""

import time


def create_first_file(filename: str = "file_one.txt") -> None:
    """Write the first text file with some sample content."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write("This is the first file.\n")
        f.write("It contains a short greeting.\n")
        f.write("Hello from file one!\n")
    print(f"Created {filename}")


def create_second_file(filename: str = "file_two.txt") -> None:
    """Write the second text file with different content."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write("This is the second file.\n")
        f.write("Its content is different from the first.\n")
        f.write("Goodbye from file two!\n")
    print(f"Created {filename}")


def main() -> None:
    print("Starting...")

    create_first_file()

    # Pause so the whole script takes about 10 seconds to run.
    print("Working (sleeping for 10 seconds)...")
    time.sleep(10)

    create_second_file()

    print("Done. Both files were created.")


if __name__ == "__main__":
    main()
