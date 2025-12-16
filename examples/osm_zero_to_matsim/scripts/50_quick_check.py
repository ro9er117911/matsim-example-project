#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def _latest_iteration_dir(iters_dir: Path) -> Path | None:
    candidates: list[tuple[int, Path]] = []
    for child in iters_dir.iterdir():
        if not child.is_dir():
            continue
        if not child.name.startswith("it."):
            continue
        try:
            it = int(child.name.split(".", 1)[1])
        except Exception:
            continue
        candidates.append((it, child))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p[0])[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Quick sanity check for a MATSim output directory.")
    parser.add_argument("--output", required=True, help="MATSim output directory")
    args = parser.parse_args()

    out = Path(args.output)

    basics = ["scorestats.csv", "modestats.csv", "ITERS"]
    missing_basics = [name for name in basics if not (out / name).exists()]
    if missing_basics:
        print("[ERROR] Missing basic outputs:")
        for name in missing_basics:
            print(" -", out / name)
        return 2

    # Prefer top-level output_events/output_plans when present, otherwise fall back to the last iters folder.
    output_events = out / "output_events.xml.gz"
    output_plans = out / "output_plans.xml.gz"
    if output_events.exists() and output_plans.exists():
        checked = [output_events, output_plans]
    else:
        it_dir = _latest_iteration_dir(out / "ITERS")
        if it_dir is None:
            print("[ERROR] No iteration folders found under:", out / "ITERS")
            return 2
        it = it_dir.name.split(".", 1)[1]
        checked = [
            it_dir / f"{it}.events.xml.gz",
            it_dir / f"{it}.plans.xml.gz",
        ]

    missing = [p for p in checked if not p.exists()]
    if missing:
        print("[WARN] Output directory exists, but key files are missing:")
        for p in missing:
            print(" -", p)
        return 1

    print("[OK] Output looks present:")
    for p in checked:
        print(f" - {p} ({p.stat().st_size/1024:.1f} KiB)")
    for name in ["scorestats.csv", "modestats.csv"]:
        p = out / name
        print(f" - {p} ({p.stat().st_size/1024:.1f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
