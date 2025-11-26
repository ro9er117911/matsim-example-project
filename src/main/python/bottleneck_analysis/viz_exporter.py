"""
Visualization export for bottleneck analysis.

Generates GeoJSON and time-series CSV files for visualization in GIS tools.
"""

import json
from pathlib import Path
from typing import List

from .models import BottleneckReport, BottleneckLink
from .utils import parse_wkt_geometry


def export_geojson(report: BottleneckReport, output_path: Path) -> None:
    """
    Exports bottleneck report as GeoJSON for map visualization.

    Args:
        report: BottleneckReport object
        output_path: Path to output GeoJSON file

    Output Format:
        GeoJSON FeatureCollection with LineString geometries.
        Each feature represents a bottleneck link with properties:
        - link_id, vc_ratio, severity, color, volume, capacity, etc.
    """
    features = []

    for link in report.bottlenecks:
        # Parse WKT geometry to coordinate list
        coordinates = parse_wkt_geometry(link.geometry) if link.geometry else []

        if not coordinates:
            # Skip links without valid geometry
            continue

        # Create GeoJSON feature
        feature = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coordinates},
            "properties": {
                "link_id": link.link_id,
                "rank": link.rank,
                "from_node": link.from_node,
                "to_node": link.to_node,
                "vc_ratio": round(link.vc_ratio, 3),
                "volume": link.volume,
                "capacity": link.capacity,
                "freespeed": link.freespeed,
                "lanes": link.lanes,
                "length": link.length,
                "severity": link.severity,
                "color": link.color,
            },
        }
        features.append(feature)

    # Create GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "scenario": report.scenario_name,
            "timestamp": report.timestamp.isoformat(),
            "total_links": report.total_links,
            "bottleneck_count": report.bottleneck_count,
            "vc_threshold": report.vc_threshold,
            "worst_vc_ratio": round(report.worst_vc_ratio, 3) if report.worst_vc_ratio else None,
        },
        "features": features,
    }

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)

    print(f"GeoJSON heatmap saved: {output_path}")
    print(f"  Features (links): {len(features)}")
    print(f"  Coordinate system: EPSG:3826 (TWD97 / TM2 zone 121)")
    print(
        f"  To view: Import into QGIS, kepler.gl, or Mapbox with custom styling based on 'severity' or 'vc_ratio'"
    )


def export_timeseries_csv(
    bottlenecks: List[BottleneckLink],
    output_path: Path,
    time_steps: List[str] = None,
) -> None:
    """
    Exports time-series CSV for temporal analysis.

    Note: This is a placeholder for future event-based analysis.
    Currently exports static snapshot data.

    Args:
        bottlenecks: List of BottleneckLink objects
        output_path: Path to output CSV file
        time_steps: List of time strings (HH:MM:SS format)
    """
    import csv

    # For quick analysis, we don't have temporal data
    # Export a static snapshot instead
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "link_id",
                "time",
                "vc_ratio",
                "volume",
                "capacity",
                "severity",
                "color",
            ]
        )

        for link in bottlenecks:
            # Single time snapshot (end of simulation)
            writer.writerow(
                [
                    link.link_id,
                    "end_of_simulation",
                    round(link.vc_ratio, 3),
                    link.volume,
                    link.capacity,
                    link.severity,
                    link.color,
                ]
            )

    print(f"Time-series CSV saved: {output_path}")
    print(
        f"  Note: Quick analysis mode provides static snapshot only. Use --mode events for temporal data."
    )


def create_severity_legend() -> dict:
    """
    Creates a legend mapping severity levels to colors.

    Returns:
        Dictionary with severity levels and color codes
    """
    return {
        "normal": {"threshold": "< 0.5", "color": "#00FF00", "description": "Free flow"},
        "moderate": {
            "threshold": "0.5 - 0.7",
            "color": "#FFFF00",
            "description": "Moderate traffic",
        },
        "congested": {
            "threshold": "0.7 - 0.85",
            "color": "#FFA500",
            "description": "Congested",
        },
        "heavy": {
            "threshold": "0.85 - 1.0",
            "color": "#FF4500",
            "description": "Heavy congestion",
        },
        "critical": {"threshold": "> 1.0", "color": "#FF0000", "description": "Bottleneck"},
    }


def export_legend_json(output_path: Path) -> None:
    """
    Exports severity legend as JSON for visualization tools.

    Args:
        output_path: Path to output JSON file
    """
    legend = create_severity_legend()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {"title": "Bottleneck Severity Legend", "levels": legend},
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Legend JSON saved: {output_path}")
