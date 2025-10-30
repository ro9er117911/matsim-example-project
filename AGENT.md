# MATSim Example Project – Agent Guide

## Project Snapshot
- Java 21 project built with Maven; main entry points sit in `src/main/java/org/matsim/project`, with helpers under `src/main/java/org/matsim/project/tools`.
- Tests live in `src/test/java/org/matsim/project`, driven by JUnit 5 (JUnit Jupiter).
- The shaded executable appears as `matsim-example-project-0.0.1-SNAPSHOT.jar` at the repo root after packaging.
- A pre-bundled `pt2matsim` toolchain is vendored under `pt2matsim/work/pt2matsim-25.8-shaded.jar` and referenced via a `system`-scoped dependency in `pom.xml`.

## Build & Test
- `./mvnw clean package` builds the shaded jar and resolves dependencies.
- `./mvnw test` executes the unit and integration tests (JUnit 5).
- `java -jar matsim-example-project-0.0.1-SNAPSHOT.jar` launches the MATSim GUI once a build is complete.

## Big Data Safety
- Treat MATSim scenario data as huge: **do not open, expand, or stream large `.xml`, `.xml.gz`, `.osm`, `.pbf`, or GTFS assets without an explicit request**.
- High-risk directories include `pt2matsim/`, `scenarios/`, `original-input-data/`, and `output/`. Prefer metadata (e.g., filenames, sizes) or user-provided excerpts over file contents.
- If inspection is ever unavoidable, confirm with the user and use targeted commands (`rg`, `zcat | head`, etc.) to avoid reading entire files.

## Workflow Notes
- Favor `rg` for searches and `apply_patch` for focused edits; leave existing user modifications untouched.
- The project already depends on many MATSim contrib modules—remove or adjust them only when requested.
- Remember that MATSim simulations can generate massive outputs; coordinate with the user before running long simulations or producing new datasets.

## When In Doubt
- Ask before interacting with heavy data sources or changing scenario inputs.
- Surface any uncertainties about MATSim configuration, external data licensing, or toolchain versions so the user can advise.
