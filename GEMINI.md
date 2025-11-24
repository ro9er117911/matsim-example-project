# Project Overview

This project is a Multi-Agent Transport Simulation (MATSim) setup focused on modeling urban transportation systems, specifically the Taipei metro network. It uses MATSim 2025.0, a powerful simulation framework, alongside Java 21 and Maven for building and dependency management. The project incorporates `pt2matsim` for GTFS (General Transit Feed Specification) to MATSim conversion, enabling comprehensive public transit simulations.

**Key Features:**

*   **Public Transit Simulation:** Complete GTFS-to-MATSim pipeline for accurate public transport modeling.
*   **Multimodal Network:** Supports car, public transit, and walk modes.
*   **SwissRailRaptor:** Utilizes a fast public transit routing algorithm.
*   **Taipei Metro Integration:** Includes 5 metro lines (BL, G, O, R, BR) for the Taipei region.
*   **Test Populations:** Provides 50-agent and 100-agent test scenarios.
*   **Python Tools:** Scripts for population generation and analysis.

# Building and Running

## Prerequisites

*   Java Development Kit (JDK) 21
*   Maven 3.6+
*   Git

## Build the project

To build the project, navigate to the root directory and execute:

```bash
./mvnw clean package
```

This command compiles the Java code, runs tests, and packages the application into an executable JAR file.

## Run the MATSim GUI

To launch the MATSim graphical user interface (GUI) with the default configuration:

```bash
java -jar matsim-example-project-0.0.1-SNAPSHOT.jar
```

## Run with a specific scenario

To run a simulation with a predefined scenario configuration, for example, the `equil` scenario:

```bash
java -jar matsim-example-project-00.1-SNAPSHOT.jar scenarios/equil/config_min.xml
```

For more complex scenarios, such as the Taipei Metro Test with 50 agents:

```bash
java -Xmx4g -jar matsim-example-project-0.0.1-SNAPSHOT.jar \
  scenarios/corridor/taipei_test/config.xml \
  --config:plans.inputPlansFile test_population_50.xml
```

## Run Tests

To execute all unit and integration tests:

```bash
./mvnw test
```

To run a specific test class:

```bash
./mvnw test -Dtest=RunMatsimTest
```

# Development Conventions

## Project Structure

The project follows a standard Maven directory structure with specific additions for MATSim scenarios and documentation:

```
matsim-example-project/
├── src/main/java/           # Java source code
│   └── org/matsim/project/
│       ├── RunMatsim.java   # Basic entry point
│       ├── RunMatsimApplication.java  # CLI entry point
│       └── tools/           # PT conversion tools
├── scenarios/               # Simulation scenario configurations
├── pt2matsim/               # GTFS conversion pipeline
├── docs/                    # Comprehensive project documentation
├── output/                  # Default directory for simulation results
└── defaultConfig.xml        # Complete MATSim configuration reference
```

## Code Style and Contributions

*   The project uses Java 21.
*   Contributions are welcome via the following process:
    1.  Fork the repository.
    2.  Create a new feature branch.
    3.  Implement your changes.
    4.  Ensure all tests pass by running `./mvnw test`.
    5.  Submit a pull request.

## Documentation

Comprehensive documentation is available in the `docs/` directory, covering quick starts, architecture, configuration, troubleshooting, and specialized guides for public transit, agent development, and output analysis.

## Coordinate System

The default coordinate system used in the simulations is **EPSG:3826** (TWD97 / TM2 zone 121, Taiwan).

# Output Analysis

After running simulations, key output files for analysis include:

*   `output/scorestats.png`: Visualizes convergence of agent scores.
*   `output/modestats.png`: Displays mode share statistics.
*   `output/output_trips.csv.gz`: Contains detailed trip data.
*   `output/output_events.xml.gz`: Comprehensive log of all simulation events.
