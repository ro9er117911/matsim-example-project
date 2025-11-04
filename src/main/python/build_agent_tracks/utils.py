"""
Utility functions for time conversion and file handling.
"""
from __future__ import annotations

import gzip
import typing as T
from pathlib import Path
from datetime import timedelta


def hhmmss_to_seconds(s: str) -> T.Optional[int]:
    """Convert HH:MM:SS to seconds. Accepts 'undefined' -> None."""
    if s is None:
        return None
    s = s.strip()
    if not s or s == "undefined":
        return None
    parts = s.split(":")
    if len(parts) != 3:
        # Sometimes MATSim prints float seconds; try to parse as number
        try:
            return int(float(s))
        except Exception:
            return None
    h, m, sec = parts
    return int(h) * 3600 + int(m) * 60 + int(sec)


def seconds_to_hhmmss(x: T.Optional[int]) -> T.Optional[str]:
    """Convert seconds to HH:MM:SS format."""
    if x is None:
        return None
    if x < 0:
        x = 0
    return str(timedelta(seconds=int(x)))


def open_maybe_gz(p: T.Union[str, Path]):
    """Open either gzipped or plain text file transparently."""
    p = str(p)
    if p.endswith(".gz"):
        return gzip.open(p, "rt", encoding="utf-8")
    return open(p, "rt", encoding="utf-8")
