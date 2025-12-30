# Taipei Simulation Server Migration Guide

This guide provides instructions for setting up and running the Taipei simulation on a new server.

## Prerequisites

1.  **Java 21**: Ensure Java 21 is installed.
    ```bash
    java -version
    ```
2.  **Maven Wrapper**: Use the bundled `./mvnw` in the project root to ensure consistent Maven versions and dependencies.
3.  **Memory**: The simulation requires at least 8GB of heap memory (12GB recommended).

## Setup Steps

1.  **Clone / Copy Repository**: Transfer the entire `matsim-example-project` folder to the new server.
2.  **Verify Input Files**: Ensure the following files are present:
    - [network.xml.gz](file:///Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/taipei_shp_map/output/network.xml.gz)
    - [population_5000.xml.gz](file:///Users/ro9air/matsim-example-project/5000_disatar/01_raw_data/taipei_shp_map/output/population_5000.xml.gz)
3.  **Build (Optional but recommended)**:
    ```bash
    ./mvnw clean compile
    ```

## Running the Simulation

Use the provided runner script which has been optimized for this simulation:

```bash
cd 5000_disatar/06_taipei_test
bash run_taipei_simulation.sh
```

### Script Features
-   **Maven Wrapper**: Uses `./mvnw` automatically.
-   **Custom Runner**: Calls `org.matsim.project.RunMatsim` which includes:
    -   **SimWrapper**: Automatic generation of visualization dashboards.
    -   **NetworkCleaner**: Automatically fixes disconnected road segments for car routing.

## Troubleshooting

-   **Memory Issues**: Adjust `JAVA_MEM` in `run_taipei_simulation.sh` if needed.
-   **Output Location**: Results are saved in `output_taipei_car_5000` at the project root by default when using the script.

## Why previous runs failed
-   **Old Output (`output_taipei_car_5000_old`)**: Failed due to (1) missing Maven path, (2) using standard MATSim core instead of project custom runner, and (3) network connectivity issues which have now been resolved in the code.
