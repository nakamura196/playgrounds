# CollectionBuilder テーマに戻したい機能

このサイト（play.ldas.jp）で足した機能のうち、ほかの CollectionBuilder のサイトでも使えそうなものの一覧。
テーマ（~/git/collectionbuilder/cb-ja-demo、nakamura196/collectionbuilder-csv）に後でまとめて反映するためのもの。
反映したら、その項目に「反映済み（テーマ側のコミット）」と書く。

場所はこのリポジトリの `site/` からの相対パス。比べた相手は cb-ja-demo（ce806c8 から写した時点）。

## 1. 語彙で値を管理する欄（優先: 高）

`_data/config-metadata.csv` に `vocab` の列を足し、欄の値を `_data/vocab/<表>.csv` の id で持つ仕組み。

- `_plugins/vocab_labels.rb`: 組み立てのときに `<欄>_name` の列を足す。中身はその言語の名前（`label_<lang>`、無ければ `label_en`、無ければ id）
- 一覧の絞り込み（config-browse）と検索（config-search、cjk_index）は `<欄>_name` を見る。人は「ツリーハウス」で探せ、id の「treehouse」は出ない
- 元の欄には id を残す。資料のページの語彙へのリンクと JSON-LD は id を使う
- `_includes/item/metadata.html`: `vocab` のある欄は、名前を出して `/vocab/#<id>` にリンクする

テーマに入れるときに決めること:
- 語彙の表の列（id / label_ja / label_en / description_* / broader など）をどこまで決め打ちにするか

## 2. 語彙の用語から「この値を持つ資料」へのリンク（優先: 高）

語彙のページの各用語に「この遊具がある遊び場（N か所）」のように、一覧の絞り込みへのリンクと件数を出す。
0 件の用語にはリンクを出さない。

- 飛び先は `/browse.html#<欄>_name:<その言語の名前>`。一覧のページは `#欄:語` の形をもともと読める
- 2026-10-12 時点では未実装。まずこのサイトで作り、うまくいったらテーマへ戻す
- 2026-10-12 このサイトで実装した（テーマには未反映）。遊具の型（18 語）と設備（5 語）に、日英ともリンクが出る
  - `_plugins/vocab_labels.rb`: 語彙の表の各用語に `count_<欄>`（その id を持つ資料の数）と `browse_name`（`<欄>_name` に入れた名前）を足す
  - `pages/vocab.html`: `count_<欄>` が 1 以上の用語にだけリンクを出す
  - 落とし穴: 一覧の絞り込みは部分一致。ある名前が別の名前に含まれると（例: 「雲梯」は「回る輪の雲梯（…）」に含まれる）、飛び先の件数が表示より多くなる。組み立てのときに食い違いを数え、あれば警告を出す（今は 0 件なので出ない）。テーマに入れるなら、絞り込みに完全一致を足すかどうかを決める
  - 大分類（categories）と製品には、資料の欄が直接は無いので出していない

関連: 資料のページでは、`vocab` のある欄の値は語彙のページへ飛ぶ。そのため、テーマ本来の
`browse_link`（値から一覧の絞り込みへ飛ぶ）が効かなくなっている。
「語彙へ」と「同じ値の資料へ」の両方を出す形を、テーマ側で決めたい。

## 3. 語彙のページと SKOS の JSON-LD（優先: 中）

- `pages/vocab.html`: 人が読む語彙のページ。各用語に `id` のアンカーがあり、概念の URI（`<lod-base>/vocab/#<id>`）がそのまま開く
- `pages/vocab-jsonld.json`: 同じ語彙を SKOS で出す
- 今は遊具に特有の作り（型・大分類・製品の 3 つの表）。テーマに入れるなら、表 1 つ・broader だけの最小の形にする

## 4. 資料ごとの JSON-LD と URI の基点（優先: 中）

- `_layouts/item/jsonld.json`: 資料ごとに `items/<objectid>.jsonld` を出す
- `_config.yml` の `lod-base`: URI の基点を 1 か所で持つ。日本語版と英語版で同じ URI になる
- `_includes/head/head.html`: 資料のページに `<link rel="alternate" type="application/ld+json">` を出す（`theme.yml` の `item-jsonld` で切り替え）
- 型（このサイトは schema:Park）は決め打ちなので、テーマでは設定で選べるようにする

## 5. 共有用の画像とメタタグ（優先: 中）

- `scripts/make_og_image.py` で 1200×630 の共有用画像を言語ごとに作る（`assets/img/og-ja.jpg` / `og-en.jpg`）
- `_includes/head/page-meta.html`: ページの og:image をこの画像にし、幅と高さを出す。トップページでは題名を繰り返さない
- `_includes/head/item-meta.html`: 写真の無い資料はサイトの共有用画像を使う。説明は日本語版なら `description_ja` を優先し、160 字で切る
- `_includes/head/head.html`: canonical を出す（`/index.html` は `/` にそろえる）
- `pages/robots.txt` を足した

## 6. トップページの近道の欄を設定で選ぶ（優先: 低）

- `_layouts/home-museum.html`: 検索の下の近道（チップ）が `era` 決め打ちだった。ページの `chip-field` で欄を選べるようにした
- 「調査した資料を新しい順に 6 件」の欄は、このサイトに特有（`survey_seq`）。テーマには入れない

## 7. 組み立てと公開の手順（優先: 低）

- `scripts/deploy-pages.zsh`: 日本語版と英語版を Docker（ruby:3.3）で組み、`.nojekyll` を足して gh-pages に 1 コミットで push する。Actions を使わない
- 英語版は `--config _config.yml,_config.en.yml -d _site/en`

## テーマを直すときの落とし穴

- Liquid では `contains` が予約語。`ty.contains` は動かないので `ty['contains']` と書く
- cb-ja-demo は開発時に referrer を送らない設定がある。OpenStreetMap のタイルは 403 になる
