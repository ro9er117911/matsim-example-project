# MATSim Simulation Execution

This skill helps configure and run MATSim simulations with proper parameters and troubleshoot execution issues.

## When to Activate This Skill

Activate when user mentions:
- "Run MATSim simulation"
- "Configure simulation"
- "Simulation not converging"
- "Adjust scoring parameters"
- "Run config.xml"
- "Simulation stuck/failing"

## Workflow

### Step 1: Validate Configuration

```bash
# Check config file exists and is valid XML
xmllint --noout config.xml

# Verify referenced files exist
for file in $(grep -oP 'value="\K[^"]*\.xml[^"]*' config.xml); do
  [ -f "$file" ] && echo "✓ $file" || echo "✗ MISSING: $file"
done

# Check critical parameters
grep 'lastIteration' config.xml
grep 'coordinateSystem' config.xml
grep 'outputDirectory' config.xml
```

### Step 2: Check defaultConfig.xml Reference

**ALWAYS consult defaultConfig.xml before modifying configs**

Key parameters to verify (line numbers in defaultConfig.xml):
- **controller.lastIteration** (line 31): Default 1000 is too long for testing, use 10-50
- **controller.outputDirectory** (line 42): Avoid overwriting results
- **controller.overwriteFiles** (line 44): Set to `deleteDirectoryIfExists` for testing
- **global.coordinateSystem** (line 106): Must match network/population CRS
- **routing.networkModes** (line 242): Must include all simulated modes
- **transit.useTransit** (line 504): Must be true for PT scenarios

### Step 3: Choose Execution Method

**Option 1: Command-line with JAR**
```bash
# Build first if needed
./mvnw clean package

# Run with default config
java -Xmx8g -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar scenarios/equil/config.xml
```

**Option 2: Maven exec with parameter overrides**
```bash
./mvnw exec:java -Dexec.mainClass="org.matsim.project.RunMatsim" \
  -Dexec.args="config.xml \
    --config:controller.lastIteration 10 \
    --config:controller.outputDirectory ./test_output \
    --config:controller.overwriteFiles deleteDirectoryIfExists"
```

**Option 3: GUI for exploration**
```bash
java -jar target/matsim-example-project-0.0.1-SNAPSHOT.jar
# Opens GUI to select config and adjust parameters
```

### Step 4: Monitor Execution

```bash
# Watch log in real-time
tail -f output/logfile.log

# Check for errors
grep -i "error\|exception" output/logfileWarningsErrors.log

# Monitor progress
watch -n 5 'ls -lh output/ITERS/'
```

### Step 5: Validate Results

```bash
# Check convergence
open output/scorestats.png

# Check mode distribution
cat output/modestats.csv

# Count completed iterations
ls output/ITERS/ | grep -c 'it\.'
```

## Common Configuration Patterns

### PT-Only Scenario
```xml
<module name="qsim">
  <param name="mainMode" value="pt"/>
  <param name="usingTransitInMobsim" value="true"/>
</module>

<module name="routing">
  <param name="networkModes" value=""/>
  <!-- PT not teleported, not in networkModes -->
</module>

<module name="transit">
  <param name="useTransit" value="true"/>
  <param name="routingAlgorithmType" value="SwissRailRaptor"/>
</module>
```

### Multimodal Scenario
```xml
<module name="qsim">
  <param name="mainMode" value="car,pt"/>
  <param name="usingTransitInMobsim" value="true"/>
</module>

<module name="routing">
  <param name="networkModes" value="car"/>
  <!-- PT uses SwissRailRaptor -->
</module>
```

## Common Issues

### Issue 1: Simulation Doesn't Converge
**Symptom**: scorestats.png shows no stabilization
**Fixes**:
- Increase iterations to 50-100
- Adjust scoring parameters
- Check fractionOfIterationsToDisableInnovation=0.8

### Issue 2: Out of Memory
**Symptom**: java.lang.OutOfMemoryError
**Fixes**:
- Increase heap: `java -Xmx16g`
- Reduce output frequency: writeEventsInterval=50
- Use population sampling

### Issue 3: Wrong Coordinate System
**Symptom**: Agents in wrong locations, routing fails
**Fix**: Ensure consistent CRS across all files (EPSG:3826 for Taiwan)

### Issue 4: Stuck Agents
**Symptom**: WARN Agent XXX is stuck
**Fixes**:
- Increase stuckTime to 30s
- Check activities are within network bounds
- Enable removeStuckVehicles=true

## Pre-Run Checklist

- [ ] Start with 10-50 iterations for testing
- [ ] Use `deleteDirectoryIfExists` to avoid conflicts
- [ ] Validate all input files exist
- [ ] Check coordinate system is consistent
- [ ] Set reasonable memory (`-Xmx8g` minimum)
- [ ] For PT: verify transit modules enabled

## Post-Run Validation

- [ ] Review scorestats.png for convergence
- [ ] Check modestats.csv for mode distribution
- [ ] Validate events have expected patterns
- [ ] Check logfileWarningsErrors.log for issues

## File References

- CLAUDE.md: Lines 15-111 (Build & Run), 267-323 (Configuration)
- Default config: `defaultConfig.xml`
- Entry points: `src/main/java/org/matsim/project/RunMatsim*.java`
- Troubleshooting: `docs/6-troubleshooting.md`
