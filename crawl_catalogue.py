# -*- coding: utf-8 -*-
"""Build the searchable copy of the Koha catalogue used by LIBRARY.html.

Reads the public OPAC result pages (lavasaopac.christuniversity.in) with several broad
queries, merges them by biblionumber and writes library-catalogue.json next to this script:

    {"built": "YYYY-MM-DD", "n": 11875, "r": [{"i": 26537, "t": "title", "a": "author",
     "p": "publisher, year", "c": "call number"}, ...]}

    python crawl_catalogue.py            # full crawl
    python crawl_catalogue.py --quick    # first 2 pages per query (test)

update.sh runs this daily and pushes the file; LIBRARY.html reads it from raw.githubusercontent.com.
"""
import datetime
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "library-catalogue.json")
OPAC = "https://lavasaopac.christuniversity.in/cgi-bin/koha/opac-search.pl"
QUERIES = ["a", "the", "of", "and", "in", "to", "for", "by", "on", "with", "an", "i", "management", "law", "india", "journal", "2020", "2015", "2010", "2005"]
COUNT = 100
DELAY = 0.4


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; LavasaLibraryIndex/1.0)"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            time.sleep(2 + attempt * 3)
    return ""


def txt(s):
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<br\s*/?>", " · ", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]*>", " ", s))
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([.,;])", r"\1", s)
    return s.strip()


def field(chunk, cls):
    m = re.search(r'<div class="results_summary %s">(.*?)</div>' % cls, chunk, re.S)
    if not m:
        return ""
    return txt(re.sub(r'<span class="label">.*?</span>', "", m.group(1), count=1, flags=re.S))


def records(page):
    out = []
    for chunk in page.split('<td class="selectcol">')[1:]:
        m = re.search(r'<a href="[^"]*biblionumber=(\d{1,9})"[^>]*class="title"[^>]*>(.*?)</a>', chunk, re.S)
        if not m:
            continue
        title = txt(re.sub(r'<span class="title_resp_stmt">.*?</span>', "", m.group(2), count=1, flags=re.S))
        title = re.sub(r"\s*[/:;,.]+\s*$", "", title)
        if not title:
            continue
        ul = re.search(r'<ul class="author resource_list">(.*?)</ul>', chunk, re.S)
        authors = [txt(x) for x in re.findall(r"<li>(.*?)</li>", ul.group(1), re.S)] if ul else []
        authors = [re.sub(r"\s*\[[^\]]*\]\s*$", "", a) for a in authors if a][:3]
        cn = re.search(r'<span class="CallNumber">(.*?)</span>', chunk, re.S)
        out.append({"i": int(m.group(1)), "t": title[:220], "a": "; ".join(authors)[:140],
                    "p": field(chunk, "publisher")[:110], "c": txt(cn.group(1))[:40] if cn else ""})
    return out


def main():
    quick = "--quick" in sys.argv
    tmp = OUT + ".tmp"
    seen = {}
    for q in QUERIES:
        offset, total = 0, None
        while True:
            url = "%s?idx=kw&q=%s&count=%d&offset=%d" % (OPAC, urllib.parse.quote(q), COUNT, offset)
            page = get(url)
            if total is None:
                m = re.search(r"returned\s+([\d,]+)\s+result", page)
                total = int(m.group(1).replace(",", "")) if m else 0
            rs = records(page)
            for r in rs:
                seen[r["i"]] = r
            offset += COUNT
            if not rs or offset >= total or (quick and offset >= 2 * COUNT):
                break
            time.sleep(DELAY)
        print("%-12s total %5s  collected %6d" % (q, total, len(seen)), flush=True)
        time.sleep(DELAY)
    rs = sorted(seen.values(), key=lambda r: r["i"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    if len(rs) < 5000 and not quick:
        sys.exit("only %d records collected; keeping the previous file" % len(rs))
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"built": datetime.date.today().isoformat(), "n": len(rs), "r": rs}, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, OUT)
    print("wrote", len(rs), "records,", os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
