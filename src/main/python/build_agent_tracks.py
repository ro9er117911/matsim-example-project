"""
Build agent tracks: Extract MATSim agent legs and build time-sampled tracks.

This is a backward-compatible wrapper that imports the refactored modules.
For detailed documentation, see build_agent_tracks/ package.

Usage:
  python build_agent_tracks.py --plans plans.xml.gz --schedule schedule.xml --out analysis/

For Activity Matching enabled (new in v1.0):
  python build_agent_tracks.py --plans plans.xml.gz --schedule schedule.xml --out analysis/

To skip Activity Matching (faster):
  python build_agent_tracks.py --plans plans.xml.gz --schedule schedule.xml --out analysis/ --skip-activity-matching
"""

# Import the main pipeline function from the new modular structure
from build_agent_tracks.main import main

if __name__ == "__main__":
    main()
