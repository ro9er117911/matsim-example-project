# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Documentation
- Consolidated duplicate documentation files into organized structure
- Created comprehensive [Simulation Guide](docs/simulation-guide.md) from 4 separate guides
- Created comprehensive [Via Export Guide](docs/via-export.md) from 2 separate guides
- Moved specialized guides to `docs/` directory for better organization
- Archived historical summaries to `archive/summaries/`

---

## [2025-11-17] - Documentation Consolidation

### Added
- `docs/simulation-guide.md` - Comprehensive guide for running MATSim simulations (46 & 100 agents)
- `docs/via-export.md` - Complete Via platform export pipeline guide
- `docs/agent-generation.md` - Agent population generation guide (moved from root)
- `docs/early-stop-strategy.md` - Early stopping implementation (moved from root)
- `docs/output-analysis.md` - Simulation output analysis guide (moved from root)
- `docs/agent-journey-guide.md` - Agent journey building guide (moved from archive)
- `CHANGELOG.md` - This file

### Changed
- Reorganized documentation into logical structure under `docs/`
- Archived historical summaries to `archive/summaries/`

### Removed
- `SIMULATION_GUIDE_V2.md` - Content merged into `docs/simulation-guide.md`
- `SIMULATION_GUIDE_IMPROVED_POPULATION.md` - Content merged into `docs/simulation-guide.md`
- `RUN_100_AGENTS_SIMULATION.md` - Content merged into `docs/simulation-guide.md`
- `SIMULATION_SUMMARY.md` - Content merged into `docs/simulation-guide.md`
- `VIA_EXPORT_SETUP.md` - Content merged into `docs/via-export.md`
- `VIA_EXPORT_WORKFLOW.md` - Content merged into `docs/via-export.md`

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
│   ├── 1-quick-start.md
│   ├── 2-architecture.md
│   ├── 3-public-transit.md
│   ├── 4-agent-development.md
│   ├── 5-configuration.md
│   ├── 6-troubleshooting.md
│   ├── simulation-guide.md    # NEW: Consolidated simulation guide
│   ├── via-export.md          # NEW: Consolidated Via export guide
│   ├── agent-generation.md    # MOVED from root
│   ├── early-stop-strategy.md # MOVED from root
│   ├── output-analysis.md     # MOVED from root
│   └── agent-journey-guide.md # MOVED from archive
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
- **Quick Start**: [docs/1-quick-start.md](docs/1-quick-start.md)
- **Simulation Guide**: [docs/simulation-guide.md](docs/simulation-guide.md)
- **Via Export Guide**: [docs/via-export.md](docs/via-export.md)
- **Troubleshooting**: [docs/6-troubleshooting.md](docs/6-troubleshooting.md)

---

**Maintained by**: MATSim Example Project Team
**Last Updated**: 2025-11-17
