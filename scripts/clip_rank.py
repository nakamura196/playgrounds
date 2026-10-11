"""試験用の画像を CLIP で文章と照らし合わせ、上位を一覧画像にする。

使い方: python3 scripts/clip_rank.py [上位の数=24]
入力:   data/testset/*.jpg
出力:   data/clip/<問い>.jpg（上位の一覧画像）、data/clip/scores.json

問いは「回る輪の雲梯」と、取り違えやすい遊具（まっすぐな雲梯、回転遊具）。
各画像の点数は、問いの中で最も近いものへの割合（ソフトマックス）で出す。
"""
import json
import pathlib
import sys

import torch
from PIL import Image, ImageDraw
from transformers import CLIPModel, CLIPProcessor

ROOT = pathlib.Path(__file__).resolve().parent.parent / "data"
MODEL = "openai/clip-vit-large-patch14"
PROMPTS = {
    "spinning": "a photo of spinning monkey bars: a horizontal wheel of hand rings that rotates around a central pole on a playground",
    "straight": "a photo of straight horizontal monkey bars, a ladder on a playground",
    "merry": "a photo of a merry-go-round on a playground",
    "swing": "a photo of a swing set on a playground",
    "slide": "a photo of a playground slide",
    "other": "a photo of a park",
}


def sheet(paths, scores, dest, size=256, cols=6):
    rows = (len(paths) + cols - 1) // cols
    im = Image.new("RGB", (cols * size, rows * size), "white")
    d = ImageDraw.Draw(im)
    for i, (p, s) in enumerate(zip(paths, scores)):
        t = Image.open(p).convert("RGB")
        t.thumbnail((size, size))
        x, y = (i % cols) * size, (i // cols) * size
        im.paste(t, (x, y))
        d.rectangle([x, y, x + 120, y + 18], fill="black")
        d.text((x + 3, y + 3), f"{i + 1}. {p.stem} {s:.2f}", fill="white")
    im.save(dest, quality=85)


def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model = CLIPModel.from_pretrained(MODEL).to(dev).eval()
    proc = CLIPProcessor.from_pretrained(MODEL)
    paths = sorted((ROOT / "testset").glob("*.jpg"))
    with torch.no_grad():
        t = proc(text=list(PROMPTS.values()), return_tensors="pt", padding=True).to(dev)
        tf = model.get_text_features(**t)
        tf = tf / tf.norm(dim=-1, keepdim=True)
        feats, ok = [], []
        for i in range(0, len(paths), 32):
            batch = []
            for p in paths[i:i + 32]:
                try:
                    batch.append(Image.open(p).convert("RGB"))
                    ok.append(p)
                except Exception:
                    pass
            x = proc(images=batch, return_tensors="pt").to(dev)
            f = model.get_image_features(**x)
            feats.append(f / f.norm(dim=-1, keepdim=True))
        imf = torch.cat(feats)
        probs = (100 * imf @ tf.T).softmax(dim=-1).cpu()
    out = ROOT / "clip"
    out.mkdir(exist_ok=True)
    names = list(PROMPTS)
    scores = {p.stem: dict(zip(names, map(float, probs[i]))) for i, p in enumerate(ok)}
    (out / "scores.json").write_text(json.dumps(scores, indent=1))
    for j, name in enumerate(names[:3]):
        order = probs[:, j].argsort(descending=True)[:k]
        sheet([ok[i] for i in order], [float(probs[i, j]) for i in order], out / f"{name}.jpg")
    top = (probs.argmax(dim=-1) == 0).sum().item()
    print(f"images={len(ok)} top1_spinning={top}")


if __name__ == "__main__":
    main()
