"""
Utility functions for MATSim population validation.

Reuses patterns from existing codebase (parsers.py, validate_population.py).
"""
import gzip
from pathlib import Path
from typing import Union, Optional


def open_maybe_gz(file_path: Union[str, Path], mode: str = 'r'):
    """
    Open a file that might be gzipped.

    Args:
        file_path: Path to file (with or without .gz extension)
        mode: File mode ('r' for read, 'w' for write)

    Returns:
        File handle (regular or gzip)
    """
    file_path = Path(file_path)

    if file_path.suffix == '.gz':
        if 'b' not in mode:
            mode = mode + 't'  # Add text mode if not binary
        return gzip.open(file_path, mode, encoding='utf-8' if 't' in mode else None)
    else:
        return open(file_path, mode, encoding='utf-8' if 'b' not in mode else None)


def hhmmss_to_seconds(time_str: Optional[str]) -> Optional[int]:
    """
    Convert HH:MM:SS time string to seconds.

    Args:
        time_str: Time string in HH:MM:SS format or None

    Returns:
        Total seconds or None if input is None
    """
    if not time_str:
        return None

    try:
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
    except (ValueError, AttributeError):
        return None

    return None


def seconds_to_hhmmss(seconds: int) -> str:
    """
    Convert seconds to HH:MM:SS format.

    Args:
        seconds: Total seconds

    Returns:
        Time string in HH:MM:SS format
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calculate Euclidean distance between two points.

    Args:
        x1, y1: First point coordinates
        x2, y2: Second point coordinates

    Returns:
        Distance in same units as input coordinates (meters for EPSG:3826)
    """
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
