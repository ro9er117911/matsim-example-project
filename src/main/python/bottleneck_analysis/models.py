"""
Data models for bottleneck analysis.

Defines dataclasses for representing bottleneck analysis results.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
import pandas as pd


@dataclass
class BottleneckLink:
    """Represents a single bottleneck link with its metrics."""

    link_id: str
    from_node: str
    to_node: str
    capacity: float
    volume: float
    vc_ratio: float
    freespeed: float
    lanes: float
    length: float
    geometry: Optional[str] = None
    rank: Optional[int] = None

    @property
    def severity(self) -> str:
        """Returns severity level based on V/C ratio."""
        if self.vc_ratio < 0.5:
            return "normal"
        elif self.vc_ratio < 0.7:
            return "moderate"
        elif self.vc_ratio < 0.85:
            return "congested"
        elif self.vc_ratio < 1.0:
            return "heavy"
        else:
            return "critical"

    @property
    def color(self) -> str:
        """Returns hex color code for visualization."""
        if self.vc_ratio < 0.5:
            return "#00FF00"  # Green
        elif self.vc_ratio < 0.7:
            return "#FFFF00"  # Yellow
        elif self.vc_ratio < 0.85:
            return "#FFA500"  # Orange
        elif self.vc_ratio < 1.0:
            return "#FF4500"  # Red-Orange
        else:
            return "#FF0000"  # Red

    def to_dict(self) -> Dict:
        """Converts to dictionary for JSON serialization."""
        return {
            "link_id": self.link_id,
            "from_node": self.from_node,
            "to_node": self.to_node,
            "capacity": self.capacity,
            "volume": self.volume,
            "vc_ratio": round(self.vc_ratio, 3),
            "freespeed": self.freespeed,
            "lanes": self.lanes,
            "length": self.length,
            "geometry": self.geometry,
            "rank": self.rank,
            "severity": self.severity,
            "color": self.color,
        }


@dataclass
class BottleneckReport:
    """Complete bottleneck analysis report."""

    scenario_name: str
    timestamp: datetime
    total_links: int
    bottleneck_count: int
    vc_threshold: float
    worst_vc_ratio: float
    avg_network_delay_s: Optional[float]
    bottlenecks: List[BottleneckLink] = field(default_factory=list)
    top_n: int = 50

    def to_summary_dict(self) -> Dict:
        """Generates summary dictionary for JSON export."""
        return {
            "scenario": self.scenario_name,
            "timestamp": self.timestamp.isoformat(),
            "analysis": {
                "total_links": self.total_links,
                "bottleneck_count": self.bottleneck_count,
                "vc_threshold": self.vc_threshold,
                "worst_vc_ratio": round(self.worst_vc_ratio, 3) if self.worst_vc_ratio else None,
                "avg_network_delay_s": (
                    round(self.avg_network_delay_s, 2) if self.avg_network_delay_s else None
                ),
            },
            "top_10_bottlenecks": [b.to_dict() for b in self.bottlenecks[:10]],
            "severity_breakdown": self._get_severity_breakdown(),
        }

    def _get_severity_breakdown(self) -> Dict[str, int]:
        """Counts bottlenecks by severity level."""
        breakdown = {"critical": 0, "heavy": 0, "congested": 0, "moderate": 0, "normal": 0}
        for b in self.bottlenecks:
            breakdown[b.severity] += 1
        return breakdown

    def to_dataframe(self) -> pd.DataFrame:
        """Converts bottlenecks to pandas DataFrame."""
        data = [
            {
                "rank": b.rank,
                "link_id": b.link_id,
                "from_node": b.from_node,
                "to_node": b.to_node,
                "capacity": b.capacity,
                "volume": b.volume,
                "vc_ratio": round(b.vc_ratio, 3),
                "freespeed": b.freespeed,
                "lanes": b.lanes,
                "length": b.length,
                "severity": b.severity,
                "geometry": b.geometry,
            }
            for b in self.bottlenecks
        ]
        return pd.DataFrame(data)
