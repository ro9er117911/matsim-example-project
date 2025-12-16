# Agent Development Guide

## Agent Basics

In MATSim, an **agent** (or **person**) represents an individual with:
- **Activities** - Things they do (home, work, shop, etc.)
- **Legs** - Trips between activities (car, pt, walk, etc.)
- **Plans** - Sequences of activities and legs

## Population File Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">

<population>
    <person id="agent_001">
        <plan selected="yes">
            <!-- Morning: Home → Work -->
            <activity type="home" x="300000" y="2770000" end_time="07:30:00"/>
            <leg mode="pt"/>
            <activity type="work" x="305000" y="2771000" end_time="17:00:00"/>

            <!-- Evening: Work → Home -->
            <leg mode="car"/>
            <activity type="home" x="300000" y="2770000"/>
        </plan>
    </person>
</population>
```

## Agent Types

### 1. PT Agent (Public Transit)

**Pattern**: Home → PT → Work → PT → Home

```xml
<person id="pt_agent_01">
    <plan selected="yes">
        <!-- Morning trip -->
        <activity type="home" x="294035.05" y="2762173.24" end_time="07:00:00"/>
        <leg mode="walk"/>
        <activity type="pt interaction" x="294035.05" y="2762173.24" max_dur="00:05:00"/>
        <leg mode="pt"/>
        <activity type="pt interaction" x="303804.19" y="2770590.71" max_dur="00:05:00"/>
        <leg mode="walk"/>
        <activity type="work" x="303804.19" y="2770590.71" end_time="17:00:00"/>

        <!-- Evening trip -->
        <leg mode="walk"/>
        <activity type="pt interaction" x="303804.19" y="2770590.71" max_dur="00:05:00"/>
        <leg mode="pt"/>
        <activity type="pt interaction" x="294035.05" y="2762173.24" max_dur="00:05:00"/>
        <leg mode="walk"/>
        <activity type="home" x="294035.05" y="2762173.24"/>
    </plan>
</person>
```

**Key Points**:
- Use `pt interaction` activities for boarding/alighting
- Include walk legs for access/egress
- Set `max_dur` for interactions (typically 5 min)

### 2. Car Agent

**Pattern**: Home → Car → Work → Car → Home

```xml
<person id="car_agent_01">
    <plan selected="yes">
        <activity type="home" x="300488.79" y="2769778.54" end_time="07:30:00"/>
        <leg mode="car"/>
        <activity type="work" x="305544.29" y="2770487.68" end_time="17:00:00"/>
        <leg mode="car"/>
        <activity type="home" x="300488.79" y="2769778.54"/>
    </plan>
</person>
```

### 3. Walk Agent

**Pattern**: Home → Walk → Work → Walk → Home

```xml
<person id="walk_agent_01">
    <plan selected="yes">
        <activity type="home" x="301278.16" y="2770528.60" end_time="08:00:00"/>
        <leg mode="walk"/>
        <activity type="work" x="302208.73" y="2771006.76" end_time="14:00:00"/>
        <leg mode="walk"/>
        <activity type="home" x="301278.16" y="2770528.60"/>
    </plan>
</person>
```

### 4. Multimodal Agent

**Pattern**: Home → Walk → PT → Walk → Work → Car → Home

```xml
<person id="multimodal_agent_01">
    <plan selected="yes">
        <!-- Morning: PT -->
        <activity type="home" x="294035.05" y="2762173.24" end_time="07:00:00"/>
        <leg mode="walk"/>
        <activity type="pt interaction" x="294035.05" y="2762173.24" max_dur="00:05:00"/>
        <leg mode="pt"/>
        <activity type="pt interaction" x="303804.19" y="2770590.71" max_dur="00:05:00"/>
        <leg mode="walk"/>
        <activity type="work" x="303804.19" y="2770590.71" end_time="17:00:00"/>

        <!-- Evening: Car -->
        <leg mode="car"/>
        <activity type="home" x="294035.05" y="2762173.24"/>
    </plan>
</person>
```

## Coordinate Systems

### Using Coordinates (x, y)

**Recommended**: Let MATSim find nearest link automatically

```xml
<activity type="home" x="294035.05" y="2762173.24" end_time="07:00:00"/>
```

### Using Link IDs

**Advanced**: Manually specify network link

```xml
<activity type="home" link="81226" x="294035.05" y="2762173.24" end_time="07:00:00"/>
```

**Warning**: Link must exist in network.xml

## Activity Types

Common activity types:

| Type | Description | Typical Duration |
|------|-------------|------------------|
| `home` | Residence | Overnight |
| `work` | Employment | 8-9 hours |
| `shop` | Shopping | 0.5-2 hours |
| `leisure` | Recreation | 1-3 hours |
| `education` | School/University | 6-8 hours |
| `pt interaction` | PT boarding/alighting | 1-5 minutes |

## Time Specification

### End Time

Activity ends at specific time:
```xml
<activity type="home" x="..." y="..." end_time="07:30:00"/>
```

### Duration

Activity lasts for specified duration:
```xml
<activity type="work" x="..." y="..." dur="08:00:00"/>
```

### Maximum Duration

Activity lasts up to specified duration (for interactions):
```xml
<activity type="pt interaction" x="..." y="..." max_dur="00:05:00"/>
```

### No End Time

Last activity in plan (stay forever):
```xml
<activity type="home" x="..." y="..."/>
```

## Generating Populations

### Python Script Example

```python
def generate_pt_agent(agent_id, home_x, home_y, work_x, work_y, departure_time):
    return f'''
    <person id="pt_agent_{agent_id:03d}">
        <plan selected="yes">
            <activity type="home" x="{home_x}" y="{home_y}" end_time="{departure_time}"/>
            <leg mode="walk"/>
            <activity type="pt interaction" x="{home_x}" y="{home_y}" max_dur="00:05:00"/>
            <leg mode="pt"/>
            <activity type="pt interaction" x="{work_x}" y="{work_y}" max_dur="00:05:00"/>
            <leg mode="walk"/>
            <activity type="work" x="{work_x}" y="{work_y}" end_time="17:00:00"/>
            <leg mode="walk"/>
            <activity type="pt interaction" x="{work_x}" y="{work_y}" max_dur="00:05:00"/>
            <leg mode="pt"/>
            <activity type="pt interaction" x="{home_x}" y="{home_y}" max_dur="00:05:00"/>
            <leg mode="walk"/>
            <activity type="home" x="{home_x}" y="{home_y}"/>
        </plan>
    </person>
    '''
```

See `generate_test_population.py` for complete example.

## Validation

### Validate Link References

```bash
# Extract link IDs from population
grep -o 'link="[^"]*"' population.xml | sort -u > plan_links.txt

# Extract link IDs from network
grep '<link id=' network.xml | grep -o 'id="[^"]*"' | sort -u > network_links.txt

# Find missing links
comm -23 plan_links.txt network_links.txt
```

### Check Agent Count

```bash
grep -c "<person id=" population.xml
```

### Verify Activity Types

```bash
grep -o 'type="[^"]*"' population.xml | sort | uniq -c
```

## Best Practices

✅ **DO**:
- Use closed-loop routes (end where you started)
- Include `pt interaction` for PT agents
- Set realistic activity durations
- Use coordinate-based activities (not link-based)
- Distribute departure times to avoid congestion

❌ **DON'T**:
- Leave activities without end time (except last one)
- Forget walk legs for PT access/egress
- Use invalid coordinates (outside network bounds)
- Create zero-duration activities
- Use link IDs that don't exist in network

## Example: Test Population

See `scenarios/corridor/taipei_test/test_population_50.xml`:

- **30 PT agents** - All 5 Taipei metro lines
- **15 car agents** - Mixed peak/off-peak
- **5 walk agents** - Short distances

Generated with `generate_test_population.py`.

## Advanced: Multiple Plans

Agents can have multiple plan alternatives (MATSim selects best):

```xml
<person id="agent_choice">
    <plan selected="yes" score="120.5">
        <!-- Plan 1: PT -->
        <activity type="home" x="..." y="..." end_time="07:00:00"/>
        <leg mode="pt"/>
        <activity type="work" x="..." y="..." end_time="17:00:00"/>
        <leg mode="pt"/>
        <activity type="home" x="..." y="..."/>
    </plan>

    <plan selected="no" score="95.3">
        <!-- Plan 2: Car -->
        <activity type="home" x="..." y="..." end_time="07:30:00"/>
        <leg mode="car"/>
        <activity type="work" x="..." y="..." end_time="17:00:00"/>
        <leg mode="car"/>
        <activity type="home" x="..." y="..."/>
    </plan>
</person>
```

MATSim will evolve plans over iterations and select the highest-scoring one.

## Next Steps

- [Configuration Reference](5-configuration.md) - Scoring parameters
- [Troubleshooting](6-troubleshooting.md) - Common agent issues
