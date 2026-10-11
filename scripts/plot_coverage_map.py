"""遊び場ごとに、50 m 以内の Mapillary 画像の有無を地図に打つ（記事用）。

使い方: python3 scripts/plot_coverage_map.py <出力PNG>
背景地図は入れない（点の分布だけ）。凡例の数は data/mapillary_coverage.jsonl から数える。
"""
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

from mapillary_summary import DATA, facing

for f in ("Hiragino Sans", "Hiragino Maru Gothic ProN"):
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = f
        break

rows = [json.loads(l) for l in (DATA / "mapillary_coverage.jsonl").read_text().splitlines() if l]
groups = {"none": [], "any": [], "facing": []}
for r in rows:
    near = [h for h in r["hits"] if h["dist"] <= 50]
    k = "facing" if any(facing(h) for h in near) else "any" if near else "none"
    groups[k].append((r["lon"], r["lat"]))

n = len(rows)
fig, ax = plt.subplots(figsize=(10, 7.5), dpi=150)
style = {
    "none": dict(c="#c9d3d5", s=6, marker="o", label=f"50 m 以内に画像なし（{len(groups['none']):,}）"),
    "any": dict(c="#a8703a", s=14, marker="^", label=f"画像はあるが遊び場を向いていない（{len(groups['any']):,}）"),
    "facing": dict(c="#0f5b66", s=16, marker="s", label=f"遊び場を向いた画像あり（{len(groups['facing']):,}）"),
}
for k in ("none", "any", "facing"):
    if groups[k]:
        xs, ys = zip(*groups[k])
        ax.scatter(xs, ys, linewidths=0, **style[k])
ax.set_aspect(1 / 0.653)  # 北緯 49 度付近の経度の縮み
ax.set_xlabel("経度")
ax.set_ylabel("緯度")
ax.set_title(f"Metro Vancouver の遊び場 {n:,} か所と、半径 50 m 以内の Mapillary 画像", fontsize=13)
ax.legend(loc="upper right", frameon=True, fontsize=10)
ax.grid(color="#eeeeee", linewidth=0.6)
fig.tight_layout()
fig.savefig(sys.argv[1])
print({k: len(v) for k, v in groups.items()})
