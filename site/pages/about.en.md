---
# English version; inherits the rest of the front matter from the default page (_plugins/cb_i18n.rb)
title: About
permalink: /about.html
lang: en
heading: About
---

## The parks

Parks with playgrounds, taken from the City of Vancouver open data ([parks](https://opendata.vancouver.ca/explore/dataset/parks/) and [parks-facilities](https://opendata.vancouver.ca/explore/dataset/parks-facilities/), retrieved 2026-10-11).
Each record is one park, because the open data gives the number of playgrounds per park but not where each one is.
Map positions are the park's reference point, not the playground itself.

Park information contains information licensed under the Open Government Licence – Vancouver.

## Recording the equipment

Equipment is recorded on site visits with photographs.
Photographs are taken when no children are present, and no photograph showing children is published.

Equipment types are defined by shape and movement.
Product names are not used as type names; products are listed separately and point to a type.
The definitions draw on the equipment entries of [Chicago Playgrounds](https://chicagoplaygrounds.com/), with the correspondence noted where it has been checked.
See the [equipment vocabulary](vocab/).

## Getting the data

- All parks: CSV and JSON from the [Data](data.html) page
- Each park: `items/<id>.jsonld` (JSON-LD with schema.org)
- Equipment vocabulary: [vocab/vocab.jsonld](vocab/vocab.jsonld) (SKOS)

Built with [CollectionBuilder](https://collectionbuilder.github.io/).
