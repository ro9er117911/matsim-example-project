# SimWrapper Visualization Workflow

This document outlines the workflow for generating SimWrapper dashboards for the evacuation simulation and lists other compatible visualization types.

## 1. Quick Start: One-Click Dashboard

We have set up an automated script to process MATSim output events and generate a complete SimWrapper dashboard.

**Steps:**
1.  Run your simulation (ensure `output/output/output_events.xml.gz` exists).
2.  Execute the generation script:
    ```bash
    ./generate_dashboard.sh
    ```
3.  Open SimWrapper (install via `npm install -g simwrapper-server` and run `simwrapper`, or drop the folder into the website).
4.  Navigate to the `analysis/simwrapper` folder.

**What you get:**
*   **Evacuation Map**: A gridded heatmap of average evacuation times (XYT format).
*   **Cumulative Curve**: A line chart showing the number of agents reaching safety over time.
*   **Flow Rate**: A bar chart showing arrivals per minute.
*   **O/D Density**: Hexagon map showing where evacuees started and ended.
*   **Time Tables**: A categorized table of evacuation times (e.g., <10min, 10-20min).

---

## 2. Manual Workflow & Script Details

The `generate_dashboard.sh` script wraps a Python tool `tools/make_evac_simwrapper.py`.

### The Python Tool (`tools/make_evac_simwrapper.py`)
This script parses the raw XML events stream (memory efficiently) and extracts:
*   `actend` (pre-evac) coordinates and time.
*   `actstart` (post-evac) coordinates and time.
*   `arrival` times.

It then calculates statistics and writes:
*   `dashboard-evacuation.yml`: The main configuration file for SimWrapper.
*   `evac_*.csv`: various data files referenced by the dashboard.

**Usage:**
```bash
python3 tools/make_evac_simwrapper.py [EVENTS_FILE] --outdir [OUTPUT_DIR] --cells [GRID_RESOLUTION]
```

---

## 3. Other SimWrapper Capabilities

SimWrapper is very flexible. Besides the evacuation dashboard we built, here are other visualizations you can add by generating the appropriate files.

### A. Network & Traffic
| Visualization | Required File | Format | Description |
| :--- | :--- | :--- | :--- |
| **Link Volumes** | `counts.csv` or `links.csv` | CSV | Network links colored by volume/capacity. CSV needs `linkId` and value columns. |
| **Network Changes**| `output_network_change_events.xml` | XML | Validates time-dependent network changes (e.g., bridge closing). |

### B. Agents & Trips
| Visualization | Required File | Format | Description |
| :--- | :--- | :--- | :--- |
| **Agent Animation** | `output_events.xml.gz` | XML | **(Native Support)** SimWrapper can play back vehicle movements directly from the events file. Just ensure `output_network.xml.gz` and `output_events.xml.gz` are in the same folder. |
| **PT Ridership** | `stop_counts.csv` | CSV | Visualize boardings/alightings at transit stops. |
| **Aggregated Plans**| `plans.csv.gz` | CSV | XY points of activity locations (home/work/etc). |

### C. Spatial Analysis
| Visualization | Required File | Format | Description |
| :--- | :--- | :--- | :--- |
| **Shapefiles** | `zones.zip` (shp) or `.geojson` | SHP/GeoJSON | Overlay TAZ, hazard zones, or administrative boundaries. |
| **Hexagons** | `data.csv` | CSV | Aggregate any point data (x,y) into hexagonal bins (like we did for O/D). |

### D. General Plots
*   **Scatter Plots**: `type: scatter` in YAML.
*   **Sankey Diagrams**: Great for visualizing mode shifts or O/D flows between major districts.
*   **Kepler.gl Integration**: SimWrapper can embed Kepler.gl configs for advanced geospatial interaction.

## 4. Configuration Reference

*   **Official Documentation**: [https://github.com/simwrapper/simwrapper](https://github.com/simwrapper/simwrapper)
*   **Dashboard Config**: The YAML files (`dashboard-*.yml`) control the layout. You can edit `analysis/simwrapper/dashboard-evacuation.yml` to change colors, titles, or adding new panels.
