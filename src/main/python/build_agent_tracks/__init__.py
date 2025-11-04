"""
Build agent tracks: Extract MATSim agent legs and build time-sampled tracks.

Main API:
  - run_pipeline(): Orchestrate the entire pipeline
  - parse_population_or_plans(): Parse MATSim XML
  - build_legs_table(): Create detailed legs DataFrame
  - build_tracks_from_legs(): Generate time-sampled points
  - match_activity_to_tracks(): Add activity information to tracks

Example usage:
  from build_agent_tracks.main import run_pipeline

  outputs = run_pipeline(
      plans_path="output/plans.xml.gz",
      population_fallback="population.xml.gz",
      events_path="output/events.xml.gz",
      outdir="analysis",
      schedule_path="transitSchedule.xml",
  )
"""

__version__ = "1.0.0"
