"""遊び場ごとに、近くに位置情報付きの Commons 画像が何枚あるかを数える。

使い方: python3 scripts/commons_coverage.py [半径m=50]
入力:   data/osm_playgrounds.json
出力:   data/commons_coverage.json（遊び場ごとの画像タイトルと距離）

遊び場の位置は OSM の中心点。広い遊び場では端の写真を取りこぼす。
"""
import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "playground-search-research/0.1 (https://github.com/nakamura196)"
DATA = pathlib.Path(__file__).resolve().parent.parent / "data"


def geosearch(lat, lon, radius):
    q = urllib.parse.urlencode({
        "action": "query", "list": "geosearch", "gscoord": f"{lat}|{lon}",
        "gsradius": radius, "gslimit": 100, "gsnamespace": 6, "format": "json",
    })
    req = urllib.request.Request(f"https://commons.wikimedia.org/w/api.php?{q}", headers={"User-Agent": UA})
    for i in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)["query"]["geosearch"]
        except urllib.error.HTTPError as e:
            time.sleep(int(e.headers.get("Retry-After") or 30 * (i + 1)))
        except Exception:
            time.sleep(10 * (i + 1))
    raise RuntimeError(f"geosearch failed at {lat},{lon}")


def main():
    radius = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    pgs = json.loads((DATA / "osm_playgrounds.json").read_text())
    out = []
    for i, p in enumerate(pgs):
        hits = geosearch(p["lat"], p["lon"], radius)
        out.append({"osm": p["osm"], "lat": p["lat"], "lon": p["lon"],
                    "hits": [{"title": h["title"], "dist": h["dist"]} for h in hits]})
        if i % 200 == 0:
            print(i, len(pgs), flush=True)
        time.sleep(1)
    (DATA / "commons_coverage.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    n = sum(1 for o in out if o["hits"])
    print(f"radius={radius} playgrounds={len(out)} with_any_image={n}")


if __name__ == "__main__":
    main()
