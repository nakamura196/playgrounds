"""AI の試験用に、Commons の遊び場・遊具の画像（縮小版）を集める。

使い方: python3 scripts/commons_testset.py
出力:   data/testset/<pageid>.jpg, data/testset/index.json（タイトル・分類・ライセンス）

分類を下位へ 2 段まで辿る。画像は幅 512px の縮小版だけを取る。
"""
import json
import pathlib
import time
import urllib.parse
import urllib.request

UA = "playground-search-research/0.1 (https://github.com/nakamura196)"
API = "https://commons.wikimedia.org/w/api.php"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "testset"
ROOTS = ["Monkey bars", "Playground equipment in Canada", "Playgrounds in British Columbia",
         "Merry-go-rounds (playground)", "Climbing frames"]
MAX_FILES = 600


def api(**params):
    params.update(format="json")
    req = urllib.request.Request(f"{API}?{urllib.parse.urlencode(params)}", headers={"User-Agent": UA})
    for i in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception:
            time.sleep(10 * (i + 1))
    raise RuntimeError(params)


def members(cat):
    out, cont = [], {}
    while True:
        d = api(action="query", list="categorymembers", cmtitle=f"Category:{cat}", cmlimit=500, **cont)
        out += d.get("query", {}).get("categorymembers", [])
        if "continue" not in d:
            return out
        cont = d["continue"]
        time.sleep(1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = {}
    for root in ROOTS:
        queue, seen = [(root, 0)], set()
        while queue:
            cat, depth = queue.pop()
            if cat in seen:
                continue
            seen.add(cat)
            for m in members(cat):
                if m["ns"] == 6 and m["title"].lower().endswith((".jpg", ".jpeg", ".png")):
                    files.setdefault(m["pageid"], {"title": m["title"], "cats": []})["cats"].append(cat)
                elif m["ns"] == 14 and depth < 2:
                    queue.append((m["title"].removeprefix("Category:"), depth + 1))
            time.sleep(1)
        print(root, len(files), flush=True)
    ids = list(files)[:MAX_FILES]
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        d = api(action="query", pageids="|".join(map(str, chunk)), prop="imageinfo",
                iiprop="url|extmetadata", iiurlwidth=512)
        for pid, page in d["query"]["pages"].items():
            info = page["imageinfo"][0]
            meta = info.get("extmetadata", {})
            files[int(pid)].update(thumb=info["thumburl"], page=info["descriptionurl"],
                                   license=meta.get("LicenseShortName", {}).get("value"))
        time.sleep(1)
    for pid in ids:
        dest = OUT / f"{pid}.jpg"
        if dest.exists() or "thumb" not in files[pid]:
            continue
        req = urllib.request.Request(files[pid]["thumb"], headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                dest.write_bytes(r.read())
        except Exception as e:
            print("skip", pid, e)
        time.sleep(0.5)
    (OUT / "index.json").write_text(json.dumps({p: files[p] for p in ids}, ensure_ascii=False, indent=1))
    print("downloaded", len(list(OUT.glob("*.jpg"))))


if __name__ == "__main__":
    main()
