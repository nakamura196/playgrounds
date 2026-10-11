---
title: このサイトについて
layout: about
permalink: /about.html
credits: false
heading: このサイトについて
sub-heading:
padding: 4em
---

## 収録している公園

City of Vancouver のオープンデータ（[parks](https://opendata.vancouver.ca/explore/dataset/parks/) と [parks-facilities](https://opendata.vancouver.ca/explore/dataset/parks-facilities/)、2026-10-11 取得）から、遊び場のある公園を選びました。
1 件は 1 つの公園です。
オープンデータには遊び場ごとの位置がなく、公園ごとの数しかないためです。
地図の位置は公園の代表点で、遊び場そのものの位置ではありません。

公園の情報は Open Government Licence – Vancouver のもとで利用しています。

## 遊具の記録

遊具は、現地で写真を撮りながら記録します。
撮影は子どもが写らない時間に行い、子どもの写った写真は載せません。

遊具の種類は、形と動きで定義しています。
製品名を種類の名前にはせず、製品は別の表から種類を指します。
定義は [Chicago Playgrounds](https://chicagoplaygrounds.com/) の遊具の項目を参考にし、対応が確かめられたものは対応を記しています。
詳しくは[遊具の語彙](vocab/)をご覧ください。

## データの取り出し

- 公園の一覧: [データ](data.html)のページから CSV・JSON
- 各公園: `items/<番号>.jsonld`（schema.org の語彙で書いた JSON-LD）
- 遊具の語彙: [vocab/vocab.jsonld](vocab/vocab.jsonld)（SKOS）

このサイトは [CollectionBuilder](https://collectionbuilder.github.io/) で作っています。
