"""OSM の遊び場（leisure=playground）と市のデータ（parks-facilities の Playgrounds）を突き合わせる。

一時スクリプト。docs/notes/coverage.md の「2026-10-12 検討: OSM にあって市のデータに無い遊び場」の数を再現する。

使い方: python3 scripts/compare_osm_city.py [--refresh]
入力:   data/opendata/parks.json, parks-facilities.json（build_cb_csv.py と同じ）
        OSM はバンクーバー市の境界・公園・学校・遊び場を Overpass から取り、data/cache/osm_compare.json に置く
        （--refresh で取り直す）

分け方:
  1. 市の境界を囲む長方形の中の OSM の遊び場を、OSM の公園（leisure=park）・学校（amenity=school）の区画の中にあるかで分ける
  2. 公園の中のものは、市の遊び場のある公園の点から MATCH_M 以内か、区画の名前が市の公園名と一致すれば「市にある」
  3. 残りを市の公園一覧（parks、遊び場の有無を問わない）と名前・位置で合わせ、
     市の公園なのに遊び場の一覧に無いものを出す。位置で合わせるのは名前の無い区画だけ。市の外かは境界で判定
"""
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union, polygonize

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "opendata"
CACHE = ROOT / "data" / "cache" / "osm_compare.json"
UA = "playground-search-research/0.1"
CITY = 3600000000 + 1852574  # City of Vancouver（admin_level=8）
MATCH_M = 350


def overpass(q):
    body = urllib.parse.urlencode({"data": q}).encode()
    for i in range(4):
        req = urllib.request.Request("https://overpass-api.de/api/interpreter", body, {"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)["elements"]
        except urllib.error.HTTPError as err:
            if err.code not in (429, 504) or i == 3:
                raise
            time.sleep(30 * (i + 1))


def fetch():
    # 境界の内外を見比べられるよう、遊び場・区画は市より少し広い範囲で取る
    bbox = "49.18,-123.30,49.36,-122.98"
    data = {
        "city": overpass(f"[out:json][timeout:120];rel({CITY - 3600000000});out geom;"),
        "playgrounds": overpass(f'[out:json][timeout:120];nwr["leisure"="playground"]({bbox});out center tags;'),
        "parks": overpass(f'[out:json][timeout:180];(way["leisure"="park"]({bbox});rel["leisure"="park"]({bbox}););out geom tags;'),
        "schools": overpass(f'[out:json][timeout:180];(way["amenity"="school"]({bbox});rel["amenity"="school"]({bbox}););out geom tags;'),
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data))
    return data


def shape(e):
    """way / relation（out geom）を shapely の面にする。面にならなければ None。"""
    if e["type"] == "way":
        pts = [(g["lon"], g["lat"]) for g in e.get("geometry", [])]
        return Polygon(pts).buffer(0) if len(pts) >= 4 and pts[0] == pts[-1] else None
    ways = [m for m in e.get("members", []) if m["type"] == "way" and m.get("geometry")]
    outer = [[(g["lon"], g["lat"]) for g in m["geometry"]] for m in ways if m["role"] != "inner"]
    inner = [[(g["lon"], g["lat"]) for g in m["geometry"]] for m in ways if m["role"] == "inner"]
    o = unary_union(list(polygonize(outer)))
    if o.is_empty:
        return None
    i = unary_union(list(polygonize(inner)))
    return o.difference(i) if not i.is_empty else o


def areas(elems):
    out = []
    for e in elems:
        s = shape(e)
        if s is not None and not s.is_empty:
            out.append((s, e.get("tags", {}).get("name", "")))
    return out


def norm(name):
    n = name.lower().replace("’", "'")
    n = re.sub(r"\bst\b\.?", "street", n)
    n = re.sub(r"\b(park|the|neighbourhood|community|at|on)\b", " ", n)
    return re.sub(r"[^a-z0-9]+", " ", n).strip()


def dist_m(lat1, lon1, lat2, lon2):
    x = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    y = math.radians(lat2 - lat1)
    return 6371000 * math.hypot(x, y)


def containing(pt, polys):
    """pt を含む区画のうち、いちばん小さいものの名前（無ければ None）。"""
    hits = [(s.area, name) for s, name in polys if s.contains(pt)]
    return min(hits)[1] if hits else None


def main():
    data = fetch() if "--refresh" in sys.argv or not CACHE.exists() else json.loads(CACHE.read_text())
    city = shape(data["city"][0])
    env = city.envelope
    parks_osm = areas(data["parks"])
    schools = areas(data["schools"])

    parks = json.load(open(SRC / "parks.json"))
    fac = json.load(open(SRC / "parks-facilities.json"))
    pg_ids = {r["parkid"] for r in fac if r["facilitytype"] == "Playgrounds"}
    city_pg = [p for p in parks if p["parkid"] in pg_ids and p.get("googlemapdest")]
    city_pg_names = {norm(p["name"]) for p in city_pg}
    print(f"市の遊び場: {len(pg_ids)} 公園・{sum(r['facilitycount'] for r in fac if r['facilitytype'] == 'Playgrounds')} か所")

    rows = []
    for e in data["playgrounds"]:
        c = e.get("center") or e
        pt = Point(c["lon"], c["lat"])
        park = containing(pt, parks_osm)
        school = None if park is not None else containing(pt, schools)
        rows.append({"osm": f"{e['type']}/{e['id']}", "lat": c["lat"], "lon": c["lon"],
                     "tags": e.get("tags", {}), "park": park, "school": school,
                     "in_city": city.contains(pt)})
    # 「市内」は市の境界を囲む長方形。ノースバンクーバーの海沿いやリッチモンドの一部も入る（後で境界で分ける）
    inside = [r for r in rows if env.contains(Point(r["lon"], r["lat"]))]
    in_park = [r for r in inside if r["park"] is not None]
    in_school = [r for r in inside if r["park"] is None and r["school"] is not None]
    other = [r for r in inside if r["park"] is None and r["school"] is None]
    print(f"市内の OSM の遊び場 {len(inside)} 点（取得 {len(rows)}）: 公園の中 {len(in_park)}、学校の中 {len(in_school)}、どちらでもない {len(other)}")
    print(f"学校: {len({r['school'] for r in in_school})} 校・{len(in_school)} 点")
    private = [r for r in other if r["tags"].get("access") in ("private", "customers", "no", "permissive")]
    print(f"どちらでもないうち access=private 等: {len(private)} 点")

    def near_city_pg(r):
        return min(dist_m(r["lat"], r["lon"], p["googlemapdest"]["lat"], p["googlemapdest"]["lon"]) for p in city_pg)

    missing = [r for r in in_park if not (near_city_pg(r) <= MATCH_M or norm(r["park"] or "") in city_pg_names)]
    print(f"公園で市のデータに無いもの {len(missing)} 点")

    # 市の公園一覧（遊び場の有無を問わない）と名前・位置で合わせる
    by_name = {norm(p["name"]): p for p in parks}
    result = {}
    for r in missing:
        # 名前のある区画は名前だけで合わせる（Rainbow Park の点は Yaletown Park の点から 200 m で、位置で合わせると取り違える）
        p = by_name.get(norm(r["park"])) if r["park"] else None
        if p is None and not r["park"]:
            near = min((p for p in parks if p.get("googlemapdest")),
                       key=lambda p: dist_m(r["lat"], r["lon"], p["googlemapdest"]["lat"], p["googlemapdest"]["lon"]))
            d = dist_m(r["lat"], r["lon"], near["googlemapdest"]["lat"], near["googlemapdest"]["lon"])
            if d <= MATCH_M:
                p = near
        if p:
            key = ("city", p["name"])
        elif not r["in_city"]:
            key = ("outside", r["park"] or f"(名前なし) {r['lat']:.5f},{r['lon']:.5f}")
        else:
            key = ("other", r["park"] or f"(名前なし) {r['lat']:.5f},{r['lon']:.5f}")
        result.setdefault(key, []).append(r)

    city_parks = sorted(k[1] for k in result if k[0] == "city")
    print(f"\n市の公園なのに遊び場の一覧に無い: {len(city_parks)} 公園")
    for n in city_parks:
        print(f"  {n}（{len(result[('city', n)])} 点）")
    print(f"\n市の外: {len([k for k in result if k[0] == 'outside'])} 公園")
    for k in sorted(k for k in result if k[0] == "outside"):
        print(f"  {k[1]}（{len(result[k])} 点）")
    print("\n市内だが市の公園一覧に無いもの:")
    for k in sorted(k for k in result if k[0] == "other"):
        print(f"  {k[1]}（{len(result[k])} 点）")
    return result


if __name__ == "__main__":
    main()
