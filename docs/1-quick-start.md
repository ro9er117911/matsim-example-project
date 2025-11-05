# Quick Start Guide

## Prerequisites

- Java 21
- Maven 3.6+

## Build & Run

```bash
# Build the project
./mvnw clean package

# Run MATSim GUI
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar

# Run with example scenario
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config_min.xml

# Run with more memory (for large scenarios)
java -Xmx8g -jar matsim-example-project-0.0.1-SNAPSHOT.jar config.xml
```

## Test Your Setup

```bash
# Run all tests
./mvnw test

# Run specific test
./mvnw test -Dtest=RunMatsimTest
```

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
└── output/                      # Simulation results
```

## Next Steps

- [Architecture Overview](2-architecture.md) - Understand the system design
- [Public Transit Setup](3-public-transit.md) - Work with PT networks
- [Agent Development](4-agent-development.md) - Create custom agents
- [Configuration Reference](5-configuration.md) - Configure scenarios
