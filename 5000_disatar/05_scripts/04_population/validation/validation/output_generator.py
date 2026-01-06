"""
Filtered population writer and validation report generator.

Generates:
1. filtered_population.xml.gz - Only valid and converted agents
2. validation_report.csv - Per-agent validation details
3. validation_summary.json - Statistics
"""
import csv
import json
import gzip
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, List, Set
from collections import Counter

from .utils import open_maybe_gz


class FilteredPopulationWriter:
    """
    Generate filtered population.xml and reports.

    Outputs:
    1. filtered_population.xml.gz - Only valid agents
    2. validation_report.csv - Per-agent validation details
    3. validation_summary.json - Statistics
    """

    def __init__(self, output_dir: str):
        """
        Initialize writer with output directory.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_filtered_population(
        self,
        input_xml_path: str,
        valid_agent_ids: Set[str],
        modified_agents: Dict[str, ET.Element]
    ):
        """
        Write filtered population XML with only valid agents.

        Uses iterparse to handle large files efficiently.

        Args:
            input_xml_path: Path to original population.xml(.gz)
            valid_agent_ids: Set of agent IDs to include
            modified_agents: Dict of agent_id -> modified <person> element (for car→PT conversions)
        """
        output_path = self.output_dir / "filtered_population.xml.gz"

        # Create output root
        root = ET.Element('population')

        # Parse input and filter
        with open_maybe_gz(input_xml_path) as f:
            context = ET.iterparse(f, events=("start", "end"))
            _, input_root = next(context)

            for event, elem in context:
                if event == "end" and elem.tag == "person":
                    agent_id = elem.get("id")

                    if agent_id in valid_agent_ids:
                        # Check if agent was modified (car→PT conversion)
                        if agent_id in modified_agents:
                            # Use modified version
                            person_elem = modified_agents[agent_id]
                        else:
                            # Use original
                            person_elem = elem

                        # Deep copy to avoid reference issues
                        root.append(self._deep_copy_elem(person_elem))

                    # Clear to free memory
                    elem.clear()

        # Add DOCTYPE and write
        self._write_population_xml(root, output_path)

        print(f"  ✓ Wrote filtered population: {output_path}")
        print(f"    - Included agents: {len(valid_agent_ids)}")

    def write_validation_report(
        self,
        agent_results: List[Dict]
    ):
        """
        Write per-agent CSV validation report.

        Columns:
        - agent_id, original_mode, final_mode, status, reason
        - origin_x, origin_y, dest_x, dest_y
        - car_reachable, pt_accessible

        Args:
            agent_results: List of validation result dictionaries
        """
        output_path = self.output_dir / "validation_report.csv"

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'agent_id', 'original_mode', 'final_mode', 'status', 'reason',
                'origin_x', 'origin_y', 'dest_x', 'dest_y',
                'car_reachable', 'pt_accessible'
            ])
            writer.writeheader()

            for result in agent_results:
                # Format coordinates
                origin_coords = result.get('origin_coords')
                dest_coords = result.get('dest_coords')

                row = {
                    'agent_id': result['agent_id'],
                    'original_mode': result['original_mode'],
                    'final_mode': result.get('final_mode', ''),
                    'status': result['status'],
                    'reason': result['reason'],
                    'origin_x': f"{origin_coords[0]:.2f}" if origin_coords else '',
                    'origin_y': f"{origin_coords[1]:.2f}" if origin_coords else '',
                    'dest_x': f"{dest_coords[0]:.2f}" if dest_coords else '',
                    'dest_y': f"{dest_coords[1]:.2f}" if dest_coords else '',
                    'car_reachable': result.get('car_reachable', ''),
                    'pt_accessible': result.get('pt_accessible', '')
                }
                writer.writerow(row)

        print(f"  ✓ Wrote validation report: {output_path}")

    def write_summary_statistics(
        self,
        agent_results: List[Dict],
        processing_time_seconds: float
    ):
        """
        Write JSON summary statistics.

        Statistics:
        - total_agents, valid_agents, converted_agents, invalid_agents
        - mode_breakdown: {mode: count}
        - invalid_reasons: {reason: count}
        - conversion_rate

        Args:
            agent_results: List of validation result dictionaries
            processing_time_seconds: Total processing time
        """
        output_path = self.output_dir / "validation_summary.json"

        # Calculate statistics
        total_agents = len(agent_results)
        valid_agents = sum(1 for r in agent_results if r['status'] in ['valid', 'converted'])
        converted_agents = sum(1 for r in agent_results if r['status'] == 'converted')
        invalid_agents = sum(1 for r in agent_results if r['status'] == 'invalid')

        # Mode breakdown (final modes)
        mode_breakdown = Counter()
        for result in agent_results:
            if result['status'] in ['valid', 'converted']:
                mode_breakdown[result.get('final_mode', 'unknown')] += 1

        # Invalid reasons breakdown
        invalid_reasons = Counter()
        for result in agent_results:
            if result['status'] == 'invalid':
                invalid_reasons[result['reason']] += 1

        # Conversion rate
        conversion_rate = converted_agents / total_agents if total_agents > 0 else 0.0

        summary = {
            'total_agents': total_agents,
            'valid_agents': valid_agents,
            'converted_agents': converted_agents,
            'invalid_agents': invalid_agents,
            'mode_breakdown': dict(mode_breakdown),
            'invalid_reasons': dict(invalid_reasons),
            'conversion_rate': round(conversion_rate, 4),
            'processing_time_seconds': round(processing_time_seconds, 2)
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        print(f"  ✓ Wrote validation summary: {output_path}")
        print(f"\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        print(f"Total agents:      {total_agents}")
        print(f"Valid agents:      {valid_agents} ({valid_agents/total_agents*100:.1f}%)")
        print(f"Converted (car→PT): {converted_agents} ({conversion_rate*100:.1f}%)")
        print(f"Invalid agents:    {invalid_agents} ({invalid_agents/total_agents*100:.1f}%)")
        print(f"\nMode breakdown:")
        for mode, count in sorted(mode_breakdown.items()):
            print(f"  {mode}: {count}")
        if invalid_reasons:
            print(f"\nInvalid reasons:")
            for reason, count in sorted(invalid_reasons.items(), key=lambda x: x[1], reverse=True):
                print(f"  {reason}: {count}")
        print(f"\nProcessing time:   {processing_time_seconds:.2f} seconds")
        print("=" * 70)

    def _deep_copy_elem(self, elem: ET.Element) -> ET.Element:
        """Deep copy an XML element to avoid reference issues."""
        new_elem = ET.Element(elem.tag, attrib=elem.attrib)
        new_elem.text = elem.text
        new_elem.tail = elem.tail

        for child in elem:
            new_elem.append(self._deep_copy_elem(child))

        return new_elem

    def _write_population_xml(self, root: ET.Element, output_path: Path):
        """Write population XML with DOCTYPE declaration."""
        # Convert to string
        xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')

        # Add XML declaration and DOCTYPE
        xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_output += '<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n'
        xml_output += xml_str

        # Write compressed
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            f.write(xml_output)
