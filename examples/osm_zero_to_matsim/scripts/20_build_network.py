#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / "pom.xml").exists():
            return parent
    raise FileNotFoundError("Cannot locate repo root (missing pom.xml in parents)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a MATSim (car+walk) network from OSM using this repo's shaded jar.",
    )
    parser.add_argument("--osm", required=True, help="Input OSM file (.osm/.pbf)")
    parser.add_argument("--out", required=True, help="Output MATSim network (.xml or .xml.gz)")
    parser.add_argument(
        "--out-clean",
        default=None,
        help="Optional cleaned network output (.xml/.xml.gz). Runs NetworkCleaner.",
    )
    parser.add_argument(
        "--java-xmx",
        default="2g",
        help="Java heap, e.g. 2g, 8g (default: 2g)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = find_repo_root(script_dir)
    jar = repo_root / "matsim-example-project-0.0.1-SNAPSHOT.jar"
    if not jar.exists():
        raise FileNotFoundError(f"Missing {jar}. Run: ./mvnw clean package -DskipTests")

    osm = Path(args.osm).resolve()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    osm_suffix = osm.suffix.lower()
    if osm_suffix in {".pbf"} or osm.name.lower().endswith(".osm.pbf"):
        main_class = "org.matsim.project.tools.BuildCarWalkNetworkFromOsm"
        cmd = [
            "java",
            f"-Xmx{args.java_xmx}",
            "-cp",
            str(jar),
            main_class,
            str(osm),
            str(out),
        ]
        if args.out_clean:
            out_clean = Path(args.out_clean).resolve()
            out_clean.parent.mkdir(parents=True, exist_ok=True)
            cmd.append(str(out_clean))
    else:
        main_class = "org.matsim.project.tools.BuildNetworkFromOsmXml"
        cmd = [
            "java",
            f"-Xmx{args.java_xmx}",
            "-cp",
            str(jar),
            main_class,
            str(osm),
            str(out),
        ]

    print("[INFO] Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(repo_root))
    return result.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
