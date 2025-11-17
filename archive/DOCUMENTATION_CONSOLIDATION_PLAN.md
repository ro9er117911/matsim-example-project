# Documentation Consolidation Plan

**Created**: 2025-11-17
**Status**: Analysis Complete, Ready for Execution

## Overview

This document outlines the plan to consolidate and streamline all `.md` files in the project to reduce redundancy and improve organization.

## Current State Analysis

### Root Directory Files (15 files, ~141KB total)

#### Simulation Guides (Duplicative - 4 files)
1. **SIMULATION_GUIDE_V2.md** (14K) - Version 2 with 46 agents
2. **SIMULATION_GUIDE_IMPROVED_POPULATION.md** (15K) - 50 agents guide
3. **RUN_100_AGENTS_SIMULATION.md** (7.2K) - 100 agents guide
4. **SIMULATION_SUMMARY.md** (6.5K) - General summary

**Issue**: Overlapping content, multiple versions of similar information
**Recommendation**: Consolidate into single `docs/simulation-guide.md` with sections for different population sizes

#### Via Export Guides (Duplicative - 2 files)
1. **VIA_EXPORT_SETUP.md** (6.0K) - Setup instructions
2. **VIA_EXPORT_WORKFLOW.md** (9.2K) - Workflow details

**Issue**: Split content that should be unified
**Recommendation**: Merge into single `docs/via-export.md`

#### Implementation Summaries (Potentially Redundant - 3 files)
1. **IMPLEMENTATION_SUMMARY.md** (11K)
2. **WEEKLY_EXECUTION_SUMMARY.md** (7.9K)
3. **WORK_COMPLETION_SUMMARY.md** (11K)

**Issue**: Historical summaries that may be outdated
**Recommendation**: Move to `archive/summaries/` and create single `CHANGELOG.md` reference

#### Specialized Guides (Keep - 3 files)
1. **AGENT_GENERATION_README.md** (7.9K) - Agent generation specifics
2. **EARLY_STOP_STRATEGY.md** (6.9K) - Early stopping implementation
3. **SIMULATION_OUTPUT_GUIDE.md** (21K) - Output analysis

**Recommendation**: Move to `docs/` with clearer names:
- `docs/agent-generation.md`
- `docs/early-stop-strategy.md`
- `docs/output-analysis.md`

#### Core Documentation (Keep - 2 files)
1. **README.md** (4.5K) - Project entry point ✅
2. **CLAUDE.md** (31K) - AI assistant guidance ✅

**Recommendation**: Keep at root, update README to point to consolidated docs

#### Algorithmic Notes (Unclear - 1 file)
1. **algo.md** (6.1K)

**Recommendation**: Review and either move to `docs/algorithms.md` or archive

### docs/ Directory (Well-Organized - 7 files)

**Current Structure** ✅ Good:
1. `1-quick-start.md`
2. `2-architecture.md`
3. `3-public-transit.md`
4. `4-agent-development.md`
5. `5-configuration.md`
6. `6-troubleshooting.md`
7. `README.md` (index)

**Recommendation**: Keep structure, add consolidated guides

### Working Journal (archive/working_journal/ - 24+ files)

**Issue**: Mix of dated entries and timeless guides
**Recommendation**:
- Keep dated entries (2025-11-*.md) in `archive/working_journal/`
- Move timeless guides to `docs/`:
  - `Agent-Journey-Building-Guide.md` → `docs/agent-journey-guide.md`
  - `population_explain.md` → merge into `docs/4-agent-development.md`
  - `Via-Export-Quick-Start.md` → merge into consolidated Via guide

## Proposed New Structure

```
matsim-example-project/
├── README.md                    # Project overview (updated)
├── CLAUDE.md                    # AI assistant guide (keep)
├── CHANGELOG.md                 # NEW: Consolidated changelog
│
├── docs/
│   ├── README.md               # Documentation index
│   ├── 1-quick-start.md        # Existing
│   ├── 2-architecture.md       # Existing
│   ├── 3-public-transit.md     # Existing
│   ├── 4-agent-development.md  # Existing (expand)
│   ├── 5-configuration.md      # Existing
│   ├── 6-troubleshooting.md    # Existing
│   ├── simulation-guide.md     # NEW: Consolidated simulation guide
│   ├── via-export.md           # NEW: Consolidated Via guide
│   ├── agent-generation.md     # Moved from root
│   ├── output-analysis.md      # Moved from root
│   ├── early-stop-strategy.md  # Moved from root
│   └── agent-journey-guide.md  # Moved from archive
│
├── archive/
│   ├── summaries/              # NEW: Historical summaries
│   │   ├── implementation-summary.md
│   │   ├── weekly-execution-summary.md
│   │   └── work-completion-summary.md
│   └── working_journal/        # Existing (dated entries)
│       └── ...
│
└── .claude/
    └── commands/
        └── agent.md            # Recently added
```

## Consolidation Tasks

### Phase 1: Merge Duplicate Content
- [ ] Create `docs/simulation-guide.md` from 4 simulation guides
- [ ] Create `docs/via-export.md` from 2 Via guides
- [ ] Review and merge population explanation into `docs/4-agent-development.md`

### Phase 2: Relocate Files
- [ ] Move AGENT_GENERATION_README.md → docs/agent-generation.md
- [ ] Move EARLY_STOP_STRATEGY.md → docs/early-stop-strategy.md
- [ ] Move SIMULATION_OUTPUT_GUIDE.md → docs/output-analysis.md
- [ ] Move Agent-Journey-Building-Guide.md → docs/agent-journey-guide.md

### Phase 3: Archive Historical Content
- [ ] Move summaries to archive/summaries/
- [ ] Create CHANGELOG.md with references to archived summaries

### Phase 4: Update References
- [ ] Update README.md to point to new locations
- [ ] Update docs/README.md index
- [ ] Update CLAUDE.md with new file references
- [ ] Check for broken links in all docs

### Phase 5: Cleanup
- [ ] Delete redundant root-level files
- [ ] Verify all git references
- [ ] Update .gitignore if needed

## Files to Delete After Consolidation

Root level (after content is merged):
- SIMULATION_GUIDE_V2.md
- SIMULATION_GUIDE_IMPROVED_POPULATION.md
- RUN_100_AGENTS_SIMULATION.md
- SIMULATION_SUMMARY.md
- VIA_EXPORT_SETUP.md
- VIA_EXPORT_WORKFLOW.md
- IMPLEMENTATION_SUMMARY.md (after archiving)
- WEEKLY_EXECUTION_SUMMARY.md (after archiving)
- WORK_COMPLETION_SUMMARY.md (after archiving)

## Benefits

1. **Single Source of Truth**: No duplicate information
2. **Clear Organization**: All docs in `docs/` directory
3. **Easier Maintenance**: Update one file instead of multiple
4. **Better Discoverability**: Logical structure in docs/
5. **Clean Root**: Only essential files (README, CLAUDE.md, CHANGELOG.md)

## Next Steps

1. Get approval for this plan
2. Execute Phase 1 (merge duplicates)
3. Execute Phase 2 (relocate)
4. Execute Phase 3 (archive)
5. Execute Phase 4 (update references)
6. Execute Phase 5 (cleanup)
7. Verify and commit changes

## Rollback Plan

All changes will be in a dedicated branch. If issues arise:
1. Review git diff
2. Restore specific files if needed
3. Merge only approved changes

---

**Note**: This is a non-breaking change. All content will be preserved, just reorganized for better structure.
