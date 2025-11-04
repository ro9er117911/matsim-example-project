"""
Filter and report on vehicle usage by agents.
"""
from __future__ import annotations

from pathlib import Path

from .utils import seconds_to_hhmmss


def create_vehicle_usage_report(total_vehicles: int, used_vehicles: dict[str, dict], outdir: str) -> str:
    """
    Generate a text report summarizing vehicle filtering statistics.

    Args:
        total_vehicles: Total number of vehicles defined in transitVehicles.xml
        used_vehicles: Dict from load_actively_used_vehicles
        outdir: Output directory

    Returns:
        Path to report file
    """
    report_path = str(Path(outdir) / "vehicle_usage_report.txt")

    used_count = len(used_vehicles)
    compression_ratio = 100.0 * (1.0 - used_count / total_vehicles) if total_vehicles > 0 else 0.0

    with open(report_path, "w") as f:
        f.write("=" * 70 + "\n")
        f.write("VEHICLE FILTERING REPORT\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"Total vehicles defined:        {total_vehicles}\n")
        f.write(f"Vehicles used by agents:       {used_count}\n")
        f.write(f"Vehicles filtered out:         {total_vehicles - used_count}\n")
        f.write(f"Compression ratio:             {compression_ratio:.1f}%\n\n")

        if used_vehicles:
            f.write("AGENT-USED VEHICLES:\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'Vehicle ID':<30} {'Mode':<10} {'Agents':<8} {'Time Range'}\n")
            f.write("-" * 70 + "\n")

            for veh_id in sorted(used_vehicles.keys()):
                veh_info = used_vehicles[veh_id]
                mode = veh_info.get("mode", "unknown")
                agent_count = veh_info.get("agent_count", 0)
                first_t = veh_info.get("first_use_time_s", 0)
                last_t = veh_info.get("last_use_time_s", 0)
                time_range = f"{seconds_to_hhmmss(first_t)} - {seconds_to_hhmmss(last_t)}"

                f.write(f"{veh_id:<30} {mode:<10} {agent_count:<8} {time_range}\n")

        f.write("\n" + "=" * 70 + "\n")

    return report_path


def write_filtered_vehicles_csv(used_vehicles: dict[str, dict], outdir: str) -> str:
    """
    Generate a CSV file with filtered vehicles (agent-used only).

    Args:
        used_vehicles: Dict from load_actively_used_vehicles
        outdir: Output directory

    Returns:
        Path to CSV file
    """
    import pandas as pd
    from .utils import seconds_to_hhmmss

    csv_path = str(Path(outdir) / "filtered_vehicles.csv")

    rows = []
    for veh_id in sorted(used_vehicles.keys()):
        veh_info = used_vehicles[veh_id]
        rows.append({
            "vehicle_id": veh_id,
            "mode": veh_info.get("mode", "unknown"),
            "first_use_time_s": veh_info.get("first_use_time_s", 0),
            "last_use_time_s": veh_info.get("last_use_time_s", 0),
            "first_use_time": seconds_to_hhmmss(veh_info.get("first_use_time_s", 0)),
            "last_use_time": seconds_to_hhmmss(veh_info.get("last_use_time_s", 0)),
            "agent_count": veh_info.get("agent_count", 0),
        })

    df_vehicles = pd.DataFrame(rows)
    df_vehicles.to_csv(csv_path, index=False)

    return csv_path
