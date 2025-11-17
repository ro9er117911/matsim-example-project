# MATSim Project Documentation

Complete documentation for the MATSim Example Project.

## 📚 Documentation Index

### Getting Started

**[1. Quick Start Guide](1-quick-start.md)**
- Installation and prerequisites
- Build and run commands
- Testing your setup
- Project structure overview

### Understanding the System

**[2. Architecture Overview](2-architecture.md)**
- System components and entry points
- Core workflow and data flow
- Testing architecture
- Design patterns and technology stack

### Working with Public Transit

**[3. Public Transit Guide](3-public-transit.md)** ⭐ **Most Important for PT**
- Complete GTFS-to-MATSim pipeline
- Step-by-step PT setup
- pt2matsim tools and configuration
- Common PT issues and solutions
- Configuration checklist
- Validation and best practices

### Running Simulations

**[Simulation Guide](simulation-guide.md)** ⭐ **Complete Simulation Walkthrough**
- Running simulations with 46 or 100 agents
- Population composition and features
- Step-by-step execution
- Validation and verification
- Expected results and metrics
- Troubleshooting simulation issues

**[Via Export Guide](via-export.md)**
- Exporting simulation results to Via platform
- Lightweight visualization data
- File isolation and workflow
- Command reference and parameters
- Verification and troubleshooting

### Creating Populations

**[4. Agent Development](4-agent-development.md)**
- Agent types (PT, car, walk, multimodal)
- Population file structure
- Activity and leg specification
- Time specification
- Python generation examples
- Validation techniques

**[Agent Generation](agent-generation.md)**
- Population generation scripts
- Station and route configuration
- Constraint validation
- Generation patterns

**[Agent Journey Guide](agent-journey-guide.md)**
- Building agent journeys
- Journey templates
- Multi-leg trip planning

### Analysis and Output

**[Output Analysis](output-analysis.md)**
- Analyzing simulation results
- Score and mode statistics
- Event log analysis
- Performance metrics

**[Early Stop Strategy](early-stop-strategy.md)**
- Early termination patterns
- Convergence detection
- Optimization strategies

### Configuration

**[5. Configuration Reference](5-configuration.md)**
- Essential modules (controller, global, routing, qsim, transit)
- Command-line overrides
- Common configuration patterns
- Performance tuning
- Configuration validation

### Problem Solving

**[6. Troubleshooting](6-troubleshooting.md)** ⭐ **Check Here When Things Break**
- Common errors and solutions
- PT-specific issues
- Network problems
- Agent issues
- Performance problems
- Debugging strategies

## 🎯 Quick Navigation

### By Task

| I want to... | Read this |
|--------------|-----------|
| Set up the project | [Quick Start](1-quick-start.md) |
| Understand how MATSim works | [Architecture](2-architecture.md) |
| Work with public transit | [PT Guide](3-public-transit.md) ⭐ |
| Run a simulation | [Simulation Guide](simulation-guide.md) ⭐ |
| Export to Via platform | [Via Export Guide](via-export.md) |
| Create custom populations | [Agent Development](4-agent-development.md) |
| Generate agent populations | [Agent Generation](agent-generation.md) |
| Analyze simulation results | [Output Analysis](output-analysis.md) |
| Configure a scenario | [Configuration](5-configuration.md) |
| Fix an error | [Troubleshooting](6-troubleshooting.md) ⭐ |

### By Component

| Component | Documentation |
|-----------|---------------|
| GTFS conversion | [PT Guide §2](3-public-transit.md#step-by-step-setup) |
| Network preparation | [PT Guide §3](3-public-transit.md#3-prepare-network) |
| PT mapping | [PT Guide §4](3-public-transit.md#4-map-schedule-to-network) |
| SwissRailRaptor | [PT Guide §5](3-public-transit.md#5-configure-matsim) |
| Population generation | [Agent Development](4-agent-development.md) |
| Config modules | [Configuration](5-configuration.md) |

## 🔧 Configuration Quick Reference

**Complete config reference**: [`../defaultConfig.xml`](../defaultConfig.xml)

**Key modules**:
- Controller (iterations, output) - [Config §Controller](5-configuration.md#controller-module)
- Global (CRS, threads) - [Config §Global](5-configuration.md#global-settings)
- Routing (modes) - [Config §Routing](5-configuration.md#routing-configuration)
- Transit (PT settings) - [Config §Transit](5-configuration.md#transit-module)
- QSim (simulation) - [Config §QSim](5-configuration.md#qsim-queue-simulation)

## 🚨 Most Common Issues

1. **PT agents teleport directly** → [Troubleshooting: PT Direct Transmission](6-troubleshooting.md#pt-agents-using-direct-transmission)
2. **ClassCastException route** → [Troubleshooting: ClassCastException](6-troubleshooting.md#classcastexception-transitpassengerroute--networkroute)
3. **Network not connected** → [Troubleshooting: Network Warnings](6-troubleshooting.md#network-not-connected-warnings)
4. **Too many artificial links** → [PT Guide: Mapping Issues](3-public-transit.md#issue-too-many-artificial-links)

## 📋 Essential Checklists

### Before Running PT Simulation

From [PT Guide](3-public-transit.md#configuration-checklist):

- [ ] `transit.useTransit = true`
- [ ] PT **NOT** in `routing.networkModes`
- [ ] PT **NOT** in `teleportedModeParameters`
- [ ] Multimodal network exists
- [ ] `transitSchedule.xml` and `transitVehicles.xml` present

### Before Modifying Config

From [Configuration](5-configuration.md#critical-parameters-checklist):

- [ ] Check `defaultConfig.xml` for parameter reference
- [ ] Set `controller.lastIteration` appropriately
- [ ] Set `global.coordinateSystem` correctly
- [ ] Verify all file paths exist
- [ ] Test with small population first

## 🔍 Search Tips

### Finding Config Parameters

1. Search `defaultConfig.xml` for parameter name
2. Check line number in comments
3. See [Configuration Reference](5-configuration.md) for explanation

Example:
```bash
# Find lastIteration in defaultConfig.xml
grep -n "lastIteration" ../defaultConfig.xml
# Result: line 31
```

### Finding Solutions

1. Check error message
2. Search [Troubleshooting](6-troubleshooting.md) for keyword
3. Check relevant guide (PT → [PT Guide](3-public-transit.md))

## 📦 Additional Resources

- **README**: [`../README.md`](../README.md) - Project overview
- **CLAUDE.md**: [`../CLAUDE.md`](../CLAUDE.md) - AI assistant guidance
- **Changelog**: [`../CHANGELOG.md`](../CHANGELOG.md) - Complete project history
- **Examples**: `../scenarios/corridor/taipei_test/` - Test scenarios
- **Archive**: [`../archive/`](../archive/) - Historical documentation and summaries

## 🌐 External Resources

- **MATSim Documentation**: https://matsim.org/docs
- **MATSim Mailing List**: matsim@googlegroups.com
- **pt2matsim GitHub**: https://github.com/matsim-org/pt2matsim

---

**Last Updated**: 2025-11-17 | **Documentation Version**: 2.0
