"""Check that every rebuilt subpage of site-moi keeps the content of its original in site-goc.

Compares, inside each page's view block, the counts of: data-i18n texts, inline translations (data-en,
data-en-alt), image sources and alts, links, and product figures. Also checks that <head> only differs
in the stylesheet, fonts and theme colour.

    python tools/check_pages.py
"""
import re
import sys
from collections import Counter

from build_pages import GOC, MOI, PAGES, read

# Removed on purpose (user request, 2026-10-25): "Hình ảnh sản phẩm từ website chính thức của các hãng."
ALLOWED_MISSING = {"i18n": {("prod.gallery.note", "Hình ảnh sản phẩm từ website chính thức của các hãng.")}}

CHECKS = {
    "i18n": r'data-i18n="([^"]+)">(.*?)</',
    "data-en": r'data-en="([^"]*)"',
    "data-en-alt": r'data-en-alt="([^"]*)"',
    "img": r'<img src="([^"]+)"',
    "alt": r'alt="([^"]*)"',
    "href": r'href="([^"]+)"',
    "figure": r'<figure',
    # every piece of visible text between tags, whitespace-collapsed
    "text": r'>([^<>]*\S[^<>]*)<',
}
ALLOWED_MISSING["text"] = {"Hình ảnh sản phẩm từ website chính thức của các hãng."}
HEAD_CHANGES = ("theme-color", "/assets/fonts/", "/assets/css/", "format-detection")
# +1 format-detection meta, -1 line: three Google Fonts lines became two font preloads
HEAD_LINE_DELTA = 0
# Pages whose content must be copied byte for byte: route -> (first marker, last marker) of the block
VERBATIM = {"chinh-sach-bao-mat": ("<!-- Vietnamese version -->", "</article>\n        </div>")}


# Section kicker labels removed on purpose (quieter pass, 2026-10-28): headings carry the section on their own
REMOVED_LABEL_KEYS = {"tech.process.eyebrow", "int.process.eyebrow", "prod.svc.eyebrow", "prod.faq.eyebrow"}
DECORATIVE_IMG = re.compile(r'<img [^>]*alt=""[^>]*>')
# Photo galleries added at the user's request (2026-10-28, /noi-that/): new content, not in site-goc
ADDED_BLOCK = re.compile(r'<!-- gallery -->.*?<!-- /gallery -->', re.S)


def normalize(name, match):
    return " ".join(match.split()) if name == "text" else match


def view_of(html, route):
    return html[html.index("<!-- view:%s -->" % route):html.index("<!-- /view:%s -->" % route)]


def main():
    failed = 0
    for page in PAGES:
        route = page["route"]
        old = read(GOC, page["path"], "index.html")
        new = read(MOI, page["path"], "index.html")
        old_view, new_view = view_of(old, route), ADDED_BLOCK.sub("", view_of(new, route))
        problems = []
        for name, pattern in CHECKS.items():
            a = Counter(normalize(name, m) for m in re.findall(pattern, old_view, re.S))
            b = Counter(normalize(name, m) for m in re.findall(pattern, new_view, re.S))
            # decorative images added by the redesign (alt="") may repeat a content photo; they are not content
            b_content = Counter(normalize(name, m) for m in re.findall(pattern, DECORATIVE_IMG.sub("", new_view), re.S))
            removed = {txt for key, txt in re.findall(CHECKS["i18n"], old_view, re.S) if key in REMOVED_LABEL_KEYS}
            removed = {" ".join(x.split()) for x in removed}
            missing = {k: v for k, v in (a - b).items()
                       if k not in ALLOWED_MISSING.get(name, ())
                       and not (name == "i18n" and k[0] in REMOVED_LABEL_KEYS)
                       and not (name == "text" and k in removed)}
            if missing:
                problems.append("%s missing %s" % (name, missing))
            # i18n/href may legitimately repeat (index panel, extra call button); everything else must not
            if name not in ("i18n", "href", "alt", "text") and b_content - a:
                problems.append("%s extra %s" % (name, dict(b_content - a)))
        if route in VERBATIM:
            start, end = VERBATIM[route]
            block = old_view[old_view.index(start):old_view.rindex(end) + len(end)]
            if block not in new_view:
                problems.append("verbatim block changed")
        old_head = old[:old.index("<body")].splitlines()
        new_head = new[:new.index("<body")].splitlines()
        changed = [l for l in new_head if l not in old_head]
        if any(not any(c in l for c in HEAD_CHANGES) for l in changed) or len(new_head) - len(old_head) != HEAD_LINE_DELTA:
            problems.append("head changed: %s" % changed)
        print("%-24s %s" % (route, "OK" if not problems else "FAIL"))
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
