# Archive

This directory contains archived documentation and working logs that have been superseded by the new documentation structure.

## Migration Guide

Old documentation has been **reorganized and improved** in the new `docs/` directory.

### Old → New Mapping

| Old Location | New Location | Notes |
|-------------|--------------|-------|
| `AGENT.md` | `docs/4-agent-development.md` | Simplified and updated |
| `PT_ERROR_HANDLING.md` | `docs/3-public-transit.md` + `docs/6-troubleshooting.md` | Merged and expanded |
| `PT_SETUP_REPORT.md` | `docs/3-public-transit.md` | Complete PT guide |
| `REFACTORING_SUMMARY.md` | `changelog/2025-11.md` | Now in changelog |
| `working_journal/*.md` | `archive/working_journal/` | Historical logs |

## What's Archived

### `/archive/old_docs/`

Original root-level documentation files:
- `AGENT.md` - Original agent guide (superseded by `docs/4-agent-development.md`)
- `PT_ERROR_HANDLING.md` - PT error handling (merged into `docs/3-public-transit.md`)
- `PT_SETUP_REPORT.md` - PT setup report (merged into `docs/3-public-transit.md`)
- `REFACTORING_SUMMARY.md` - Refactoring notes (moved to `changelog/2025-11.md`)

### `/archive/working_journal/`

Daily work logs and development journals:
- `2025-10-29.md` - Initial PT setup
- `2025-11-03-*.md` - PT fixes and documentation updates
- `2025-11-04-*.md` - Vehicle filtering and multimodal success
- `Agent-Journey-Building-Guide.md` - Agent building guide
- `population_explain.md` - Population explanation
- `agent-work-logs/` - Detailed agent work logs by role

## Current Documentation

**For current information**, see:

📚 **Main Documentation**: [`docs/`](../docs/)
1. Quick Start Guide
2. Architecture Overview
3. Public Transit Guide
4. Agent Development
5. Configuration Reference
6. Troubleshooting

📝 **Project Overview**: [`README.md`](../README.md)

🤖 **AI Guidance**: [`CLAUDE.md`](../CLAUDE.md)

📅 **Recent Changes**: [`changelog/2025-11.md`](../changelog/2025-11.md)

## Why Archive?

The original documentation structure had several issues:
- **Too many files** (28 MD files)
- **Overlapping content** (PT errors covered in multiple places)
- **Unclear hierarchy** (no obvious order)
- **Verbose** (CLAUDE.md was 19K)

The new structure is:
- **Hierarchical** (numbered docs in order)
- **Comprehensive** (complete guides in one place)
- **Concise** (focused on essentials)
- **Maintainable** (clear separation of concerns)

## Accessing Archived Content

Files in this directory are retained for historical reference only. **Do not use these for current development**.

If you need information from archived docs, check the new documentation first - it's more up-to-date and complete.

---

**Documentation Reorganization Date**: 2025-11-05
