#!/usr/bin/env python3
"""
MATSim Bottleneck Analysis Tool - CLI

Analyzes road bottlenecks in MATSim simulation outputs.

Usage:
    python analyze_bottlenecks.py --output-dir output_metro_0300_0618 --mode quick
    python analyze_bottlenecks.py --output-dir output_metro_0300_0618 --mode quick --export-geojson

Author: Claude Code
Date: 2025-11-26
"""

import argparse
import sys
from pathlib import Path

from .quick_analyzer import analyze_quick, export_report_csv, export_report_json, print_summary


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze road bottlenecks in MATSim simulation outputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick analysis with default settings
  python -m bottleneck_analysis.analyze_bottlenecks --output-dir output_metro_0300_0618

  # Custom threshold and top N
  python -m bottleneck_analysis.analyze_bottlenecks --output-dir output_metro_0300_0618 --vc-threshold 0.9 --top-n 100

  # With GeoJSON export
  python -m bottleneck_analysis.analyze_bottlenecks --output-dir output_metro_0300_0618 --export-geojson

  # Custom output directory
  python -m bottleneck_analysis.analyze_bottlenecks --output-dir output_metro_0300_0618 --out analysis_results
        """,
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Path to MATSim output directory (containing output_links.csv.gz, output_legs.csv.gz)",
    )

    parser.add_argument(
        "--mode",
        choices=["quick", "events", "viz"],
        default="quick",
        help="Analysis mode: quick (CSV-based), events (event-based), viz (visualization only). Default: quick",
    )

    parser.add_argument(
        "--vc-threshold",
        type=float,
        default=0.85,
        help="V/C ratio threshold for identifying bottlenecks. Default: 0.85",
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=50,
        help="Number of top bottlenecks to export. Default: 50",
    )

    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory for analysis results. Default: <output-dir>/bottleneck_analysis",
    )

    parser.add_argument(
        "--export-geojson",
        action="store_true",
        help="Export bottlenecks as GeoJSON for map visualization",
    )

    parser.add_argument(
        "--export-timeseries",
        action="store_true",
        help="Export time-series CSV for temporal analysis (requires events mode)",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output",
    )

    args = parser.parse_args()

    # Validate output directory
    if not args.output_dir.exists():
        print(f"Error: Output directory does not exist: {args.output_dir}", file=sys.stderr)
        return 1

    # Set default output directory
    if args.out is None:
        args.out = args.output_dir / "bottleneck_analysis"

    # Create output directory
    args.out.mkdir(parents=True, exist_ok=True)

    try:
        if args.mode == "quick":
            # Perform quick CSV analysis
            report = analyze_quick(
                output_dir=args.output_dir,
                vc_threshold=args.vc_threshold,
                top_n=args.top_n,
            )

            # Export CSV report
            csv_path = args.out / "bottleneck_quick_report.csv"
            export_report_csv(report, csv_path)

            # Export JSON summary
            json_path = args.out / "bottleneck_quick_summary.json"
            export_report_json(report, json_path)

            # Print summary
            if not args.quiet:
                print_summary(report, show_top_n=10)

            # Export GeoJSON if requested
            if args.export_geojson:
                print("Exporting GeoJSON visualization...")
                from .viz_exporter import export_geojson

                geojson_path = args.out / "bottleneck_heatmap.geojson"
                export_geojson(report, geojson_path)

            print()
            print("=" * 80)
            print("ANALYSIS COMPLETE")
            print("=" * 80)
            print(f"Output directory: {args.out}")
            print(f"  - CSV report: bottleneck_quick_report.csv")
            print(f"  - JSON summary: bottleneck_quick_summary.json")
            if args.export_geojson:
                print(f"  - GeoJSON heatmap: bottleneck_heatmap.geojson")
            print()

        elif args.mode == "events":
            print("Event-based analysis is not yet implemented.", file=sys.stderr)
            print("Please use --mode quick for now.", file=sys.stderr)
            return 1

        elif args.mode == "viz":
            print("Visualization-only mode is not yet implemented.", file=sys.stderr)
            print("Please use --mode quick --export-geojson instead.", file=sys.stderr)
            return 1

        return 0

    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
