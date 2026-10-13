# frozen_string_literal: true

# Adds a `<field>_name` column to the collection data for every field that has a
# `vocab` table in _data/config-metadata.csv (now: equipment → types, amenities → amenities). The column
# holds the labels of the ids in the site's language (label_<lang>, then label_en,
# then the id), joined with ";".
#
# The `<field>` column keeps the ids: item pages link them to /vocab/#<id> and the
# JSON-LD points at the concepts. Browse filters and search (lunr store and the
# cjk_index preset, both reading _data/config-search.csv) use `<field>_name`, so
# people filter and search by "ぶらんこ" / "Swings", not by "swing".
#
# It also writes, on each term of the table, `count_<field>` (how many items have
# that id) and `browse_name` (the label used in `<field>_name`), so the vocab page
# can link a term to /browse.html#<field>_name:<label>. Browse matches by
# substring, so a label inside another label (e.g. 雲梯) would show more items
# than counted; that case is reported as a build warning.
#
# Runs at :post_read, before the generators (item pages, cjk_index) read the data.
module VocabLabels
  def self.add_label_columns(site)
    rows = site.data[site.config['metadata'].to_s]
    return unless rows.is_a?(Array)

    lang = site.config['lang'].to_s
    Array(site.data['config-metadata']).each do |f|
      vocab = f['vocab'].to_s
      next if vocab.empty?

      table = Array(site.data.dig('vocab', vocab))
      labels = table.to_h do |t|
        [t['id'].to_s, [t["label_#{lang}"], t['label_en'], t['id']].map(&:to_s).find { |l| !l.strip.empty? }]
      end
      field = f['field']
      counts = Hash.new(0)
      rows.each do |row|
        ids = row[field].to_s.split(';').map(&:strip).reject(&:empty?)
        ids.uniq.each { |id| counts[id] += 1 }
        row["#{field}_name"] = ids.map { |id| labels.fetch(id, id) }.join(';') unless ids.empty?
      end
      table.each do |t|
        id = t['id'].to_s
        t['browse_name'] = labels[id]
        t["count_#{field}"] = counts[id]
        next if counts[id].zero?

        shown = rows.count { |row| row["#{field}_name"].to_s.upcase.include?(labels[id].upcase) }
        next if shown == counts[id]

        Jekyll.logger.warn 'VocabLabels:', "#{field}:#{labels[id]} links to #{shown} items in browse, but #{counts[id]} have the id #{id}"
      end
    end
  end
end

Jekyll::Hooks.register :site, :post_read do |site|
  VocabLabels.add_label_columns(site)
end
