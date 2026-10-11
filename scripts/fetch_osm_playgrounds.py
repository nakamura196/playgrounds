"""Metro Vancouver の遊び場（leisure=playground）と遊具（playground=*）を OSM から取る。

使い方: python3 scripts/fetch_osm_playgrounds.py
出力:   data/osm_playgrounds.json, data/osm_equipment.json
"""
import json
import pathlib
import urllib.parse
import urllib.request

AREA = 3600000000 + 2218280  # Metro Vancouver Regional District
UA = "playground-search-research/0.1"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data"


def overpass(q):
    body = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request("https://overpass-api.de/api/interpreter", body, {"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["elements"]


def point(e):
    c = e.get("center") or e
    return c["lat"], c["lon"]


def main():
    OUT.mkdir(exist_ok=True)
    pgs = overpass(f'[out:json][timeout:240];area({AREA})->.a;nwr(area.a)["leisure"="playground"];out center tags;')
    eq = overpass(f'[out:json][timeout:240];area({AREA})->.a;nwr(area.a)["playground"];out center tags;')
    rows = [{"osm": f"{e['type']}/{e['id']}", "lat": point(e)[0], "lon": point(e)[1], "tags": e.get("tags", {})} for e in pgs]
    eqs = [{"osm": f"{e['type']}/{e['id']}", "lat": point(e)[0], "lon": point(e)[1], "tags": e.get("tags", {})} for e in eq]
    (OUT / "osm_playgrounds.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    (OUT / "osm_equipment.json").write_text(json.dumps(eqs, ensure_ascii=False, indent=1))
    print(f"playgrounds={len(rows)} equipment={len(eqs)}")


if __name__ == "__main__":
    main()
