"""City of Vancouver のオープンデータから、CollectionBuilder 用の CSV を作る。

入力（data/opendata/ に置く。取得は下の URL を curl で）:
  parks.json            https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/parks/exports/json
  parks-facilities.json https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/parks-facilities/exports/json

出力: collection/playgrounds.csv（遊び場のある公園 1 つにつき 1 行。遊具の欄は現地調査で埋める）

オープンデータには遊び場ごとの位置が無く、公園ごとの数（facilitycount）しか無い。
そのため 1 行 = 1 公園とし、遊び場の数は playground_count に入れる。
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "opendata"
OUT = ROOT / "collection" / "playgrounds.csv"

# CollectionBuilder-CSV の標準の欄 + この案件で足す欄
FIELDS = [
    "objectid", "title", "description", "location", "latitude", "longitude",
    "subject", "type", "display_template", "source", "rights",
    "parkid", "neighbourhood", "playground_count", "hectare", "washrooms",
    "equipment", "surveyed",
]

RIGHTS = "Contains information licensed under the Open Government Licence – Vancouver"
SOURCE = "City of Vancouver Open Data: parks, parks-facilities (retrieved 2026-10-11)"


def main():
    parks = {p["parkid"]: p for p in json.load(open(SRC / "parks.json"))}
    facilities = json.load(open(SRC / "parks-facilities.json"))

    by_park = {}
    for f in facilities:
        by_park.setdefault(f["parkid"], []).append(f)

    rows = []
    for parkid, fs in by_park.items():
        pg = [f for f in fs if f["facilitytype"] == "Playgrounds"]
        if not pg:
            continue
        p = parks[parkid]
        count = sum(f["facilitycount"] for f in pg)
        others = sorted(f["facilitytype"] for f in fs if f["facilitytype"] != "Playgrounds")
        address = " ".join(x for x in [p.get("streetnumber"), p.get("streetname")] if x)
        geo = p.get("googlemapdest") or {}
        noun = "playground" if count == 1 else "playgrounds"
        rows.append({
            "objectid": f"park{parkid:03d}",
            "title": p["name"],
            "description": f"{count} {noun} in {p['name']} ({p['neighbourhoodname']}). Equipment not yet surveyed.",
            "location": f"{address}, Vancouver, BC" if address else "Vancouver, BC",
            "latitude": geo.get("lat", ""),
            "longitude": geo.get("lon", ""),
            # CollectionBuilder の絞り込み（subject）に、公園の他の施設を入れる
            "subject": ";".join(others),
            "type": "Place",
            "display_template": "record",
            "source": SOURCE,
            "rights": RIGHTS,
            "parkid": parkid,
            "neighbourhood": p["neighbourhoodname"],
            "playground_count": count,
            "hectare": p.get("hectare", ""),
            "washrooms": p.get("washrooms", ""),
            "equipment": "",
            "surveyed": "",
        })

    rows.sort(key=lambda r: r["title"])
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} parks, {sum(r['playground_count'] for r in rows)} playgrounds -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
