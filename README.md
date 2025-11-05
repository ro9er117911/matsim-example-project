# MATSim Example Project

Multi-Agent Transport Simulation project for modeling urban transportation systems, with focus on Taipei metro network.

## Quick Start

```bash
# Build the project
./mvnw clean package

# Run MATSim GUI
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar

# Run with scenario
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config_min.xml
```

## Technology Stack

- **Java 21** - Programming language
- **Maven** - Build system
- **MATSim 2025.0** - Simulation framework
- **pt2matsim** - GTFS-to-MATSim converter

## Project Structure

```
matsim-example-project/
├── src/main/java/               # Java source code
│   └── org/matsim/project/
│       ├── RunMatsim.java       # Basic entry point
│       ├── RunMatsimApplication.java  # CLI entry point
│       └── tools/               # PT conversion tools
├── scenarios/                   # Scenario configurations
│   ├── equil/                  # Example scenario
│   └── corridor/taipei_test/   # Taipei metro test
├── pt2matsim/                   # GTFS conversion pipeline
├── docs/                        # Documentation
├── output/                      # Simulation results
└── defaultConfig.xml            # Complete config reference
```

## Documentation

📚 **Comprehensive guides in [`docs/`](docs/)**:

1. [Quick Start Guide](docs/1-quick-start.md) - Installation and first run
2. [Architecture Overview](docs/2-architecture.md) - System design
3. [Public Transit Guide](docs/3-public-transit.md) - GTFS-to-MATSim workflow
4. [Agent Development](docs/4-agent-development.md) - Creating populations
5. [Configuration Reference](docs/5-configuration.md) - All config options
6. [Troubleshooting](docs/6-troubleshooting.md) - Common issues

📝 **For AI Assistants**: See [`CLAUDE.md`](CLAUDE.md) for project-specific guidance

📅 **Changelog**: See [`changelog/`](changelog/) for recent changes

## Features

- ✅ **Public Transit Simulation** - Complete GTFS-to-MATSim pipeline
- ✅ **Multimodal Network** - Car, PT, walk support
- ✅ **SwissRailRaptor** - Fast PT routing algorithm
- ✅ **Taipei Metro** - 5 metro lines (BL, G, O, R, BR)
- ✅ **Test Population** - 50-agent test scenario included
- ✅ **Python Tools** - Population generation and analysis

## Development Setup

### Prerequisites

- Java 21
- Maven 3.6+
- Git

### IDE Setup

**IntelliJ IDEA**:
```
File → New → Project from Version Control
Paste repository URL → Clone
```

**Eclipse**:
```
File → Import → Git → Projects from Git → Clone URI
File → Import → Maven → Existing Maven Projects
```

### Run Tests

```bash
# All tests
./mvnw test

# Specific test
./mvnw test -Dtest=RunMatsimTest
```

## Example Scenarios

### Equil Test Scenario
```bash
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config_min.xml
```

### Taipei Metro Test (50 agents)
```bash
java -Xmx4g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  scenarios/corridor/taipei_test/config.xml \
  --config:plans.inputPlansFile test_population_50.xml
```

## Generate Custom Populations

```bash
# Edit generate_test_population.py with your stations/routes
python generate_test_population.py

# Output: scenarios/corridor/taipei_test/test_population_50.xml
```

## Coordinate System

Default: **EPSG:3826** (TWD97 / TM2 zone 121, Taiwan)

## Output Analysis

After simulation, check:
- `output/scorestats.png` - Convergence
- `output/modestats.png` - Mode share
- `output/output_trips.csv.gz` - Trip data
- `output/output_events.xml.gz` - All events

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests: `./mvnw test`
5. Submit pull request

## Support

- 📖 **Documentation**: [`docs/`](docs/)
- 🐛 **Issues**: GitHub Issues
- 💬 **MATSim Help**: matsim@googlegroups.com
- 🌐 **MATSim Docs**: https://matsim.org/docs

## Licenses

- **MATSim code** (`src/`): [GPL v2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
- **Input/output files** (`scenarios/`, `output/`): [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/)
- **Original data** (`original-input-data/`): Individual licenses

## Recent Updates

See [`changelog/2025-11.md`](changelog/2025-11.md) for:
- Documentation restructure (2025-11-05)
- Test population generator (2025-11-05)
- PT SwissRailRaptor fix (2025-11-03)
- Vehicle filtering implementation (2025-11-04)

---

**Built with MATSim** | [matsim.org](https://matsim.org) | Version 2025.0
