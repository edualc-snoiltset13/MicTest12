"""
Streaming file compression helpers for the Barber Booking Agent.

Uses gzip from the standard library and reads/writes in fixed-size chunks
so files much larger than memory can be processed safely.
"""

import gzip
import os
import shutil

CHUNK_SIZE = 1024 * 1024  # 1 MiB


def compress_file(src_path, dst_path=None, level=6, chunk_size=CHUNK_SIZE):
    """Compress src_path to dst_path (gzip). Returns (dst_path, original, compressed)."""
    if dst_path is None:
        dst_path = src_path + ".gz"
    original = os.path.getsize(src_path)
    with open(src_path, "rb") as src, gzip.open(dst_path, "wb", compresslevel=level) as dst:
        shutil.copyfileobj(src, dst, length=chunk_size)
    compressed = os.path.getsize(dst_path)
    return dst_path, original, compressed


def decompress_file(src_path, dst_path=None, chunk_size=CHUNK_SIZE):
    """Decompress a gzip file at src_path to dst_path. Returns dst_path."""
    if dst_path is None:
        if src_path.endswith(".gz"):
            dst_path = src_path[:-3]
        else:
            dst_path = src_path + ".out"
    with gzip.open(src_path, "rb") as src, open(dst_path, "wb") as dst:
        shutil.copyfileobj(src, dst, length=chunk_size)
    return dst_path
