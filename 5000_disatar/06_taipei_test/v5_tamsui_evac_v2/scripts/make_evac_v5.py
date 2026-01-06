import argparse, gzip, math
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

def weighted_quantile(values, quantiles, sample_weight=None):
    values = np.asarray(values, dtype=float)
    quantiles = np.asarray(quantiles, dtype=float)
    if sample_weight is None:
        sample_weight = np.ones(len(values), dtype=float)
    else:
        sample_weight = np.asarray(sample_weight, dtype=float)
    sorter = np.argsort(values)
    values = values[sorter]
    sample_weight = sample_weight[sorter]
    cdf = np.cumsum(sample_weight) - 0.5 * sample_weight
    cdf /= np.sum(sample_weight)
    return np.interp(quantiles, cdf, values)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("events_gz", help="path to output_events.xml.gz")
    ap.add_argument("--outdir", default=".", help="output directory")
    ap.add_argument("--cells", type=int, default=10, help="grid cells per side (N)")
    ap.add_argument("--epsg", default="EPSG:3857", help="CRS string written to .xyt.csv header")
    ap.add_argument("--base_time", type=float, default=0.0, help="seconds offset for plotting (e.g., 25200 for 07:00)")
    args = ap.parse_args()

    pre = {}   # person -> (x,y,time)
    post = {}  # person -> (x,y,time)
    arrival = {}  # person -> time

    print(f"Reading events from {args.events_gz}...")
    with gzip.open(args.events_gz, "rb") as f:
        for ev, el in ET.iterparse(f, events=("end",)):
            if el.tag != "event":
                continue
            typ = el.attrib.get("type")
            pid = el.attrib.get("person")
            # Patch for v5: home -> pre-evac, evacuation -> post-evac
            if typ == "actend" and el.attrib.get("actType") == "home":
                pre[pid] = (float(el.attrib["x"]), float(el.attrib["y"]), float(el.attrib["time"]))
            elif typ == "actstart" and el.attrib.get("actType") == "evacuation":
                post[pid] = (float(el.attrib["x"]), float(el.attrib["y"]), float(el.attrib["time"]))
            elif typ == "arrival" and pid is not None and pid not in arrival:
                arrival[pid] = float(el.attrib["time"])
            el.clear()

    print(f"Found {len(pre)} 'home' ends, {len(post)} 'evacuation' starts, {len(arrival)} arrivals.")

    rows = []
    for pid, (sx, sy, st) in pre.items():
        if pid not in post:
            continue
        ex, ey, et = post[pid]
        at = arrival.get(pid, et)
        evac_time = at - st
        rows.append((pid, sx, sy, ex, ey, st, at, evac_time))

    df = pd.DataFrame(rows, columns=[
        "person","start_x","start_y","end_x","end_y","start_time","arrival_time","evac_time_s"
    ])
    if df.empty:
        print("No matched 'home'/'evacuation' pairs found in events. Check if simulation ran long enough for agents to arrive at destinations.")
        return

    print(f"Matched {len(df)} agents. Generating outputs to {args.outdir}...")

    # 1) O/D points for hexagons
    df[["person","start_x","start_y","end_x","end_y","evac_time_s"]].to_csv(f"{args.outdir}/evac_od.csv", index=False)

    # 2) cumulative curve
    curve = df[["arrival_time"]].copy()
    curve["time_s"] = curve["arrival_time"] - args.base_time
    curve = curve.sort_values("time_s")
    curve["agents"] = np.arange(1, len(curve)+1)
    curve[["time_s","agents"]].to_csv(f"{args.outdir}/evac_cumulative.csv", index=False)

    # 3) flow per minute
    rate = df[["arrival_time"]].copy()
    rate["time_s"] = rate["arrival_time"] - args.base_time
    rate["minute"] = np.floor(rate["time_s"] / 60).astype(int)
    rate = rate.groupby("minute").size().reset_index(name="arrivals")
    rate["time_s"] = rate["minute"] * 60
    rate[["time_s","arrivals"]].to_csv(f"{args.outdir}/evac_rate_per_min.csv", index=False)

    # 4) grid mean evacuation time
    N = args.cells
    sx = df["start_x"].to_numpy()
    sy = df["start_y"].to_numpy()
    if len(sx) > 0:
        xmin, xmax = sx.min(), sx.max()
        ymin, ymax = sy.min(), sy.max()
        padx = (xmax - xmin) * 0.02 if xmax > xmin else 100
        pady = (ymax - ymin) * 0.02 if ymax > ymin else 100
        xmin -= padx; xmax += padx; ymin -= pady; ymax += pady
        
        width = xmax - xmin
        height = ymax - ymin
        if width == 0: width = 1
        if height == 0: height = 1

        dx = width / N
        dy = height / N
        ix = np.clip(((sx - xmin) / dx).astype(int), 0, N-1)
        iy = np.clip(((sy - ymin) / dy).astype(int), 0, N-1)

        df2 = df.copy()
        df2["ix"] = ix
        df2["iy"] = iy
        cell = df2.groupby(["ix","iy"]).agg(
            mean_evac=("evac_time_s","mean"),
            agents=("person","count"),
        ).reset_index()
        cell["x"] = xmin + (cell["ix"] + 0.5) * dx
        cell["y"] = ymin + (cell["iy"] + 0.5) * dy
        xyt = cell[["x","y","mean_evac"]].copy()
        xyt.insert(0, "time", 0.0)
        xyt.columns = ["time","x","y","value"]

        with open(f"{args.outdir}/evac_time_grid.xyt.csv","w",encoding="utf-8") as f:
            f.write(f"# {args.epsg}\n")
            xyt.to_csv(f, index=False)

    # 5) bins table
    vals = df["evac_time_s"].to_numpy()
    qs = weighted_quantile(vals, [0.2,0.4,0.6,0.8])
    bps = []
    last = -1e18
    for v in map(float, qs):
        if v > last + 1e-9:
            bps.append(v); last = v
    if not bps: bps = [vals.mean()] if len(vals) > 0 else [0]
    
    bps = bps[:4]
    edges = [0.0] + bps + [float("inf")]
    labels = [f"> {edges[i]:.0f}s" for i in range(len(edges)-1)]
    
    try:
        df["bin"] = pd.cut(df["evac_time_s"], bins=edges, right=False, labels=labels)
        bins = df.groupby("bin", observed=True).agg(
            agents=("person","count"),
            mean_evac_s=("evac_time_s","mean"),
        ).reset_index()
        bins["pct"] = bins["agents"] / bins["agents"].sum()
        bins.to_csv(f"{args.outdir}/evac_bins.csv", index=False)
    except Exception as e:
        print(f"Error creating bins: {e}")

    # 6) dashboard yaml
    import yaml
    dash = {
        "header": {
            "tab": "Evacuation",
            "title": "Evacuation summary (v5 Tamsui)",
            "description": "Grid mean evacuation time + cumulative curve + arrivals per minute + O/D density + bins table"
        },
        "layout": {
            "row1": [
                {
                    "type": "xytime",
                    "title": "Evacuation time (mean by origin cell)",
                    "height": 12.0,
                    "radius": 40,
                    "breakpoints": bps,
                    "file": "evac_time_grid.xyt.csv"
                },
                {
                    "type": "line",
                    "title": "Cumulative evacuated agents",
                    "dataset": "evac_cumulative.csv",
                    "x": "time_s",
                    "columns": ["agents"],
                    "xAxisName": "time (s)",
                    "yAxisName": "agents"
                },
                {
                    "type": "bar",
                    "title": "Arrivals per minute (evacuation flow)",
                    "dataset": "evac_rate_per_min.csv",
                    "x": "time_s",
                    "columns": ["arrivals"],
                    "xAxisName": "time (s)",
                    "yAxisName": "arrivals/min"
                }
            ],
            "row2": [
                {
                    "type": "hexagons",
                    "title": "Origin / Safe density (counts)",
                    "height": 12.0,
                    "file": "evac_od.csv",
                    "projection": args.epsg,
                    "radius": 200,
                    "aggregations": {
                        "OD": [
                            {"title": "Origins", "x": "start_x", "y": "start_y"},
                            {"title": "Safe", "x": "end_x", "y": "end_y"}
                        ]
                    }
                },
                {
                    "type": "csv",
                    "title": "Evacuation time bins (agents)",
                    "dataset": "evac_bins.csv",
                    "enableFilter": True
                }
            ]
        }
    }
    with open(f"{args.outdir}/dashboard-evacuation.yml","w",encoding="utf-8") as f:
        yaml.safe_dump(dash, f, sort_keys=False, allow_unicode=True)
    
    print("Done.")

if __name__ == "__main__":
    main()
