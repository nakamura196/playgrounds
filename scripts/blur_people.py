#!/usr/bin/env python3
"""Pixelate every person in playground photos before they go to Commons.

Runs before `scripts/commons_upload.py prepare` (point `source` at the output).

How people are found (all on this machine; the photos are not sent anywhere):

- person outlines from YOLO11-seg, run on the whole photo and again on
  overlapping tiles, so that small people far away are also found
- faces from OpenCV YuNet, also on tiles, to catch people whose body is hidden
  behind equipment
- each outline is widened a little, then pixelated with blocks scaled to the
  person's size (strong enough that it cannot be undone)

The low thresholds lean towards masking too much. Always look at the review
images: masked areas are outlined in red (person) and blue (face). Anything
missed can be added with --extra (boxes in the oriented photo, in pixels).

EXIF (date, GPS, camera) is copied from the original so that `prepare` can
read it; the orientation is baked into the pixels and set to 1.

Environment (outside the repo):

    uv venv ~/.cache/blur-venv --python 3.12
    VIRTUAL_ENV=~/.cache/blur-venv uv pip install ultralytics opencv-python
    # YuNet: ~/.cache/blur-models/face_detection_yunet_2023mar.onnx (opencv_zoo)

Usage:

    ~/.cache/blur-venv/bin/python scripts/blur_people.py data/private/raw/2026-10-12/*.jpg -o data/private/blur/2026-10-12
    ... --extra "PXL_xxx.jpg:100,200,300,500"     # x1,y1,x2,y2, may be repeated
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps
from ultralytics import YOLO

YUNET = Path.home() / ".cache/blur-models/face_detection_yunet_2023mar.onnx"


def tiles(w: int, h: int, n_long: int = 3, overlap: float = 0.25):
    """Overlapping tiles: n_long along the long side, fewer along the short."""
    n_short = max(1, round(n_long * min(w, h) / max(w, h)))
    nx, ny = (n_long, n_short) if w >= h else (n_short, n_long)
    tw, th = int(w / (nx - (nx - 1) * overlap)), int(h / (ny - (ny - 1) * overlap))
    for j in range(ny):
        for i in range(nx):
            x = 0 if nx == 1 else round(i * (w - tw) / (nx - 1))
            y = 0 if ny == 1 else round(j * (h - th) / (ny - 1))
            yield x, y, tw, th


def person_masks(model: YOLO, img: np.ndarray, conf: float) -> list[tuple[np.ndarray, tuple]]:
    """Each found person as (full-size bool mask, box). Duplicates from tiles are kept;
    they only add to the union."""
    h, w = img.shape[:2]
    out = []
    windows = [(0, 0, w, h, 1920)] + [(x, y, tw, th, 1280) for x, y, tw, th in tiles(w, h)]
    for x, y, tw, th, size in windows:
        crop = img[y:y + th, x:x + tw]
        r = model.predict(crop, imgsz=size, conf=conf, classes=[0], retina_masks=True,
                          verbose=False)[0]
        if r.masks is None:
            continue
        for m, b in zip(r.masks.data.cpu().numpy(), r.boxes.xyxy.cpu().numpy()):
            full = np.zeros((h, w), bool)
            full[y:y + th, x:x + tw] = m[:th, :tw] > 0.5
            out.append((full, (b[0] + x, b[1] + y, b[2] + x, b[3] + y)))
    return out


def faces(img: np.ndarray, score: float) -> list[tuple]:
    h, w = img.shape[:2]
    det = cv2.FaceDetectorYN.create(str(YUNET), "", (320, 320), score, 0.3, 5000)
    found = []
    for x, y, tw, th in [(0, 0, w, h)] + list(tiles(w, h, 4)):
        crop = img[y:y + th, x:x + tw]
        scale = min(1.0, 1600 / max(tw, th))
        small = cv2.resize(crop, None, fx=scale, fy=scale) if scale < 1 else crop
        det.setInputSize((small.shape[1], small.shape[0]))
        _, f = det.detect(small)
        for row in (f if f is not None else []):
            fx, fy, fw, fh = row[:4] / scale
            found.append((fx + x, fy + y, fx + x + fw, fy + y + fh))
    return found


def pixelate(img: np.ndarray, mask: np.ndarray, block: int) -> None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return
    x1, x2, y1, y2 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    region = img[y1:y2, x1:x2]
    sw, sh = max(1, (x2 - x1) // block), max(1, (y2 - y1) // block)
    small = cv2.resize(region, (sw, sh), interpolation=cv2.INTER_AREA)
    big = cv2.resize(small, (x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST)
    m = mask[y1:y2, x1:x2]
    region[m] = big[m]


def widen(mask: np.ndarray, px: int) -> np.ndarray:
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1))
    return cv2.dilate(mask.astype(np.uint8), k) > 0


def process(path: Path, out_dir: Path, model: YOLO, args, extra: list[tuple]) -> dict:
    pil = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    img = cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR)
    h, w = img.shape[:2]
    persons = person_masks(model, img, args.conf)
    face_boxes = faces(img, args.face_score)

    masks = []  # (mask, block size, kind)
    for m, (x1, y1, x2, y2) in persons:
        ph = y2 - y1
        masks.append((widen(m, int(6 + ph * 0.04)), max(8, int(ph / args.body_blocks)), "person"))
    for x1, y1, x2, y2 in face_boxes + extra:
        fw, fh = x2 - x1, y2 - y1
        m = np.zeros((h, w), np.uint8)
        cv2.ellipse(m, (int((x1 + x2) / 2), int((y1 + y2) / 2)),
                    (int(fw * 0.8), int(fh * 0.9)), 0, 0, 360, 1, -1)
        masks.append((m > 0, max(8, int(fh / args.face_blocks)), "face"))

    for m, block, _ in masks:
        pixelate(img, m, block)

    out = out_dir / path.name.replace(".MP.jpg", ".jpg")
    cv2.imwrite(str(out), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    subprocess.run(["exiftool", "-q", "-overwrite_original", "-TagsFromFile", str(path),
                    "-EXIF:all", "-GPS:all", "-IFD1:all=", "-Orientation=1", "-n", str(out)],
                   check=True)

    # review image: outlines of everything masked
    rev = img.copy()
    for m, _, kind in masks:
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(rev, cs, -1, (0, 0, 255) if kind == "person" else (255, 128, 0),
                         max(3, w // 600))
    s = 1600 / max(w, h)
    (out_dir / "review").mkdir(exist_ok=True)
    cv2.imwrite(str(out_dir / "review" / out.name), cv2.resize(rev, None, fx=s, fy=s),
                [cv2.IMWRITE_JPEG_QUALITY, 85])
    return {"file": path.name, "out": out.name, "person_hits": len(persons),
            "face_hits": len(face_boxes), "extra": len(extra)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photos", nargs="+", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--conf", type=float, default=0.15, help="person threshold (low = mask more)")
    ap.add_argument("--face-score", type=float, default=0.6)
    ap.add_argument("--body-blocks", type=float, default=20, help="blocks along a person's height")
    ap.add_argument("--face-blocks", type=float, default=6, help="blocks along a face's height")
    ap.add_argument("--model", default="yolo11x-seg.pt")
    ap.add_argument("--extra", action="append", default=[], help="FILE:x1,y1,x2,y2")
    args = ap.parse_args()

    extra: dict[str, list[tuple]] = {}
    for e in args.extra:
        name, box = e.rsplit(":", 1)
        extra.setdefault(name, []).append(tuple(float(v) for v in box.split(",")))

    args.out.mkdir(parents=True, exist_ok=True)
    model = YOLO(args.model)
    log = []
    for p in args.photos:
        r = process(p, args.out, model, args, extra.get(p.name, []))
        print(json.dumps(r))
        log.append(r)
    (args.out / "blur_log.json").write_text(json.dumps(log, indent=1))


if __name__ == "__main__":
    main()
