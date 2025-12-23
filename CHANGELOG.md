# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Documentation
- Consolidated duplicate documentation files into organized structure
- Created comprehensive [Simulation Guide](docs/05-simulation/simulation-guide.md) from 4 separate guides
- Created comprehensive [Via Export Guide](docs/05-simulation/via-export.md) from 2 separate guides
- Moved specialized guides to `docs/` directory for better organization
- Archived historical summaries to `archive/summaries/`

---

## [2025-11-17] - Documentation Consolidation

### Added
- `docs/05-simulation/simulation-guide.md` - Comprehensive guide for running MATSim simulations (46 & 100 agents)
- `docs/05-simulation/via-export.md` - Complete Via platform export pipeline guide
- `docs/04-population/agent-generation.md` - Agent population generation guide (moved from root)
- `docs/05-simulation/early-stop-strategy.md` - Early stopping implementation (moved from root)
- `docs/07-analysis/output-analysis.md` - Simulation output analysis guide (moved from root)
- `docs/04-population/agent-journey-guide.md` - Agent journey building guide (moved from archive)
- `CHANGELOG.md` - This file

### Changed
- Reorganized documentation into logical structure under `docs/`
- Archived historical summaries to `archive/summaries/`

### Removed
- `SIMULATION_GUIDE_V2.md` - Content merged into `docs/05-simulation/simulation-guide.md`
- `SIMULATION_GUIDE_IMPROVED_POPULATION.md` - Content merged into `docs/05-simulation/simulation-guide.md`
- `RUN_100_AGENTS_SIMULATION.md` - Content merged into `docs/05-simulation/simulation-guide.md`
- `SIMULATION_SUMMARY.md` - Content merged into `docs/05-simulation/simulation-guide.md`
- `VIA_EXPORT_SETUP.md` - Content merged into `docs/05-simulation/via-export.md`
- `VIA_EXPORT_WORKFLOW.md` - Content merged into `docs/05-simulation/via-export.md`

---

## Historical Summaries (Archived)

For historical implementation summaries and weekly reports, see:
- [Implementation Summary](archive/summaries/IMPLEMENTATION_SUMMARY.md)
- [Weekly Execution Summary](archive/summaries/WEEKLY_EXECUTION_SUMMARY.md)
- [Work Completion Summary](archive/summaries/WORK_COMPLETION_SUMMARY.md)

---

## [2025-11-12] - 100 Agents Population

### Added
- 100-agent population with 30 transfer agents
- PT-only agents (no car availability) for transfer testing
- Generation script: `src/main/python/generate_test_population_100.py`

### Features
- 20 single-line PT agents
- 30 transfer PT agents (BL↔G, G↔R, O↔R, etc.)
- 40 car agents
- 10 walk agents
- All agents PT-only with proper SwissRailRaptor configuration

---

## [2025-11-05] - Via Export Enhancement

### Added
- Dual-filtering system for agent and vehicle events
- Time-range filtering for precise vehicle trajectory capture
- Checkpoint mechanism for progress reporting
- Enhanced compression (99.6% event reduction)

### Changed
- Via export now includes real-time vehicle movement
- Separate `forVia/` directory to prevent MATSim GUI overwriting
- Updated export pipeline documentation

---

## [2025-11-05] - Improved Population (46 Agents)

### Added
- 46-agent improved population with realistic behavior
- PT transfer agents (6 agents with multi-line routes)
- Car distance constraints (minimum 1km trips)
- Mode consistency validation

### Fixed
- Car agents trapped outside network bounds
- Ultra-long PT routes (40+ hours)
- Agents not using proper modes
- Missing PT transfer routes

### Features
- 20 single-line PT agents
- 6 transfer PT agents
- 15 car agents (OSM boundary constrained)
- 5 walk agents

---

## Project Structure

```
matsim-example-project/
├── docs/                       # Consolidated documentation
│   ├── README.md              # Documentation index
│   ├── 01-getting-started/quick-start.md
│   ├── 02-architecture/architecture-overview.md
│   ├── 03-public-transit/public-transit-guide.md
│   ├── 04-population/agent-development.md
│   ├── 05-simulation/simulation-guide.md
│   ├── 06-disaster-evacuation/evacuation-guide.md
│   ├── 07-analysis/output-analysis.md
│   ├── 08-configuration/configuration-reference.md
│   ├── 09-operations/remote-server-setup.md
│   ├── 10-troubleshooting/troubleshooting.md
│   ├── 11-modes/motorcycle/motorcycle-quick-start.md
│   └── 12-notes/matsim-pipeline-complete-guide.md
│
├── archive/
│   ├── summaries/             # Historical summaries
│   │   ├── IMPLEMENTATION_SUMMARY.md
│   │   ├── WEEKLY_EXECUTION_SUMMARY.md
│   │   └── WORK_COMPLETION_SUMMARY.md
│   └── working_journal/       # Dated development notes
│
├── README.md                  # Project overview
├── CLAUDE.md                  # AI assistant guidance
└── CHANGELOG.md               # This file
```

---

## Links

- **Documentation Index**: [docs/README.md](docs/README.md)
- **Quick Start**: [docs/01-getting-started/quick-start.md](docs/01-getting-started/quick-start.md)
- **Simulation Guide**: [docs/05-simulation/simulation-guide.md](docs/05-simulation/simulation-guide.md)
- **Via Export Guide**: [docs/05-simulation/via-export.md](docs/05-simulation/via-export.md)
- **Troubleshooting**: [docs/10-troubleshooting/troubleshooting.md](docs/10-troubleshooting/troubleshooting.md)

---

**Maintained by**: MATSim Example Project Team
**Last Updated**: 2025-11-17
