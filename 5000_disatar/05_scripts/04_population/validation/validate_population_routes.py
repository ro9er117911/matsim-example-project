#!/usr/bin/env python3
"""
Validate MATSim population routes with directional routing and car→PT mode conversion.

Usage:
    python validate_population_routes.py \\
        --population population.xml.gz \\
        --network network-with-pt-final.xml \\
        --schedule transitSchedule-mapped.xml.gz \\
        --output-dir ./validation_output \\
        --max-walk-distance 500 \\
        --max-snap-distance 300 \\
        --progress
"""

import argparse
import time
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Set, Dict, List

from validation import (
    DirectedNetworkGraph,
    DirectionalRoutingValidator,
    PTCoverageValidator,
    AgentRouteProcessor,
    FilteredPopulationWriter,
    open_maybe_gz
)


class PopulationValidator:
    """Main population validator orchestrator."""

    def __init__(self, args):
        """Initialize validator with command-line arguments."""
        self.args = args
        self.network_graph = None
        self.routing_validator = None
        self.pt_validator = None
        self.agent_processor = None
        self.output_writer = None

    def run(self):
        """Execute full validation pipeline."""
        start_time = time.time()

        print("=" * 70)
        print("MATSIM POPULATION ROUTE VALIDATOR")
        print("=" * 70)
        print(f"\nInput files:")
        print(f"  Population:  {self.args.population}")
        print(f"  Network:     {self.args.network}")
        print(f"  Schedule:    {self.args.schedule}")
        print(f"\nOutput directory: {self.args.output_dir}")
        print(f"\nParameters:")
        print(f"  Max walk distance:  {self.args.max_walk_distance}m")
        print(f"  Max snap distance:  {self.args.max_snap_distance}m")
        print(f"  Batch size:         {self.args.batch_size}")
        print("\n" + "=" * 70)

        # Step 1: Load and parse network
        print("\n[1/5] Loading network...")
        self.network_graph = DirectedNetworkGraph(self.args.network)

        # Step 2: Initialize routing validator
        print("\n[2/5] Initializing routing validator...")
        self.routing_validator = DirectionalRoutingValidator(self.network_graph)

        # Step 3: Load transit schedule
        print("\n[3/5] Loading transit schedule...")
        self.pt_validator = PTCoverageValidator(self.args.schedule)

        # Step 4: Initialize agent processor
        print("\n[4/5] Initializing agent processor...")
        self.agent_processor = AgentRouteProcessor(
            routing_validator=self.routing_validator,
            pt_validator=self.pt_validator,
            max_snap_distance=self.args.max_snap_distance,
            max_walk_distance=self.args.max_walk_distance
        )

        # Step 5: Process population
        print("\n[5/5] Processing population...")
        agent_results, modified_agents = self._process_population()

        # Step 6: Generate outputs
        print("\n[6/6] Generating outputs...")
        self._generate_outputs(agent_results, modified_agents, time.time() - start_time)

        print("\n✓ Validation complete!")
        return agent_results

    def _process_population(self) -> tuple[List[Dict], Dict]:
        """
        Process all agents in population.

        Returns:
            Tuple of (agent_results, modified_agents)
        """
        agent_results = []
        modified_agents = {}  # agent_id -> modified <person> element
        processed_count = 0
        batch_start_time = time.time()

        with open_maybe_gz(self.args.population) as f:
            context = ET.iterparse(f, events=("start", "end"))
            _, root = next(context)

            for event, elem in context:
                if event == "end" and elem.tag == "person":
                    # Process agent
                    result = self.agent_processor.process_agent(elem)
                    agent_results.append(result)

                    # If agent was converted (car→PT), save modified element
                    if result['status'] == 'converted':
                        modified_agents[result['agent_id']] = self._deep_copy_elem(elem)

                    processed_count += 1

                    # Progress reporting
                    if self.args.progress and processed_count % self.args.batch_size == 0:
                        elapsed = time.time() - batch_start_time
                        rate = self.args.batch_size / elapsed if elapsed > 0 else 0
                        print(f"  Processed {processed_count} agents ({rate:.1f} agents/sec)")
                        batch_start_time = time.time()

                    # Clear to free memory
                    elem.clear()

        print(f"  ✓ Processed {processed_count} agents")

        return agent_results, modified_agents

    def _generate_outputs(
        self,
        agent_results: List[Dict],
        modified_agents: Dict,
        processing_time: float
    ):
        """Generate filtered population and validation reports."""
        self.output_writer = FilteredPopulationWriter(self.args.output_dir)

        # Determine valid agents
        valid_agent_ids = set()
        for result in agent_results:
            if result['status'] in ['valid', 'converted']:
                valid_agent_ids.add(result['agent_id'])

        # Write filtered population
        print(f"\n  Writing filtered population...")
        self.output_writer.write_filtered_population(
            self.args.population,
            valid_agent_ids,
            modified_agents
        )

        # Write validation report
        print(f"  Writing validation report...")
        self.output_writer.write_validation_report(agent_results)

        # Write summary statistics
        print(f"  Writing validation summary...")
        self.output_writer.write_summary_statistics(agent_results, processing_time)

        # Print cache statistics
        cache_stats = self.routing_validator.get_cache_stats()
        print(f"\n  Routing cache stats:")
        print(f"    Cache size: {cache_stats['cache_size']}")
        print(f"    Cache hit rate: {cache_stats['cache_hits']/cache_stats['cache_size']*100:.1f}%")

    def _deep_copy_elem(self, elem: ET.Element) -> ET.Element:
        """Deep copy an XML element."""
        new_elem = ET.Element(elem.tag, attrib=elem.attrib)
        new_elem.text = elem.text
        new_elem.tail = elem.tail

        for child in elem:
            new_elem.append(self._deep_copy_elem(child))

        return new_elem


def main():
    parser = argparse.ArgumentParser(
        description='Validate MATSim population routes with mode conversion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  # Basic validation
  python validate_population_routes.py \\
    --population 5000_disatar/working_temp/population.xml.gz \\
    --network 5000_disatar/03_phase2_production/networks/network-with-pt-final.xml \\
    --schedule 5000_disatar/03_phase2_production/schedules/transitSchedule-mapped.xml.gz \\
    --output-dir 5000_disatar/validation_output

  # With custom parameters
  python validate_population_routes.py \\
    --population population.xml.gz \\
    --network network.xml \\
    --schedule schedule.xml.gz \\
    --output-dir validation_output \\
    --max-walk-distance 600 \\
    --max-snap-distance 400 \\
    --progress
        """
    )

    # Required inputs
    parser.add_argument(
        '--population',
        required=True,
        help='Input population.xml.gz file'
    )

    parser.add_argument(
        '--network',
        required=True,
        help='MATSim network.xml file (with PT links)'
    )

    parser.add_argument(
        '--schedule',
        required=True,
        help='Transit schedule.xml.gz file'
    )

    # Output settings
    parser.add_argument(
        '--output-dir',
        default='./validation_output',
        help='Output directory for filtered population and reports (default: ./validation_output)'
    )

    # Validation parameters
    parser.add_argument(
        '--max-walk-distance',
        type=float,
        default=500.0,
        help='Maximum walking distance to PT stop in meters (default: 500)'
    )

    parser.add_argument(
        '--max-snap-distance',
        type=float,
        default=300.0,
        help='Maximum coordinate-to-link snapping distance in meters (default: 300)'
    )

    # Performance tuning
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Process agents in batches (default: 100)'
    )

    parser.add_argument(
        '--progress',
        action='store_true',
        help='Show progress bar during processing'
    )

    args = parser.parse_args()

    # Validate input files exist
    for file_path, name in [
        (args.population, 'Population'),
        (args.network, 'Network'),
        (args.schedule, 'Schedule')
    ]:
        if not Path(file_path).exists():
            print(f"ERROR: {name} file not found: {file_path}")
            return 1

    # Run validation
    validator = PopulationValidator(args)
    validator.run()

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
