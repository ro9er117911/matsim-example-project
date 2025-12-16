#!/usr/bin/env python3
"""
Generate SimWrapper Dashboard YAMLs.
Implements the fixes for Dashboard 1 (Map), Dashboard 4 (Table), and Dashboard 3 (Columns).
Also moves text descriptions to external .md files to avoid SimWrapper errors.
Usage: python3 generate_dashboard_yamls.py --output_dir output
"""

import argparse
import os
import yaml
import pandas as pd

NETWORK_GEOJSON = os.environ.get("NETWORK_GEOJSON", "network_wgs84_congestion.geojson")

def generate_yamls(output_dir):
    
    # Helper to write MD files
    def write_md(filename, content):
        with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
            f.write(content)
            
    # Helper to write YAML files
    def write_yaml(filename, data):
        with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    # ---------------------------------------------------------
    # 1. Dashboard 1 - Evacuation Performance
    # ---------------------------------------------------------
    desc1 = """### 1. 撤離成效分析
- **左圖**：撤離完成率曲線。
- **中圖**：平均撤離時間地圖。
- **右圖**：撤離時間分級。
"""
    write_md("dashboard-1-desc.md", desc1)
    
    yaml1 = {
        "header": {
            "title": "1. 撤離成效 (Evacuation Performance)",
            "description": "撤離完成率、空間分佈與時間分級",
            "thumbnail": "modestats.png"
        },
        "layout": {
            "Description": [{
                "type": "text",
                "title": "撤離績效分析",
                "file": "dashboard-1-desc.md"
            }],
            "Charts": [
                {
                    "type": "line",
                    "width": 1,
                    "title": "撤離完成率 (Cumulative)",
                    "dataset": "evac_cumulative.csv",
                    "x": "minute",
                    "columns": ["cumulative_agents"],
                    "legendName": ["Agents"],
                    "xAxisName": "Time (min)",
                    "yAxisName": "Count"
                },
                {
                    "type": "bar",
                    "width": 1,
                    "title": "撤離時間分級",
                    "dataset": "evac_bins.csv",
                    "x": "range",
                    "columns": ["count"],
                    "xAxisName": "Bin",
                    "yAxisName": "Agents"
                }
            ],
            "Map": [
                {
                    "type": "map",
                    "width": 2,
                    "title": "平均撤離時間地圖",
                    "description": "Average Evacuation Time",
                    "center": [121.43, 25.18],
                    "zoom": 12,
                    "datasets": {
                         "grid": "evac_time_grid.csv"
                    },
                    "display": {
                         "pointColor": {
                             "dataset": "grid",
                             "columnName": "evac_duration_min",
                             "colorRamp": { "ramp": "Spectral", "steps": 10, "reverse": True }
                         },
                         "pointRadius": {
                              "dataset": "grid",
                              "columnName": "evac_duration_min",
                              "scaleFactor": 50
                         },
                         "fill": {},
                         "fillHeight": {},
                         "radius": {}
                    },
                    "shapes": {
                         "file": NETWORK_GEOJSON,
                         "join": "id"
                    }
                }
            ]
        }
    }
    write_yaml("dashboard-1.yaml", yaml1)

    # ---------------------------------------------------------
    # 2. Dashboard 2 - Traffic Bottlenecks
    # ---------------------------------------------------------
    desc2 = """### 2. 交通瓶頸地圖
顯示 V/C Ratio (Volume / Capacity) > 1.0 的嚴重擁塞路段。
"""
    write_md("dashboard-2-desc.md", desc2)

    yaml2 = {
        "header": {
            "title": "2. 交通瓶頸 (Traffic Bottlenecks)",
            "description": "擁塞熱點",
            "thumbnail": "modestats.png"
        },
        "layout": {
             "Description": [{
                "type": "text",
                "title": "交通擁塞熱圖",
                "file": "dashboard-2-desc.md"
            }],
            "Map_0300_0315": [
                {
                    "type": "map",
                    "title": "03:00-03:15",
                    "height": 10,
                    "datasets": {"congestion": "link_congestion_0300_0315.csv"},
                    "display": {
                        "lineColor": {
                            "dataset": "congestion",
                            "columnName": "v_c",
                            "join": "linkId",
                            "colorRamp": {"ramp": "Magma", "steps": 5}
                        },
                        "lineWidth": {
                            "dataset": "congestion",
                            "columnName": "v_c",
                            "join": "linkId",
                            "scaleFactor": 10
                        },
                        "fill": {}, "fillHeight": {}, "radius": {}
                    },
                    "shapes": {"file": NETWORK_GEOJSON, "join": "id"}
                }
            ],
            "Map_0315_0330": [
                {
                    "type": "map",
                    "title": "03:15-03:30",
                    "height": 10,
                    "datasets": {"congestion": "link_congestion_0315_0330.csv"},
                    "display": {
                        "lineColor": {
                            "dataset": "congestion",
                            "columnName": "v_c",
                            "join": "linkId",
                            "colorRamp": {"ramp": "Magma", "steps": 5}
                        },
                        "lineWidth": {
                            "dataset": "congestion",
                            "columnName": "v_c",
                            "join": "linkId",
                            "scaleFactor": 10
                        },
                        "fill": {}, "fillHeight": {}, "radius": {}
                    },
                    "shapes": {"file": NETWORK_GEOJSON, "join": "id"}
                }
            ]
        }
    }
    write_yaml("dashboard-2.yaml", yaml2)
    
    # ---------------------------------------------------------
    # 3. Dashboard 3 - Time Series
    # ---------------------------------------------------------
    desc3 = """### 3. 關鍵路段時序分析
針對 Top 10 最擁塞路段，分析其前 60 分鐘內的變化。
"""
    write_md("dashboard-3-desc.md", desc3)
    
    # Dynamic Columns Detection
    cols = []
    vc_file = os.path.join(output_dir, "bottleneck_curves_vc.csv")
    if os.path.exists(vc_file):
        try:
            df = pd.read_csv(vc_file)
            # All columns except 'time_min' and 'level_0'/'index' etc.
            cols = [c for c in df.columns if c not in ['time_min', 'index', 'Unnamed: 0']]
            print(f"Detected columns for D3: {cols}")
        except Exception as e:
            print(f"Warning: Could not read {vc_file}: {e}")
    else:
        print(f"Warning: {vc_file} missing. Using fallback.")
        
    # If cols empty, provide a fallback or dummy
    if not cols:
        cols = ["Value"] 
        
    yaml3 = {
        "header": { "title": "3. 關鍵斷面 (Key Sections)", "description": "Top 10 瓶頸時序", "thumbnail": "modestats.png"},
        "layout": {
            "Description": [{"type": "text", "title": "說明", "file": "dashboard-3-desc.md"}],
            "VC_Analysis": [
                {
                    "type": "line", "title": "V/C Ratio", "dataset": "bottleneck_curves_vc.csv",
                    "x": "time_min", "columns": cols, "xAxisName": "Time", "yAxisName": "V/C"
                }
            ],
            "TT_Analysis": [
                {
                    "type": "line", "title": "TT Ratio", "dataset": "bottleneck_curves_tt.csv",
                    "x": "time_min", "columns": cols, "xAxisName": "Time", "yAxisName": "Ratio"
                }
            ]
        }
    }
    write_yaml("dashboard-3.yaml", yaml3)
    
    # ---------------------------------------------------------
    # 4. Dashboard 4 - Policy Summary
    # ---------------------------------------------------------
    # Generate Markdown Table manually to avoid SimWrapper Table component issues
    summary_file = os.path.join(output_dir, "policy_summary_transposed.csv")
    md_table = "### 關鍵指標 (KPIs)\n\n| Metric | Value |\n|---|---|\n"
    
    if os.path.exists(summary_file):
        try:
            df = pd.read_csv(summary_file)
            for _, row in df.iterrows():
                md_table += f"| {row['Metric']} | {row['Value']} |\n"
        except:
            md_table += "| Error | Could not read data |\n"
    else:
        md_table += "| Error | File missing |\n"
        
    write_md("dashboard-4-table.md", md_table)
    
    desc4 = """### 4. 政策摘要
情境模擬結果摘要，包含平均撤離時間、P95 撤離時間與總撤離人數。
"""
    write_md("dashboard-4-desc.md", desc4)

    yaml4 = {
        "header": { "title": "4. 政策摘要 (Policy Summary)", "description": "KPIs", "thumbnail": "modestats.png"},
        "layout": {
             "Description": [{"type": "text", "title": "摘要", "file": "dashboard-4-desc.md"}],
             "Table": [
                 {
                     "type": "text",
                     "title": "KPIs Table",
                     "file": "dashboard-4-table.md"
                 }
             ]
        }
    }
    write_yaml("dashboard-4.yaml", yaml4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', required=True)
    args = parser.parse_args()
    generate_yamls(args.output_dir)
