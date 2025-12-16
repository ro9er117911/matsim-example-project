#!/usr/bin/env python3
"""
Regression Check for Evacuation Simulation

Compares current output against baseline to verify reproducibility.

Metrics checked:
1. Event count (total events in output_events.xml.gz)
2. Evacuation completion rate (agents that left network / total agents)
3. Maximum travel time (longest evacuation time)

Usage:
    python regression_check.py --baseline PATH --current PATH
    python regression_check.py --current PATH  # (prints metrics only)
"""

import argparse
import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict


def count_events(events_file: Path) -> dict:
    """
    Parse events file and extract key metrics.
    
    Returns dict with:
    - total_events: int
    - agents: set of agent IDs
    - departures: dict[agent_id] -> departure_time
    - arrivals: dict[agent_id] -> arrival_time
    - left_network: set of agent IDs that left network
    """
    metrics = {
        'total_events': 0,
        'agents': set(),
        'departures': {},
        'arrivals': {},
        'left_network': set(),
        'event_types': defaultdict(int)
    }
    
    print(f"Parsing: {events_file}")
    
    opener = gzip.open if str(events_file).endswith('.gz') else open
    
    with opener(events_file, 'rt', encoding='utf-8') as f:
        # Use iterparse for memory efficiency
        for event, elem in ET.iterparse(f, events=('end',)):
            if elem.tag == 'event':
                metrics['total_events'] += 1
                event_type = elem.get('type', '')
                metrics['event_types'][event_type] += 1
                
                person = elem.get('person', '')
                time = float(elem.get('time', 0))
                
                if person and not person.startswith('pt_'):
                    metrics['agents'].add(person)
                    
                    if event_type == 'departure':
                        if person not in metrics['departures']:
                            metrics['departures'][person] = time
                    
                    elif event_type == 'arrival':
                        metrics['arrivals'][person] = time
                    
                    elif event_type == 'PersonLeavesNetworkEvent':
                        metrics['left_network'].add(person)
                
                # Clear element to save memory
                elem.clear()
    
    return metrics


def compute_evacuation_stats(metrics: dict) -> dict:
    """Compute evacuation statistics from parsed metrics."""
    
    total_agents = len(metrics['agents'])
    departed_agents = len(metrics['departures'])
    left_network = len(metrics['left_network'])
    
    # Completion rate
    completion_rate = (left_network / total_agents * 100) if total_agents > 0 else 0
    
    # Travel times
    travel_times = []
    for agent in metrics['departures']:
        if agent in metrics['arrivals']:
            tt = metrics['arrivals'][agent] - metrics['departures'][agent]
            if tt > 0:
                travel_times.append(tt)
    
    max_travel_time = max(travel_times) if travel_times else 0
    avg_travel_time = sum(travel_times) / len(travel_times) if travel_times else 0
    
    return {
        'total_events': metrics['total_events'],
        'total_agents': total_agents,
        'departed_agents': departed_agents,
        'left_network': left_network,
        'completion_rate': completion_rate,
        'max_travel_time': max_travel_time,
        'avg_travel_time': avg_travel_time,
        'event_types': dict(metrics['event_types'])
    }


def print_stats(label: str, stats: dict):
    """Pretty print statistics."""
    print(f"\n{'='*50}")
    print(f"{label}")
    print('='*50)
    print(f"Total Events:        {stats['total_events']:,}")
    print(f"Total Agents:        {stats['total_agents']}")
    print(f"Departed Agents:     {stats['departed_agents']}")
    print(f"Left Network:        {stats['left_network']}")
    print(f"Completion Rate:     {stats['completion_rate']:.1f}%")
    print(f"Max Travel Time:     {stats['max_travel_time']:.0f}s ({stats['max_travel_time']/60:.1f} min)")
    print(f"Avg Travel Time:     {stats['avg_travel_time']:.0f}s ({stats['avg_travel_time']/60:.1f} min)")
    print('='*50)


def compare(baseline_stats: dict, current_stats: dict, tolerance: float = 0.05) -> bool:
    """
    Compare baseline and current stats.
    Returns True if within tolerance.
    """
    print("\n" + "="*50)
    print("COMPARISON RESULTS")
    print("="*50)
    
    passed = True
    
    # Event count comparison
    baseline_events = baseline_stats['total_events']
    current_events = current_stats['total_events']
    event_diff = abs(current_events - baseline_events) / baseline_events if baseline_events > 0 else 0
    event_status = "✅" if event_diff <= tolerance else "❌"
    print(f"{event_status} Event Count:     {current_events:,} vs {baseline_events:,} (diff: {event_diff*100:.1f}%)")
    if event_diff > tolerance:
        passed = False
    
    # Completion rate comparison
    baseline_rate = baseline_stats['completion_rate']
    current_rate = current_stats['completion_rate']
    rate_diff = abs(current_rate - baseline_rate)
    rate_status = "✅" if rate_diff <= tolerance * 100 else "❌"
    print(f"{rate_status} Completion Rate: {current_rate:.1f}% vs {baseline_rate:.1f}% (diff: {rate_diff:.1f}%)")
    if rate_diff > tolerance * 100:
        passed = False
    
    # Max travel time comparison
    baseline_max = baseline_stats['max_travel_time']
    current_max = current_stats['max_travel_time']
    max_diff = abs(current_max - baseline_max) / baseline_max if baseline_max > 0 else 0
    max_status = "✅" if max_diff <= tolerance else "❌"
    print(f"{max_status} Max Travel Time: {current_max:.0f}s vs {baseline_max:.0f}s (diff: {max_diff*100:.1f}%)")
    if max_diff > tolerance:
        passed = False
    
    print("="*50)
    
    if passed:
        print("✅ REGRESSION TEST PASSED")
    else:
        print("❌ REGRESSION TEST FAILED")
    
    return passed


def main():
    parser = argparse.ArgumentParser(description="Regression check for evacuation simulation")
    parser.add_argument('--baseline', type=Path, help='Baseline output directory')
    parser.add_argument('--current', type=Path, required=True, help='Current output directory')
    parser.add_argument('--tolerance', type=float, default=0.05, 
                        help='Tolerance for differences (default: 0.05 = 5%%)')
    
    args = parser.parse_args()
    
    # Find events file in current directory
    current_events = args.current / 'output_events.xml.gz'
    if not current_events.exists():
        current_events = args.current / 'output_events.xml'
    
    if not current_events.exists():
        print(f"ERROR: Events file not found in {args.current}")
        exit(1)
    
    # Parse current
    current_metrics = count_events(current_events)
    current_stats = compute_evacuation_stats(current_metrics)
    print_stats("CURRENT RUN", current_stats)
    
    # Parse baseline and compare (if provided)
    if args.baseline:
        baseline_events = args.baseline / 'output_events.xml.gz'
        if not baseline_events.exists():
            baseline_events = args.baseline / 'output_events.xml'
        
        if not baseline_events.exists():
            print(f"WARNING: Baseline events file not found in {args.baseline}")
            exit(0)
        
        baseline_metrics = count_events(baseline_events)
        baseline_stats = compute_evacuation_stats(baseline_metrics)
        print_stats("BASELINE", baseline_stats)
        
        passed = compare(baseline_stats, current_stats, args.tolerance)
        exit(0 if passed else 1)
    
    print("\nNo baseline provided. Use --baseline PATH to compare.")


if __name__ == '__main__':
    main()
