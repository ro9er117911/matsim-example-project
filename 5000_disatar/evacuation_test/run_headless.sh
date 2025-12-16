#!/bin/bash

# Configuration
# Adjust MAX_RAM based on your machine (e.g., 4g, 16g, 32g)
MAX_RAM="16g"
JAR_PATH="../../matsim-example-project-0.0.1-SNAPSHOT.jar"

# Input Arguments
CONFIG_FILE=$1

if [ -z "$CONFIG_FILE" ]; then
    echo "Usage: $0 <path-to-config.xml>"
    echo "Example: $0 ./output/config.xml"
    exit 1
fi

if [ ! -f "$JAR_PATH" ]; then
    echo "Error: MATSim JAR not found at $JAR_PATH"
    echo "Please build the project first: ./mvnw clean package"
    exit 1
fi

echo "----------------------------------------------------------------"
echo "Starting MATSim Evacuation Simulation (Headless Mode)"
echo "Config: $CONFIG_FILE"
echo "Memory: $MAX_RAM"
echo "----------------------------------------------------------------"

# Run command
java -Xmx$MAX_RAM \
     -Djava.awt.headless=true \
     -jar $JAR_PATH \
     $CONFIG_FILE

echo "----------------------------------------------------------------"
echo "Simulation Finished."
