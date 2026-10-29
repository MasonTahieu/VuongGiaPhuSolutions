"""Static pre-launch audit of site-moi: SEO tags, headings, links, images, translations, page weight.

    python tools/audit.py
"""
import json
import os
import re
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site-moi")


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []          # (tag, attrs)
        self.headings = []      # (level, text)
        self.ids = []
        self._h = None
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if "id" in a:
            self.ids.append(a["id"])
        if re.fullmatch(r"h[1-6]", tag):
            self._h = [int(tag[1]), ""]
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if self._h and tag == "h%d" % self._h[0]:
            self.headings.append((self._h[0], " ".join(self._h[1].split())))
            self._h = None
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._h:
            self._h[1] += data
        if self._in_title:
            self.title += data


def local_file(url):
    """Map a site URL (/x/y/, /a.png?v=1) to a file in site-moi, or None for external URLs."""
    u = urlparse(url)
    if u.scheme in ("http", "https") and u.netloc not in ("vuonggiaphu.com", "www.vuonggiaphu.com"):
        return None
    if u.scheme in ("mailto", "tel") or url.startswith("#") or u.scheme == "data":
        return None
    path = unquote(u.path)
    if not path:
        return None
    if path.endswith("/"):
        path += "index.html"
    return os.path.join(SITE, *path.strip("/").split("/"))


def main():
    pages = sorted(os.path.relpath(os.path.join(d, f), SITE).replace(os.sep, "/")
                   for d, _, fs in os.walk(SITE) for f in fs if f == "index.html")
    en = open(os.path.join(SITE, "assets", "js", "i18n-en.js"), encoding="utf-8").read()
    en_keys = set(re.findall(r"^\s*'([^']+)':", en, re.M))
    sitemap = open(os.path.join(SITE, "sitemap.xml"), encoding="utf-8").read()
    sitemap_paths = {urlparse(u).path for u in re.findall(r"<loc>([^<]+)</loc>", sitemap)}

    issues = {}
    weights = {}
    titles, descriptions = {}, {}
    for rel in pages:
        html = open(os.path.join(SITE, rel), encoding="utf-8").read()
        p = Page()
        p.feed(html)
        url_path = "/" + rel[:-len("index.html")]
        out = issues.setdefault(url_path, [])
        metas = {a.get("name") or a.get("property"): a.get("content") for t, a in p.tags if t == "meta"}
        links = [(a.get("rel"), a.get("href"), a.get("hreflang")) for t, a in p.tags if t == "link"]

        # --- SEO ---
        title = " ".join(p.title.split())
        desc = metas.get("description") or ""
        titles.setdefault(title, []).append(url_path)
        descriptions.setdefault(desc, []).append(url_path)
        if not 10 <= len(title) <= 65:
            out.append("title length %d: %s" % (len(title), title))
        if not 70 <= len(desc) <= 170:
            out.append("description length %d" % len(desc))
        canon = [h for r, h, _ in links if r == "canonical"]
        if canon != ["https://vuonggiaphu.com" + url_path]:
            out.append("canonical %s" % canon)
        if sorted(hl for r, _, hl in links if r == "alternate") != ["en", "vi", "x-default"]:
            out.append("hreflang set incomplete")
        for key in ("og:title", "og:description", "og:image", "og:url"):
            if not metas.get(key):
                out.append("missing %s" % key)
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            try:
                json.loads(block)
            except ValueError as e:
                out.append("JSON-LD invalid: %s" % e)
        if url_path not in sitemap_paths:
            out.append("not in sitemap.xml")
        h1 = [t for lvl, t in p.headings if lvl == 1]
        if len(h1) != 1:
            out.append("h1 count %d" % len(h1))
        last = 1
        for lvl, text in p.headings:
            if lvl > last + 1:
                out.append("heading jumps h%d -> h%d (%s)" % (last, lvl, text[:40]))
            last = lvl

        # --- ids, links, images ---
        dup = {i for i in p.ids if p.ids.count(i) > 1}
        if dup:
            out.append("duplicate ids %s" % sorted(dup))
        size = len(html.encode("utf-8"))
        images = []
        for tag, a in p.tags:
            for attr in ("href", "src", "data-src"):
                url = a.get(attr)
                if not url or (tag == "link" and a.get("rel") in ("canonical", "alternate", "preconnect")):
                    continue
                if url.startswith("#"):
                    if url[1:] and url[1:] not in p.ids:
                        out.append("anchor target missing %s" % url)
                    continue
                f = local_file(url)
                if f is None:
                    continue
                if tag == "a" and urlparse(url).fragment:
                    target_html = open(f, encoding="utf-8").read() if os.path.exists(f) else ""
                    if 'id="%s"' % urlparse(url).fragment not in target_html:
                        out.append("anchor target missing %s" % url)
                if not os.path.exists(f):
                    out.append("broken %s %s" % (attr, url))
            if tag == "img":
                if a.get("alt") is None:
                    out.append("img without alt %s" % a.get("src"))
                if not (a.get("width") and a.get("height")) and a.get("loading") != "lazy":
                    out.append("img without width/height (layout shift) %s" % a.get("src"))
                f = local_file(a.get("src", ""))
                if f and os.path.exists(f):
                    images.append((a.get("src"), os.path.getsize(f), a.get("loading") == "lazy"))
        # data-i18n keys must have an English translation
        markup = re.sub(r"<!--.*?-->", "", html, flags=re.S)  # the translation how-to comment mentions data-i18n="key"
        keys = set(re.findall(r'data-i18n="([^"]+)"', markup))
        for pair in re.findall(r'data-i18n-attr="([^"]+)"', markup):
            keys |= {kv.split(":")[1].strip() for kv in pair.split(";")}
        missing_en = sorted(k for k in keys if k not in en_keys)
        if missing_en:
            out.append("no English for %s" % missing_en)
        seen = {}
        for src, b, lazy in images:
            seen[src] = (b, lazy)
        weights[url_path] = (size, sum(b for b, _ in seen.values()), sum(b for b, lazy in seen.values() if not lazy), len(seen))

    for t, ps in titles.items():
        if len(ps) > 1:
            issues.setdefault("(site)", []).append("duplicate title on %s" % ps)
    for d, ps in descriptions.items():
        if len(ps) > 1:
            issues.setdefault("(site)", []).append("duplicate description on %s" % ps)

    print("== Issues ==")
    total = 0
    for page, out in issues.items():
        for o in out:
            print("%-32s %s" % (page, o))
            total += 1
    print("(%d issues)" % total)

    print("\n== Weight (KB): html | all images | images loaded up front | image count ==")
    for page, (h, img, eager, n) in sorted(weights.items(), key=lambda x: -x[1][1]):
        print("%-32s %6.1f | %7.1f | %7.1f | %d" % (page, h / 1024, img / 1024, eager / 1024, n))
    for name in ("assets/css/v2.css", "assets/js/main.js", "assets/js/i18n-en.js"):
        f = os.path.join(SITE, name)
        if os.path.exists(f):
            print("%-32s %6.1f KB" % (name, os.path.getsize(f) / 1024))


if __name__ == "__main__":
    main()
