# MATSim Skills Library

This directory contains Claude Code skills for common MATSim workflows. Each skill provides step-by-step guidance, troubleshooting, and validation for specific tasks.

## Available Skills

### 1. SwissRailRaptor Configuration & Troubleshooting
**Directory**: `1-swissrailraptor/`

Configures SwissRailRaptor routing algorithm for PT simulations and troubleshoots common PT routing issues.

**Use when**:
- PT agents not boarding vehicles
- No transfers happening
- Agents using direct transmission instead of PT

**Files**:
- `SKILL.md` - Main workflow with diagnostics and fixes
- `reference.md` - Parameter documentation and integration guide
- `examples.md` - Configuration examples for different scenarios

---

### 2. PT Network Mapping with pt2matsim
**Directory**: `2-pt-mapping/`

Maps transit schedules onto road networks using pt2matsim library, with parameter tuning for different network types.

**Use when**:
- Mapping transit schedule to network
- PT mapping is stuck or slow
- Too many artificial links created

**Files**:
- `SKILL.md` - Step-by-step mapping workflow
- `reference.md` - Complete parameter reference with presets
- `examples.md` - Real-world mapping scenarios (metro, bus, hybrid)

---

### 3. Network Validation & Troubleshooting
**Directory**: `3-network-validation/`

Validates MATSim networks, diagnoses common issues, and prepares networks for PT mapping.

**Use when**:
- "Network is not connected" warnings
- Link validation errors
- Preparing network for PT

**Files**:
- `SKILL.md` - Validation workflow and common fixes

---

### 4. MATSim Simulation Execution
**Directory**: `4-simulation/`

Configures and runs MATSim simulations with proper parameters.

**Use when**:
- Running simulations
- Configuring simulation parameters
- Troubleshooting convergence issues

**Files**:
- `SKILL.md` - Execution workflow and configuration patterns

---

### 5. GTFS to MATSim Conversion
**Directory**: `5-gtfs-conversion/`

Converts GTFS transit data to MATSim format.

**Use when**:
- Converting GTFS feeds
- Importing transit schedules
- Setting up PT from GTFS

**Files**:
- `SKILL.md` - Full GTFS conversion pipeline

---

### 6. Via Platform Export Generation
**Directory**: `6-via-export/`

Exports MATSim results for Via platform visualization with optimized file sizes.

**Use when**:
- Exporting for Via platform
- Creating filtered visualization data

**Files**:
- `SKILL.md` - Export workflow with filtering options

---

## Shared References

The `_shared/` directory contains reusable references used across multiple skills:

### validation-commands.md
Quick lookup for common validation patterns:
- Network inspection (nodes, links, bounds, modes)
- PT boarding validation (PersonEntersVehicle events)
- Transfer station validation (stopAreaId checks)
- PT mapping validation (artificial link percentage)
- Population link validation

### common-configs.md
Reusable configuration templates:
- SwissRailRaptor simple PT-only configuration
- SwissRailRaptor multimodal configuration
- PT Mapping artificial mode preset
- PT Mapping metro/bus presets
- Testing configuration template

### troubleshooting-matrix.md
Consolidated troubleshooting across all skills:
- Issue symptoms → diagnosis → fixes
- Cross-skill issue tracking
- Decision trees for complex problems
- Common root causes (missing ground network, CRS mismatch, etc.)

### prerequisite-checks.md
Pre-run validation scripts:
- File existence validation
- Configuration validation (XML syntax, referenced files)
- GTFS validation
- Population link validation
- CRS consistency checks
- Complete pre-simulation checklist script

**Use shared references for**: Quick lookups, copy-paste commands, troubleshooting across skills

---

## Skill Usage

Claude Code will automatically activate the appropriate skill when you mention trigger phrases. Each skill provides:

1. **Trigger conditions** - When Claude should activate this skill
2. **Required inputs** - What files/data are needed
3. **Step-by-step workflow** - Detailed execution steps
4. **Validation commands** - How to verify success (see `_shared/validation-commands.md` for full reference)
5. **Troubleshooting** - Common issues and fixes (see `_shared/troubleshooting-matrix.md` for complete matrix)
6. **File references** - Links to relevant project files

## Typical Workflow Chains

### New PT Project Setup
1. **GTFS Conversion** (skill 5) → Convert transit data
2. **PT Mapping** (skill 2) → Map schedule to network
3. **Network Validation** (skill 3) → Validate result
4. **SwissRailRaptor Config** (skill 1) → Configure routing
5. **Simulation** (skill 4) → Run simulation
6. **Via Export** (skill 6) → Visualize results

### Troubleshooting PT Issues
1. **SwissRailRaptor** (skill 1) → Check routing configuration
2. **Network Validation** (skill 3) → Verify network integrity
3. **Simulation** (skill 4) → Re-run with fixes

### Quick Testing Cycle
1. **PT Mapping** (skill 2 - artificial mode) → Fast mapping
2. **Simulation** (skill 4 - 10 iterations) → Quick test
3. **Via Export** (skill 6) → Check results

## Skill Priority (by error-proneness)

1. **SwissRailRaptor** - Most critical, most error-prone
2. **PT Mapping** - Complex, can hang for hours
3. **Network Validation** - Prerequisite for other workflows
4. **Simulation** - Frequently used, many parameters
5. **GTFS Conversion** - Entry point for PT workflows
6. **Via Export** - Least error-prone, well-documented

## Skill Architecture

### Individual Skills (Workflow-Focused)
Each skill provides a **complete, self-contained workflow** for a specific task:
- Step-by-step execution instructions
- Context-specific validation commands
- Inline troubleshooting for skill-specific issues
- Real-world examples with narrative

**Design principle**: Users can follow a single SKILL.md from start to finish without jumping between files.

### Shared References (Lookup-Focused)
The `_shared/` directory provides **quick reference lookups** for cross-cutting patterns:
- Copy-paste validation commands
- Reusable configuration templates
- Comprehensive troubleshooting matrix
- Pre-run validation scripts

**Design principle**: Single source of truth for commands used across multiple skills.

### When to Use What

**Use Individual Skills when**:
- Following a complete workflow (GTFS → mapping → simulation)
- Learning a new MATSim task
- Troubleshooting a skill-specific issue

**Use Shared References when**:
- Need a specific validation command quickly
- Looking up configuration template
- Diagnosing issues across multiple skills
- Running pre-flight checks

## Skill Development Notes

Skills were created based on analysis of:
- `CLAUDE.md` - Project documentation and best practices
- `working_journal/` - Debugging sessions and lessons learned
- `docs/` - Official documentation
- Real usage patterns in the matsim-example-project

Each skill includes:
- Concrete commands (no placeholders)
- Real file paths from this project
- Validation steps with expected outputs
- Common error scenarios with fixes
- Links to relevant working journals and `_shared/` references

## Contributing

When adding new skills:
1. Follow the SKILL.md template structure
2. Include trigger conditions at the top
3. Provide step-by-step workflows
4. Add validation commands with expected outputs
5. Document common pitfalls
6. Reference actual files in the project

## File References

- Main documentation: `/Users/ro9air/matsim-example-project/CLAUDE.md`
- Working journals: `/Users/ro9air/matsim-example-project/working_journal/`
- Tools: `/Users/ro9air/matsim-example-project/src/main/java/org/matsim/project/tools/`
- Configs: `/Users/ro9air/matsim-example-project/scenarios/`
