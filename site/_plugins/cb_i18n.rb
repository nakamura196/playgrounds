# frozen_string_literal: true

#########
#
# CollectionBuilder i18n helper
#
# Lets one repository build the same collection in several interface languages,
# one build per language (e.g. `jekyll build --config _config.yml,_config.en.yml`).
# Runs right after Jekyll reads the site, before any page is generated or rendered:
#
# 1. Page variants: a page whose front matter has `lang:` is kept only when it
#    matches site.lang, and then replaces the page without `lang:` at the same URL.
#    So pages/about.md (default) + pages/about.en.md (lang: en, same permalink)
#    gives the English text in the English build and the default text otherwise.
#    The variant inherits the default page's front matter; keys it sets win.
#
# 2. Config labels: _data/config-*.csv hold labels in the site's main language.
#    _data/locale/<lang>.yml can override them under `config_labels`, keyed by the
#    CSV's `field` column (`stub` for config-nav). A plain string sets display_name;
#    a hash sets any columns (display_name, facet_name, sort_name):
#
#      config_labels:
#        config-nav:
#          /browse.html: Browse
#        config-browse:
#          era: { facet_name: Period }
#
#    Templates keep reading f.display_name etc. unchanged.
#
#########

module CollectionBuilderI18n
  KEY_COLUMN = { 'config-nav' => 'stub' }.freeze

  def self.select_page_variants(site)
    lang = site.config['lang'].to_s
    variants = site.pages.select { |p| p.data['lang'] }
    return if variants.empty?

    # drop variants for other languages
    site.pages.reject! { |p| p.data['lang'] && p.data['lang'].to_s != lang }
    # a variant for this language replaces the default page at the same URL,
    # inheriting its front matter (layout, item lists, options), so the
    # variant only needs permalink, lang and the keys it translates
    defaults = site.pages.select { |p| p.data['lang'].nil? }.group_by(&:url)
    site.pages.select { |p| p.data['lang'] }.each do |v|
      base = defaults.fetch(v.url, []).first
      next unless base

      v.data.replace(base.data.merge(v.data))
      site.pages.delete(base)
    end
  end

  def self.apply_config_labels(site)
    lang = site.config['lang'].to_s
    labels = site.data.dig('locale', lang, 'config_labels')
    return unless labels.is_a?(Hash)

    labels.each do |csv, overrides|
      rows = site.data[csv]
      next unless rows.is_a?(Array) && overrides.is_a?(Hash)

      key = KEY_COLUMN.fetch(csv, 'field')
      rows.each do |row|
        o = overrides[row[key].to_s]
        next if o.nil?

        o = { 'display_name' => o } unless o.is_a?(Hash)
        # nav dropdown children point at their parent's display_name
        if csv == 'config-nav' && o['display_name'] && row['display_name']
          old = row['display_name']
          rows.each { |r| r['dropdown_parent'] = o['display_name'] if r['dropdown_parent'] == old }
        end
        o.each { |col, val| row[col] = val }
      end
    end
  end
end

Jekyll::Hooks.register :site, :post_read do |site|
  CollectionBuilderI18n.select_page_variants(site)
  CollectionBuilderI18n.apply_config_labels(site)
end
