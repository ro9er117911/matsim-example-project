# MATSim Population Route Validator

Validates MATSim population files by checking route reachability on directional networks and automatically converting unreachable car agents to PT mode when possible.

## Features

- **Directional Routing Validation**: Respects one-way links in network
- **Automatic Car→PT Conversion**: Converts car agents to PT when car route is unreachable but PT route exists
- **PT Accessibility Validation**: Checks if PT agents can access stops within walking distance
- **Memory Efficient**: Uses iterparse for streaming XML processing
- **Spatial Indexing**: KDTree-based fast coordinate snapping (with scipy) or fallback to linear search
- **Comprehensive Reports**: CSV, JSON, and filtered population outputs

## Installation

### Requirements

- Python 3.8+
- NetworkX (`pip install networkx`)
- scipy (optional, for faster spatial queries): `pip install scipy`

### Quick Setup

```bash
# Install required packages
pip install networkx

# Optional: Install scipy for better performance
pip install scipy
```

## Usage

### Basic Command

```bash
python validate_population_routes.py \
    --population ../working_temp/population.xml.gz \
    --network ../03_phase2_production/networks/network-with-pt-final.xml \
    --schedule ../03_phase2_production/schedules/transitSchedule-mapped-final.xml.gz \
    --output-dir ../validation_output \
    --progress
```

### Command-Line Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--population` | Yes | - | Input population.xml(.gz) file |
| `--network` | Yes | - | MATSim network.xml file |
| `--schedule` | Yes | - | Transit schedule.xml(.gz) file |
| `--output-dir` | No | `./validation_output` | Output directory |
| `--max-walk-distance` | No | 500.0 | Max walking distance to PT stops (meters) |
| `--max-snap-distance` | No | 300.0 | Max coordinate-to-link snapping distance (meters) |
| `--batch-size` | No | 100 | Agent processing batch size |
| `--progress` | No | False | Show progress during processing |

### Example: 5000-Agent Scenario

```bash
python validate_population_routes.py \
    --population ../working_temp/population.xml.gz \
    --network ../03_phase2_production/networks/network-with-pt-final.xml \
    --schedule ../03_phase2_production/schedules/transitSchedule-mapped-final.xml.gz \
    --output-dir ../validation_output \
    --max-walk-distance 500 \
    --max-snap-distance 300 \
    --progress
```

## Output Files

The validator generates three output files in the specified output directory:

### 1. `filtered_population.xml.gz`

Filtered population containing only valid agents (valid car routes, valid PT routes, and car→PT conversions).

- Valid car agents: unchanged
- Converted agents: `<leg mode="car">` changed to `<leg mode="pt">`
- Invalid agents: removed

### 2. `validation_report.csv`

Per-agent validation details with columns:

| Column | Description |
|--------|-------------|
| `agent_id` | Agent identifier |
| `original_mode` | Original mode from legs (car, pt, walk) |
| `final_mode` | Final mode after validation (may be converted) |
| `status` | Validation status: `valid`, `converted`, or `invalid` |
| `reason` | Reason for status |
| `origin_x`, `origin_y` | Origin coordinates |
| `dest_x`, `dest_y` | Destination coordinates |
| `car_reachable` | Whether car route is reachable (True/False) |
| `pt_accessible` | Whether PT is accessible (True/False) |

### 3. `validation_summary.json`

Summary statistics in JSON format:

```json
{
  "total_agents": 5000,
  "valid_agents": 4235,
  "converted_agents": 542,
  "invalid_agents": 223,
  "mode_breakdown": {
    "car": 2103,
    "pt": 1950,
    "walk": 182
  },
  "invalid_reasons": {
    "car_unreachable_no_pt_no_origin_stops": 123,
    "car_unreachable_no_pt_no_route": 100
  },
  "conversion_rate": 0.1084,
  "processing_time_seconds": 245.3
}
```

## Validation Logic

### Car Agents

1. Snap origin and destination to nearest `car`-compatible network links
2. Check directional reachability using BFS on car subgraph
3. If **unreachable**:
   - Check PT accessibility (stops within 500m, route exists)
   - If PT accessible: **Convert to PT mode** (change `<leg mode="car">` to `<leg mode="pt">`)
   - If PT not accessible: **Mark invalid** and remove from population

### PT Agents

1. Find accessible PT stops within walking distance (default: 500m)
2. Check if route exists between origin and destination stops (direct or single transfer)
3. If no accessible stops or no route: **Mark invalid** and remove

### Walk Agents

- Always considered valid (no validation performed)

## Performance

### Expected Performance (5000-agent scenario)

- **Runtime**: 3-4 minutes
- **Memory**: 300-400 MB peak
- **Processing rate**: ~36 agents/second

### Optimization Features

- **Routing cache**: 60-70% hit rate for reachability queries
- **Spatial indexing**: KDTree for O(log n) coordinate snapping
- **Streaming XML**: iterparse to avoid loading entire file into memory
- **Batch processing**: Progress reporting every 100 agents

## Module Architecture

```
validation/
├── __init__.py                  - Package exports
├── utils.py                     - Utility functions
├── network_graph.py             - DirectedNetworkGraph (NetworkX + KDTree)
├── routing_validator.py         - DirectionalRoutingValidator (BFS reachability)
├── pt_validator.py              - PTCoverageValidator (stop accessibility)
├── agent_processor.py           - AgentRouteProcessor (car→PT conversion)
└── output_generator.py          - FilteredPopulationWriter (reports)
```

## Algorithm Details

### Directional Routing

- Uses NetworkX `has_path()` with BFS for reachability checks
- Builds mode-specific subgraphs (e.g., car-only network)
- Caches routing results for performance

### PT Accessibility

- **Stop accessibility**: KDTree or linear search within `max_walk_distance`
- **Route validation**: Checks for direct routes or single-transfer connections
- **Simplified approach**: Does not simulate full SwissRailRaptor routing

### Coordinate Snapping

- Snaps activity coordinates to nearest network link midpoints
- Mode-specific filtering (car links vs PT stops)
- Configurable maximum distance threshold

## Troubleshooting

### scipy not available warning

```
Warning: scipy not available. Coordinate snapping will use slower linear search.
```

**Solution**: Install scipy for better performance: `pip install scipy`

**Impact**: Validation will still work but may be 2-3x slower for large networks.

### No agents in filtered population

Check `validation_summary.json` for `invalid_reasons`. Common causes:

- `no_origin_link` / `no_dest_link`: Coordinates too far from network (increase `--max-snap-distance`)
- `no_origin_stops` / `no_dest_stops`: No PT stops nearby (increase `--max-walk-distance`)
- `unreachable`: Network connectivity issues (check for disconnected components)

### Very slow processing

- Install scipy: `pip install scipy`
- Reduce network size (filter unnecessary links)
- Increase `--batch-size` for less frequent progress reporting

## Advanced Usage

### Custom Validation Thresholds

```bash
# Allow longer walking distances and link snapping
python validate_population_routes.py \
    --population population.xml.gz \
    --network network.xml \
    --schedule schedule.xml.gz \
    --output-dir validation_output \
    --max-walk-distance 800 \
    --max-snap-distance 500
```

### Quiet Mode (No Progress)

```bash
# Omit --progress flag
python validate_population_routes.py \
    --population population.xml.gz \
    --network network.xml \
    --schedule schedule.xml.gz \
    --output-dir validation_output
```

## Integration with MATSim Workflow

### Typical Workflow

1. **Generate population** from ABM data:
   ```bash
   python json_to_population.py --input raw_data.json --output population.xml.gz
   ```

2. **Validate routes**:
   ```bash
   python validate_population_routes.py \
       --population population.xml.gz \
       --network network.xml \
       --schedule schedule.xml.gz \
       --output-dir validation_output
   ```

3. **Run MATSim simulation** with filtered population:
   ```bash
   java -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
       --config config.xml \
       --population validation_output/filtered_population.xml.gz
   ```

## References

- **NetworkX**: https://networkx.org/
- **MATSim**: https://matsim.org/
- **KDTree**: https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.html
