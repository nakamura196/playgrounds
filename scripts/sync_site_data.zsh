#!/usr/bin/env zsh
# collection/ と vocab/ の CSV を、サイト（site/_data/）に写す。
# 正本は collection/ と vocab/。site/_data/ 側は直接書き換えない。
# 使い方: zsh scripts/sync_site_data.zsh
set -euo pipefail
ROOT=${0:A:h:h}
cp $ROOT/collection/playgrounds.csv $ROOT/site/_data/playgrounds.csv
for f in categories types products amenities; do
  cp $ROOT/vocab/$f.csv $ROOT/site/_data/vocab/$f.csv
done
echo "copied: playgrounds.csv, vocab/{categories,types,products,amenities}.csv"
