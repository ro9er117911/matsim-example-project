# Network Validation & Troubleshooting

This skill helps validate MATSim networks, diagnose common network issues, and prepare networks for PT mapping.

## When to Activate This Skill

Activate when user mentions:
- "Network is not connected"
- "Validate network"
- "Link not found in network"
- "Zero-length links"
- "Clean network for PT"
- "Prepare network for mapping"
- "Network validation errors"

## Workflow

### Step 1: Basic Network Inspection

```bash
# Check file exists
ls -lh network.xml.gz

# Count nodes and links
gunzip -c network.xml.gz | grep -c '<node '
gunzip -c network.xml.gz | grep -c '<link '

# Check coordinate bounds
gunzip -c network.xml.gz | grep -oP 'x="\K[^"]*' | sort -n | head -1  # Min X
gunzip -c network.xml.gz | grep -oP 'x="\K[^"]*' | sort -n | tail -1  # Max X
```

### Step 2: Validate Mode Configuration

```bash
# Extract all modes in network
gunzip -c network.xml.gz | grep -o 'modes="[^"]*"' | sort | uniq -c

# Expected output should match config.xml routing.networkModes
grep 'networkModes' config.xml
```

### Step 3: Run Automated Network Cleaning

For PT scenarios, use PrepareNetworkForPTMapping:

```bash
./mvnw exec:java \
  -Dexec.mainClass="org.matsim.project.tools.PrepareNetworkForPTMapping" \
  -Dexec.args="network.xml.gz network-cleaned.xml.gz"
```

This tool:
- Adds 'pt' mode to all subway/rail links
- Runs NetworkUtils.cleanNetwork() to remove disconnected components
- Reports statistics

### Step 4: Common Issue Checks

**Check for zero-length links**:
```bash
gunzip -c network.xml.gz | grep 'length="0.0"' | head -10
```

**Check for missing PT modes on subway links**:
```bash
gunzip -c network.xml.gz | grep 'subway' | grep -v 'pt' | wc -l
# Should be 0
```

**Validate capacity values**:
```bash
gunzip -c network.xml.gz | grep 'capacity=' | sed 's/.*capacity="\([^"]*\)".*/\1/' | sort -n | head -20
```

### Step 5: Validate Population Link References

```bash
# Extract link IDs from population
grep -o 'link="[^"]*"' population.xml | sort -u > plan_links.txt

# Extract link IDs from network
gunzip -c network.xml.gz | grep '<link id=' | grep -o 'id="[^"]*"' | sort -u > network_links.txt

# Find missing links
comm -23 plan_links.txt network_links.txt
# Should be empty
```

## Common Issues

### Issue 1: Network Not Connected

**Symptom**: Warnings during simulation or PT mapping
**Fix**: Run PrepareNetworkForPTMapping or use NetworkUtils.cleanNetwork()

### Issue 2: Zero-Length Links

**Symptom**: Warnings about link length = 0.0
**Fix**: Set minimum length in network generation or manually edit

### Issue 3: Mode Mismatch

**Symptom**: Config references modes not in network
**Fix**: Either add modes to network or remove from config

### Issue 4: Missing PT Modes

**Symptom**: Subway links don't have 'pt' mode
**Fix**: Run PrepareNetworkForPTMapping

## Validation Checklist

- [ ] Network loads without errors
- [ ] Coordinate bounds contain population activities
- [ ] All modes in config exist in network
- [ ] No zero-length links (or acceptable for PT)
- [ ] No "Network not connected" warnings after cleaning
- [ ] PT links have 'pt' mode if using transit
- [ ] All population activity links exist in network

## File References

- Tool: `src/main/java/org/matsim/project/tools/PrepareNetworkForPTMapping.java`
- CLAUDE.md: Lines 214-261, 325-375
- Troubleshooting guide: `docs/6-troubleshooting.md`
