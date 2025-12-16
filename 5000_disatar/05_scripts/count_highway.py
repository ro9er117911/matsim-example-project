#!/usr/bin/env python3
"""
Count OSM highway types kept in a MATSim network.

Usage:
  python3 count_highway.py [network.xml[.gz]]
If no argument is provided, defaults to ./network.xml in the current working directory.
"""

import gzip
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import BinaryIO, Iterator


def open_maybe_gzip(path: Path) -> BinaryIO:
	"""Open xml or xml.gz in binary mode."""
	return gzip.open(path, "rb") if path.suffix == ".gz" else open(path, "rb")


def iter_highways(path: Path) -> Iterator[str]:
	"""Yield highway attribute values from each link."""
	with open_maybe_gzip(path) as fh:
		for _, element in ET.iterparse(fh):
			if element.tag != "link":
				element.clear()
				continue
			attrs = element.find("attributes")
			if attrs is None:
				element.clear()
				continue
			for attr in attrs.findall("attribute"):
				if attr.get("name") == "osm:way:highway":
					yield (attr.text or "").strip()
			element.clear()


def main() -> None:
	target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("network.xml")
	if not target.exists():
		sys.exit(f"Path not found: {target}")

	counter: Counter[str] = Counter()
	for highway in iter_highways(target):
		if highway:
			counter[highway] += 1

	for highway, count in counter.most_common():
		print(f"{highway}\t{count}")


if __name__ == "__main__":
	main()
