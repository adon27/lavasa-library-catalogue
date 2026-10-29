#!/bin/sh
cd "$(dirname "$0")" || exit 1
python3 -I crawl_catalogue.py || exit 1
git add library-catalogue.json
if git diff --cached --quiet; then
  echo "no change"
  exit 0
fi
git -c user.name="Adon Dominic" -c user.email="71404040+adon27@users.noreply.github.com" commit -q -m "Catalogue update $(date +%F)"
git push -q origin HEAD
