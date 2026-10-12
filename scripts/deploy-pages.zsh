#!/usr/bin/env zsh
# Builds the site (Japanese at /, English at /en/) and publishes it to the gh-pages branch,
# which GitHub Pages serves at https://play.ldas.jp (Settings → Pages → Deploy from a branch: gh-pages, /).
# Publishing from a branch uses no Actions minutes.
#
# Prerequisites: Docker running; run on main with main up to date.
# Usage: zsh scripts/deploy-pages.zsh
# What it does: copies collection/ and vocab/ into site/_data/, builds both languages in Docker (ruby:3.3),
# builds with JEKYLL_ENV=production (CollectionBuilder adds the description, OGP and DC meta tags only then),
# adds .nojekyll (the build is already done; GitHub must not run Jekyll again), and force-pushes site/_site/
# as one commit to origin/gh-pages. The branch keeps no history: it is a build output.
set -euo pipefail

root=${0:A:h:h}
cd "$root"
branch=$(git rev-parse --abbrev-ref HEAD)
if [[ $branch != main ]]; then print -u2 "deploy-pages: run on main (now on $branch)"; exit 1; fi
if [[ -n $(git status --porcelain -- collection vocab site) ]]; then print -u2 "deploy-pages: commit collection/, vocab/ and site/ first"; exit 1; fi
rev=$(git rev-parse --short HEAD)
remote=$(git remote get-url origin)

zsh scripts/sync_site_data.zsh
rm -rf site/_site
docker run --rm -v "$root/site":/srv -w /srv -e BUNDLE_PATH=vendor/bundle-docker -e JEKYLL_ENV=production ruby:3.3 sh -c 'bundle install --quiet && bundle exec jekyll build && bundle exec jekyll build --config _config.yml,_config.en.yml -d _site/en'
touch site/_site/.nojekyll

tmp=$(mktemp -d)
cp -R site/_site/. "$tmp"
cd "$tmp"
git init -q -b gh-pages
git add -A
git -c user.name="$(git -C "$root" config user.name)" -c user.email="$(git -C "$root" config user.email)" commit -q -m "Build of main $rev"
git push -q --force "$remote" gh-pages
cd "$root"
rm -rf "$tmp"
print "deploy-pages: pushed the build of $rev to gh-pages ($(du -sh site/_site | cut -f1))"
