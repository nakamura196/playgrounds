"""遊び場ごとに、近くに Mapillary の画像が何枚あるかを数える。

使い方: MAPILLARY_TOKEN=... python3 scripts/mapillary_coverage.py [半径m=100]
        （鍵は 1Password から: op run --env-file=.env.local -- python3 scripts/mapillary_coverage.py）
入力:   data/osm_playgrounds.json
出力:   data/mapillary_coverage.jsonl（1 行 1 遊び場。途中で止めても続きから再開する）

遊び場の位置は OSM の中心点。半径の正方形で API に問い合わせ、円の内側だけ残す。
画像ごとに、撮影位置から遊び場への方角とカメラの向きの差（facing_diff, 度）も残す。
360 度写真（is_pano）は向きに関係なく写りうる。
"""
import json
import math
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
OUT = DATA / "mapillary_coverage.jsonl"
LIMIT = 2000  # API の 1 回あたりの上限
FIELDS = "id,geometry,captured_at,compass_angle,is_pano,camera_type"


def dist_bearing(lat1, lon1, lat2, lon2):
    """点 1 から点 2 への距離 (m) と方角 (度, 北=0 時計回り)。"""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    d = 2 * 6371008.8 * math.asin(math.sqrt(a))
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return d, (math.degrees(math.atan2(y, x)) + 360) % 360


def query(token, bbox):
    q = urllib.parse.urlencode({"fields": FIELDS, "limit": LIMIT, "bbox": ",".join(map(str, bbox))})
    req = urllib.request.Request(f"https://graph.mapillary.com/images?{q}",
                                 headers={"Authorization": f"OAuth {token}"})
    for i in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)["data"]
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise
            if e.code == 500 and b"reduce the amount" in e.read():
                # 写真が密集した場所。範囲を 4 つに分けて問い合わせ直す
                w, s, e_, n = bbox
                mx, my = (w + e_) / 2, (s + n) / 2
                return [im for b in ((w, s, mx, my), (mx, s, e_, my), (w, my, mx, n), (mx, my, e_, n))
                        for im in query(token, b)]
            time.sleep(int(e.headers.get("Retry-After") or 15 * (i + 1)))
        except Exception:
            time.sleep(10 * (i + 1))
    raise RuntimeError(f"search failed at {bbox}")


def search(token, lat, lon, radius):
    dlat = radius / 111320
    dlon = radius / (111320 * math.cos(math.radians(lat)))
    return query(token, (lon - dlon, lat - dlat, lon + dlon, lat + dlat))


def main():
    radius = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    token = os.environ["MAPILLARY_TOKEN"].strip()
    pgs = json.loads((DATA / "osm_playgrounds.json").read_text())
    done = set()
    if OUT.exists():
        done = {json.loads(l)["osm"] for l in OUT.read_text().splitlines() if l}
    with OUT.open("a") as f:
        for i, p in enumerate(pgs):
            if p["osm"] in done:
                continue
            raw = search(token, p["lat"], p["lon"], radius)
            hits = []
            for im in raw:
                lon, lat = im["geometry"]["coordinates"]
                d, b = dist_bearing(lat, lon, p["lat"], p["lon"])
                if d > radius:
                    continue
                ca = im.get("compass_angle")
                diff = None if ca is None else round(abs((b - ca + 180) % 360 - 180), 1)
                hits.append({"id": im["id"], "dist": round(d, 1), "facing_diff": diff,
                             "captured_at": im.get("captured_at"), "is_pano": im.get("is_pano"),
                             "camera_type": im.get("camera_type")})
            f.write(json.dumps({"osm": p["osm"], "lat": p["lat"], "lon": p["lon"], "radius": radius,
                                "truncated": len(raw) >= LIMIT, "hits": hits}) + "\n")
            f.flush()
            if i % 200 == 0:
                print(i, len(pgs), flush=True)
            time.sleep(0.2)
    print("done")


if __name__ == "__main__":
    main()
