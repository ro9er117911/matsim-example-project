"""
Quick CSV-based bottleneck analysis.

Analyzes bottlenecks using MATSim output CSV files (output_links.csv.gz and output_legs.csv.gz).
Provides fast V/C ratio calculation and bottleneck identification.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional
import pandas as pd

from .models import BottleneckLink, BottleneckReport
from .utils import validate_output_dir, parse_time_column, safe_divide


def analyze_quick(
    output_dir: Path,
    vc_threshold: float = 0.85,
    top_n: int = 50,
) -> BottleneckReport:
    """
    Performs quick bottleneck analysis using CSV output files.

    Args:
        output_dir: Path to MATSim output directory
        vc_threshold: V/C ratio threshold for identifying bottlenecks (default: 0.85)
        top_n: Number of top bottlenecks to return (default: 50)

    Returns:
        BottleneckReport object containing analysis results

    Raises:
        FileNotFoundError: If required output files are missing
        ValueError: If data format is invalid
    """
    # Validate output directory
    output_dir = Path(output_dir)
    validate_output_dir(output_dir)

    print(f"Analyzing bottlenecks in: {output_dir}")
    print(f"V/C threshold: {vc_threshold}")
    print(f"Top N: {top_n}")
    print()

    # Load links data
    print("Loading network links...")
    links_path = output_dir / "output_links.csv.gz"
    links_df = pd.read_csv(links_path, sep=";", low_memory=False)
    total_links = len(links_df)
    print(f"  Total links: {total_links}")

    # Calculate V/C ratio
    print("Calculating V/C ratios...")
    links_df["volume"] = pd.to_numeric(links_df.get("vol_car", 0), errors="coerce").fillna(0)
    links_df["capacity"] = pd.to_numeric(links_df["capacity"], errors="coerce").fillna(1)
    links_df["vc_ratio"] = links_df.apply(
        lambda row: safe_divide(row["volume"], row["capacity"], default=0.0), axis=1
    )

    # Filter bottlenecks
    bottlenecks_df = links_df[links_df["vc_ratio"] >= vc_threshold].copy()
    bottlenecks_df = bottlenecks_df.sort_values("vc_ratio", ascending=False)
    bottleneck_count = len(bottlenecks_df)
    print(f"  Bottlenecks found (V/C >= {vc_threshold}): {bottleneck_count}")

    # Get worst V/C ratio
    worst_vc = bottlenecks_df["vc_ratio"].max() if bottleneck_count > 0 else 0.0
    print(f"  Worst V/C ratio: {worst_vc:.3f}")

    # Load legs data for delay calculation
    print("Loading trip legs for delay analysis...")
    legs_path = output_dir / "output_legs.csv.gz"
    try:
        legs_df = pd.read_csv(legs_path, sep=";", low_memory=False)
        print(f"  Total legs: {len(legs_df)}")

        # Parse wait time
        wait_time_s = parse_time_column(legs_df, "wait_time")
        avg_delay = wait_time_s.mean() if len(wait_time_s) > 0 else None
        if avg_delay:
            print(f"  Average network delay: {avg_delay:.2f} seconds ({avg_delay/60:.2f} minutes)")
    except Exception as e:
        print(f"  Warning: Could not calculate delay - {e}")
        avg_delay = None

    # Build BottleneckLink objects
    print(f"Building report for top {top_n} bottlenecks...")
    bottlenecks = []
    for rank, (idx, row) in enumerate(bottlenecks_df.head(top_n).iterrows(), start=1):
        link = BottleneckLink(
            link_id=str(row["link"]),
            from_node=str(row.get("from_node", "")),
            to_node=str(row.get("to_node", "")),
            capacity=float(row["capacity"]),
            volume=float(row["volume"]),
            vc_ratio=float(row["vc_ratio"]),
            freespeed=float(row.get("freespeed", 0)),
            lanes=float(row.get("lanes", 1)),
            length=float(row.get("length", 0)),
            geometry=row.get("geometry", None),
            rank=rank,
        )
        bottlenecks.append(link)

    # Create report
    report = BottleneckReport(
        scenario_name=output_dir.name,
        timestamp=datetime.now(),
        total_links=total_links,
        bottleneck_count=bottleneck_count,
        vc_threshold=vc_threshold,
        worst_vc_ratio=worst_vc,
        avg_network_delay_s=avg_delay,
        bottlenecks=bottlenecks,
        top_n=top_n,
    )

    print()
    print(f"Analysis complete!")
    print(f"  Identified {bottleneck_count} bottlenecks")
    print(f"  Top {len(bottlenecks)} bottlenecks prepared for export")

    return report


def export_report_csv(report: BottleneckReport, output_path: Path) -> None:
    """
    Exports bottleneck report to CSV file.

    Args:
        report: BottleneckReport object
        output_path: Path to output CSV file
    """
    df = report.to_dataframe()
    df.to_csv(output_path, index=False)
    print(f"CSV report saved: {output_path}")


def export_report_json(report: BottleneckReport, output_path: Path) -> None:
    """
    Exports bottleneck report summary to JSON file.

    Args:
        report: BottleneckReport object
        output_path: Path to output JSON file
    """
    import json

    summary = report.to_summary_dict()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"JSON summary saved: {output_path}")


def print_summary(report: BottleneckReport, show_top_n: int = 10) -> None:
    """
    Prints summary of bottleneck analysis to console.

    Args:
        report: BottleneckReport object
        show_top_n: Number of top bottlenecks to display
    """
    print()
    print("=" * 80)
    print(f"BOTTLENECK ANALYSIS SUMMARY: {report.scenario_name}")
    print("=" * 80)
    print(f"Analysis Time: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Links: {report.total_links}")
    print(f"Bottleneck Count (V/C >= {report.vc_threshold}): {report.bottleneck_count}")
    print(f"Worst V/C Ratio: {report.worst_vc_ratio:.3f}")
    if report.avg_network_delay_s:
        print(
            f"Average Network Delay: {report.avg_network_delay_s:.2f}s "
            f"({report.avg_network_delay_s/60:.2f} min)"
        )
    print()

    # Severity breakdown
    severity = report._get_severity_breakdown()
    print("Severity Breakdown:")
    print(f"  Critical (V/C > 1.0):  {severity['critical']}")
    print(f"  Heavy (V/C 0.85-1.0):  {severity['heavy']}")
    print(f"  Congested (V/C 0.7-0.85): {severity['congested']}")
    print()

    # Top bottlenecks
    print(f"Top {show_top_n} Bottlenecks:")
    print("-" * 80)
    print(
        f"{'Rank':<5} {'Link ID':<12} {'V/C':<8} {'Volume':<10} {'Capacity':<10} {'Severity':<12}"
    )
    print("-" * 80)

    for i, link in enumerate(report.bottlenecks[:show_top_n]):
        print(
            f"{link.rank:<5} {link.link_id:<12} {link.vc_ratio:<8.3f} "
            f"{link.volume:<10.0f} {link.capacity:<10.0f} {link.severity:<12}"
        )

    print("=" * 80)
    print()
