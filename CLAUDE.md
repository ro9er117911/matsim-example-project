# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working with this MATSim project.

## Project Overview

MATSim (Multi-Agent Transport Simulation) project for urban transportation systems modeling.

- **Language**: Java 21
- **Build**: Maven
- **Framework**: MATSim 2025.0
- **Focus**: Taipei metro network with public transit

## Quick Commands

```bash
# Build
./mvnw clean package

# Test
./mvnw test

# Run simulation
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar config.xml

# Run with memory
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar config.xml
```

## Key Entry Points

| File | Purpose |
|------|---------|
| `RunMatsim.java` | Basic entry point |
| `RunMatsimApplication.java` | CLI entry with picocli |
| `src/main/java/org/matsim/project/tools/` | PT conversion tools |
| `generate_test_population.py` | Python population generator |

## Critical Data Handling

**⚠️ NEVER read large files without explicit request**:

### High-Risk Directories
- `pt2matsim/data/` - GTFS feeds
- `pt2matsim/out/` - Converted data
- `scenarios/*/` - Large XML files
- `output/` - Simulation outputs

### High-Risk Files
- `*.xml.gz` - Compressed MATSim data
- `*events.xml*` - Event logs (extremely large)
- `*.osm`, `*.pbf` - OSM data

### Safe Alternatives
```bash
# Check file sizes first
ls -lh file.xml.gz

# Preview compressed files
zcat file.xml.gz | head -50

# Preview uncompressed files
head -50 file.xml

# Search with grep
grep "pattern" file.xml
```

## Documentation Structure

**Detailed guides** → [`docs/`](docs/):

1. `docs/1-quick-start.md` - Setup and first run
2. `docs/2-architecture.md` - System design
3. `docs/3-public-transit.md` - **Complete PT guide** (GTFS, mapping, troubleshooting)
4. `docs/4-agent-development.md` - Population creation
5. `docs/5-configuration.md` - **Config reference** (all modules)
6. `docs/6-troubleshooting.md` - Common issues

**Complete config reference** → `defaultConfig.xml` (with line numbers)

## Public Transit Quick Reference

### Tools

Located in `src/main/java/org/matsim/project/tools/`:
- `GtfsToMatsim` - GTFS → MATSim
- `PrepareNetworkForPTMapping` - Clean network
- `pt2matsim` jar - PT mapping (vendored at `pt2matsim/work/pt2matsim-25.8-shaded.jar`)

### Critical PT Configuration

```xml
<!-- Enable transit -->
<module name="transit">
    <param name="useTransit" value="true"/>
    <param name="transitModes" value="pt"/>
    <param name="routingAlgorithmType" value="SwissRailRaptor"/>
</module>

<!-- PT NOT in teleported modes -->
<module name="routing">
    <param name="networkModes" value="car"/>
    <!-- PT must NOT be here -->
</module>

<!-- Enable PT in QSim -->
<module name="qsim">
    <param name="mainMode" value="car,pt"/>
    <param name="usingTransitInMobsim" value="true"/>
</module>
```

**See [`docs/3-public-transit.md`](docs/3-public-transit.md) for complete PT setup**

## Common Issues & Quick Fixes

| Issue | Solution |
|-------|----------|
| PT direct transmission | Remove PT from teleported modes |
| ClassCastException route | Build multimodal network (car+walk+PT) |
| Network not connected | Run `PrepareNetworkForPTMapping` |
| Too many artificial links | Increase `maxLinkCandidateDistance` to 300-500m |

**See [`docs/6-troubleshooting.md`](docs/6-troubleshooting.md) for all issues**

## Configuration Best Practices

✅ **Always check `defaultConfig.xml` first** (complete reference with line numbers)

✅ **Critical parameters before running**:
- `controller.lastIteration` (line 31) - Set to 10-50 for testing
- `controller.overwriteFiles` (line 44) - Use `deleteDirectoryIfExists`
- `global.coordinateSystem` (line 106) - Must be `EPSG:3826`
- `routing.networkModes` (line 242) - Must NOT include `pt`
- `transit.useTransit` (line 504) - Must be `true` for PT

**See [`docs/5-configuration.md`](docs/5-configuration.md) for all modules**

## Testing Strategy

```bash
# Always run tests before committing
./mvnw test

# Test with small population first
# 10-50 agents for testing, 100+ for production
```

## Coordinate System

Default: **EPSG:3826** (TWD97 / TM2 zone 121, Taiwan)

## Output Structure

```
output/
├── output_events.xml.gz       # All events (most important)
├── output_plans.xml.gz        # Final agent plans
├── scorestats.csv/png         # Convergence check
├── modestats.csv/png          # Mode share
└── ITERS/                     # Per-iteration outputs
```

**See README.md for complete output file descriptions**

## Best Practices for AI Assistants

1. **Check documentation first**: `docs/` directory
2. **Verify file sizes**: `ls -lh` before reading
3. **Use grep/head**: Don't read large XML files directly
4. **Test incrementally**: Small populations first
5. **Validate config**: Check `defaultConfig.xml` for parameter reference
6. **Use TodoWrite**: Track multi-step tasks

## PT Setup Checklist

Before running PT simulations:

- [ ] Multimodal network exists (car + walk + PT)
- [ ] `transit.useTransit = true`
- [ ] PT **NOT** in `routing.networkModes`
- [ ] PT **NOT** in `teleportedModeParameters`
- [ ] `transit.routingAlgorithmType = "SwissRailRaptor"`
- [ ] `transitSchedule.xml` and `transitVehicles.xml` exist
- [ ] Network modes match `routing.networkModes`

**Complete checklist in [`docs/3-public-transit.md`](docs/3-public-transit.md)**

## Key Files Reference

| File | Purpose |
|------|---------|
| `defaultConfig.xml` | Complete config reference (all parameters with line numbers) |
| `docs/3-public-transit.md` | Complete PT guide |
| `docs/5-configuration.md` | Config module explanations |
| `docs/6-troubleshooting.md` | Error solutions |
| `generate_test_population.py` | Example population generator |
| `scenarios/corridor/taipei_test/test_population_50.xml` | Test population (50 agents) |

## Changelog

See [`changelog/2025-11.md`](changelog/2025-11.md) for recent changes.

## Getting Help

When stuck:
1. Check relevant doc in `docs/`
2. Search `defaultConfig.xml` for parameter
3. Check `output/logfileWarningsErrors.log`
4. See troubleshooting guide

---

**This file contains core guidance. Detailed instructions are in [`docs/`](docs/).**
