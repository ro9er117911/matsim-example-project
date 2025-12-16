# MATSim Taipei Transport Simulation Project

## Tech Stack
- **Java 21** + **Maven** + **MATSim 2025.0**
- **pt2matsim** (vendored JAR: `pt2matsim/work/pt2matsim-25.8-shaded.jar`)
- **Python 3** for tooling and analysis
- **Coordinate System**: `EPSG:3826` (TWD97, Taiwan)

## Build & Run
```bash
./mvnw clean package                    # Build shaded JAR
./mvnw test                             # Run all tests
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar config.xml  # Run simulation
```

## Project Layout
| Path | Purpose |
|------|---------|
| `src/main/java/org/matsim/project/` | Entry points: `RunMatsim.java`, `RunMatsimApplication.java` |
| `src/main/java/org/matsim/project/tools/` | Java tools: GTFS conversion, network preparation |
| `src/main/python/` | Python tools: population generation, Via export, analysis |
| `scenarios/` | Scenario configs: network, population, transit schedule |
| `5000_disatar/` | Evacuation scenarios (staggered evacuation, coastal closures) |
| `pt2matsim/` | GTFS-to-MATSim conversion pipeline |
| `tools/` | Shell/Python utilities for dashboards, validation |
| `docs/` | Comprehensive documentation |
| `defaultConfig.xml` | **Reference for all MATSim config parameters** |

## Critical Rules

### 1. Large File Safety
**NEVER read these directly** — files can be 100MB+:
- `*.xml.gz` in `scenarios/`, `output/`, `pt2matsim/out/`  
- `*.osm`, `*.pbf` files
- `*events.xml*` files

**Use instead:**
```bash
ls -lh file.xml.gz          # Check size
zcat file.xml.gz | head -50 # Preview compressed
rg 'pattern' file.xml.gz    # Search with ripgrep
```

### 2. Shell Tool Preferences
| Task | Use | Avoid |
|------|-----|-------|
| Find files | `fd` | `find` |
| Text search | `rg` (ripgrep) | `grep` |
| Code structure | `ast-grep --lang java -p 'pattern'` | grep for code |
| JSON | `jq` | python |
| XML/YAML extract | `yq` | manual parsing |

### 3. Configuration Workflow
1. **Check `defaultConfig.xml` first** for available parameters
2. Create minimal scenario config with only required overrides
3. Use CLI overrides for testing: `--config:controller.lastIteration 10`

## Key MATSim Patterns

### Public Transit (SwissRailRaptor)
```xml
<!-- PT must NOT be in teleportedModeParameters -->
<module name="transit">
  <param name="useTransit" value="true"/>
  <param name="routingAlgorithmType" value="SwissRailRaptor"/>
</module>
<module name="swissRailRaptor">
  <param name="useIntermodalAccessEgress" value="false"/>  <!-- Use false for simple PT -->
</module>
```

### Common Gotchas
- **PT teleportation**: Remove PT from `teleportedModeParameters` to enable proper routing
- **Network modes**: `routing.networkModes` must match actual link modes in network
- **Zero-length links**: Cause simulation warnings — set minimum 1.0m
- **TransitVehicles**: Must always provide `transitVehicles.xml` with PT

## Scenario Types

### Active: `5000_disatar/05_combined_evac/`
- 5000-agent Taipei coastal evacuation
- Staggered departure with tsunami zone closures
- SimWrapper dashboard integration via `run_dashboard_pipeline.sh`

### Test: `scenarios/equil/`
- 50-100 agent test populations
- SwissRailRaptor PT routing
- Via export support

## Python Tools

### Population Generation
```bash
python src/main/python/generate_test_population.py  # 50-agent
python src/main/python/generate_test_population_500.py  # 500-agent
```

### Via Export Pipeline
```bash
python src/main/python/build_agent_tracks.py \
  --plans output/output_plans.xml.gz \
  --events output/output_events.xml.gz \
  --export-filtered-events \
  --out via_export/
```

### Dashboard Generation
```bash
./tools/run_dashboard_pipeline.sh output/
```

## Output Analysis
| File | Purpose |
|------|---------|
| `scorestats.csv/png` | Score convergence per iteration |
| `modestats.csv/png` | Mode share statistics |
| `output_trips.csv.gz` | Detailed trip data |
| `output_events.xml.gz` | Complete event log |

## Mermaid Syntax
Use **half-width (ASCII) punctuation only** — no full-width Chinese characters in colons, parentheses, or arrows.
