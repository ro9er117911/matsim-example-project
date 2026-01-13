# Implementation Plan: Main-Road Priority PT Integration Pipeline

## Objective
To resolve network connectivity gaps (Umbrella Patterns) in PT mapping by automatically connecting problematic transit stops/shapes to the nearest major road infrastructure (Main-Road Priority). This ensures buses are mapped to high-quality, high-capacity links used by private vehicles, which is critical for disaster evacuation accuracy.

## Architecture & Workflow

### 1. Diagnostic Stage (The "Umbrella" Finder)
- **Tool**: `diagnose_network_gaps.py`
- **Logic**: Parse the PTMapper logs to identify "Umbrella Links" (links that consistently fail to reach subsequent stop candidates).
- **Output**: `failed_connections.csv` containing `shape_id`, `stop_id`, and the coordinate of the failure.

### 2. Spatial Query Stage (Main-Road Selection)
- **Input**: `network.xml.gz`, `failed_connections.csv`.
- **Logic**: For each failure point:
    - Search for the nearest links within 200m.
    - Filter candidates by `ROADCLASS` (Prioritize classes like `1` or `2`, representing Motorways or Trunk roads).
    - Select the candidate that is part of the largest Strongly Connected Component (SCC).
- **Tool Selection**: Use `pyproj` for distance and `xml.etree.ElementTree` for network parsing.

### 3. Automated Bridge Construction
- **Task**: Modify `network.xml.gz` to add "Artificial PT Bridges".
- **Implementation**:
    - Build a new link connecting the transit stop facility coordinate directly to the chosen Main-Road link's nodes.
    - Set the mode of this new link to `bus`.
    - Ensure the topology remains valid MATSim-wise (Nodes must exist or be created).

### 4. PT Mapping Execution (Iterative)
- **Logic**: Rerun `PublicTransitMapperWithShapes` with the modified network.
- **Goal**: Since the "Umbrella Link" now has a valid exit path to a main artery, the mapping success rate should approach 100%.

## Proposed Files to be Created

### [NEW] `pt_bridge_generator.py`
A Python script to automate the selection of main roads and the XML generation for bridge links.

### [MODIFY] `ptmapper-config.xml`
Update to include the new modified network as input.

## Acceptance Criteria
1. The **"Umbrella Pattern"** in the GeoJSON diagnostic should disappear or be significantly reduced.
2. Bus routes should be visually confirmed to traverse major evacuation routes rather than stalling in dead-end alleys.
3. Total "Artificial Links" (`pt_link_...`) should be localized at stop access points rather than spanning long unmapped distances.

---

# Task: Implement Main-Road Priority PT Integration

## Task Breakdown
- [ ] **Data Extraction**
    - [ ] Run a baseline 400-route mapping on the server to generate a full error log.
    - [ ] Run `diagnose_network_gaps.py` to extract all failure points.
- [ ] **Algorithm Development**
    - [ ] Create `find_nearest_main_road(coord, network)` function.
    - [ ] Create `xml_append_link(network, from_node, to_node, mode='bus')` function.
- [ ] **Execution & Batching**
    - [ ] Process all 450 routes.
    - [ ] Output `network_v6_pt_ready.xml.gz`.
- [ ] **Final Verification**
    - [ ] Generate final `network_gaps_visualization.geojson`.
    - [ ] Verify that bus transit routes intersect correctly with high-capacity road links.
