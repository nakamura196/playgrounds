"""遊び場の近くの Mapillary 画像を取り込み、CLIP で「回る輪の雲梯」らしさの順に並べる。

使い方: MAPILLARY_TOKEN=... python3 scripts/mapillary_clip.py [半径m=50] [1 か所あたりの上限=10] [上位の数=48]
入力:   data/mapillary_coverage.jsonl
出力:   data/mapillary_thumbs/<id>.jpg（1024px の縮小画像。git に入れない）
        data/clip/mapillary_scores.json、data/clip/mapillary_<問い>.jpg（上位の一覧画像）

対象は、半径以内で遊び場のほうを向いた（向きの差 45 度以内か 360 度写真）画像。1 か所につき近い順に上限まで。
道路から撮った写真では遊具が小さく写るので、1 枚を左・中・右の正方形に切って 3 回照らし、最大を点数にする。
"""
import json
import os
import pathlib
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from clip_rank import MODEL, PROMPTS, sheet  # noqa: E402

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
THUMBS = DATA / "mapillary_thumbs"


def fetch(token, iid):
    dest = THUMBS / f"{iid}.jpg"
    if dest.exists():
        return dest
    for i in range(4):
        try:
            req = urllib.request.Request(f"https://graph.mapillary.com/{iid}?fields=thumb_1024_url",
                                         headers={"Authorization": f"OAuth {token}"})
            with urllib.request.urlopen(req, timeout=60) as r:
                url = json.load(r)["thumb_1024_url"]
            with urllib.request.urlopen(url, timeout=60) as r:
                dest.write_bytes(r.read())
            return dest
        except Exception:
            time.sleep(5 * (i + 1))
    return None


def crops(im):
    w, h = im.size
    if w <= h * 1.2:
        return [im]
    s = h
    return [im.crop((x, 0, x + s, s)) for x in (0, (w - s) // 2, w - s)]


def main():
    radius = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 48
    token = os.environ["MAPILLARY_TOKEN"].strip()
    rows = [json.loads(l) for l in (DATA / "mapillary_coverage.jsonl").read_text().splitlines() if l]
    pick = {}
    for r in rows:
        hs = [h for h in r["hits"] if h["dist"] <= radius
              and (h["is_pano"] or (h["facing_diff"] is not None and h["facing_diff"] <= 45))]
        for h in sorted(hs, key=lambda h: h["dist"])[:per]:
            pick.setdefault(h["id"], (r["osm"], h["dist"]))
    print(f"images to score: {len(pick)} from {len({v[0] for v in pick.values()})} playgrounds", flush=True)
    THUMBS.mkdir(exist_ok=True)
    with ThreadPoolExecutor(8) as ex:
        paths = [p for p in ex.map(lambda i: fetch(token, i), pick) if p]
    print(f"downloaded: {len(paths)}", flush=True)

    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model = CLIPModel.from_pretrained(MODEL).to(dev).eval()
    proc = CLIPProcessor.from_pretrained(MODEL)
    names = list(PROMPTS)
    scores = {}
    with torch.no_grad():
        t = proc(text=list(PROMPTS.values()), return_tensors="pt", padding=True).to(dev)
        tf = model.get_text_features(**t)
        tf = tf / tf.norm(dim=-1, keepdim=True)
        for i in range(0, len(paths), 16):
            batch, owner = [], []
            for p in paths[i:i + 16]:
                try:
                    cs = crops(Image.open(p).convert("RGB"))
                except Exception:
                    continue
                batch += cs
                owner += [p] * len(cs)
            x = proc(images=batch, return_tensors="pt").to(dev)
            f = model.get_image_features(**x)
            f = f / f.norm(dim=-1, keepdim=True)
            probs = (100 * f @ tf.T).softmax(dim=-1).cpu()
            for p, pr in zip(owner, probs):
                cur = scores.get(p.stem)
                if cur is None or pr[0] > cur["spinning"]:
                    scores[p.stem] = dict(zip(names, map(float, pr)))
            if i % 800 == 0:
                print("scored", i, len(paths), flush=True)
    for iid, s in scores.items():
        s["osm"], s["dist"] = pick[iid]
    out = DATA / "clip"
    out.mkdir(exist_ok=True)
    (out / "mapillary_scores.json").write_text(json.dumps(scores, indent=1))
    order = sorted(scores, key=lambda i: -scores[i]["spinning"])[:k]
    sheet([THUMBS / f"{i}.jpg" for i in order], [scores[i]["spinning"] for i in order], out / "mapillary_spinning.jpg")
    for i in order[:k]:
        print(i, scores[i]["osm"], scores[i]["dist"], round(scores[i]["spinning"], 3))


if __name__ == "__main__":
    main()
