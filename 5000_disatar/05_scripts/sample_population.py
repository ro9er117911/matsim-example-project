"""
Sample a fraction of persons from MATSim population.xml

Usage:
    python sample_population.py <input_file> <output_file> <sample_fraction>

Example:
    python sample_population.py population.xml population_sample.xml.gz 0.05
"""

import xml.etree.ElementTree as ET
import random
import gzip
import sys

def sample_population(input_file, output_file, sample_fraction=0.05, compress=True):
    """
    Sample a fraction of persons from MATSim population.xml

    Args:
        input_file: Path to input population.xml
        output_file: Path to output sampled population
        sample_fraction: Fraction to sample (default 0.05 = 5%)
        compress: Whether to gzip compress output
    """
    print(f"Reading population from: {input_file}")

    # Parse input XML
    tree = ET.parse(input_file)
    root = tree.getroot()

    # Get all person elements
    persons = root.findall('person')
    total_count = len(persons)
    sample_size = int(total_count * sample_fraction)

    print(f"Total population: {total_count}")
    print(f"Sample fraction: {sample_fraction * 100}%")
    print(f"Sample size: {sample_size}")

    # Random sampling
    random.seed(42)  # Reproducible sampling
    sampled_persons = random.sample(persons, sample_size)

    print(f"Sampled {len(sampled_persons)} persons (IDs: {[p.get('id') for p in sampled_persons[:5]]}...)")

    # Remove all persons from root
    for person in persons:
        root.remove(person)

    # Add sampled persons back
    for person in sampled_persons:
        root.append(person)

    # Write output
    if compress and not output_file.endswith('.gz'):
        output_file += '.gz'

    print(f"Writing sampled population to: {output_file}")

    # Write with MATSim DOCTYPE declaration
    if output_file.endswith('.gz'):
        import io
        buffer = io.BytesIO()
        tree.write(buffer, encoding='utf-8', xml_declaration=True)
        xml_content = buffer.getvalue().decode('utf-8')

        # Insert DOCTYPE after XML declaration
        lines = xml_content.split('\n', 1)
        xml_with_doctype = lines[0] + '\n<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n\n' + lines[1]

        with gzip.open(output_file, 'wt', encoding='utf-8') as f:
            f.write(xml_with_doctype)
    else:
        import io
        buffer = io.StringIO()
        tree.write(buffer, encoding='utf-8', xml_declaration=True)
        xml_content = buffer.getvalue()

        # Insert DOCTYPE after XML declaration
        lines = xml_content.split('\n', 1)
        xml_with_doctype = lines[0] + '\n<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n\n' + lines[1]

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_with_doctype)

    print(f"✓ Sampled population saved to: {output_file}")
    print(f"  ({sample_size} agents)")

if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'working_temp/population.xml'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'working_temp/population_sample_5pct.xml.gz'
    sample_fraction = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05

    sample_population(input_file, output_file, sample_fraction, compress=True)
