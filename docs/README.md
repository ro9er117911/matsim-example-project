# MATSim Project Documentation

Complete documentation for the MATSim Example Project.

> **Single source of truth**: see [`../PROJECT_WIKI.md`](../PROJECT_WIKI.md) for the canonical project map and disaster-evacuation workflow.

## 📚 Documentation Index

### Getting Started

**[Quick Start Guide](01-getting-started/quick-start.md)**
- Installation and prerequisites
- Build and run commands
- Testing your setup
- Project structure overview

### Understanding the System

**[Architecture Overview](02-architecture/architecture-overview.md)**
- System components and entry points
- Core workflow and data flow
- Testing architecture
- Design patterns and technology stack

**[Algorithm Notes](02-architecture/algorithm-notes.md)**
- Internal routing and algorithm notes

### Working with Public Transit (PT)

**[Public Transit Guide](03-public-transit/public-transit-guide.md)** ⭐ **Most Important for PT**
- Complete GTFS-to-MATSim pipeline
- Step-by-step PT setup
- pt2matsim tools and configuration
- Common PT issues and solutions
- Configuration checklist
- Validation and best practices

**PT Mapping & GTFS**
- [GTFS Mapping Guide](03-public-transit/gtfs-mapping-guide.md)
- [PT Mapping Strategy](03-public-transit/pt-mapping-strategy.md)
- [GTFS Tools Guide](03-public-transit/gtfs/gtfs-tools-guide.md)
- [GTFS Merge Analysis](03-public-transit/gtfs/gtfs-merge-analysis.md)
- [PT Mapping Quick Start](03-public-transit/pt/pt-mapping-quick-start.md)
- [Next Agent Instructions](03-public-transit/pt/next-agent-instructions.md)
- [SwissRailRaptor Report](03-public-transit/swissrail-report.md)

### Creating Populations

**[Agent Development](04-population/agent-development.md)**
- Agent types (PT, car, walk, multimodal)
- Population file structure
- Activity and leg specification
- Time specification
- Python generation examples
- Validation techniques

**[Agent Generation](04-population/agent-generation.md)**
- Population generation scripts
- Station and route configuration
- Constraint validation
- Generation patterns

**[Agent Journey Guide](04-population/agent-journey-guide.md)**
- Building agent journeys
- Journey templates
- Multi-leg trip planning

### Running Simulations

**[Simulation Guide](05-simulation/simulation-guide.md)** ⭐ **Complete Simulation Walkthrough**
- Running simulations with 46 or 100 agents
- Population composition and features
- Step-by-step execution
- Validation and verification
- Expected results and metrics
- Troubleshooting simulation issues

**[Via Export Guide](05-simulation/via-export.md)**
- Exporting simulation results to Via platform
- Lightweight visualization data
- File isolation and workflow
- Command reference and parameters
- Verification and troubleshooting

**[Early Stop Strategy](05-simulation/early-stop-strategy.md)**
- Early termination patterns
- Convergence detection
- Optimization strategies

### Disaster / Evacuation Scenarios

**[Evacuation & Disaster Guide](06-disaster-evacuation/evacuation-guide.md)** ⭐ **Project-specific**
- How this repo models tsunami/flood evacuation (5000_disatar)
- Time-variant network (changeEvents) and hazard data
- Recommended configs and pipelines

**[Disaster Config Notes](06-disaster-evacuation/config-metro-100k-evac-notes.md)**
- Notes for large-scale evacuation configs

**[Disaster Workflow (5000_disatar)](../5000_disatar/05_combined_evac/WORKFLOW.md)**
- End-to-end pipeline for staggered evacuation + SimWrapper outputs

### Analysis and Output

**[Output Analysis](07-analysis/output-analysis.md)**
- Analyzing simulation results
- Score and mode statistics
- Event log analysis
- Performance metrics

**[SimWrapper Workflow](07-analysis/simwrapper-workflow.md)**
- Dashboard generation and visualization pipeline

**[Verification Report](07-analysis/reports/simulation-verification-report.md)**
- Simulation verification summary

### Configuration

**[Configuration Reference](08-configuration/configuration-reference.md)**
- Essential modules (controller, global, routing, qsim, transit)
- Command-line overrides
- Common configuration patterns
- Performance tuning
- Configuration validation

### Operations

**[Remote Server Setup](09-operations/remote-server-setup.md)**
- Remote environment setup and data sync

### Troubleshooting

**[Troubleshooting Guide](10-troubleshooting/troubleshooting.md)** ⭐ **Check Here When Things Break**
- Common errors and solutions
- PT-specific issues
- Network problems
- Agent issues
- Performance problems
- Debugging strategies

**[VS Code Crash Diagnosis](10-troubleshooting/vs-code-crash-diagnosis.md)**
- Editor crash handling

### Modes & Extras

**Motorcycle Mode**
- [Motorcycle Quick Start](11-modes/motorcycle/motorcycle-quick-start.md)
- [Motorcycle Repair Plan](11-modes/motorcycle/motorcycle-repair-plan.md)

### Notes & Background

- [MATSim Pipeline Complete Guide](12-notes/matsim-pipeline-complete-guide.md)
- [Gemini Notes](12-notes/gemini.md)
- [SimWrapper Notes](12-notes/matsimwrap.md)
- Snippets: `12-notes/snippets/`

## 🎯 Quick Navigation

### By Task

| I want to... | Read this |
|--------------|-----------|
| Set up the project | [Quick Start](01-getting-started/quick-start.md) |
| Understand how MATSim works | [Architecture](02-architecture/architecture-overview.md) |
| Work with public transit | [PT Guide](03-public-transit/public-transit-guide.md) ⭐ |
| Run a simulation | [Simulation Guide](05-simulation/simulation-guide.md) ⭐ |
| Run disaster evacuation | [Evacuation Guide](06-disaster-evacuation/evacuation-guide.md) ⭐ |
| Export to Via platform | [Via Export Guide](05-simulation/via-export.md) |
| Create custom populations | [Agent Development](04-population/agent-development.md) |
| Generate agent populations | [Agent Generation](04-population/agent-generation.md) |
| Analyze simulation results | [Output Analysis](07-analysis/output-analysis.md) |
| Configure a scenario | [Configuration](08-configuration/configuration-reference.md) |
| Fix an error | [Troubleshooting](10-troubleshooting/troubleshooting.md) ⭐ |

### By Component

| Component | Documentation |
|-----------|---------------|
| GTFS conversion | [PT Guide §2](03-public-transit/public-transit-guide.md#step-by-step-setup) |
| Network preparation | [PT Guide §3](03-public-transit/public-transit-guide.md#3-prepare-network) |
| PT mapping | [PT Guide §4](03-public-transit/public-transit-guide.md#4-map-schedule-to-network) |
| SwissRailRaptor | [PT Guide §5](03-public-transit/public-transit-guide.md#5-configure-matsim) |
| Population generation | [Agent Development](04-population/agent-development.md) |
| Config modules | [Configuration](08-configuration/configuration-reference.md) |

## 🔧 Configuration Quick Reference

**Complete config reference**: [`../defaultConfig.xml`](../defaultConfig.xml)

**Key modules**:
- Controller (iterations, output) - [Config §Controller](08-configuration/configuration-reference.md#controller-module)
- Global (CRS, threads) - [Config §Global](08-configuration/configuration-reference.md#global-settings)
- Routing (modes) - [Config §Routing](08-configuration/configuration-reference.md#routing-configuration)
- Transit (PT settings) - [Config §Transit](08-configuration/configuration-reference.md#transit-module)
- QSim (simulation) - [Config §QSim](08-configuration/configuration-reference.md#qsim-queue-simulation)

## 🚨 Most Common Issues

1. **PT agents teleport directly** → [Troubleshooting: PT Direct Transmission](10-troubleshooting/troubleshooting.md#pt-agents-using-direct-transmission)
2. **ClassCastException route** → [Troubleshooting: ClassCastException](10-troubleshooting/troubleshooting.md#classcastexception-transitpassengerroute--networkroute)
3. **Network not connected** → [Troubleshooting: Network Warnings](10-troubleshooting/troubleshooting.md#network-not-connected-warnings)
4. **Too many artificial links** → [PT Guide: Mapping Issues](03-public-transit/public-transit-guide.md#issue-too-many-artificial-links)

## 📋 Essential Checklists

### Before Running PT Simulation

From [PT Guide](03-public-transit/public-transit-guide.md#configuration-checklist):

- [ ] `transit.useTransit = true`
- [ ] PT **NOT** in `routing.networkModes`
- [ ] PT **NOT** in `teleportedModeParameters`
- [ ] Multimodal network exists
- [ ] `transitSchedule.xml` and `transitVehicles.xml` present

### Before Modifying Config

From [Configuration](08-configuration/configuration-reference.md#critical-parameters-checklist):

- [ ] Check `defaultConfig.xml` for parameter reference
- [ ] Set `controller.lastIteration` appropriately
- [ ] Set `global.coordinateSystem` correctly
- [ ] Verify all file paths exist
- [ ] Test with small population first

## 🔍 Search Tips

### Finding Config Parameters

1. Search `defaultConfig.xml` for parameter name
2. Check line number in comments
3. See [Configuration Reference](08-configuration/configuration-reference.md) for explanation

Example:
```bash
# Find lastIteration in defaultConfig.xml
grep -n "lastIteration" ../defaultConfig.xml
# Result: line 31
```

### Finding Solutions

1. Check error message
2. Search [Troubleshooting](10-troubleshooting/troubleshooting.md) for keyword
3. Check relevant guide (PT → [PT Guide](03-public-transit/public-transit-guide.md))

## 📦 Additional Resources

- **README**: [`../README.md`](../README.md) - Project overview
- **SSoT**: [`../PROJECT_WIKI.md`](../PROJECT_WIKI.md) - Canonical project map + disaster workflow
- **CLAUDE.md**: [`../CLAUDE.md`](../CLAUDE.md) - AI assistant guidance
- **Changelog**: [`../CHANGELOG.md`](../CHANGELOG.md) - Complete project history
- **Disaster network build**: `../5000_disatar/00_docs/NETWORK_README.md`
- **Disaster simulation workflow**: `../5000_disatar/05_combined_evac/WORKFLOW.md`
- **Examples**: `../scenarios/corridor/taipei_test/` - Test scenarios
- **Archive**: [`../archive/`](../archive/) - Historical documentation and summaries

## 🌐 External Resources

- **MATSim Documentation**: https://matsim.org/docs
- **MATSim Mailing List**: matsim@googlegroups.com
- **pt2matsim GitHub**: https://github.com/matsim-org/pt2matsim

---

**Last Updated**: 2025-12-23 | **Documentation Version**: 3.0
