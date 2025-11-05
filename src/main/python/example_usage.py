#!/usr/bin/env python
"""
Example usage of the refactored build_agent_tracks module.

This script shows different ways to use the build_agent_tracks package:
1. Simple CLI usage
2. Programmatic usage with custom options
3. Activity-aware analysis
"""

import sys
from pathlib import Path

# Example 1: Simple programmatic usage
print("=" * 70)
print("Example 1: Simple Programmatic Usage")
print("=" * 70)

# You can import individual functions
from build_agent_tracks.parsers import parse_population_or_plans
from build_agent_tracks.legs_builder import build_legs_table
from build_agent_tracks.tracks_builder import build_tracks_from_legs
from build_agent_tracks.activity_matcher import (
    extract_activities_by_person,
    match_activity_to_tracks,
)

code_example_1 = '''
# Parse population file
plans = parse_population_or_plans("scenarios/equil/forVia/plans.xml.gz")
print(f"Loaded {len(plans)} agents")

# Build legs table
legs_df = build_legs_table(plans)
print(f"Created {len(legs_df)} leg entries")

# Build time-sampled tracks
tracks_df = build_tracks_from_legs(legs_df, dt=5)
print(f"Generated {len(tracks_df)} track points")

# Add activity information
activities = extract_activities_by_person(plans)
tracks_df = match_activity_to_tracks(tracks_df, activities)
print(f"Matched activities for {len(activities)} agents")

# Save to CSV
tracks_df.to_csv("output/tracks_with_activities.csv", index=False)
'''

print(code_example_1)

# Example 2: Using the full pipeline
print("\n" + "=" * 70)
print("Example 2: Full Pipeline with run_pipeline()")
print("=" * 70)

code_example_2 = '''
from build_agent_tracks.main import run_pipeline

# Run the complete pipeline
outputs = run_pipeline(
    plans_path="output/plans.xml.gz",
    population_fallback="population.xml.gz",
    events_path="output/events.xml.gz",
    outdir="analysis/",
    dt=5,  # 5-second sampling
    schedule_path="transitSchedule.xml",
    add_activity_matching=True,
)

print("Output files:")
for key, path in outputs.items():
    print(f"  {key}: {path}")
'''

print(code_example_2)

# Example 3: Activity-aware analysis
print("\n" + "=" * 70)
print("Example 3: Activity-Aware Analysis")
print("=" * 70)

code_example_3 = '''
import pandas as pd

# Read the generated tracks
tracks = pd.read_csv("analysis/tracks_dt5s.csv")

# 1. Time spent in each activity
activity_time = tracks.groupby(["person_id", "activity_type"]).agg({
    "time_s": "count",  # Number of track points (proportional to time)
}).rename(columns={"time_s": "minutes"})

print("Time spent in each activity (in 5-second intervals):")
print(activity_time)

# 2. Mode usage per activity
mode_per_activity = tracks.groupby(
    ["activity_type", "mode"]
).size().reset_index(name="points")

print("\\nMode usage by activity type:")
print(mode_per_activity.pivot_table(
    index="activity_type",
    columns="mode",
    values="points",
    fill_value=0
))

# 3. Activity transition analysis
for person_id in tracks["person_id"].unique()[:3]:
    person_tracks = tracks[tracks["person_id"] == person_id]
    activities = person_tracks.drop_duplicates("activity_sequence")[[
        "activity_sequence", "activity_type"
    ]].sort_values("activity_sequence")

    print(f"\\nActivity sequence for {person_id}:")
    for seq, act_type in zip(activities["activity_sequence"],
                             activities["activity_type"]):
        print(f"  [{seq}] {act_type}")
'''

print(code_example_3)

# Example 4: CLI usage
print("\n" + "=" * 70)
print("Example 4: Command-Line Usage")
print("=" * 70)

cli_examples = '''
# Basic usage
python build_agent_tracks.py \\
  --plans output/plans.xml.gz \\
  --out analysis/

# With transit schedule enrichment
python build_agent_tracks.py \\
  --plans output/plans.xml.gz \\
  --schedule transitSchedule.xml \\
  --out analysis/

# Complete pipeline with all options
python build_agent_tracks.py \\
  --plans output/plans.xml.gz \\
  --population population.xml.gz \\
  --schedule transitSchedule.xml \\
  --events output/events.xml.gz \\
  --out analysis/ \\
  --dt 5 \\
  --include-mode walk \\
  --include-mode pt \\
  --include-mode subway

# Skip activity matching for faster processing
python build_agent_tracks.py \\
  --plans output/plans.xml.gz \\
  --out analysis/ \\
  --skip-activity-matching

# Custom modes and sampling interval
python build_agent_tracks.py \\
  --plans output/plans.xml.gz \\
  --out analysis/ \\
  --dt 10 \\
  --include-mode walk \\
  --include-mode pt
'''

print(cli_examples)

# Example 5: Batch processing
print("\n" + "=" * 70)
print("Example 5: Batch Processing Multiple Scenarios")
print("=" * 70)

batch_example = '''
from pathlib import Path
from build_agent_tracks.main import run_pipeline

# Process multiple scenario outputs
scenarios = [
    "scenarios/equil/forVia",  # Via export folder (isolated from MATSim GUI output)
    "scenarios/taipei/forVia",
    "scenarios/test/forVia",
]

for scenario_dir in scenarios:
    plans_path = f"{scenario_dir}/plans.xml.gz"
    schedule_path = f"{scenario_dir}/../transitSchedule.xml"
    outdir = f"analysis/{Path(scenario_dir).parent.name}"

    if Path(plans_path).exists():
        print(f"Processing {scenario_dir}...")
        outputs = run_pipeline(
            plans_path=plans_path,
            schedule_path=schedule_path,
            outdir=outdir,
        )
        print(f"  ✓ Generated {len(outputs)} outputs")
'''

print(batch_example)

# Example 6: Custom modifications
print("\n" + "=" * 70)
print("Example 6: Custom Pipeline Modifications")
print("=" * 70)

custom_example = '''
from build_agent_tracks.parsers import parse_population_or_plans
from build_agent_tracks.legs_builder import build_legs_table
from build_agent_tracks.tracks_builder import build_tracks_from_legs
from build_agent_tracks.activity_matcher import (
    extract_activities_by_person,
    match_activity_to_tracks,
    add_activity_summaries,
)
import pandas as pd

# Parse and process
plans = parse_population_or_plans("plans.xml.gz")
legs_df = build_legs_table(plans)
tracks_df = build_tracks_from_legs(legs_df, dt=10)  # 10-second sampling

# Add activity information
activities = extract_activities_by_person(plans)
tracks_df = match_activity_to_tracks(tracks_df, activities)
tracks_df = add_activity_summaries(tracks_df)

# Custom filtering: only work activities
work_tracks = tracks_df[tracks_df["activity_type"] == "work"]

# Custom filtering: only PT modes
pt_work_tracks = work_tracks[work_tracks["mode"].isin(["pt", "subway", "bus"])]

# Analyze
print(f"PT track points from work: {len(pt_work_tracks)}")
print(f"Unique agents: {pt_work_tracks['person_id'].nunique()}")

# Save custom result
pt_work_tracks.to_csv("analysis/pt_from_work.csv", index=False)
'''

print(custom_example)

print("\n" + "=" * 70)
print("For more details, see:")
print("  - build_agent_tracks/README.md")
print("  - REFACTORING_SUMMARY.md")
print("=" * 70)
