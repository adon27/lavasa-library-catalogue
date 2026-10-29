#!/bin/sh
cd "$(dirname "$0")" || exit 1
n=0
until python3 -I crawl_catalogue.py; do
  n=$((n+1))
  [ "$n" -ge 3 ] && exit 1
  sleep 1800
done
git add library-catalogue.json
if git diff --cached --quiet; then
  echo "no change"
  exit 0
fi
git -c user.name="Adon Dominic" -c user.email="71404040+adon27@users.noreply.github.com" commit -q -m "Catalogue update $(date +%F)"
git push -q origin HEAD
