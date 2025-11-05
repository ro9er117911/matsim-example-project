# Architecture Overview

## System Components

### Entry Points

MATSim simulations can be launched via three entry points:

| Class | Description | Use Case |
|-------|-------------|----------|
| `RunMatsim.java` | Basic manual setup | Learning, simple scenarios |
| `RunMatsimApplication.java` | Modern CLI with picocli | Production, complex scenarios |
| `RunMatsimFromExamplesUtils.java` | Built-in examples | Testing, demos |

All follow the **three-phase pattern**:
1. **Config** - Load and customize configuration
2. **Scenario** - Build network, population, facilities
3. **Controler** - Run simulation with custom modules

### Core Workflow

```
Config.xml → Scenario (Network + Population) → Controler → Output
              ↑                                    ↑
         GTFS/OSM Data                    Custom Modules
```

## Public Transit Pipeline

Located in `src/main/java/org/matsim/project/tools/`:

1. **GtfsToMatsim** - GTFS → MATSim schedule/vehicles
2. **ConvertGtfsCoordinates** - CRS transformation
3. **PrepareNetworkForPTMapping** - Network preparation
4. **pt2matsim PublicTransitMapper** - Map schedule to network
5. **PreRoutePt** - Pre-route PT legs in population

## Data Flow

```
GTFS zip files → GtfsToMatsim → transitSchedule.xml
                                 transitVehicles.xml
                                        ↓
OSM data → network.xml ← PrepareNetworkForPTMapping
                ↓
     pt2matsim mapper → mapped schedule
                ↓
        population.xml → MATSim Controler → output/
```

## Testing Architecture

- **JUnit 5** for all tests
- **MatsimTestUtils** for integration tests
- **RunMatsimTest** - Validates output against reference files
- Test scenarios in `ExamplesUtils.getTestScenarioURL()`

## Output Structure

```
output/
├── output_config.xml          # Final configuration
├── output_events.xml.gz       # All simulation events
├── output_plans.xml.gz        # Final agent plans
├── output_network.xml.gz      # Network state
├── scorestats.csv/png         # Convergence metrics
├── modestats.csv/png          # Mode share statistics
└── ITERS/                     # Per-iteration outputs
    ├── it.0/
    │   ├── 0.events.xml.gz
    │   ├── 0.plans.xml.gz
    │   └── 0.legHistogram*.png
    └── it.N/
```

## Key Design Patterns

### Template Method Pattern
`RunMatsimApplication` provides hooks:
```java
prepareConfig(Config config)
prepareScenario(Scenario scenario)
prepareControler(Controler controler)
```

### Dependency Injection
MATSim uses **Guice** for module binding:
```java
controler.addOverridingModule(new AbstractModule() {
    @Override
    public void install() {
        bind(MyService.class).to(MyServiceImpl.class);
    }
});
```

## Technology Stack

- **Java 21** - Language
- **Maven** - Build system
- **MATSim 2025.0** - Simulation framework
- **pt2matsim 25.8** - PT conversion (vendored JAR)
- **picocli** - CLI framework
- **JUnit 5** - Testing
- **Guice** - Dependency injection

## Coordinate System

Default CRS: **EPSG:3826** (TWD97 / TM2 zone 121, Taiwan)

Configure in `defaultConfig.xml`:
```xml
<module name="global">
    <param name="coordinateSystem" value="EPSG:3826"/>
</module>
```

## Next Steps

- [Public Transit Guide](3-public-transit.md) - PT setup details
- [Configuration Reference](5-configuration.md) - All config options
