#!/usr/bin/env bash
# Prepare variant configs and run simulation for 100k scenario.
# [DEPRECATED] Via export - now using SimWrapper for visualization.
# Variants are defined below (v1 control, v2 treatment).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BASE_CONFIG="${ROOT}/scenarios/equil/config_metro_0300_0618_100000.xml"
# [DEPRECATED] VIA export - now using SimWrapper
# RUNNER="${ROOT}/scripts/run_simulation_with_via_export.sh"
RUNNER="${ROOT}/5000_disatar/05_scripts/05_simulation/run_simulation.sh"

# Enforce JVM memory cap (12 GB) for downstream runner/maven
MEM_OPTS="-Xms12g -Xmx12g -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200"
export JAVA_OPTS="${MEM_OPTS}"
export MAVEN_OPTS="${MEM_OPTS}"
echo "Using JVM opts: ${MEM_OPTS}"

generate_config() {
  local label="$1"
  local last_iter="$2"
  local outdir="$3"
  local stuck_time="$4"
  local use_capacity="$5"
  local reroute_weight="$6"
  local dest="${ROOT}/scenarios/equil/config_metro_0300_0618_100000_${label}.xml"
  python3 - "$BASE_CONFIG" "$dest" "$last_iter" "$outdir" "$stuck_time" "$use_capacity" "$reroute_weight" <<'PY'
import sys, xml.etree.ElementTree as ET
base, dest, last_iter, outdir, stuck_time, use_capacity, reroute_weight = sys.argv[1:]
last_iter = int(last_iter)
stuck_time = float(stuck_time)
reroute_weight = float(reroute_weight)
change_weight = round(1.0 - reroute_weight, 6)

tree = ET.parse(base)
root = tree.getroot()

def set_param(module_name, param_name, value):
    for mod in root.findall("module"):
        if mod.get("name") == module_name:
            for p in mod.findall("param"):
                if p.get("name") == param_name:
                    p.set("value", str(value))
                    return
            # if not found, create
            p = ET.SubElement(mod, "param")
            p.set("name", param_name)
            p.set("value", str(value))
            return

# Controller settings
set_param("controller", "outputDirectory", outdir)
set_param("controller", "lastIteration", last_iter)
set_param("controller", "writeEventsInterval", max(1, last_iter))
set_param("controller", "writePlansInterval", max(1, last_iter))

# QSim
set_param("qsim", "stuckTime", stuck_time)

# SwissRailRaptor capacity toggle
set_param("swissRailRaptor", "useCapacityConstraints", str(use_capacity).lower())

# Replanning weights
for mod in root.findall("module"):
    if mod.get("name") == "replanning":
        for ps in mod.findall("parameterset"):
            if ps.get("type") != "strategysettings":
                continue
            name = ps.find("param[@name='strategyName']")
            weight = ps.find("param[@name='weight']")
            if name is None or weight is None:
                continue
            if name.get("value") == "ChangeExpBeta":
                weight.set("value", str(change_weight))
            elif name.get("value") == "ReRoute":
                weight.set("value", str(reroute_weight))

# Write with DOCTYPE
xml_bytes = ET.tostring(root, encoding="utf-8")
xml_header = b'<?xml version="1.0" encoding="UTF-8"?>\n'
doctype = b'<!DOCTYPE config SYSTEM "http://www.matsim.org/files/dtd/config_v2.dtd">\n'
with open(dest, "wb") as f:
    f.write(xml_header)
    f.write(doctype)
    f.write(xml_bytes)
print(f"Generated config: {dest}")
PY
}

run_variant() {
  local label="$1"
  local last_iter outdir stuck_time use_capacity reroute_weight
  case "$label" in
    v1)
      last_iter=100
      outdir="${ROOT}/scenarios/equil/100000_output_v1"
      stuck_time=3600
      use_capacity=false
      reroute_weight=0.1
      ;;
    v2)
      last_iter=500
      outdir="${ROOT}/scenarios/equil/100000_output_v2"
      stuck_time=7200
      use_capacity=true
      reroute_weight=0.3
      ;;
    *)
      echo "Unknown variant: $label (expected v1 or v2)" >&2
      exit 1
      ;;
  esac
  generate_config "$label" "$last_iter" "$outdir" "$stuck_time" "$use_capacity" "$reroute_weight"
  local cfg="${ROOT}/scenarios/equil/config_metro_0300_0618_100000_${label}.xml"
  "${RUNNER}" "${cfg}"
}

if [[ $# -eq 0 ]]; then
  # Run both variants
  run_variant v1
  run_variant v2
else
  for v in "$@"; do
    run_variant "$v"
  done
fi
