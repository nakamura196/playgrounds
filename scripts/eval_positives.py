"""正解の写真を、Mapillary の写真（はずれ）に混ぜたとき何位に来るかを測る。

使い方: python3 scripts/eval_positives.py
入力:   data/private/positives/*（正解。git に入れない）
        data/clip/mapillary_scores.json（はずれ。scripts/mapillary_clip.py の出力）
出力:   画面に、正解ごとの点数と順位

点数の出し方は mapillary_clip.py と同じ（左・中・右の正方形に切り、「回る輪の雲梯」の割合の最大）。
はずれの中に本物の回る雲梯が混じっている可能性は、上位を目で確かめて除く。
"""
import json
import pathlib
import sys

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from clip_rank import MODEL, PROMPTS  # noqa: E402
from mapillary_clip import crops  # noqa: E402

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"


def main():
    neg = json.loads((DATA / "clip" / "mapillary_scores.json").read_text())
    negs = sorted((s["spinning"] for s in neg.values()), reverse=True)
    paths = sorted(p for p in (DATA / "private" / "positives").iterdir() if p.suffix.lower() in (".jpg", ".png"))
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model = CLIPModel.from_pretrained(MODEL).to(dev).eval()
    proc = CLIPProcessor.from_pretrained(MODEL)
    with torch.no_grad():
        t = proc(text=list(PROMPTS.values()), return_tensors="pt", padding=True).to(dev)
        tf = model.get_text_features(**t)
        tf = tf / tf.norm(dim=-1, keepdim=True)
        print(f"negatives (Mapillary) = {len(negs)}  top negative score = {negs[0]:.3f}")
        for p in paths:
            cs = crops(Image.open(p).convert("RGB"))
            x = proc(images=cs, return_tensors="pt").to(dev)
            f = model.get_image_features(**x)
            f = f / f.norm(dim=-1, keepdim=True)
            s = float((100 * f @ tf.T).softmax(dim=-1)[:, 0].max())
            rank = 1 + sum(n > s for n in negs)
            print(f"{p.name:50s} score={s:.3f} rank={rank} / {len(negs) + 1}")


if __name__ == "__main__":
    main()
