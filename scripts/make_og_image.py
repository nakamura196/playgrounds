"""トップページの共有用画像（OGP、1200×630）を、日本語と英語の 2 枚作る。

左にサイト名と一行の説明、右に Wesbrook Park の写真（Wikimedia Commons、自分の撮影、CC BY 4.0）。
公園のページは各公園の写真をそのまま使うので、この画像はトップと、写真の無いページだけに出る。

写真は Commons から 1280 px の縮小版を取り、data/cache/ に置く（data/ は git の外）。
字体は macOS のヒラギノ角ゴシック。画像にしてしまうので、字体のファイルは配らない。

使い方: python3 scripts/make_og_image.py
出力:   site/assets/img/og-ja.jpg, site/assets/img/og-en.jpg
"""
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "assets" / "img"
CACHE = ROOT / "data" / "cache" / "og"
PHOTO = ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/"
         "Wesbrook_Park_playground%2C_UBC%2C_Vancouver%2C_2026-10-11_04.jpg/"
         "1280px-Wesbrook_Park_playground%2C_UBC%2C_Vancouver%2C_2026-10-11_04.jpg")
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc"
FONT_TEXT = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"

W, H = 1200, 630
SPLIT = 600            # 写真の左端
PAD = 64
GREEN = (47, 107, 79)  # サイトの primary（_data/config-theme-colors.csv）
INK = (31, 42, 36)
GREY = (90, 98, 94)

TEXT = {
    "ja": {
        "title": ["バンクーバーの", "遊び場"],
        "lead": ["公園の遊び場を、遊具の種類から", "探せるようにする記録"],
        "credit": "写真: Wesbrook Park（UBC）",
    },
    "en": {
        "title": ["Vancouver", "Playgrounds"],
        "lead": ["A record of park playgrounds,", "searchable by play equipment"],
        "credit": "Photo: Wesbrook Park (UBC)",
    },
}


def photo():
    path = CACHE / "wesbrook-04-1280.jpg"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(PHOTO, headers={"User-Agent": "play.ldas.jp og image (nakamura196)"})
        path.write_bytes(urllib.request.urlopen(req).read())
    im = Image.open(path).convert("RGB")
    # 右の枠（600×630）を埋めるように縮め、中央で切る
    w, h = W - SPLIT, H
    scale = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    x = (im.width - w) // 2
    y = (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def make(lang, ph):
    t = TEXT[lang]
    im = Image.new("RGB", (W, H), "white")
    im.paste(ph, (SPLIT, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, SPLIT, 10), fill=GREEN)
    title = ImageFont.truetype(FONT_BOLD, 64 if lang == "ja" else 72)
    lead = ImageFont.truetype(FONT_TEXT, 30)
    small = ImageFont.truetype(FONT_TEXT, 24)
    y = 150
    for line in t["title"]:
        d.text((PAD, y), line, font=title, fill=INK)
        y += 100
    y += 24
    for line in t["lead"]:
        d.text((PAD, y), line, font=lead, fill=GREY)
        y += 46
    d.text((PAD, H - PAD - 24), "play.ldas.jp", font=small, fill=GREEN)
    # 写真の上の小さな表示（右下）
    cw = d.textlength(t["credit"], font=small)
    d.rectangle((W - cw - 36, H - 52, W, H), fill=(0, 0, 0))
    d.text((W - cw - 18, H - 44), t["credit"], font=small, fill="white")
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"og-{lang}.jpg"
    im.save(out, quality=85, optimize=True, progressive=True)
    print(out.relative_to(ROOT), f"{out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    ph = photo()
    for lang in TEXT:
        make(lang, ph)
