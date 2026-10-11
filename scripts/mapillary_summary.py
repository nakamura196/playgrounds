"""data/mapillary_coverage.jsonl を集計する。

使い方: python3 scripts/mapillary_summary.py
「向いている」= カメラの向きと遊び場への方角の差が 45 度以内、または 360 度写真。
"""
import json
import pathlib
import statistics

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"


def facing(h):
    return h["is_pano"] or h.get("camera_type") in ("spherical", "equirectangular") or (h["facing_diff"] is not None and h["facing_diff"] <= 45)


def main():
    rows = [json.loads(l) for l in (DATA / "mapillary_coverage.jsonl").read_text().splitlines() if l]
    n = len(rows)
    print(f"playgrounds={n} truncated={sum(r['truncated'] for r in rows)}")
    for r_m in (10, 25, 50, 100):
        any_ = [r for r in rows if any(h["dist"] <= r_m for h in r["hits"])]
        fac = [r for r in rows if any(h["dist"] <= r_m and facing(h) for h in r["hits"])]
        cnt = [sum(h["dist"] <= r_m for h in r["hits"]) for r in any_]
        med = statistics.median(cnt) if cnt else 0
        print(f"<= {r_m:3d} m: any {len(any_):4d} ({len(any_)/n:5.1%})  facing {len(fac):4d} ({len(fac)/n:5.1%})  median images where any {med}")
    hits50 = [h for r in rows for h in r["hits"] if h["dist"] <= 50]
    print(f"images <=50m: {len(hits50)}  pano {sum(bool(h['is_pano']) for h in hits50)}")
    years = {}
    for r in rows:
        ys = [h["captured_at"] for h in r["hits"] if h["dist"] <= 50 and h["captured_at"]]
        if ys:
            y = __import__("datetime").datetime.utcfromtimestamp(max(ys) / 1000).year
            years[y] = years.get(y, 0) + 1
    print("newest image year (<=50m):", dict(sorted(years.items())))


if __name__ == "__main__":
    main()
