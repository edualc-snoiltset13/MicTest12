"""
Tests for compression.py — exercises the streaming helpers against
genuinely large files (multi-MB) to verify correctness and memory safety.

Run:
    python -m unittest test_compression
    python test_compression.py            # also runs unittest
"""

import hashlib
import os
import secrets
import tempfile
import unittest

from compression import compress_file, decompress_file, CHUNK_SIZE


def _sha256(path, chunk=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _write_repeating(path, size, pattern=b"barber-booking-agent "):
    """Write highly compressible repeating data of approximately `size` bytes."""
    block = pattern * (CHUNK_SIZE // len(pattern) + 1)
    written = 0
    with open(path, "wb") as f:
        while written < size:
            remaining = size - written
            f.write(block[:remaining])
            written += min(len(block), remaining)


def _write_random(path, size):
    """Write incompressible random data of approximately `size` bytes."""
    written = 0
    with open(path, "wb") as f:
        while written < size:
            chunk = min(CHUNK_SIZE, size - written)
            f.write(secrets.token_bytes(chunk))
            written += chunk


class CompressLargeFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="compress_test_")

    def tearDown(self):
        for name in os.listdir(self.tmp):
            os.remove(os.path.join(self.tmp, name))
        os.rmdir(self.tmp)

    def _path(self, name):
        return os.path.join(self.tmp, name)

    def test_compress_decompress_roundtrip_repeating_10mb(self):
        src = self._path("repeating.bin")
        size = 10 * 1024 * 1024
        _write_repeating(src, size)
        original_hash = _sha256(src)

        gz, original, compressed = compress_file(src)

        self.assertEqual(original, size)
        self.assertTrue(os.path.exists(gz))
        self.assertLess(compressed, original // 10,
                        "highly repetitive data should compress to <10% of original")

        os.remove(src)
        out = decompress_file(gz)

        self.assertEqual(os.path.getsize(out), size)
        self.assertEqual(_sha256(out), original_hash)

    def test_compress_decompress_roundtrip_random_5mb(self):
        src = self._path("random.bin")
        size = 5 * 1024 * 1024
        _write_random(src, size)
        original_hash = _sha256(src)

        gz, original, compressed = compress_file(src, dst_path=self._path("random.gz"))

        self.assertEqual(original, size)
        # Random data does not compress well — gzip overhead may even add bytes.
        self.assertLess(abs(compressed - original) / original, 0.05,
                        "random data should be within 5% of the original size")

        out = decompress_file(gz, dst_path=self._path("random.out"))
        self.assertEqual(_sha256(out), original_hash)

    def test_default_destination_paths(self):
        src = self._path("data.bin")
        _write_repeating(src, 1 * 1024 * 1024)

        gz, _, _ = compress_file(src)
        self.assertEqual(gz, src + ".gz")

        os.remove(src)
        out = decompress_file(gz)
        self.assertEqual(out, src)
        self.assertTrue(os.path.exists(out))

    def test_compression_level_affects_size(self):
        src = self._path("level.bin")
        _write_repeating(src, 2 * 1024 * 1024)

        _, _, size_low = compress_file(src, dst_path=self._path("low.gz"), level=1)
        _, _, size_high = compress_file(src, dst_path=self._path("high.gz"), level=9)

        # Higher level should produce equal-or-smaller output for non-trivial inputs.
        self.assertLessEqual(size_high, size_low)

    def test_empty_file_roundtrip(self):
        src = self._path("empty.bin")
        open(src, "wb").close()

        gz, original, compressed = compress_file(src)
        self.assertEqual(original, 0)
        self.assertGreater(compressed, 0, "gzip header is always written")

        os.remove(src)
        out = decompress_file(gz)
        self.assertEqual(os.path.getsize(out), 0)

    def test_streaming_uses_bounded_memory(self):
        """Sanity check: verify chunked copy by patching shutil.copyfileobj."""
        import shutil
        observed = []
        original_copy = shutil.copyfileobj

        def spy(src, dst, length=None):
            observed.append(length)
            return original_copy(src, dst, length=length)

        shutil.copyfileobj = spy
        try:
            src = self._path("stream.bin")
            _write_repeating(src, 3 * 1024 * 1024)
            compress_file(src)
            decompress_file(src + ".gz")
        finally:
            shutil.copyfileobj = original_copy

        self.assertEqual(len(observed), 2)
        self.assertTrue(all(n == CHUNK_SIZE for n in observed),
                        f"expected chunked copies of {CHUNK_SIZE}, got {observed}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
