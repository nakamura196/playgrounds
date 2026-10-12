# 写真の集まり具合（Mapillary / Commons）

Metro Vancouver の遊び場の遊具を、写真から検索できるサイトを作る。
写真は Mapillary と Wikimedia Commons から集め、CLIP で文章と画像の両方から検索し、
OpenStreetMap（OSM）の公園一覧と地図に出す、という構想。
作り始める前に、そもそも写真がどれだけあるかを確かめる。

## 2026-10-10 Myrtle Park（North Vancouver）で 1 か所試す

対象: 回る輪の雲梯（輪が回転する雲梯）。

- OSM: 公園は way/397550739（中心 49.3203, -122.9488、District of North Vancouver の Cove Cliff）。
  遊び場は 3 つ（way/394994133、way/397556889、way/1291855488）と水遊び場 1 つ（way/397556891）。
  個々の遊具は登録されていない
- Commons: 遊び場の中心から半径 500 m 以内の位置情報付き画像は 3 枚で、どれも OpenBenches
  （記念ベンチの写真を集める取り組み）のベンチ。名前で検索すると "Myrtle Park" は
  英国 Bingley の同名の公園ばかり出る
- Mapillary: API の鍵が無いので、mapillary.com の地図で目視した。公園の西の Deep Cove Road 沿いの
  遊歩道に撮影の跡が 1 本あり、撮影範囲の表示は出ている。公園内と Deep Cove Road には撮影の跡が無い

結論: 両方とも写っていない。Mapillary は主に道路から撮るので、公園の奥の遊具は写りにくい。

## 2026-10-10 Metro Vancouver 全体の OSM

`scripts/fetch_osm_playgrounds.py`。範囲は OSM relation 2218280（Metro Vancouver Regional District）。

- 遊び場（leisure=playground）: 2,736 か所
- 遊具（playground=*）: 1,488 件。内訳の上位は swing 491、structure 227、slide 138、hopscotch 90、
  climbingframe 89、splash_pad 69。monkey_bars は 8 件。回る輪の雲梯に当たる値は無い

OSM の遊具の記録は少なく、種類の分け方も粗い。検索の手がかりは写真の側から取る必要がある。

## 却下・保留した案

- Google 画像検索・ストリートビュー・Google マップの写真を集める: 却下。
  検索結果の写真は撮影者ごとに権利があり、まとめて取り込むことは Google の規約でも禁じられている。
  地図サービスの写真は保存も、それをもとにしたデータ（CLIP の特徴量を含む）を作ることも禁じられている。
  CLIP が見分けられるかを数枚で試すだけなら、手で保存した画像を手元で使い、リポジトリにも公開サイトにも入れない

## 2026-10-10 Flickr

API の鍵が無いので、flickr.com の検索画面で、自由に使える条件（CC と PD）の写真に絞って見た。

- "Myrtle Park North Vancouver": 25 枚。入り江の景色、水遊び場、野球場、近くの店。回る雲梯は 0 枚
- "monkey bars spinning": 13 枚。どれも遊具と無関係
- 分かったこと: Flickr の写真には遊具の名前がほぼ付いていない。言葉では探せず、画像の中身から探す必要がある

## 2026-10-10 対象の遊具の呼び名

Google 画像検索の結果を目で見て確かめた。中心の柱のまわりを水平の輪が回り、輪に付いた取っ手にぶら下がる。
英語の呼び名は spinning monkey bars / monkey bar wheel。製品の例は
Little Tikes Commercial "Fun Wheels"、Belson "360° Orbital Horizontal Ladder"、
Landscape Structures "Circular Horizontal Ladder"、PWAP "Hold'n Spin Spinner"。
先行事例として chicagoplaygrounds.com（シカゴの遊び場の遊具を 1 つずつ登録しているサイト。
"Overhead Spinning Rings" の項目がある）。

## 2026-10-10 CLIP で見分けられるか（小さな試験）

`scripts/commons_testset.py` → `scripts/clip_rank.py`。モデルは openai/clip-vit-large-patch14
（Hugging Face transformers 4.57.6、Apple の GPU（MPS）で実行）。

- 画像: Commons の Category:Monkey bars / Merry-go-rounds (playground) / Climbing frames を 2 段まで辿った 93 枚
  （Playground equipment in Canada と Playgrounds in British Columbia はその名前の分類が無く 0 枚）。
  ここに回る雲梯の写真 2 枚（PWAP と swingsetmall.com のページの代表画像）を混ぜて 95 枚
- 問い: 「回る輪の雲梯」と、取り違えやすい 5 つ（まっすぐな雲梯、回転遊具、ぶらんこ、すべり台、公園）。
  6 つの中での割合で点数を出す
- 結果: 回る雲梯の 2 枚は 95 枚中 1 位（0.96）と 3 位（0.93）。2 位は円形の網の回転遊具（0.93）、
  4 位は吊り輪（0.82）、5 位はドーム型のジャングルジム（0.74）。「丸い・輪・頭上」の形は捉えているが、
  丸い遊具一般との区別は甘い
- 限界: 正解が 2 枚だけで、どちらも遊具が大きく写った製品写真。Mapillary のように遠くから小さく写る写真では
  未確認。正解の 2 枚は手元の試験だけに使い、`data/private/` に置いて git に入れない（`data/` ごと除外済み）

主張の候補: 写真に遊具名の付いていない一般の写真群（Flickr）でも、CLIP の文章検索で特定の遊具を上位に出せる
（根拠は上の 95 枚の試験。正解を増やした再試験が要る）。

## 2026-10-10 Commons の位置情報付き画像は、遊び場の近くにどれだけあるか

`scripts/commons_coverage.py 50`。OSM の遊び場 2,736 か所の中心点から、Commons の geosearch
（位置情報付きファイル、名前空間 6）で半径 50 m 以内を引いた。約 1 時間半かかった（1 か所 1 秒の待ちを入れた）。

- 半径 50 m 以内に画像が 1 枚でもある遊び場: 122 か所（4.5%）。25 m 以内は 49 か所、10 m 以内は 8 か所
- 引っかかった画像は延べ 457 枚。1 か所に 41 枚集まる所もある（Gastown、Granville Island など名所の近く）
- 題名に遊び場らしい語（playground、swing など）がある画像を持つ遊び場は 5 か所。うち 1 枚は子犬の写真で、
  実質 4 か所（Hastings Mill Playground など）
- 多いのは街並み・建物・駅・桜の写真。Commons に移された Mapillary の画像も 55 枚（5 か所）あった。
  ISS から地球を撮った写真が座標付きで引っかかる例もあり、位置情報だけでは中身は保証されない
- 題名だけで数えたので、遊具が写っていても題名に出ていない画像は取りこぼしている（中身は未確認）

結論: Commons は遊具の写真の供給源としてはほぼ使えない。近くに画像があるのは 4.5%、
遊び場を写したと題名から分かるのは 2,736 か所中 4 か所。写真の主な供給源は Mapillary
（と、利用者の投稿）になる。

主張の候補: 都市の遊び場について、Commons の位置情報付き画像は 4.5% の遊び場にしか無く、
遊具を写したものは 0.2% に満たない（根拠は本節の実測）。

## 2026-10-10 Mapillary の写真は、遊び場の近くにどれだけあるか（途中経過）

`scripts/mapillary_coverage.py 100`。Commons と同じく OSM の遊び場の中心点から、Mapillary の画像検索 API
（graph.mapillary.com/images、範囲指定）で半径 100 m 以内を引いた。鍵は 1Password の「Mapillary」の access_token
（読み取り専用のアプリ playground-search-research を登録して発行）。集計は `scripts/mapillary_summary.py`。
「向いている」は、カメラの向きと遊び場への方角の差が 45 度以内、または 360 度写真。

- 1,102 か所まで取った時点（全 2,736 か所の 40%）: 半径 50 m 以内に画像がある遊び場 16.2%、
  向いている画像がある遊び場 11.3%。25 m 以内は 6.6%、10 m 以内は 1.0%。Commons（50 m で 4.5%）より多い
- 50 m 以内の画像 7,827 枚の内訳は通常のカメラ 5,664、魚眼 1,931、360 度 193。撮影年は 2015〜2026 年に散らばる
- 360 度写真なのに is_pano が偽のものがある。camera_type（spherical）でも判定するように直した
- 写真が密集した場所では API が 500「量を減らせ」を返す（例 49.2124, -122.6564）。範囲を 4 つに分けて取り直すようにした
- Myrtle Park の 3 つの遊び場は、いちばん近い画像でも 245 m。2018 年 1 月の 1 回の撮影で、道路沿いを横向きに撮ったもの

全 2,736 か所を取り終えた（同日。量が多すぎて打ち切られた検索は 0 件。500 が出た 49.2124, -122.6564 も取れている）。

| 半径 | 画像がある遊び場 | 向いている画像がある遊び場 | 画像がある所の枚数（中央値） |
|---|---|---|---|
| 10 m | 26（1.0%） | 8（0.3%） | 2.5 |
| 25 m | 193（7.1%） | 78（2.9%） | 7 |
| 50 m | 491（17.9%） | 345（12.6%） | 23 |
| 100 m | 1,063（38.9%） | 778（28.4%） | 48 |

- 途中経過（40% の時点で 50 m 16.2%、向いている 11.3%）から大きくは動かなかった
- 50 m 以内の画像は 24,241 枚、うち 360 度 1,077 枚
- 50 m 以内に画像がある 491 か所で、いちばん新しい画像の撮影年: 2014 年 4、2015 年 15、2016 年 1、2017 年 23、
  2018 年 51、2019 年 15、2020 年 86、2021 年 69、2022 年 20、2023 年 31、2024 年 73、2025 年 22、2026 年 81。
  2023 年以降に撮られた画像があるのは 207 か所で、全体の 7.6%
- 分かったこと: 遊具の方を向いた画像が 50 m 以内にあるのは、8 か所に 1 か所。
  遊具の入れ替えに追いつける新しさ（2023 年以降）まで求めると、さらに少ない。
  Mapillary だけで遊具の一覧を作るのは難しい
- 確かめていないこと: 「向いている」画像に、実際に遊具が写っているか（木や建物で隠れていないか）は見ていない

主張の候補: 都市圏の遊び場 2,736 か所のうち、Mapillary で遊具の方を向いた画像が 50 m 以内にあるのは 12.6%
（向きを問わなければ 17.9%）。Wikimedia Commons は向きを問わず 4.5%（根拠は本節と前の節の測定）。

## 2026-10-10 CLIP は実際の写真で回る雲梯を見分けられるか

`scripts/mapillary_clip.py 50 10` → `scripts/eval_positives.py`。

- はずれ: 遊び場から 50 m 以内で向いている Mapillary 画像を、1 か所につき近い順に 10 枚まで。176 か所の 998 枚
  （1024px の縮小画像）。1 枚を左・中・右の正方形に切り、「回る輪の雲梯」の割合の最大を点数にした
- 正解: Google マップの Myrtle Park / Myrtle Park Playground の投稿写真から、回る雲梯が写った 3 枚を
  Claude in Chrome で画面ごと保存した（真下からの接写、3 つの輪を横から、全体写真の奥に小さく 2 つ）。
  前の試験の製品写真 2 枚も加えた。`data/private/positives/` に置き、git にも公開サイトにも入れない
- 結果（999 枚中の順位）: 製品写真 2 枚は 1 位。Google マップの 3 枚は 156 位（奥に小さく、0.080）、
  173 位（接写、0.070）、297 位（横から 3 つ、0.028）。はずれの最高点は 0.89 で、車の屋根から撮った 360 度写真
- 分かったこと: CLIP の文章検索がうまくいったのは、遊具だけが大きく写った製品写真だけだった。
  人が撮った実際の写真では、輪が画面いっぱいに写っていても見分けられなかった。
  3 つの輪が横からはっきり写った写真が、いちばん順位が低い
- 確かめていないこと: 正解は 1 か所の 3 枚だけ。画像を手がかりにした検索（正解の写真に似た写真を探す）や、
  小さく切って照らす方法、検出用に学習したモデルは試していない

主張の候補: 汎用の画像と文章のモデル（CLIP）による文章検索は、特定の遊具を製品写真では 1 位に出せるが、
利用者の撮った写真では 999 枚中 156〜297 位に沈む（根拠は本節の測定）。
自分で撮る写真は、遊具全体を背景から離して撮るか、撮った人が遊具名を付ける必要がある。

## 2026-10-11 訂正: CLIP の小さな試験の画像の出どころ

「CLIP で見分けられるか（小さな試験）」の節で、画像を Monkey bars / Merry-go-rounds (playground) /
Climbing frames から取ったと書いたが誤り。data/testset/index.json の分類を数え直すと、
Monkey bars 59 枚と Playgrounds in British Columbia（下位の Playgrounds in Vancouver、Terra Nova Adventure Park を含む）34 枚だった。
Commons の API で確かめると、Merry-go-rounds (playground) は存在せず、Climbing frames は中身の無い転送用の分類
（実体は Jungle gyms）。testset.log は累計の枚数を、次に辿る分類の名前と並べて出していたので読み違えた。

あわせて、記事にするため数え直した点:
- 題名に遊び場らしい語がある Commons 画像を持つ遊び場は、"Play Ground" の表記揺れを含めるかで 3〜4 か所
- Myrtle Park の 245 m は 100 m の全件取得とは別に範囲を広げて見た値で、data/mapillary_coverage.jsonl からは再現できない

記事: tech.ldas.jp/ja/posts/playground-photo-coverage-vancouver/（地図は scripts/plot_coverage_map.py で描いた）

## 2026-10-11 訂正: Myrtle Park の遊具の形

「対象の遊具の呼び名」の節で、回る雲梯を「中心の柱のまわりを水平の輪が回る」と書いたが、これは Google 画像検索で見た製品の形で、
Myrtle Park の実物ではなかった。手元の写真（data/private/positives/gmaps_myrtle_pg_02_side.png）で見ると、
横に渡した梁から水平な輪が 3 つ吊られ、それぞれが回る型。chicagoplaygrounds.com の "Overhead Spinning Rings"（13 か所）と同じ型。

製品名も確かめ直した（2026-10-11、各社のページ）:
- 同じ型: Little Tikes Commercial "90° Fun Wheels"
- 別の遊具: PWAP の Hold-N-Spin は 1 本の柱の上で輪が回る型（CLIP の試験の製品写真 1 枚はこれ。もう 1 枚 swingsetmall は梁から吊る型）
- 回らない: Belson "360° Orbital Horizontal Ladder"、Landscape Structures "Circular Horizontal Ladder" は円形に組んだ固定のはしご

分かったこと: 同じ遊具が別の名前で呼ばれ、似た名前が別の遊具を指す。名前で探せない理由の具体例になる。

## 2026-10-11 再公開と、関連する数・サイト

- 記事はデジタルアーカイブの文脈で書き直し、tech-blog #258 で再公開した。
- chicagoplaygrounds.com の項目 "Overhead Spinning Rings"（https://chicagoplaygrounds.com/s/guide/item/3164）は、2026-10-11 の時点で 13 か所に付いていた。説明は「1 本の水平の梁の下に 3 つの輪、輪は自由に回る」。似た別の遊具 "Single Overhead Spinning Ring" には "Different From" という関係が張られている。語彙の設計の実例として使える。
- 続けるなら、公開には Omeka S より CollectionBuilder（https://collectionbuilder.github.io/）が向く、というのが本人の判断。サーバを持たずに静的なサイトとして置けるので、運用の費用が小さい。
- City of Vancouver のオープンデータ（2026-10-11 取得）: 公園 218（parks データセットの件数）、遊び場 136（parks-facilities の Playgrounds の facilitycount の合計）。2019 年の報道では Park Board の遊び場は 160 とされており、数え方の違いは確かめていない。Metro Vancouver 全体の OSM の遊び場 2,736 とは範囲が違う。
- 既存の写真サイト: vancouverplaygrounds.com は Vancouver 市内を中心に 54 か所の遊び場を写真つきで載せ、"Spinner" などの遊具で絞り込める（WordPress、運営者の記載なし）。

## 2026-10-11 市内を回りきれるかの見積もり

- City of Vancouver のオープンデータ（parks-facilities の Playgrounds）では、遊び場は 136 か所で、114 の公園にある。21 の地区に分かれる（多い順に Renfrew-Collingwood 12、Kensington-Cedar Cottage 11、Hastings-Sunrise 9）。
- 114 の公園の座標を、近い順にたどった直線距離の合計は約 111 km。道なりにすると 1.3 倍程度と見て約 145 km。
- 自転車で半日に 8 公園ほど回れると仮定すると、およそ 15 回で回りきれる。週 1 回なら 4 か月ほど。
- 公開の候補は CollectionBuilder（本人の案）。
- 撮影は子どもが写らない時間帯に行う。chicagoplaygrounds.com も「子どもの写った画像は載せない」と明記している。

## 2026-10-11 CollectionBuilder 用の CSV と、遊具の語彙の下書き

`scripts/build_cb_csv.py` → `collection/playgrounds.csv`。入力は data/opendata/ の parks.json（218 行）と parks-facilities.json（645 行）。

- 1 行 = 遊び場のある公園 1 つ（114 行、遊び場の合計 136）。オープンデータには遊び場ごとの位置が無く、公園ごとの数しか無いため。
  遊び場の数の内訳: 1 か所 97 公園、2 か所 14、3 か所 1、4 か所 2。複数ある公園は、現地で撮るときに遊び場ごとに分ける
- 座標は公園の代表点（googlemapdest）。遊び場そのものの位置ではない
- 遊具が無いので display_template は record（画像なしの項目）。公園の他の施設は subject に入れて絞り込みに使う

chicagoplaygrounds.com の構成を Omeka S の API（/api/resource_templates, /api/items）で読んだ（2026-10-11）:
- 遊具の型は 400 件（item set 3074）。項目は Equipment Name (schema:name)、Description、Descriptive Tag (schema:category)、
  Different From (schema:disambiguatingDescription)、Other Name (schema:alternateName)、Equipment Contains (schema:item)、Audience
- 400 件のうち Different From があるのは 123、Other Name 44、Contains 4
- 大分類は item set で持つ（Swings 12、Slides 21、Climbing 138 とその下の Vertical 53 / Traverse 26 / Net 36、Overhead 43、
  Spinning 25、See-Saws 7、Water 20、Musical 8）。1 つの型が複数の大分類に入る
- 遊び場の側は Playground Equipment (schema:amenityFeature) で型を指すだけ。設置ごとの記録（いつ見たか、どの製品か）は無い
- 製品名・メーカーの欄は無い。KOMPAN がタグに 1 件あるだけ
- Different From は片方向。3425 Single Overhead Spinning Ring → 3164 Overhead Spinning Rings はあるが、逆は無い

語彙の下書き: `vocab/categories.csv`（大分類 16）、`vocab/types.csv`（型 26）、`vocab/products.csv`（製品 4）。
- 型は形と動きで定義し、製品名を型の名前にしない（シカゴと同じ）。製品は別の表にし、型を指す（exact / close）。シカゴに無い部分
- 「別物」（different_from）は両方向に張る。シカゴとの対応は chicago_match に exact / candidate で書いた。
  exact は写真か説明文で確かめた 2 件（3164, 3425）だけで、ほかは名前で選んだ候補
- 確かめていないこと: 製品のページの URL は控えていなかったので空欄。Vancouver で実際に多い遊具はまだ数えていない

## 2026-10-11 CollectionBuilder のサイトと JSON-LD

`site/` に CollectionBuilder のサイトを組んだ。~/git/collectionbuilder/cb-ja-demo（ce806c8）を `git archive` で写し、
東大の資料・IIIF まわり（static_iiif gem、manifest のテンプレート、見本の画像）を外した。日本語版と英語版（/en/）の 2 つを組む形はそのまま。

- データは `collection/playgrounds.csv` と `vocab/*.csv` が正本。`zsh scripts/sync_site_data.zsh` で `site/_data/` に写す
- 組み立ては Docker（ruby:3.3）。手元の Ruby では gem が組めない（cb-ja-demo と同じ事情）。
  `docker run --rm -v "$PWD/site":/srv -w /srv -e BUNDLE_PATH=vendor/bundle-docker ruby:3.3 sh -c 'bundle install && bundle exec jekyll build'`、
  英語版は `--config _config.yml,_config.en.yml -d _site/en` を足す
- 公園ごとの JSON-LD: `items/<objectid>.jsonld`（114 件、`_layouts/item/jsonld.json`）。schema:Park。
  ほかの施設とトイレは amenityFeature（名前と true/false）。遊具は amenityFeature に additionalType で語彙の概念を指す。
  シカゴが遊び場から遊具の型を schema:amenityFeature で指しているのに合わせた
- 語彙: `vocab/vocab.jsonld`（SKOS、概念 46・概念体系 2）と、人が読む `vocab/` のページ。
  概念の URI は `<lod-base>/vocab/#<id>` で、ページの該当の項目が開く。
  型→大分類は skos:broader、別物は pgv:differentFrom（skos:related の下位）、含む型は dcterms:hasPart、
  シカゴとの対応は exact だけ skos:exactMatch、候補は rdfs:seeAlso（確かめていない対応を一致と書かないため）。
  製品は別の概念体系にし、型へ exact → skos:exactMatch、close → skos:closeMatch
- URI の基点は `_config.yml` の `lod-base`（仮に https://nakamura196.github.io/playgrounds）。日本語版と英語版で同じ URI になる。
  置き場所が決まったらここを 1 か所直す。JSON-LD は日本語版の組み立てでだけ作る
- 確かめたこと: 114 件と語彙が JSON として読め、rdflib で読み込める（語彙 394 トリプル、公園 計 5,406）。語彙の中で指す先の欠けは 0。
  遊具の欄を仮に埋めた組み立てで、公園のページに遊具の名前（語彙へのリンク）と JSON-LD のボタンが出ることを確かめ、データは戻した
- 落とし穴: Liquid では `contains` が予約語なので、`ty.contains` ではなく `ty['contains']` と書く。
  cb-ja-demo は開発時に referrer を送らない設定があり、OpenStreetMap のタイルは 403 になる。地図は Esri のまま使う
- Myrtle Park は City of Vancouver の公園の一覧に無い（市外）。CLIP の試験に使った遊具は、このサイトの 114 件には入らない
- まだのこと: 絞り込みの「遊具」は語彙の id がそのまま出る（名前ではない）。トイレは Y/N のまま。git に未登録で、公開先も未定

## 2026-10-11 公開先: playgrounds.ldas.jp

公開先を https://playgrounds.ldas.jp に決めた。GitHub Pages（公開リポジトリ nakamura196/playgrounds、まだ作っていない）に独自ドメインを当てる。
`_config.yml` の url と lod-base をこのドメインにし、baseurl は日本語版 ""・英語版 /en にした。`site/CNAME` を足した。

- 却下: nakamura196.github.io/playgrounds（仮置きのまま）。URI がリポジトリ名に縛られる。
  railclass ではリポジトリ名を変えたため、RDF の URI をすべて差し替えることになった
- 却下: w3id.org。転送の登録に PR の審査が要り、railclass の PR（perma-id/w3id.org#6867）もまだ通っていない。
  語彙はまだ下書きで、いま永続 URI を約束する段階ではない。安定したら w3id から playgrounds.ldas.jp へ転送する形で足せる
- ldas.jp のサブドメインなら、DNS は手元で管理でき、置き場所を GitHub Pages から移しても URI は変わらない
- 確かめたこと: 日本語版・英語版を組み直し、JSON-LD の主語に github.io が残っていないこと（0 件）、
  rdflib で 114 件と語彙をまとめて読んで 5,687 トリプル（重なりを除いた数）、hreflang が /en/ を指すことを見た

## 2026-10-11 訂正: 公開先は play.ldas.jp

上の節の playgrounds.ldas.jp を、URL が長いので play.ldas.jp に改めた（公開前・コミット前）。理由と却下した案は上の節のまま。

## 2026-10-11 公開の準備

- 公開リポジトリ nakamura196/playgrounds を作り、main を push した
- `scripts/deploy-pages.zsh`: 日本語版（/）と英語版（/en/）を Docker で組み、`.nojekyll` を足して gh-pages に 1 コミットで push する。
  Actions は使わない。組み上がりは 29 MB
- GitHub Pages は gh-pages の push で自動的に有効になった。独自ドメイン play.ldas.jp を API で登録した
- DNS（CNAME `play` → `nakamura196.github.io`、プロキシ無し）はまだ。1Password の承認がこの会話から通らなかったため

## 2026-10-11 遊具の絞り込みを名前で

- `site/_plugins/vocab_labels.rb`: config-metadata.csv で vocab を持つ欄（equipment）に、組み立てのときに `equipment_name` の欄を足す。
  中身はその言語の名前（label_ja / label_en）を ";" でつないだもの。一覧の絞り込み（config-browse）と検索（config-search）はこちらを見る
- `equipment` には id を残す。公園のページの語彙へのリンクと JSON-LD は id を使うため
- 日本語の検索の索引（cjk_index）も config-search を読むので、同じ欄で名前が入る。索引の中では「雲梯」が「云梯」のように変換されて入る（字体の揺れをそろえるため）
- 確かめ方: 写しの CSV の 2 件に仮の遊具を入れて組み、一覧の絞り込みの欄が「遊具」/「Play equipment」、値が名前になることを見て、データは戻した

## 2026-10-11 UBC 構内の遊び場: 公式の記録と、撮り方のガイドライン

Wesbrook Mall の近くから現地調査を始めたいという話から。UBC の構内と周りの住宅地は市の外で、市のオープンデータに入らない
（市のデータは古くない: parks 2025-09-22、parks-facilities 2026-07-30 更新）。

- 公式の記録: UBC Campus + Community Planning の ArcGIS
  （https://ags.gis.ubc.ca/arcgis/rest/services/Planning/ubcv_plan_landscape/MapServer/2、硬い舗装面の層）に、
  名前に Playground を含む面が 15 件（遊び場 14 か所。Hawthorn Park が 2 面）。最終更新は 2021-11 〜 2026-01。
  遊び場専用の層は無く、舗装面の種類（LSHARD_TYPE）も Concrete。名前で拾った。`data/ubc_playgrounds.json` に保存（git 外）
- Wesbrook Village の中心（49.2507, -123.2353）から 600 m 以内に 6 か所: Nobel、Mundell、Wesbrook Park、Brockhouse、Smith、Khorana
- OSM との比較: OSM は同じ範囲に名前の無い遊び場 3 つだけ（Nobel・Smith・Khorana と位置が一致）。Mundell、Wesbrook Park、Brockhouse は OSM に無い。
  公式の層のほうが漏れが少ない
- 利用条件: 層の licenseInfo は空。UBC の GIS データは UBC の構成員の教育目的、という案内がある。
  サイトに位置を写すなら Campus + Community Planning の許可が要る。それまでは調査の計画にだけ使い、サイトには現地で撮った記録（写真の撮影地点）を載せる
- Google マップは目で見る下調べには使えるが、場所の情報を写して載せることは規約で認められていない。名前の無い小さな遊び場も出にくい
- 撮り方のガイドライン: サイトに `/guide.html`（日本語・英語）を足した。人のいない時間に撮る、誰でも入れる遊び場だけ、
  遊び場の全体 → 遊具ごとの全体 → 動く所 → 銘板 の順。人が写った写真は使わない

## 2026-10-11 HTTPS の証明書

GitHub Pages に play.ldas.jp を登録して 1 時間ほど待ったが、証明書の状態は空のまま（発行の手続きが始まっていない）だった。
DNS は正しく向いていた（CNAME → nakamura196.github.io、CAA なし）。
独自ドメインを API で一度外し、付け直したところ、20 秒ほどで発行された（期限 2027-01-09）。そのあと HTTPS 必須を有効にした。
付け直しのとき、GitHub が gh-pages に「Create CNAME」のコミットを足す。次のデプロイで上書きされるが、中身は同じなので問題ない。
- 落とし穴: DNS を足す前に Pages にドメインを登録すると、発行が始まらないまま止まることがある。待つより付け直しが早い

## 2026-10-11 最初の現地調査（Wesbrook Park）と、写真の置き場所

Wesbrook Park（UBC、Wesbrook Village）で 7 枚撮った（Pixel 9a、14:21〜14:23 PDT）。

- 撮影地点は全部に入っていた。UBC の記録の遊び場の面から約 30 m。ただし最初の 6 枚は同じ値で、端末が位置を測り直していない。遊具ごとの位置には使えず、公園の位置として使う
- 遊具: 塔から下りる筒形のすべり台、回る網のかご、しなる棒の回る椅子、低い綱の網、切り株の足場、赤い輪の付いた柱（用途不明）。語彙にあるのは tube-slide と spinning-seat だけ
- 銘板・注意書きの写真は無かった。1 枚は「動く写真」（動画入りの JPEG）で、公開前に動画を外す必要がある
- 写真の置き場所は Wikimedia Commons にした。元の写真は 1 枚 5 MB 前後で、100 か所 × 20 枚だと 10 GB になり GitHub Pages に載らない。Commons なら長く残り、CC BY 4.0 も使える。サイトは Commons の写真を表示する
- 遠くに写った通行人 2 人はモザイクで隠した（撮影地点・日時の情報は残した）
- 1 枚目を投稿: https://commons.wikimedia.org/wiki/File:Wesbrook_Park_playground,_UBC,_Vancouver,_2026-10-11_01.jpg
  分類 Category:Wesbrook Park (UBC) を新設（上位: University of British Columbia, Parks in British Columbia）
- OpenStreetMap には写真は置けない。Wesbrook Park・Mundell・Brockhouse の遊び場は OSM に無いので、現地で確かめた点を後でまとめて描き足す（自分の調査なので ODbL の問題は無い）
- 残り 6 枚も投稿し、分類に 7 枚がそろった。07 の撮影地点だけ他より約 80 m 南にずれている（端末の測り直しの誤差）。ガイドラインは「人が大きく写った写真は使わない。遠くの人はぼかす」に変えた（未反映）

## 2026-10-11 撮った人の居場所を守る（公開する写真の情報を粗くする）

Commons に上げた 7 枚は、ページに撮影日時（分まで）と撮影地点が出る。写真の中の情報（日時・地点・機種）もページの下に表示される。
これで撮った人が「いつどこにいたか」が分かる。撮る場所が家の近くに集まれば、住んでいる辺りの見当も付く。

- 決めたこと（次の撮影から）: 公開する写真からは日時・地点・機種の情報を消す。日付は月まで（例 2026-10）、位置は公園の代表点だけ。撮ってすぐには上げず、何日分かためて上げる。元の写真は手元にだけ残す
- 日付をうそに書き換える案は却下。遊具は入れ替わるので、「いつあったか」がずれると記録として使えない。細かさを落とすだけにする
- 既に上げた 7 枚（2026-10-11）はそのまま残す（本人の判断）。消すなら、上げた本人が 7 日以内に取り下げる削除の手続き（Commons の即時削除 G7）が使える。上書きでは古い版が履歴に残る
- ガイドラインの「撮った後に」に 2 行足した（未反映）
- 訂正（同日）: 本人の判断で、写真の中の撮影地点と機種の情報は残すことにした。消すのは日付の細かさだけ（月まで）。時刻の無い地点だけなら、公共の公園に「いつか来た」ことしか分からない。
  ただし Commons の投稿日時は誰でも見えるので、撮ってすぐ上げると撮った日が分かる。何日分かためて上げる決まりは残す

## 2026-10-11 Wesbrook Park をサイトに載せる（市のデータに無い遊び場と、Commons の写真）

最初の現地調査の記録として、Wesbrook Park（UBC）を載せた。市のデータに無い遊び場を載せるのは初めて。

- 市のデータに無い遊び場は、手で書く表 `collection/surveyed-parks.csv` に置く。写真は `collection/photos.csv` に 1 枚 1 行で置く。
  `scripts/build_cb_csv.py` が、市のデータから作る行とこの 2 つを合わせて `collection/playgrounds.csv` を作る。市のデータを取り直しても、手で書いた行は消えない
- 番号は `ubc-wesbrook`。市の番号（park234 など）とは混ぜない。位置は最初の 6 枚の撮影地点（49.252133, -123.231881）。UBC C+CP の地図データは使わない（利用条件が不明なため）
- 確認した日は「2026-10」と月まで（写真の日付を丸める決まりに合わせた）
- 写真は Commons に置いたまま、ページから直接表示する。CollectionBuilder の「親の記録 + 子の写真」の型（compound_object）を使った。子の行には撮った人・CC BY 4.0・Commons のページへのリンクを持たせた（CC BY のクレジットの条件）
- 画像の URL は、ファイル名の MD5 から upload.wikimedia.org の住所を計算して作る。`Special:FilePath/<名前>?width=` は転送が 3 回入り、一覧の表示が遅かった。
  縮小の幅は Commons の標準の幅（330, 960）に合わせた。確かめるときに続けて 14 枚を取ると、何枚か 429（頼みすぎ）が返った。間を置くと全部 200
- IIIF: 公園ごとに Presentation 3.0 のマニフェストを `/iiif/<objectid>.json` に作る（写真のある公園だけ）。キャンバスは Commons の元の JPEG をそのまま描く。navPlace で公園の位置も入れた。
  Commons は IIIF Image API を出していない（私の知る範囲）ので、拡大して細部を見る表示はできない。拡大用の画像を自分で作ってサイトに置く案は却下（写真をサイトに持たないと決めたのと矛盾する）。
  ページの見せ方は一覧のままにして、マニフェストは「IIIF マニフェスト」「Mirador で開く」のボタンで出す（本人の要望）。マニフェストの id は日本語版・英語版で同じ（lod-base から作る）
- 用語集に 3 語を足した: 回る網のかご（rope-net-spinner）、低い綱の網（low-rope-net）、切り株の足場（stepping-stumps）。シカゴの用語集との対応は未確認。
  赤い輪が 3 つ付いた柱は用途が分からないので、用語集には足さず説明文に書いた
- トップの大きな画像は写真 04（すべり台の塔の正面）。01 は人をぼかした跡があるので避けた
- 写真のクレジットの例に、サイト全体の発行元の名前（「City of Vancouver Open Data（公園の情報）」）が入っていた。写真では誤りなので、Commons の写真では出さないようにした。
  サイト全体の発行元がこの名前になっている点（ページの説明の情報にも入る）は、まだ直していない

## 2026-10-11 IIIF マニフェストを公開した後の確認

- 公開した `https://play.ldas.jp/iiif/ubc-wesbrook.json` は、IIIF 公式の検査（presentation-validator.iiif.io、version 3.0）でエラー 0、警告 0
- 各写真（キャンバス）の題名と説明が英語だけだった（本人の指摘）。日本語も並べた（photos.csv に title_ja / description_ja、公園の行に description_ja）。331cd68
- 表示の問題（未解決）: projectmirador.org の埋め込み（Mirador 4）と uv-v4.netlify.app（Universal Viewer 4）では、写真の一覧と説明は出るが、大きな画像が出ない。
  画像そのものは 200 で届いており、Commons は CORS（別のサイトからの読み込みの許可）も `*` で返している。ブラウザの記録には「WebGL cannot be used to draw this TiledImage because it has tainted data」（Mirador）、「Error creating texture in WebGL」（UV）。
  どちらも中で使う OpenSeadragon が、画像サーバの無い 1 枚画像を WebGL で描こうとして失敗しているように見える。IIIF の見本（0001-mvm-image、1 枚画像・画像サーバ無し）は同じ Mirador で表示できたので、ビューアがこの形を全く扱えないわけではない。
  手元で Mirador 3.4.3 を動かすと画像は描かれたが、初めの表示位置がずれていた。1280 px の縮小画像に替えても同じ。原因はまだ切り分けていない
- 訂正（同日の夕方）: 改めて開くと、Mirador 4 でも UV 4 でも大きな画像が出た。直したものは無い。
  確かめたこと: (1) UV で、まだ一度も開いていない写真 05 を選んでも出た（ブラウザに残っていた画像で出たのではない）。
  (2) 上の 2 つの警告は、表示できた IIIF の見本でも同じように出る。OpenSeadragon は WebGL で描けないと普通の描き方に切り替えるので、警告は害が無い。
  手元で OpenSeadragon 5.0.1 だけを動かしても、元の画像（4000×3000、4.3 MB）・960 px の縮小・見本の画像の 3 つとも描けた。
  元の画像は curl で 0.4 秒で届く。前回出なかった理由は再現できず不明。読み込みの途中で画面を見ていた可能性がある。マニフェストは今のままでよい

## 2026-10-11 Commons に上げる前の加工を道具にした（`scripts/commons_upload.py`）

次のまとめての公開に向けて、写真の加工と投稿をまとめて行う道具を作った。
`prepare` で加工と点検、`upload` で投稿（`--yes` を付けたときだけ実際に上げる。付けなければ予行）。
写真の一覧は CSV に書き、`data/private/upload/<回>/` に置く（git の外）。

- 日付: EXIF の日時・時差・秒以下、GPS の日時を消し、XMP の撮影日に「2026-10」とだけ書く。
  EXIF の日時の欄は「年:月:日 時:分:秒」の形しか許さないので、月までの値は XMP にしか書けない
- 位置・機種・露出などは残す（決めたとおり）
- 動く写真: 主の画像の終わり（JPEG の終端の印）で切る。後ろに付いていた HDR 用の画像と動画（2.7 MB）が落ちる。6.8 MB → 4.0 MB
- 投稿する名前に年月日が入っていたら止める。いちばん新しい写真が撮ってから 3 日たっていなければ止める（`--min-age-days`）
- 加工の後に点検する。月より細かい日時の欄が残っていないか、画像の後ろに何か残っていないか、見出し部分に年月日の文字列が残っていないか
- 落とし穴: Pixel 9a の写真には、日時の欄とは別に 2 か所に撮影日時が入っていた。
  (1) HDR+ の補足情報（XMP の拡張部分。Google の作成日時が分まで入る）。
  (2) 撮影の証明書（C2PA。カメラが「この端末で撮った」と署名する仕組み）の署名の時刻「20261011212339Z」。
  (2) は日時の欄をいくら消しても残る。点検で文字列を探して初めて見つかった。どちらも丸ごと消した（加工すれば証明書は無効になるので、残す意味も無い）
- 同じ写真が既にあるかの確認は、題名と画像の SHA-1 で行う。ただし情報を書き換えると SHA-1 が変わるので、前に上げた元の写真と同じかは分からない。重複は題名で防ぐ
- 確かめたこと: 前回の 07（動く写真）と 02 で `prepare` → 予行まで。ボット用パスワードでのログインも通った（Satoru196）。実際の投稿はまだ試していない

## 2026-10-11 Wesbrook Park の写真を追加（2 回目、未投稿）

同じ日の 15:49〜16:01 PDT に 9 枚を追加で撮った。Google フォトの画面から zip でダウンロードした。
API は使わなかった。2025 年 3 月から、Google Photos の API はライブラリを自由に読めない。
写真を選ぶ画面（Picker API）を通すしかなく、手作業は減らない。
また、API で取った写真は撮影地点の情報が消されると記憶している（確かめていない）。

- 新しく写った遊具: ジップライン、登り壁、鎖で吊った取っ手のアーチ、低い平行棒。
  語彙にあるのは zip-line と climbing-wall。平行棒とアーチは語彙に無い
- 初めて銘板が撮れた。すべり台の塔の柱に Corocord 社の製造銘板（品番 Corocord15-0335-3C1、整理番号 32857、2019 年製、推奨 5〜12 歳）と、対象年齢の表示
- 新しい遊具 4 つの撮影地点は、前回の遊び場から約 90 m 南。UBC C+CP の遊び場の面（OBJECTID 857）の外。
  本人に確かめたところ、同じ公園の中。UBC の地図データの遊び場の面は、公園の遊具の一部しか囲んでいない
- ゴミ箱の 1 枚は遊具の記録と関係が薄いので外した。投稿するのは 8 枚（Commons の名前は 08〜15）
- `prepare` は 8 枚とも点検を通った。予行は「撮ってから 3 日」の決まりで止まった。投稿は 10 月 14 日以降
- 訂正（同じ日）: 「3 日待つ」決まりはやめた。Commons に残るのは投稿日時で、分かるのは「その日までに撮られていた」ことだけ。
  撮影日は月までしか出さないので、投稿日はその日その場にいた証拠にならない。
  毎回すぐ上げると「投稿日≒撮影日」と推測される傾向は出るが、本人がこの程度なら構わないと判断した。
  道具の `--min-age-days` の初期値を 0 にし、写真ガイドの「何日分かためてから公開」の行を消した。
  今回の 8 枚は当日に投稿した（08〜15、全部 Success）
- 訂正（同じ日）: 南側の新しい遊具は、子どもの遊具ではなく KOMPAN 社の屋外運動器具の一角だった（懸垂の棒、平行棒、ケトルベル形のおもりと手順の看板）。
  「ジップライン」はワイヤーではなく固いレールを滑る取っ手（KOMPAN）。Commons の 08・09・10・12 の説明を直した。
  語彙に分類 fitness と 4 語（rail-trolley, pull-up-bars, parallel-bars, kettlebell-station）、製品に Corocord15-0335-3C1 を足した

## 2026-10-11 検討: 「Commons に投稿する」ボタンと「近くの公園」

- Commons の投稿画面（Special:UploadWizard）は、URL で `categories`（`|` 区切り）・`caption`・`captionlang`・`description`・`descriptionlang`・`lat`・`lon` を前もって入れられる（https://www.mediawiki.org/wiki/Extension:UploadWizard の URL arguments）。`campaign` と `fields[]` 以外は投稿キャンペーン無しで使える、と読める（実機では未確認）
- 公園ごとの Commons の分類は、ほぼ無い。市の 114 公園のうち `Category:<公園名> (Vancouver)` があるのは 2 つ（Hillcrest Park, Kensington Park）。名前だけの `Category:<公園名>` は 32 あるが、同名の別の公園の可能性があり、そのままは使えない。上位の `Category:Playgrounds in Vancouver` はある
- 案: 分類は「Playgrounds in Vancouver」＋確かめた公園の分類だけ。無い分類を URL で入れると赤リンクの分類ができるので入れない。サイト経由の投稿を集める分類を 1 つ作る案もある（未決）
- 「近くの公園」は、ブラウザで現在地を取り、公園の位置（115 件）との距離を手元で計算して並べる。位置はサーバに送らない。HTTPS 化済みなので使える
- 確かめていないこと: スマホでの投稿画面の使い勝手、写真の中の撮影地点と URL の lat/lon のどちらが優先されるか
- 決めたこと（同日）: 「近くの公園」は CollectionBuilder の仕組みの外になるので、サイトには入れない。別のアプリも今は作らない。中村が使う場面が少なく、自分の投稿は加工の手順を通る `scripts/commons_upload.py` のほうがよいため。外の人の投稿が入り始めたら、サイトの公開データを読む小さな別ページとして考える
- 投稿のリンクは、データの表の列 `commons_upload` として足した（`scripts/build_cb_csv.py` が作る）。ページの雛形への手入れは、URL の項目にリンクの文言と注記を出せるようにした 1 か所だけ（文言は locale の `link_texts` / `link_notes`）
- Commons に `Category:Playground survey in Vancouver` を作った（上位: Playgrounds in Vancouver、ボットのアカウントで作成）。公園の分類は `collection/commons-categories.csv` に、確かめた 3 つ（Hillcrest Park (Vancouver), Kensington Park (Vancouver), Wesbrook Park (UBC)）だけ書いた
- 外の人の写真は、見てから `collection/photos.csv` に手で足す。自動では載せない
- 撮り方のガイドに「Commons に投稿する」の節を足した

## 2026-10-11 人物のモザイクを自動にする試作（`scripts/blur_people.py`）

人の多い写真も使えるようにしたい、という話から。2 回目の現地調査（Mundell Park 3 枚、Brockhouse Park 13 枚、Pixel 9a）の 16 枚で試した。

- 方法: 人の輪郭を切り抜くモデル（YOLO11x-seg、ultralytics 8.4.164）を、写真全体（1920 px）と、重なりのある区切り 6 枚（各 1280 px）にかけ、結果を全部足す。顔を探すモデル（OpenCV YuNet 2023mar）も、全体と区切り 12 枚にかける。輪郭は人の高さの 4% ＋ 6 px 広げ、人の大きさに合わせた粗いブロック（高さの 1/12、最小 12 px）でモザイクにする。閾値は低め（人 0.15、顔 0.6）で、塗りすぎる側に倒す
- 処理はすべて手元（M 系の Mac、MPS）。16 枚（4000×3000）で 2 分 26 秒
- 結果（確認用の縮小画像を目で見た）: 遠くの高さ 20〜30 px の人まで拾えた。ベビーカーの中の子は体では拾えず、顔のほうで拾えた。見落としは見つからなかった
- 誤り: 案内板や Toy Box に描かれたイラストの顔を塗った（顔のモデル）。石を人と見たらしい小さな塗りが数か所。どちらも塗りすぎの側
- EXIF（日付・GPS・機種）は元の写真から写し、向きは画素に焼き込んで 1 にした。`commons_upload.py prepare` はそのまま読める（未確認）
- 環境はリポジトリの外: `~/.cache/blur-venv`（uv、`--exclude-newer 2026-09-27`）、モデルは `~/.cache/blur-models/`
- 限界: 前景の子どもは、モザイクでも服・体格・自転車が残る。こうした写真は使わない、というガイドの線はそのまま
- 同日、ブロックの大きさを見比べた（身長方向に 12・20・32 ブロック）。12 は四角が目立って浮く。32 は髪型・姿勢・服の柄まで分かり、知り合いなら見当が付く。20 を既定にした（中村の了承済み）。顔は体と別に、顔の高さ方向 6 ブロックの粗さで塗るので、体を細かくしても顔は粗いまま

## 2026-10-11 2 回目の現地調査の写真を Commons に上げた（Mundell Park・Brockhouse Park）

- 16 枚のうち 11 枚を上げた（モザイク後、`commons_upload.py` で日付を月に丸めた）。分類 `Category:Mundell Park (UBC)`・`Category:Brockhouse Park (UBC)` を新設（上位は Wesbrook Park と同じ。位置は写真の撮影地点から）
- 上げなかった 5 枚: 手前に子どもが大きく写った 1 枚。Toy Box・水遊び場の決まりの看板・日焼けの注意書き・ごみ箱の掲示の 4 枚。看板の 4 枚は平面の絵や図が主役で、カナダのパノラマの自由（屋外の常設物を撮った写真の例外）は彫刻と建物だけが対象のため。手元の記録には残す
- 彫刻を施した岩は、彫刻として例外に入るので上げた（作者は分からない）
- 水飲み場・芝生のように遊具でない写真には「Playgrounds in Vancouver」を付けないよう、`commons_upload.py` に列 `default_categories`（no で付けない）を足した
- Mundell の遊具の写真（Mundell Park playground 02）は、遊具の前に人が多く、遊具が隠れている。人の少ない時間に撮り直す予定（中村）

## 2026-10-11 Mundell Park・Brockhouse Park をサイトに載せた。「設備」の語彙を新設

- 2 公園を `collection/surveyed-parks.csv` に、Commons の 11 枚を `collection/photos.csv` に足した。位置は写真の撮影地点（Mundell は遊具の写真、Brockhouse は丸い水遊び場の写真の地点）
- 遊具でないもの（水飲み場など）は、遊具の語彙（types）に入れず、別の語彙 `vocab/amenities.csv` にした。列は `amenities`。最初の 5 語: 水飲み場・日よけの布・芝生の広場・彫刻を施した岩・共用のおもちゃ箱（おもちゃ箱は写真を Commons に上げていないが、現地で見たので記録した）。SKOS では別の ConceptScheme（`#amenities`）、公園の JSON-LD では遊具と同じく amenityFeature から additionalType で指す。概念の URI は遊具と同じ `/vocab/#<id>` なので、id は 4 つの表で重ならないようにする
- 市のデータにある施設（`subject`、例: Water/Spray Parks）とは分けた。こちらは市の分類をそのまま写したもので、語彙として定義していない。Brockhouse の水遊び場は、市の公園と並べて絞り込めるよう `subject` にも Water/Spray Parks と入れた
- 水遊び場の中の物は遊具とみなし、既にあった大分類「水遊び」の下に型を 3 つ足した（水遊びの水路・水車・床の噴水口）。Mundell の複合遊具から「くぐるトンネル」も足した（筒形のすべり台と別物、と両方向に記した）。シカゴとの対応は未確認
- Brockhouse は、調査の日に複合遊具が見当たらなかったので、遊び場の数を 0 にした。市のデータでも Water/Spray Parks は Playgrounds と別に数えている
- 記録していないもの: Mundell の遊具は人が多く、すべり台とトンネル以外（右手の弧の形の登り遊具など）は形が確かめられない。Brockhouse の水路の緑の門の形の部品（水をせき止める物か）も未確認

## 2026-10-12 3 回目の現地調査: Kids Tree Canopy Adventure（Grouse Mountain）を例外として載せた

Grouse Mountain の山頂の子どもの遊び場で 11 枚撮った（Pixel 9a 10 枚、iPhone 12 mini 1 枚。どれも中村が撮影）。Google マップの名前は Kids Tree Canopy Adventure。

- 範囲の判断: バンクーバー市の外（ノースバンクーバー郡）。しかも Grouse Mountain のリゾートの有料の区域（Skyride で上がる）の中で、写真ガイドの「誰でも入れる遊び場だけ」に当たらない。
  本人の判断で、例外として載せた。説明文に、市の外であること・有料の区域であること・例外であることを書いた。ガイドそのものは変えていない
- 中身: 網の橋でつながったツリーハウス、斜面へ下りる筒形のすべり台、縦に登る筒形の網、木の橋。入口の看板によれば 3 歳以上が対象で、大人の付き添いが要る
- 語彙に 2 語を足した: ツリーハウス（treehouse、複合遊具）、縦に登る筒形の網（net-climbing-tube、網の遊具）。網の橋は既存の rope-net-bridge を当てた。木の橋は固定の橋で、吊り橋（plank-bridge）ではないので当てていない。シカゴとの対応は未確認
- Commons: 9 枚を上げた（`Kids Tree Canopy Adventure, Grouse Mountain, North Vancouver, 2026-10 01〜09`）。分類 `Category:Kids Tree Canopy Adventure` を新設（上位: Grouse Mountain、Playgrounds in British Columbia、Treehouses in Canada）。市の外なので「Playgrounds in Vancouver」は付けていない（`default_categories` を no）
- 上げなかった 2 枚: 木に掛けた看板 2 つ（年齢と付き添いの注意、Grouse Mountain の免責の掲示）。前回と同じく、平面の掲示が主役の写真はパノラマの自由の外のため
- モザイク: 網の橋の上の子ども（04・07）と、09 の右の人を自動で塗った。09 ではツリーハウスの丸窓を顔と見て塗っている（塗りすぎの側なので残した）
- iPhone の写真は HEIC なので、JPEG に変えてから EXIF を写した（`sips` → `exiftool -TagsFromFile`）
- 落とし穴: 02〜06 の 5 枚は撮影地点が同じ値（49.381678, -123.079689）で、遊び場から約 350 m 東にずれている。山頂の建物の辺りで測った位置が更新されていない。
  Commons のページの位置もこの値のまま。サイトの公園の位置は 08 の撮影地点（49.380117, -123.083992）を使った
- 残っていること: サイトの「Commons に投稿する」リンクは、分類を「Playground survey in Vancouver」、見出しを「…, Vancouver」で作る。市の外の公園では合わない
