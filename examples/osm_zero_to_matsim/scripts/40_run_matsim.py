#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / "pom.xml").exists():
            return parent
    raise FileNotFoundError("Cannot locate repo root (missing pom.xml in parents)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MATSim headless (example runner without GUI/SimWrapper).")
    parser.add_argument("--config", required=True, help="Path to config.xml")
    parser.add_argument("--output", default=None, help="Override controller.outputDirectory")
    parser.add_argument("--last-iteration", type=int, default=None, help="Override controller.lastIteration")
    parser.add_argument("--java-xmx", default="2g", help="Java heap, e.g. 2g, 8g (default: 2g)")
    parser.add_argument(
        "--log-level",
        default="warn",
        choices=["trace", "debug", "info", "warn", "error", "fatal"],
        help="LOG_LEVEL for log4j2 (default: warn)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = find_repo_root(script_dir)
    jar = repo_root / "matsim-example-project-0.0.1-SNAPSHOT.jar"
    if not jar.exists():
        raise FileNotFoundError(f"Missing {jar}. Run: ./mvnw clean package -DskipTests")

    config_path = Path(args.config).resolve()

    cmd = [
        "java",
        f"-Xmx{args.java_xmx}",
        "-cp",
        str(jar),
        "org.matsim.project.examples.osm.RunOsmFromScratchHeadless",
        str(config_path),
    ]
    if args.output:
        cmd += ["--config:controller.outputDirectory", str(Path(args.output).resolve())]
    if args.last_iteration is not None:
        cmd += ["--config:controller.lastIteration", str(args.last_iteration)]

    print("[INFO] Running:", " ".join(cmd))
    env = os.environ.copy()
    env["LOG_LEVEL"] = args.log_level
    result = subprocess.run(cmd, cwd=str(repo_root), env=env)

    # MATSimApplication 在某些環境下會以非 0 exit code 結束，但輸出已經寫完（常見：250）。
    # 這裡以「是否產生 ITERS/it.*/*.events.xml(.gz)」作為成功判斷。
    if result.returncode == 0:
        return 0

    output_dir = Path(args.output).resolve() if args.output else config_path.parent / "output"
    iters = output_dir / "ITERS"
    if iters.exists() and any(iters.rglob("*.events.xml.gz")):
        print(f"[WARN] MATSim exited with {result.returncode}, but output exists under: {output_dir}")
        return 0

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
