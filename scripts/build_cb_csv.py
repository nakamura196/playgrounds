"""City of Vancouver のオープンデータから、CollectionBuilder 用の CSV を作る。

入力（data/opendata/ に置く。取得は下の URL を curl で）:
  parks.json            https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/parks/exports/json
  parks-facilities.json https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/parks-facilities/exports/json

手で書く表（collection/ に置く。市のデータを取り直しても消えない）:
  surveyed-parks.csv    市のデータに無い遊び場（UBC など）。位置は現地調査の写真の撮影地点
                        equipment は vocab/types.csv、amenities（水飲み場などの設備）は vocab/amenities.csv の id を ; で並べる
  osm-parks.csv         市の公園なのに、市の遊び場の一覧に無い公園（2026-10-13 に 17 公園）。
                        compare_osm_city.py で見つけ、Google マップの航空写真とクチコミの写真で遊具を確かめたもの。
                        位置は OSM の遊び場（leisure=playground）の点（2 点あれば平均）、playground_count は OSM の点の数。
                        公園名・住所・地区などは市の parks から取る。note / note_ja は説明文の末尾に足す
  photos.csv            現地調査の写真。1 枚 1 行。写真そのものは Wikimedia Commons に置き、ここには名前と
                        元の画像の幅・高さ（IIIF マニフェストに要る。Commons の imageinfo で調べた値）だけ書く

出力: collection/playgrounds.csv（遊び場のある公園 1 つにつき 1 行。遊具の欄は現地調査で埋める。
写真は親の公園の行のすぐ後に、parentid 付きの子の行として並べる）

オープンデータには遊び場ごとの位置が無く、公園ごとの数（facilitycount）しか無い。
そのため 1 行 = 1 公園とし、遊び場の数は playground_count に入れる。
"""
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import quote, urlencode

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "opendata"
OUT = ROOT / "collection" / "playgrounds.csv"

# CollectionBuilder-CSV の標準の欄 + この案件で足す欄
FIELDS = [
    "objectid", "title", "description", "location", "latitude", "longitude",
    "subject", "type", "display_template", "source", "rights",
    "parkid", "neighbourhood", "playground_count", "hectare", "washrooms",
    "equipment", "amenities", "surveyed",
    # 写真（CollectionBuilder の複数の画像を持つ記録 compound_object と、その子の行）
    "parentid", "format", "object_location", "image_small", "image_thumb", "image_alt_text",
    "rightsstatement", "commons", "image_width", "image_height",
    # 日本語の題名と説明（IIIF マニフェストで英語と並べる。市のデータの行には無い）
    "title_ja", "description_ja",
    # Commons の投稿画面を、分類・見出し・位置を入れた状態で開く URL（公園の行だけ）
    "commons_upload",
    # 現地調査の順（surveyed-parks.csv の行の順、3 桁）。トップの「最近調べた公園」を新しい順に並べる。
    # surveyed は月までしか無いので、同じ月の中の順はこれで決める
    "survey_seq",
    # 位置の出典にした OSM の要素（osm-parks.csv の行だけ。way/123;node/456）
    "osm",
]

RIGHTS = "Contains information licensed under the Open Government Licence – Vancouver"
SOURCE = "City of Vancouver Open Data: parks, parks-facilities (retrieved 2026-10-11)"

OSM_SOURCE = ("City of Vancouver Open Data: parks, parks-facilities (retrieved 2026-10-11); "
              "position: OpenStreetMap (© OpenStreetMap contributors, ODbL)")
OSM_RIGHTS = RIGHTS + "; position © OpenStreetMap contributors, ODbL"
# Google マップは確かめるのに使っただけ。写真や位置は持ち込まない（規約上、中身を転載できない）
OSM_CHECK = "Playground equipment confirmed from aerial imagery and review photos (2026-10)."
OSM_CHECK_JA = "航空写真とクチコミの写真で遊具を確認（2026-10）。"

SURVEY_SOURCE = "Own survey"
SURVEY_RIGHTS = "CC BY 4.0"
PHOTO_RIGHTS = "Photo: Satoru Nakamura (Wikimedia Commons User:Satoru196), CC BY 4.0"
CC_BY = "https://creativecommons.org/licenses/by/4.0/"
COMMONS = "https://commons.wikimedia.org/wiki/"
UPLOAD = "https://upload.wikimedia.org/wikipedia/commons/"
UPLOAD_WIZARD = "https://commons.wikimedia.org/wiki/Special:UploadWizard"
# サイト経由の投稿を集める分類（2026-10-11 作成、上位は Playgrounds in Vancouver）
SURVEY_CATEGORY = "Playground survey in Vancouver"


def commons_urls(name):
    """Commons のファイル名から、ページ・元画像・縮小画像の URL を作る。
    画像の置き場所はファイル名の MD5 の先頭 1 文字と 2 文字で決まるので、問い合わせずに作れる
    （Special:FilePath を使うと転送が 3 回入り、表示が遅い）。
    縮小の幅は Commons が用意している標準の幅（960, 330）に合わせる。"""
    n = name.replace(" ", "_")
    h = hashlib.md5(n.encode("utf-8")).hexdigest()
    q = quote(n)
    page = f"{COMMONS}File:{q}"
    original = f"{UPLOAD}{h[0]}/{h[:2]}/{q}"
    thumb = f"{UPLOAD}thumb/{h[0]}/{h[:2]}/{q}/{{w}}px-{q}"
    return page, original, thumb.format(w=960), thumb.format(w=330)


def upload_url(row, park_categories):
    """Commons の投稿画面（UploadWizard）の URL。分類・見出し・位置を前もって入れる。
    公園の分類は commons-categories.csv で確かめたものだけ入れる（無い分類を入れると赤リンクになる）。"""
    cats = [SURVEY_CATEGORY] + park_categories.get(row["objectid"], [])
    params = {
        "categories": "|".join(cats),
        "caption": f"Playground in {row['title']}, Vancouver",
        "captionlang": "en",
    }
    if row.get("latitude") and row.get("longitude"):
        params.update(lat=row["latitude"], lon=row["longitude"])
    return f"{UPLOAD_WIZARD}?{urlencode(params, quote_via=quote)}"


def read(name):
    with open(ROOT / "collection" / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def surveyed_rows():
    """手で書いた公園の行と、その写真の行（子）を返す。公園の行に写真があれば、記録の型を compound_object にする。"""
    photos = {}
    for ph in read("photos.csv"):
        page, original, small, thumb = commons_urls(ph["commons_file"])
        photos.setdefault(ph["parentid"], []).append({
            "objectid": ph["objectid"],
            "parentid": ph["parentid"],
            "title": ph["title"],
            "description": ph["description"],
            "display_template": "image",
            "format": "image/jpeg",
            "object_location": original,
            "image_small": small,
            "image_thumb": thumb,
            "image_alt_text": ph["description"],
            "rights": PHOTO_RIGHTS,
            "rightsstatement": CC_BY,
            "commons": page,
            "image_width": ph["width"],
            "image_height": ph["height"],
            "title_ja": ph["title_ja"],
            "description_ja": ph["description_ja"],
        })
    parks = []
    for seq, p in enumerate(read("surveyed-parks.csv"), 1):
        kids = photos.get(p["objectid"], [])
        cover = next((k for k in kids if k["objectid"] == p["photo_thumb"]), kids[0] if kids else {})
        row = {k: v for k, v in p.items() if k != "photo_thumb"}
        row.update({
            "type": "Place",
            "display_template": "compound_object" if kids else "record",
            "source": SURVEY_SOURCE,
            "rights": SURVEY_RIGHTS,
            "rightsstatement": CC_BY,
            "image_small": cover.get("image_small", ""),
            "image_thumb": cover.get("image_thumb", ""),
            "image_alt_text": cover.get("image_alt_text", ""),
            "survey_seq": f"{seq:03d}",
        })
        parks.append((row, kids))
    return parks


def city_row(p, fs, count):
    """市のデータの公園 1 つを行にする。fs はその公園の施設（parks-facilities）。"""
    others = sorted(f["facilitytype"] for f in fs if f["facilitytype"] != "Playgrounds")
    address = " ".join(x for x in [p.get("streetnumber"), p.get("streetname")] if x)
    geo = p.get("googlemapdest") or {}
    noun = "playground" if count == 1 else "playgrounds"
    return {
        "objectid": f"park{p['parkid']:03d}",
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
        "parkid": p["parkid"],
        "neighbourhood": p["neighbourhoodname"],
        "playground_count": count,
        "hectare": p.get("hectare", ""),
        "washrooms": p.get("washrooms", ""),
        "equipment": "",
        "surveyed": "",
    }


def main():
    parks = {p["parkid"]: p for p in json.load(open(SRC / "parks.json"))}
    facilities = json.load(open(SRC / "parks-facilities.json"))

    by_park = {}
    for f in facilities:
        by_park.setdefault(f["parkid"], []).append(f)

    rows = []
    for parkid, fs in by_park.items():
        count = sum(f["facilitycount"] for f in fs if f["facilitytype"] == "Playgrounds")
        if count:
            rows.append(city_row(parks[parkid], fs, count))

    for o in read("osm-parks.csv"):
        parkid = int(o["parkid"])
        if parkid in by_park and any(f["facilitytype"] == "Playgrounds" for f in by_park[parkid]):
            raise SystemExit(f"osm-parks.csv: {o['title']} is already in the city's playground list")
        p = parks[parkid]
        count = int(o["playground_count"])
        row = city_row(p, by_park.get(parkid, []), count)
        noun = "playground" if count == 1 else "playgrounds"
        row.update({
            "description": " ".join(x for x in [
                f"{count} {noun} in {p['name']} ({p['neighbourhoodname']}).",
                "Not in the City's list of playgrounds; the position is from OpenStreetMap.",
                OSM_CHECK, o["note"], "Equipment not yet surveyed."] if x),
            "description_ja": "".join(x for x in [
                f"{p['name']}（{p['neighbourhoodname']}）にある遊び場 {count} か所。",
                "市の遊び場の一覧には無く、位置は OpenStreetMap による。",
                OSM_CHECK_JA, o["note_ja"], "遊具は未調査。"] if x),
            "latitude": o["latitude"],
            "longitude": o["longitude"],
            "source": OSM_SOURCE,
            "rights": OSM_RIGHTS,
            "osm": o["osm"],
        })
        rows.append(row)

    surveyed = surveyed_rows()
    rows += [park for park, _ in surveyed]
    rows.sort(key=lambda r: r["title"])
    children = {park["objectid"]: kids for park, kids in surveyed}
    rows = [x for r in rows for x in [r, *children.get(r["objectid"], [])]]
    park_categories = {}
    for c in read("commons-categories.csv"):
        park_categories.setdefault(c["objectid"], []).append(c["category"])
    for r in rows:
        if not r.get("parentid"):
            r["commons_upload"] = upload_url(r, park_categories)
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, restval="")
        w.writeheader()
        w.writerows(rows)
    parks = [r for r in rows if not r.get("parentid")]
    print(f"{len(parks)} parks, {sum(int(r['playground_count']) for r in parks)} playgrounds, "
          f"{len(rows) - len(parks)} photos -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
