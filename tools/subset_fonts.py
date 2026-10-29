"""Subset the site's fonts to Latin + Vietnamese (plus every character the pages use) and save them as WOFF2.

Source TTFs come from Google Fonts (SIL Open Font License). Download them into a folder, then:

    python tools/subset_fonts.py <folder with BeVietnamPro-400.ttf ...>

Needs fontTools and brotli. Writes site-moi/assets/fonts/<name>.woff2, declared by @font-face in v2.css.
Run it again after adding text in a script other than Latin or Vietnamese.
"""
import glob
import html
import os
import sys

from fontTools import subset

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOI = os.path.join(ROOT, "site-moi")
FONTS = ["BeVietnamPro-400", "BeVietnamPro-500", "BeVietnamPro-600", "BeVietnamPro-700",
         "PlusJakartaSans-700", "PlayfairDisplay-500"]

# Full Latin-1 and Vietnamese coverage so later copy edits never fall back to another font
VIETNAMESE = {0x102, 0x103, 0x110, 0x111, 0x128, 0x129, 0x168, 0x169, 0x1A0, 0x1A1, 0x1AF, 0x1B0,
              0x300, 0x301, 0x303, 0x309, 0x323} | set(range(0x1EA0, 0x1EFA))
PUNCTUATION = {0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x2122, 0x2192, 0x20AB}


def used_codepoints():
    files = glob.glob(os.path.join(MOI, "**", "*.html"), recursive=True)
    files += [os.path.join(MOI, "assets", "js", name) for name in ("i18n-en.js", "main.js")]
    chars = set()
    for path in files:
        with open(path, encoding="utf-8") as f:
            chars |= set(html.unescape(f.read()))
    return {ord(c) for c in chars if ord(c) >= 0x20}


def main(src):
    unicodes = used_codepoints() | set(range(0x20, 0x7F)) | set(range(0xA0, 0x100)) | VIETNAMESE | PUNCTUATION
    out_dir = os.path.join(MOI, "assets", "fonts")
    os.makedirs(out_dir, exist_ok=True)
    for name in FONTS:
        options = subset.Options()
        options.flavor = "woff2"
        options.layout_features = ["*"]
        options.name_IDs = ["*"]
        options.notdef_outline = True
        options.desubroutinize = True
        font = subset.load_font(os.path.join(src, name + ".ttf"), options)
        subsetter = subset.Subsetter(options)
        subsetter.populate(unicodes=unicodes)
        subsetter.subset(font)
        out = os.path.join(out_dir, name + ".woff2")
        subset.save_font(font, out, options)
        print("%-22s %3d KB" % (name, os.path.getsize(out) // 1024))


if __name__ == "__main__":
    main(sys.argv[1])
