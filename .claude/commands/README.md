# Claude Code Slash Commands

This directory contains custom slash commands for Claude Code to assist with MATSim development.

## Available Commands

### `/agent` - MATSim Journey Planning Assistant

Specialized assistant for creating and managing MATSim agent travel plans.

**Capabilities**:
- Create valid agent journeys (home → work → home)
- Validate population.xml structure
- Troubleshoot routing mode errors
- Design multi-modal trips (car, PT, walk)
- Apply time constraints (23:00 limit)
- Query network links and coordinates

**When to Use**:
- Creating new agents in population.xml
- Fixing validation errors in agent plans
- Understanding PT journey structure
- Finding valid link IDs and coordinates
- Applying routingMode correctly

**Usage**:
```
/agent
```

Then ask questions like:
- "Create a PT agent from BL02 to BL14"
- "Why is my agent journey validation failing?"
- "Find coordinates for station BL05"
- "Add routingMode to all legs in population.xml"

**Knowledge Base**:
- CLAUDE.md (project architecture)
- Agent-Journey-Building-Guide.md (journey planning)
- 2025-11-12-Activity-Time-Constraint.md (time limits)
- All MATSim skills (SwissRailRaptor, PT mapping, etc.)

---

## How Slash Commands Work

1. Type `/agent` in Claude Code
2. The agent prompt expands with specialized knowledge
3. Ask your MATSim agent-related question
4. The assistant applies project-specific expertise

## Adding New Commands

Create a new `.md` file in this directory:
```bash
.claude/commands/your-command.md
```

The file content becomes the prompt when `/your-command` is invoked.
