# 5000_disatar/05_scripts - Script Map

This directory groups the project scripts by workflow stage, aligned with the docs.

## Folder Map

- `02_osm_network/` - OSM/SHP network ingestion and cleanup
  - Key: `convert_shapefile_to_network.py`, `build_combined_network.py`, `clean_network_connectivity.py`, `merge_short_links.py`
- `03_gtfs_public_transit/` - GTFS and PT preprocessing
  - Key: `clip_gtfs_bbox.py`, `clip_gtfs_scientific.py`, `filter_gtfs_subset.py`, `convert_bus_shapes_to_gtfs.py`
- `04_population/` - Population generation and transforms
  - Key: `json_to_population.py`, `augment_population.py`, `generate_evacuation_population.py`
  - Validation: `04_population/validation/validate_population_routes.py`, `validate-agent-journey.sh`
- `05_simulation/` - Simulation runners
  - Key: `run_simulation.sh`, `run_100_agents_simulation.sh`, `run_experiment_100k.sh`
- `06_disaster_evacuation/` - Evacuation scenario tooling
  - Key: `generate_change_events_depth.py`, `generate_change_events.py`, `run_staggered_iter10_pipeline.sh`
- `07_analysis/` - Post-simulation analysis and dashboards
  - Key: `run_dashboard_pipeline.sh`, `analyze_agent_speeds.py`, `generate_dashboard_yamls.py`, `generate_stuck_agents_csv.py`
- `09_operations/` - Ops, monitoring, and sync helpers
  - Key: `setup_remote_server.sh`, `sync_to_server.sh`, `monitor_resources.sh`
- `90_experiments/` - One-off or exploratory scripts

## Notes

- Scenario-specific scripts (e.g. `5000_disatar/06_taipei_test`, `5000_disatar/evacuation_test`) stay in their scenario folders.
- Shared assets remain in `tools/` (for example `dashboard-5-stuck.yaml`).
- Most docs refer to these paths directly; see `docs/README.md` for the workflow order.
