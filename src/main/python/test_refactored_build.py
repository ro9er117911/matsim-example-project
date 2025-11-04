#!/usr/bin/env python
"""
Quick verification script to test the refactored build_agent_tracks modules.

This script tests:
1. All modules can be imported
2. Core functions work as expected
3. Activity matching integrates properly
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all modules can be imported."""
    print("=" * 70)
    print("Testing Module Imports...")
    print("=" * 70)

    try:
        from build_agent_tracks import utils
        print("✓ build_agent_tracks.utils")

        from build_agent_tracks import models
        print("✓ build_agent_tracks.models")

        from build_agent_tracks import parsers
        print("✓ build_agent_tracks.parsers")

        from build_agent_tracks import legs_builder
        print("✓ build_agent_tracks.legs_builder")

        from build_agent_tracks import tracks_builder
        print("✓ build_agent_tracks.tracks_builder")

        from build_agent_tracks import activity_matcher
        print("✓ build_agent_tracks.activity_matcher")

        from build_agent_tracks import vehicle_filter
        print("✓ build_agent_tracks.vehicle_filter")

        from build_agent_tracks import main
        print("✓ build_agent_tracks.main")

        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_utils():
    """Test utility functions."""
    print("\n" + "=" * 70)
    print("Testing Utility Functions...")
    print("=" * 70)

    from build_agent_tracks.utils import hhmmss_to_seconds, seconds_to_hhmmss

    # Test time conversion
    assert hhmmss_to_seconds("01:30:45") == 5445, "hhmmss_to_seconds failed"
    print("✓ hhmmss_to_seconds('01:30:45') == 5445")

    assert seconds_to_hhmmss(5445) == "1:30:45", "seconds_to_hhmmss failed"
    print("✓ seconds_to_hhmmss(5445) == '1:30:45'")

    assert hhmmss_to_seconds(None) is None, "None handling failed"
    print("✓ hhmmss_to_seconds(None) == None")

    return True


def test_models():
    """Test data models."""
    print("\n" + "=" * 70)
    print("Testing Data Models...")
    print("=" * 70)

    from build_agent_tracks.models import Activity, Leg, PersonPlan, PlanEntry

    # Create test objects
    act = Activity(type="home", x=100.0, y=200.0, link="1",
                   start_time_s=0, end_time_s=3600)
    print(f"✓ Created Activity: {act.type} at ({act.x}, {act.y})")

    leg = Leg(mode="walk", dep_time_s=3600, trav_time_s=600)
    print(f"✓ Created Leg: mode={leg.mode}, dep_time={leg.dep_time_s}s")

    entry = PlanEntry(kind="act", data=act)
    print(f"✓ Created PlanEntry: {entry.kind}")

    plan = PersonPlan(person_id="agent_1", entries=[entry])
    print(f"✓ Created PersonPlan for {plan.person_id} with {len(plan.entries)} entries")

    return True


def test_activity_matcher():
    """Test Activity matching functionality."""
    print("\n" + "=" * 70)
    print("Testing Activity Matcher (New Feature)...")
    print("=" * 70)

    from build_agent_tracks.activity_matcher import (
        extract_activities_by_person,
        _is_time_in_activity,
        _euclidean_distance_km,
    )
    from build_agent_tracks.models import Activity, PersonPlan, PlanEntry

    # Create test data
    act1 = Activity(type="home", x=100.0, y=200.0, link="1",
                    start_time_s=0, end_time_s=3600)
    act2 = Activity(type="work", x=500.0, y=600.0, link="2",
                    start_time_s=7200, end_time_s=18000)

    plan = PersonPlan(person_id="test_agent", entries=[
        PlanEntry(kind="act", data=act1),
        PlanEntry(kind="act", data=act2),
    ])

    # Test extraction
    activities = extract_activities_by_person([plan])
    assert "test_agent" in activities, "Extract activities failed"
    assert len(activities["test_agent"]) == 2, "Wrong activity count"
    print("✓ extract_activities_by_person() works correctly")

    # Test time matching
    assert _is_time_in_activity(1800, act1), "Time matching failed"
    assert not _is_time_in_activity(5000, act1), "Time matching failed (should be false)"
    print("✓ _is_time_in_activity() time matching works")

    # Test distance calculation
    dist = _euclidean_distance_km(100.0, 200.0, 100.0, 200.0)
    assert dist == 0.0, "Distance calculation failed"
    dist2 = _euclidean_distance_km(0.0, 0.0, 1000.0, 0.0)
    assert dist2 == 1.0, "Distance calculation failed"
    print("✓ _euclidean_distance_km() distance calculation works")

    return True


def test_cli_parser():
    """Test CLI argument parser."""
    print("\n" + "=" * 70)
    print("Testing CLI Argument Parser...")
    print("=" * 70)

    from build_agent_tracks.main import build_arg_parser

    parser = build_arg_parser()

    # Test parsing valid arguments
    args = parser.parse_args([
        "--plans", "plans.xml.gz",
        "--out", "/tmp/output",
        "--dt", "10",
    ])

    assert args.plans == "plans.xml.gz", "Failed to parse --plans"
    assert args.out == "/tmp/output", "Failed to parse --out"
    assert args.dt == 10, "Failed to parse --dt"
    print("✓ CLI parser correctly parses arguments")

    # Test skip-activity-matching flag
    args2 = parser.parse_args([
        "--plans", "plans.xml.gz",
        "--out", "/tmp/output",
        "--skip-activity-matching",
    ])
    assert args2.skip_activity_matching is True, "Failed to parse --skip-activity-matching"
    print("✓ CLI parser correctly handles --skip-activity-matching flag")

    return True


def main():
    """Run all tests."""
    print("\n")
    print(" " * 15 + "BUILD_AGENT_TRACKS REFACTORING VERIFICATION")
    print(" " * 20 + "Testing Modular Structure & New Features")

    tests = [
        ("Module Imports", test_imports),
        ("Utility Functions", test_utils),
        ("Data Models", test_models),
        ("Activity Matcher (NEW)", test_activity_matcher),
        ("CLI Parser", test_cli_parser),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test_name} failed")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("\n✓✓✓ All verification tests passed! ✓✓✓")
        print("\nYou can now use the refactored build_agent_tracks:")
        print("  python build_agent_tracks.py --plans <file> --out <dir>")
        print("\nWith Activity matching enabled by default!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
