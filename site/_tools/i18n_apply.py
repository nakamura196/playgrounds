#!/usr/bin/env python3
"""Replace hard-coded English UI strings with locale lookups.

Each replacement becomes {{ t.<key> | default: "<English>" }}, so a site
without _data/locale/<lang>.yml renders exactly as before. The file also
gets `{%- assign t = site.data.locale[site.lang] -%}` at its top.
Idempotent: strings already replaced are skipped.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSIGN = '{%- assign t = site.data.locale[site.lang] -%}\n'

# file -> list of (exact old text, key, English default)
# - ">Text<" text nodes and attr="Text" attributes become {{ t.key | default: "Text" }}
# - RAW entries (key, exact HTML) become {% if t.key %}{{ t.key }}{% else %}HTML{% endif %},
#   for text containing markup or quotes
R = {
    '_includes/feature/modal.html': [
        ('aria-label="Close"', 'close', 'Close'),
    ],
    '_includes/collection-side-nav.html': [
        ('aria-label="Close"', 'close', 'Close'),
    ],
    '_includes/collection-nav.html': [
        ('aria-label="Toggle navigation"', 'toggle_navigation', 'Toggle navigation'),
    ],
    '_layouts/default.html': [
        ('>Skip to main content<', 'skip_to_content', 'Skip to main content'),
    ],
    '_layouts/search.html': [
        ('aria-label="Close"', 'close', 'Close'),
        ('>Search Options<', 'search_options', 'Search Options'),
        ('>Lunr Search Options<', 'search_options', 'Search Options'),
        ('placeholder="Enter your search term..."', 'search_placeholder', 'Enter your search term...'),
        ('aria-label="Search terms"', 'search_terms', 'Search terms'),
    ],
    '_includes/nav-search-lunr.html': [
        ('placeholder="Search"', 'search', 'Search'),
        ('aria-label="Search collection items"', 'search_collection_items', 'Search collection items'),
    ],
    '_includes/item/breadcrumbs.html': [
        ('>Home<', 'home', 'Home'),
        ('>Items<', 'items', 'Items'),
    ],
    '_includes/item/citation-box.html': [
        ('>Attribution<', 'attribution', 'Attribution'),
        ('<dt>Citation:</dt>', 'citation', 'Citation:'),
    ],
    '_includes/item/rights-box.html': [
        ('>Rights<', 'rights', 'Rights'),
        ('>Rights:<', 'rights_label', 'Rights:'),
        ('>Standardized Rights:<', 'rights_standardized', 'Standardized Rights:'),
    ],
    '_includes/item/browse-buttons.html': [
        ('>&laquo; Previous<', 'previous', '&laquo; Previous'),
        ('>Back to Browse<', 'back_to_browse', 'Back to Browse'),
        ('>Next &raquo;<', 'next', 'Next &raquo;'),
    ],
    '_layouts/item/item-page-base.html': [
        ('>Item Info \n', 'item_info', 'Item Info'),
        ('aria-label="Jump to Item Info"', 'jump_to_item_info', 'Jump to Item Info'),
    ],
    '_layouts/browse.html': [
        ('aria-label="select search field to filter"', 'select_filter_field', 'select search field to filter'),
        ('title="Filter options"', 'filter_options', 'Filter options'),
        ('aria-label="Search"', 'search', 'Search'),
        ('aria-label="Start Date"', 'start_date', 'Start Date'),
        ('aria-label="End Date"', 'end_date', 'End Date'),
        ('>to<', 'to', 'to'),
        ('title="Filter items"', 'filter_items', 'Filter items'),
        ('placeholder="Filter ... "', 'filter_placeholder', 'Filter ... '),
        ('>All Fields<', 'all_fields', 'All Fields'),
        ('>Title<', 'title', 'Title'),
        ('>Content Type<', 'content_type', 'Content Type'),
        ('>Advanced Search...<', 'advanced_search', 'Advanced Search...'),
        ('>Search<', 'search', 'Search'),
        ('>Reset<', 'reset', 'Reset'),
        ('>Random<', 'random', 'Random'),
        ('placeholder="Start Date"', 'start_date', 'Start Date'),
        ('placeholder="End Date"', 'end_date', 'End Date'),
        ('>Loading...<', 'loading', 'Loading...'),
    ],
    '_includes/footer.html': [
        ('>built with<', 'built_with', 'built with'),
        ('>Last updated ', 'last_updated', 'Last updated'),
    ],
    '_includes/advanced-search-modal.html': [
        ('aria-label="Close"', 'close', 'Close'),
        ('aria-label="Boolean option"', 'boolean_option', 'Boolean option'),
        ('>AND<', 'op_and', 'AND'),
        ('>OR<', 'op_or', 'OR'),
        ('>NOT<', 'op_not', 'NOT'),
        ('aria-label="Metadata Field"', 'metadata_field', 'Metadata Field'),
        ('aria-label="Start Date"', 'start_date', 'Start Date'),
        ('placeholder="Start Date"', 'start_date', 'Start Date'),
        ('aria-label="End Date"', 'end_date', 'End Date'),
        ('placeholder="End Date"', 'end_date', 'End Date'),
        ('>to<', 'to', 'to'),
        ('>Advanced Search<', 'advanced_search_title', 'Advanced Search'),
        ('>Close<', 'close', 'Close'),
        ('>Search<', 'search', 'Search'),
        ('>All Fields<', 'all_fields', 'All Fields'),
        ('>Title<', 'title', 'Title'),
        ('aria-label="Remove condition"', 'remove_condition', 'Remove condition'),
        ('placeholder="Enter search term"', 'enter_search_term', 'Enter search term'),
        ('aria-label="Search term"', 'search_terms', 'Search term'),
    ],
    '_includes/data-download-modal.html': [
        ('>Metadata CSV<', 'dl_metadata_csv', 'Metadata CSV'),
        ('>Metadata JSON<', 'dl_metadata_json', 'Metadata JSON'),
        ('>Facets JSON<', 'dl_facets_json', 'Facets JSON'),
        ('>TimelineJS JSON<', 'dl_timeline_json', 'TimelineJS JSON'),
        ('>Download Data<', 'download_data', 'Download Data'),
        ('>Collection Data<', 'collection_data', 'Collection Data'),
        ('>Complete Metadata<', 'dl_complete', 'Complete Metadata'),
        ('>Metadata Facets<', 'dl_facets', 'Metadata Facets'),
        ('>Timeline<', 'timeline', 'Timeline'),
        ('>Website Source Code<', 'dl_source', 'Website Source Code'),
        ('>Source Code<', 'source_code', 'Source Code'),
        ('aria-label="Close"', 'close', 'Close'),
    ],
    '_includes/scroll-to-top.html': [
        ('aria-label="Up Arrow"', 'up_arrow', 'Up Arrow'),
        ('title="Back to Top"', 'back_to_top', 'Back to Top'),
        ('>Back to top<', 'back_to_top', 'Back to Top'),
    ],
    '_includes/collection-banner.html': [
        ('>Featured Image<', 'featured_image', 'Featured Image'),
    ],
    '_includes/js/browse-js.html': [
        ('>View Full Record<', 'view_full_record', 'View Full Record'),
    ],
}


RAW = {
    '_includes/data-download-modal.html': [
        ('dl_complete_desc', 'All metadata fields for all collection items, available as a CSV spreadsheet (usable in Excel, Google Sheets, and similar programs) or JSON file (often used with web applications).'),
        ('dl_facets_desc', 'List of unique values and their count for specific metadata fields, useful for understanding content of the fields.'),
        ('dl_timeline_desc', 'A time-focused JSON data export designed for use with <a href="https://timeline.knightlab.com/">TimelineJS</a>.'),
        ('dl_source_desc', 'GitHub repository containing source code for this project built with <a href="https://github.com/CollectionBuilder/collectionbuilder-csv">CollectionBuilder-CSV</a>.'),
        ('dl_intro', "Download this collection's data in a variety of reusable formats."),
    ],
    '_includes/advanced-search-modal.html': [
        ('add_another_field', 'Add Another Field'),
    ],
    '_layouts/about.html': [
        ('toc_title', '\n                    Contents\n'),
    ],
}


# ---- Entries for the upstream template as of 2026-09 (33c5271). Merged into R/RAW.
ITEM_BUTTONS = [
    ('aria-label="Item options"', 'item_options', 'Item options'),
    ('>View Transcript<', 'view_transcript', 'View Transcript'),
    ('>View on Timeline<', 'view_on_timeline', 'View on Timeline'),
    ('>View on Map<', 'view_on_map', 'View on Map'),
]
ITEM_BUTTONS_PLAIN = [
    ('%}View on Vimeo{%', '%}{{ t.view_on_vimeo | default: "View on Vimeo" }}{%'),
    ('%}View on YouTube{%', '%}{{ t.view_on_youtube | default: "View on YouTube" }}{%'),
    ('%}Link to Object{%', '%}{{ t.link_to_object | default: "Link to Object" }}{%'),
    ('%}Download {{', '%}{{ t.download | default: "Download" }} {{'),
]
EXTRA_R = {
    '_includes/item/download-buttons.html': ITEM_BUTTONS,
    '_includes/item/child/download-buttons.html': ITEM_BUTTONS,
    '_includes/item/child/compound-item-download-buttons.html': ITEM_BUTTONS + [
        ('>\n            Download\n        <', 'download', 'Download'),
    ],
    '_includes/item/mini-map.html': [('>View on Full Map<', 'view_on_full_map', 'View on Full Map')],
    '_includes/item/image-gallery.html': [('>Click to view full screen<', 'click_full_screen', 'Click to view full screen')],
    '_includes/item/child/image-gallery.html': [('>Click to view full screen<', 'click_full_screen', 'Click to view full screen')],
    '_includes/item/child/compound-item-modal-gallery.html': [
        ('aria-label="Previous Item"', 'previous_item', 'Previous Item'),
        ('>Previous Item<', 'previous_item', 'Previous Item'),
        ('aria-label="Next Item"', 'next_item', 'Next Item'),
        ('>Next Item<', 'next_item', 'Next Item'),
    ],
    '_layouts/data.html': [('>Link<', 'link', 'Link')],
    '_includes/collection-banner.html': [('title="Visit background image record"', 'visit_banner_record', 'Visit background image record')],
    '_includes/data-download-modal.html': [
        ('>Subject Metadata<', 'dl_subjects', 'Subject Metadata'),
        ('>Subjects CSV<', 'dl_subjects_csv', 'Subjects CSV'),
        ('>Subjects JSON<', 'dl_subjects_json', 'Subjects JSON'),
        ('>Locations<', 'locations', 'Locations'),
        ('>Locations CSV<', 'dl_locations_csv', 'Locations CSV'),
        ('>Locations JSON<', 'dl_locations_json', 'Locations JSON'),
        ('>Geodata JSON<', 'dl_geodata_json', 'Geodata JSON'),
    ],
    '_layouts/search.html': [],
    '_layouts/map.html': [('>Map of Collection Items<', 'map_heading', 'Map of Collection Items')],
    '_includes/cb/credits.html': [('>Technical Credits - CollectionBuilder<', 'technical_credits', 'Technical Credits - CollectionBuilder')],
    '_includes/index/description.html': [],
    '_includes/index/data-download.html': [
        ('>Download this collection\'s metadata in a variety of reusable formats.<', 'collection_as_data_desc', "Download this collection's metadata in a variety of reusable formats."),
        ('>Metadata CSV<', 'dli_metadata_csv', 'Metadata CSV'),
        ('>Metadata JSON<', 'dli_metadata_json', 'Metadata JSON'),
        ('>Subjects CSV<', 'dli_subjects_csv', 'Subjects CSV'),
        ('>Subjects JSON<', 'dli_subjects_json', 'Subjects JSON'),
        ('>Geodata JSON<', 'dli_geodata_json', 'Geodata JSON'),
        ('>Locations CSV<', 'dli_locations_csv', 'Locations CSV'),
        ('>Locations JSON<', 'dli_locations_json', 'Locations JSON'),
        ('>Timeline JSON<', 'dli_timeline_json', 'Timeline JSON'),
        ('>Facets JSON<', 'dli_facets_json', 'Facets JSON'),
        ('>Source Code<', 'source_code', 'Source Code'),
    ],
}
for _k, _v in EXTRA_R.items():
    R.setdefault(_k, []).extend(_v)

EXTRA_RAW = {
    '_includes/data-download-modal.html': [
        ('dl_subjects_desc', 'Unique values and counts of subject metadata, useful for further analyzing the content of this collection.'),
        ('dl_locations_desc', "Unique values and counts of location metadata, useful for further visualization and analysis of this collection's place names."),
        ('dl_geo_desc', 'Metadata for all collection items that have geographic coordinates in <a href="https://en.wikipedia.org/wiki/GeoJSON">GeoJSON</a> format, useful for further exploration and analysis of this collection through a geographical lens.'),
    ],
    '_layouts/search.html': [
        ('search_help_intro', 'These advanced options can be added to your query in the search box to refine your results:'),
        ('search_op_field', 'Search a specific field: use the field name, colon, then your query, e.g. <code>title:foo</code>, <code>date:1911</code>, <code>subject:tree</code>. In this collection you can use '),
        ('search_op_wildcard', 'Wildcards: add <code>*</code> to match any character(s), e.g. <code>foo*</code>, <code>*oo</code>. This is helpful for using a root to find words with all related endings.'),
        ('search_op_fuzzy', 'Fuzzy match: add <code>~</code> plus a number at the end of your query to specify a higher level of fuzziness in search, e.g. <code>foo~1</code>. This can help with misspellings.'),
        ('search_op_boost', 'Boost term: add <code>^</code> plus a number to boost the relevance of a term in your query, e.g. <code>foo^10</code>. This can help reduce clutter of unrelated results if one of your terms is most important.'),
    ],
    '_includes/cb/credits.html': [
        ('credits_p1', 'This digital collection was built with <a href="https://collectionbuilder.github.io/">CollectionBuilder</a>, an open source framework for creating digital collection and exhibit websites that is developed by librarians at the University of Idaho Library following the <a href="https://lib-static.github.io">Lib-Static</a> methodology.'),
        ('credits_p2', 'The projects uses the <a href="https://github.com/CollectionBuilder/collectionbuilder-csv">CollectionBuilder-CSV</a> template and the static site generator <a href="https://jekyllrb.com/">Jekyll</a> to create an engaging, metadata-driven interface for exploring the collection contents.'),
    ],
}
for _k, _v in EXTRA_RAW.items():
    RAW.setdefault(_k, []).extend(_v)

# PLAIN: (exact old text, exact new text). For text that sits inside Liquid tags, JS
# strings or multi-line markup. Each new text is protected while old is replaced, so
# a default that contains the old text does not get replaced again on a second run.
TPL_BADGE = '{{ t.template_labels[page.display_template] | default: page.display_template | replace: "_", " " | upcase }}'
PLAIN = {
    '_includes/js/lunr-js.html': [
        ('${results.length} Results found', '${ {{ t.results_found | default: "%n Results found" | jsonify }}.replace("%n", results.length) }'),
    ],
    '_includes/cb/jekyll-toc.html': [
        ('<a href="#technical">Technical</a>', '<a href="#technical">{{ t.technical | default: "Technical" }}</a>'),
    ],
    '_layouts/item/item-page-base.html': [
        ('{{ page.display_template | replace: "_", " " | upcase }}', TPL_BADGE),
        ('({{ children | size }} Items)', '({{ children | size }} {{ t.items_unit | default: "Items" }})'),
    ],
    '_layouts/item/item-page-full-width.html': [
        ('{{ page.display_template | replace: "_", " " | upcase }}', TPL_BADGE),
        ('({{ children | size }} Items)', '({{ children | size }} {{ t.items_unit | default: "Items" }})'),
    ],
    '_includes/item/download-buttons.html': ITEM_BUTTONS_PLAIN,
    '_includes/item/child/download-buttons.html': ITEM_BUTTONS_PLAIN,
    '_includes/item/child/compound-item-modal-gallery.html': [
        ('Item {{ forloop.index }} of {{ children | size }}',
         '{{ t.item_n_of | default: "Item %n of %total" | replace: "%n", forloop.index | replace: "%total", children.size }}'),
        ('{{ child.display_template | upcase | default: "Item" }}',
         '{{ t.template_labels[child.display_template] | default: child.display_template | default: "Item" | upcase }}'),
    ],
    '_includes/item/child/compound-item-download-buttons.html': [
        ('{% else %}Item {{ forloop.index }}{% endif %}', '{% else %}{{ t.item_n | default: "Item %n" | replace: "%n", forloop.index }}{% endif %}'),
    ],
    '_includes/collection-banner.html': [
        ('{{ site.organization-name | escape }} home"', '{{ site.organization-name | escape }}{{ t.org_home_suffix | default: " home" }}"'),
    ],
    '_includes/footer.html': [
        ('{{ site.organization-name | escape }} home"', '{{ site.organization-name | escape }}{{ t.org_home_suffix | default: " home" }}"'),
    ],
    '_layouts/browse.html': [
        ('Sort by <span id="sortFilter">', '{{ t.sort_by | default: "Sort by" }} <span id="sortFilter">'),
    ],
    '_includes/advanced-search-modal.html': [
        ('Advanced<span class="d-none d-md-inline"> Search</span>',
         '{{ t.advanced_short | default: "Advanced" }}<span class="d-none d-md-inline">{{ t.advanced_short_suffix | default: " Search" }}</span>'),
    ],
    '_layouts/search.html': [
        ('{{ fields | join: ", " }}.</li>', '{{ fields | join: ", " }}{{ t.search_op_field_end | default: "." }}</li>'),
        ('type="submit">\n                Search\n            </button>', 'type="submit">\n                {{ t.search | default: "Search" }}\n            </button>'),
    ],
    '_layouts/timeline.html': [
        ('{%- assign t = i | modulo: site.data.theme.year-nav-increment -%}', '{%- assign yr_mod = i | modulo: site.data.theme.year-nav-increment -%}'),
        ('{%- if t == 0 -%}', '{%- if yr_mod == 0 -%}'),
        ('        Year\n    </button>', '        {{ t.year_nav | default: "Year" }}\n    </button>'),
        ('</a> to <a href="#y{{ uniqueYears | last }}">', '</a> {{ t.to | default: "to" }} <a href="#y{{ uniqueYears | last }}">'),
    ],
    '_layouts/home-infographic.html': [
        ('{% include index/carousel.html title="Sample Items" %}',
         '{% assign ttl = t.sample_items | default: "Sample Items" %}{% include index/carousel.html title=ttl %}'),
        ('{% include index/featured-terms.html field="subject" title="Top Subjects" btn-color="primary" %}',
         '{% assign ttl = t.top_subjects | default: "Top Subjects" %}{% include index/featured-terms.html field="subject" title=ttl btn-color="primary" %}'),
        ('{% include index/featured-terms.html field="location" title="Locations" btn-color="outline-secondary" %}',
         '{% assign ttl = t.locations | default: "Locations" %}{% include index/featured-terms.html field="location" title=ttl btn-color="outline-secondary" %}'),
    ],
    '_includes/index/description.html': [
        ('h5">Description</', 'h5">{{ t.description | default: "Description" }}</'),
        ('>Learn More &raquo;<', '>{{ t.learn_more | default: "Learn More &raquo;" }}<'),
    ],
    '_includes/index/time.html': [
        ('h5">Time Span</', 'h5">{{ t.time_span | default: "Time Span" }}</'),
        ('{{ date-range | first }} to {{ date-range | last }}', '{{ date-range | first }} {{ t.to | default: "to" }} {{ date-range | last }}'),
        ('mt-2">View Timeline</a>', 'mt-2">{{ t.view_timeline | default: "View Timeline" }}</a>'),
    ],
    '_includes/index/data-download.html': [
        ('h5">Collection as Data</', 'h5">{{ t.collection_as_data | default: "Collection as Data" }}</'),
    ],
    '_includes/index/content.html': [
        # the loop variable was `t`, which would hide the locale table
        ('{% for t in types %}', '{% for tpl in types %}'),
        ("'item contains t'", "'item contains tpl'"),
        ('#display_template:{{ t }}"', '#display_template:{{ tpl }}"'),
        ('{{ t | upcase | replace: "_", " " }}', '{{ t.template_labels[tpl] | default: tpl | upcase | replace: "_", " " }}'),
        ('template=t %}', 'template=tpl %}'),
        ('h5">Content</', 'h5">{{ t.content | default: "Content" }}</'),
        ('{{ others }} OTHER ', '{{ others }} {{ t.other | default: "OTHER" }} '),
        ('{{ templates | size }} TOTAL ITEMS<br>', '{{ templates | size }} {{ t.total_items | default: "TOTAL ITEMS" }}<br>'),
        ('mt-2" href="{{ \'/data.html\' | relative_url }}">View table</a>', 'mt-2" href="{{ \'/data.html\' | relative_url }}">{{ t.view_table | default: "View table" }}</a>'),
    ],
    '_includes/index/carousel.html': [
        ('{%- assign btn-text = include.btn-text | default: "View Item" -%}', '{%- assign btn-text = include.btn-text | default: t.view_item | default: "View Item" -%}'),
        ('<span class="visually-hidden">Previous</span>', '<span class="visually-hidden">{{ t.carousel_prev | default: "Previous" }}</span>'),
        ('<span class="visually-hidden">Next</span>', '<span class="visually-hidden">{{ t.carousel_next | default: "Next" }}</span>'),
        ('aria-label="Slide ${i.toString()}"', 'aria-label="{{ t.slide | default: "Slide" }} ${i.toString()}"'),
    ],
    '_includes/js/table-js.html': [
        ('[ 25, 50, 100, "All"]]', '[ 25, 50, 100, {{ t.all | default: "All" | jsonify }}]]'),
        ("        buttons: [ 'excelHtml5', 'csvHtml5' ],\n",
         "        buttons: [ 'excelHtml5', 'csvHtml5' ],\n        {%- if t.datatables %}\n        // UI strings from _data/locale/<lang>.yml (DataTables language option)\n        language: {{ t.datatables | jsonify }},\n        {%- endif %}\n"),
    ],
    '_includes/js/map-js.html': [
        ("title: 'Search Map Items',", 'title: {{ t.map_search_title | default: "Search Map Items" | jsonify }},'),
        ("placeholder: 'Search map items...',", 'placeholder: {{ t.map_search_placeholder | default: "Search map items..." | jsonify }},'),
        ('>View Item</a></div>\';', '>\' + {{ t.view_item | default: "View Item" | jsonify }} + \'</a></div>\';'),
    ],
    '_includes/js/browse-js.html': [
        ('`${filteredItems.length} of {{ items | size }} items`',
         '{{ t.n_of_total | default: "%n of %total items" | jsonify }}.replace("%n", filteredItems.length).replace("%total", {{ items | size }})'),
        ("criteria.field === 'all' ? 'All Fields' :", 'criteria.field === \'all\' ? {{ t.all_fields | default: "All Fields" | jsonify }} :'),
        ("'display_template' === criteria.field ? 'Content Type' :", "'display_template' === criteria.field ? {{ t.content_type | default: \"Content Type\" | jsonify }} :"),
        ('displayValue = `${criteria.startDate} to ${criteria.endDate}`;',
         'displayValue = {{ t.date_range | default: "%s to %e" | jsonify }}.replace("%s", criteria.startDate).replace("%e", criteria.endDate);'),
        ('displayValue = `from ${criteria.startDate}`;', 'displayValue = {{ t.date_from | default: "from %s" | jsonify }}.replace("%s", criteria.startDate);'),
        ('displayValue = `until ${criteria.endDate}`;', 'displayValue = {{ t.date_until | default: "until %e" | jsonify }}.replace("%e", criteria.endDate);'),
        ('        Add Field\n    `;', '        {{ t.add_field | default: "Add Field" }}\n    `;'),
        ('${obj.display_template.toUpperCase().replace("_"," ")} ${mediaIcon}',
         '${((({{ t.template_labels | jsonify }}) || {})[obj.display_template] || obj.display_template).toUpperCase().replace("_"," ")} ${mediaIcon}'),
        ('title="link to ${obj.title}"', 'title="{{ t.link_to | default: "link to" }} ${obj.title}"'),
    ],
    '_includes/js/browse-simple-js.html': [
        ('filteredItems.length + " of {{ items | size }} items"',
         '{{ t.n_of_total | default: "%n of %total items" | jsonify }}.replace("%n", filteredItems.length).replace("%total", {{ items | size }})'),
        ("obj.template.toUpperCase().replace(\"_\",\" \") + ' '",
         "((({{ t.template_labels | jsonify }}) || {})[obj.template] || obj.template).toUpperCase().replace(\"_\",\" \") + ' '"),
        ('title="link to \' + obj.title + \'">View Full Record</a>',
         'title="{{ t.link_to | default: "link to" }} \' + obj.title + \'">{{ t.view_full_record | default: "View Full Record" }}</a>'),
    ],
}


def sub(old, key, default):
    lookup = '{{ t.%s | default: "%s" }}' % (key, default.replace('"', '&quot;'))
    if old.startswith('>') and old.endswith('<'):
        return '>' + lookup + '<'
    if old.startswith('>') and old.endswith(' \n'):
        return '>' + lookup + ' \n'
    if old.startswith('>') and old.endswith(' '):
        return '>' + lookup + ' '
    if old.startswith('<dt>'):
        return '<dt>' + lookup + '</dt>'
    m = re.match(r'^([\w-]+)="', old)
    if m:
        return '%s="%s"' % (m.group(1), lookup)
    raise ValueError(old)


for path in sorted(set(R) | set(RAW) | set(PLAIN)):
    reps = R.get(path, [])
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        continue
    s = open(p, encoding='utf-8').read()
    n = 0
    for key, html in RAW.get(path, []):
        wrapped = '{%% if t.%s %%}{{ t.%s }}{%% else %%}%s{%% endif %%}' % (key, key, html)
        if wrapped not in s and html in s:
            s = s.replace(html, wrapped)
            n += 1
    for old, key, default in reps:
        if old in s:
            s = s.replace(old, sub(old, key, default))
            n += 1
    for old, new in PLAIN.get(path, []):
        if old in s.replace(new, '\0'):
            s = s.replace(new, '\0').replace(old, new).replace('\0', new)
            n += 1
    if n and ASSIGN.strip() not in s:
        if s.startswith('---\n'):
            end = s.index('\n---\n', 4) + 5
            s = s[:end] + ASSIGN + s[end:]
        else:
            s = ASSIGN + s
    open(p, 'w', encoding='utf-8').write(s)
    print(f'{path}: {n} replaced')
