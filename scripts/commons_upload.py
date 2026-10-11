#!/usr/bin/env python3
"""Prepare playground photos for Wikimedia Commons and upload them in a batch.

The rules come from the photo guide (site/pages/guide.md) and the lab note
(docs/notes/coverage.md, 2026-10-11):

- the date taken is rounded to the month; every finer date and time is removed
  (EXIF, GPS time, XMP, the Pixel HDR+ maker note, the file name)
- the location (GPS) and the camera make/model are kept
- the video part of a Pixel "motion photo" is removed, together with the HDR
  gain map (Commons shows neither)
- photos are uploaded a few days after they were taken (--min-age-days)

Blurring people is done by hand before this step; point `source` at the
blurred file.

Batch CSV (keep it under data/private/, which is not in git):

    source,title,description_en,description_ja,categories
    PXL_20261020_....jpg,"Nobel Park playground, UBC, Vancouver, 2026-10 01.jpg",...,...,Nobel Park (UBC)

- source: path relative to the CSV
- title: Commons file name without "File:"; must not contain a full date
- categories: separated by ";" ("Playgrounds in Vancouver" is always added)

Usage:

    python3 scripts/commons_upload.py prepare data/private/upload/2026-10b/batch.csv
    python3 scripts/commons_upload.py upload  data/private/upload/2026-10b/batch.csv          # dry run
    python3 scripts/commons_upload.py upload  data/private/upload/2026-10b/batch.csv --yes    # really upload

`prepare` writes the cleaned JPEG and its wikitext to <batch dir>/out/ and
checks that no date finer than the month is left. `upload` logs in with the bot
password from 1Password ("Wikimedia Commons bot playgrounds") and writes
<batch dir>/uploaded.csv.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests

API = "https://commons.wikimedia.org/w/api.php"
UA = "playgrounds-commons-upload/0.1 (https://play.ldas.jp; User:Satoru196)"
OP_ITEM = "Wikimedia Commons bot playgrounds"
AUTHOR = "Satoru Nakamura ([[User:Satoru196|Satoru196]])"
PROJECT = "[https://play.ldas.jp Metro Vancouver playground equipment record]"
ALWAYS_CATEGORIES = ["Playgrounds in Vancouver"]

# Tags that keep a date or time finer than the month. Removed in prepare().
DATE_TAGS = [
    "-EXIF:ModifyDate=", "-EXIF:DateTimeOriginal=", "-EXIF:CreateDate=",
    "-EXIF:OffsetTime=", "-EXIF:OffsetTimeOriginal=", "-EXIF:OffsetTimeDigitized=",
    "-EXIF:SubSecTime=", "-EXIF:SubSecTimeOriginal=", "-EXIF:SubSecTimeDigitized=",
    "-GPS:GPSTimeStamp=", "-GPS:GPSDateStamp=",
    "-IPTC:all=",
]
# Groups whose dates are fine to keep (file system, the colour profile's own date).
ALLOWED_TIME_GROUPS = {"System", "ICC-header", "ICC_Profile"}
FULL_DATE = re.compile(rb"20\d\d[:\-]?[01]\d[:\-]?[0-3]\d")


def primary_jpeg_end(data: bytes, stop_at_scan: bool = False) -> int:
    """Byte offset just after the EOI of the first (primary) JPEG image.

    Everything after it (HDR gain map, motion photo MP4) is dropped.
    With stop_at_scan, return where the image data starts instead (the end of
    the metadata segments).
    """
    if data[:2] != b"\xff\xd8":
        raise ValueError("not a JPEG")
    i = 2
    n = len(data)
    while i < n:
        if data[i] != 0xFF:
            raise ValueError(f"marker expected at {i}")
        while i < n and data[i] == 0xFF:
            i += 1
        m = data[i]
        i += 1
        if m == 0xD9:
            return i
        if m == 0x01 or 0xD0 <= m <= 0xD7:
            continue
        if m == 0xDA and stop_at_scan:
            return i - 2
        seglen = int.from_bytes(data[i:i + 2], "big")
        i += seglen
        if m == 0xDA:
            # entropy-coded data: runs until a marker that is not a stuffed
            # 0xFF00 or a restart marker
            while i < n - 1:
                if data[i] == 0xFF and data[i + 1] != 0 and not (0xD0 <= data[i + 1] <= 0xD7):
                    break
                i += 1
    raise ValueError("no EOI found")


def exif_json(path: Path, *args: str) -> dict:
    out = subprocess.run(["exiftool", "-json", "-a", "-G1", *args, str(path)],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)[0]


def read_csv(batch: Path) -> list[dict]:
    with batch.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        if FULL_DATE.search(r["title"].encode()):
            sys.exit(f"title has a full date, use the month only: {r['title']}")
        if not r["title"].lower().endswith((".jpg", ".jpeg")):
            sys.exit(f"title must end with .jpg: {r['title']}")
    titles = [r["title"] for r in rows]
    if len(set(titles)) != len(titles):
        sys.exit("duplicate titles in the batch")
    return rows


def out_paths(batch: Path, title: str) -> tuple[Path, Path]:
    out = batch.parent / "out"
    stem = Path(title).stem
    return out / f"{stem}.jpg", out / f"{stem}.wikitext"


def wikitext(row: dict, month: str, lat: float | None, lon: float | None) -> str:
    cats = [c.strip() for c in row.get("categories", "").split(";") if c.strip()]
    cats += [c for c in ALWAYS_CATEGORIES if c not in cats]
    desc = f"{{{{en|1={row['description_en']}}}}}"
    if row.get("description_ja"):
        desc += f"\n{{{{ja|1={row['description_ja']}}}}}"
    lines = [
        "=={{int:filedesc}}==",
        "{{Information",
        f"|description={desc}",
        f"|date={month}",
        "|source={{own}}",
        f"|author={AUTHOR}",
        f"|other fields={{{{Information field|name=Project|value={PROJECT}}}}}",
        "}}",
    ]
    if lat is not None and lon is not None:
        lines.append(f"{{{{Location|{lat:.6f}|{lon:.6f}}}}}")
    lines += ["", "=={{int:license-header}}==", "{{self|cc-by-4.0}}", ""]
    lines += [f"[[Category:{c}]]" for c in cats]
    return "\n".join(lines) + "\n"


def check_clean(path: Path, src_size: int) -> None:
    """Fail if anything finer than the month or any motion/video data is left."""
    tags = exif_json(path, "-time:all", "-XMP:all", "-MPF:all", "-JUMBF:all", "-Trailer:all")
    bad = []
    for k, v in tags.items():
        if k == "SourceFile":
            continue
        group, name = k.split(":", 1)
        if group in ALLOWED_TIME_GROUPS:
            continue
        if k in ("XMP-photoshop:DateCreated", "XMP-x:XMPToolkit"):
            continue
        bad.append(f"{k}={v}")
    if bad:
        raise SystemExit(f"{path.name}: tags left: {bad}")
    data = path.read_bytes()
    if primary_jpeg_end(data) != len(data):
        raise SystemExit(f"{path.name}: data after the primary image")
    if FULL_DATE.search(data[:primary_jpeg_end(data, stop_at_scan=True)]):
        raise SystemExit(f"{path.name}: a full date string is still in the header")
    if b"ftypmp4" in data or b"ftypisom" in data:
        raise SystemExit(f"{path.name}: video data left")
    print(f"  ok  {path.name}  {src_size / 1e6:.1f} MB -> {len(data) / 1e6:.1f} MB")


def prepare(batch: Path) -> None:
    rows = read_csv(batch)
    (batch.parent / "out").mkdir(exist_ok=True)
    for r in rows:
        src = (batch.parent / r["source"]).resolve()
        jpg, wt = out_paths(batch, r["title"])
        info = exif_json(src, "-n", "-EXIF:DateTimeOriginal", "-GPS:GPSLatitude",
                         "-GPS:GPSLongitude", "-GPS:GPSLatitudeRef", "-GPS:GPSLongitudeRef",
                         "-XMP-GCamera:MotionPhoto")
        taken = info.get("ExifIFD:DateTimeOriginal")
        if not taken:
            raise SystemExit(f"{src.name}: no DateTimeOriginal")
        month = taken[:7].replace(":", "-")
        lat = info.get("GPS:GPSLatitude")
        lon = info.get("GPS:GPSLongitude")
        if lat is not None and info.get("GPS:GPSLatitudeRef") == "S":
            lat = -lat
        if lon is not None and info.get("GPS:GPSLongitudeRef") == "W":
            lon = -lon

        data = src.read_bytes()
        jpg.write_bytes(data[:primary_jpeg_end(data)])
        subprocess.run(
            ["exiftool", "-q", "-overwrite_original", "-XMP:all=", "-MPF:all=", "-JUMBF:all=",
             "-Trailer:all=", *DATE_TAGS,
             f"-XMP-photoshop:DateCreated={month.replace('-', ':')}",
             str(jpg)],
            check=True)
        shutil.copystat(src, jpg)  # keep the local file times as they were
        wt.write_text(wikitext(r, month, lat, lon), encoding="utf-8")
        motion = " (motion photo: video removed)" if info.get("XMP-GCamera:MotionPhoto") else ""
        print(f"{src.name} -> {jpg.name}  date {month}{motion}")
        check_clean(jpg, len(data))


def op_field(field: str) -> str:
    return subprocess.run(["op", "item", "get", OP_ITEM, "--fields", field, "--reveal"],
                          check=True, capture_output=True, text=True).stdout.strip()


def login() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    token = s.get(API, params={"action": "query", "meta": "tokens", "type": "login",
                               "format": "json"}).json()["query"]["tokens"]["logintoken"]
    r = s.post(API, data={"action": "login", "lgname": op_field("username"),
                          "lgpassword": op_field("password"), "lgtoken": token,
                          "format": "json"}).json()
    if r.get("login", {}).get("result") != "Success":
        raise SystemExit(f"login failed: {r.get('login', {}).get('reason', r)}")
    return s


def exists(s: requests.Session, title: str, sha1: str) -> str | None:
    """Return why the file cannot be uploaded (same title or same image), or None."""
    q = s.get(API, params={"action": "query", "titles": f"File:{title}", "format": "json"}).json()
    if not any("missing" in p for p in q["query"]["pages"].values()):
        return "title already exists"
    d = s.get(API, params={"action": "query", "list": "allimages", "aisha1": sha1,
                           "format": "json"}).json()
    if d["query"]["allimages"]:
        return f"same image already on Commons: {d['query']['allimages'][0]['name']}"
    return None


def upload(batch: Path, yes: bool, min_age_days: int) -> None:
    import hashlib

    rows = read_csv(batch)
    items = []
    newest = None
    for r in rows:
        jpg, wt = out_paths(batch, r["title"])
        if not jpg.exists() or not wt.exists():
            raise SystemExit(f"run prepare first: {jpg.name}")
        src = (batch.parent / r["source"]).resolve()
        taken = exif_json(src, "-EXIF:DateTimeOriginal")["ExifIFD:DateTimeOriginal"]
        day = dt.datetime.strptime(taken[:10], "%Y:%m:%d").date()
        newest = max(newest or day, day)
        items.append((r, jpg, wt))
    age = (dt.date.today() - newest).days
    if age < min_age_days:
        raise SystemExit(f"newest photo is {age} day(s) old; wait until it is {min_age_days} "
                         "(the upload time would show the day it was taken)")

    s = login() if yes else requests.Session()
    s.headers["User-Agent"] = UA
    if yes:
        csrf = s.get(API, params={"action": "query", "meta": "tokens",
                                  "format": "json"}).json()["query"]["tokens"]["csrftoken"]
    log = batch.parent / "uploaded.csv"
    new_log = not log.exists()
    with log.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_log:
            w.writerow(["title", "url", "width", "height", "result"])
        for r, jpg, wt in items:
            sha1 = hashlib.sha1(jpg.read_bytes()).hexdigest()
            why = exists(s, r["title"], sha1)
            if why:
                print(f"skip  {r['title']}: {why}")
                continue
            if not yes:
                print(f"would upload  {r['title']}  ({jpg.stat().st_size / 1e6:.1f} MB)")
                continue
            with jpg.open("rb") as fh:
                res = s.post(API, data={"action": "upload", "filename": r["title"],
                                        "text": wt.read_text(encoding="utf-8"),
                                        "comment": "Playground survey photo (own work)",
                                        "token": csrf, "format": "json"},
                             files={"file": (r["title"], fh, "image/jpeg")}).json()
            up = res.get("upload", {})
            if up.get("result") != "Success":
                print(f"FAIL  {r['title']}: {res.get('error') or up.get('warnings')}")
                w.writerow([r["title"], "", "", "", json.dumps(res, ensure_ascii=False)])
                continue
            ii = up["imageinfo"]
            print(f"done  {ii['descriptionurl']}")
            w.writerow([r["title"], ii["descriptionurl"], ii["width"], ii["height"], "Success"])
            f.flush()
            time.sleep(5)
    if not yes:
        print("dry run; add --yes to upload")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("batch", type=Path)
    u = sub.add_parser("upload")
    u.add_argument("batch", type=Path)
    u.add_argument("--yes", action="store_true", help="really upload (default: dry run)")
    u.add_argument("--min-age-days", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "prepare":
        prepare(a.batch)
    else:
        upload(a.batch, a.yes, a.min_age_days)


if __name__ == "__main__":
    main()
