"""
Utility functions for bottleneck analysis.

Provides helper functions for time parsing, file I/O, and data processing.
"""

import gzip
from pathlib import Path
from typing import Union, TextIO
import pandas as pd


def open_maybe_gz(file_path: Union[str, Path]) -> TextIO:
    """
    Opens a file, automatically detecting gzip compression.

    Args:
        file_path: Path to file (may be .gz compressed)

    Returns:
        Text file object
    """
    file_path = Path(file_path)
    if file_path.suffix == ".gz":
        return gzip.open(file_path, "rt", encoding="utf-8")
    else:
        return open(file_path, "r", encoding="utf-8")


def hhmmss_to_seconds(time_str: str) -> float:
    """
    Converts HH:MM:SS time string to seconds.

    Args:
        time_str: Time in HH:MM:SS format

    Returns:
        Time in seconds

    Examples:
        >>> hhmmss_to_seconds("01:30:00")
        5400.0
        >>> hhmmss_to_seconds("00:05:30")
        330.0
    """
    if pd.isna(time_str) or time_str == "":
        return 0.0

    parts = time_str.split(":")
    if len(parts) != 3:
        return 0.0

    try:
        hours, minutes, seconds = map(float, parts)
        return hours * 3600 + minutes * 60 + seconds
    except ValueError:
        return 0.0


def parse_time_column(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Parses a time column (HH:MM:SS format) to seconds.

    Args:
        df: DataFrame containing time column
        column: Name of time column

    Returns:
        Series with time in seconds
    """
    return df[column].apply(hhmmss_to_seconds)


def parse_wkt_geometry(wkt_str: str) -> list:
    """
    Parses WKT LINESTRING geometry to coordinate list.

    Args:
        wkt_str: WKT geometry string (e.g., "LINESTRING(121.5 25.0, 121.6 25.1)")

    Returns:
        List of [lon, lat] coordinate pairs

    Examples:
        >>> parse_wkt_geometry("LINESTRING(121.5 25.0, 121.6 25.1)")
        [[121.5, 25.0], [121.6, 25.1]]
    """
    if pd.isna(wkt_str) or not wkt_str.startswith("LINESTRING"):
        return []

    # Extract coordinates from LINESTRING(...)
    coords_str = wkt_str.replace("LINESTRING(", "").replace(")", "")
    coord_pairs = coords_str.split(", ")

    coordinates = []
    for pair in coord_pairs:
        try:
            lon, lat = map(float, pair.split())
            coordinates.append([lon, lat])
        except (ValueError, AttributeError):
            continue

    return coordinates


def format_seconds_to_hhmmss(seconds: float) -> str:
    """
    Converts seconds to HH:MM:SS format.

    Args:
        seconds: Time in seconds

    Returns:
        Time string in HH:MM:SS format

    Examples:
        >>> format_seconds_to_hhmmss(5400)
        '01:30:00'
        >>> format_seconds_to_hhmmss(90)
        '00:01:30'
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def validate_output_dir(output_dir: Path) -> bool:
    """
    Validates that output directory contains required MATSim output files.

    Args:
        output_dir: Path to MATSim output directory

    Returns:
        True if directory is valid

    Raises:
        FileNotFoundError: If required files are missing
    """
    required_files = ["output_links.csv.gz", "output_legs.csv.gz"]

    for filename in required_files:
        file_path = output_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found: {file_path}\n"
                f"Please ensure {output_dir} is a valid MATSim output directory."
            )

    return True


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divides two numbers, returning default if denominator is zero.

    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value to return if division by zero

    Returns:
        Result of division or default value
    """
    if denominator == 0 or pd.isna(denominator):
        return default
    return numerator / denominator
