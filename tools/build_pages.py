"""Rebuild the subpages of site-moi in the v2 design: /cong-nghe/, /noi-that/, /thiet-bi/.

Content (Vietnamese text, data-i18n keys, SEO <head>) is read from the scraped original in site-goc;
the shared shell (header, contact, footer, icons) is taken from the redesigned site-moi/index.html.

    python tools/build_pages.py
"""
import hashlib
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOC = os.path.join(ROOT, "site-goc")
MOI = os.path.join(ROOT, "site-moi")

# Fonts are served from /assets/fonts (OFL, subset to Latin + Vietnamese by tools/subset_fonts.py, declared in
# v2.css); the body text face and the h1 face are preloaded, so pages no longer wait on fonts.googleapis.com.
FONTS_OLD = ('  <link rel="preconnect" href="https://fonts.googleapis.com">\n'
             '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
             '  <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap" rel="stylesheet">\n')
FONTS_NEW = ('  <link rel="preload" href="/assets/fonts/BeVietnamPro-400.woff2" as="font" type="font/woff2" crossorigin>\n'
             '  <link rel="preload" href="/assets/fonts/PlusJakartaSans-700.woff2" as="font" type="font/woff2" crossorigin>\n')


def versioned(url):
    """url with a content hash, so browsers fetch the new file whenever it changes."""
    with open(os.path.join(MOI, *url.strip("/").split("/")), "rb") as f:
        return url + "?v=" + hashlib.sha1(f.read()).hexdigest()[:8]


def stamp_homepage():
    """Point the hand-written homepage (the shell of every subpage) at the current asset versions.
    Returns the versioned stylesheet URL."""
    path = os.path.join(MOI, "index.html")
    html = read(path)
    new = html
    for attr, url in [("href", "/assets/css/v2.css"), ("src", "/assets/js/i18n-en.js"), ("src", "/assets/js/main.js")]:
        stamped = versioned(url)
        new = re.sub(r'%s="%s(\?v=[0-9a-f]+)?"' % (attr, re.escape(url)), '%s="%s"' % (attr, stamped), new, count=1)
        assert stamped in new, url
    new = responsive_imgs(new)
    if new != html:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)
    return versioned("/assets/css/v2.css")



# Product photos are 800px but never shown wider than ~42vw on phones or ~230px on desktop:
# offer the 500px copy (made by ffmpeg next to each photo) and let the browser pick.
# The /thiet-bi/ hero collage is shown up to ~400px and loads first, so it keeps the full photo.
PRODUCT_SIZES = "(max-width: 760px) 42vw, 230px"


def responsive_imgs(html):
    def add(m):
        tag, src = m.group(0), m.group(1)
        small = src[:-len(".webp")] + "-500.webp"
        if "srcset=" in tag or not os.path.exists(os.path.join(MOI, *small.strip("/").split("/"))):
            return tag
        return tag.replace('src="%s"' % src, 'src="%s" srcset="%s 500w, %s 800w" sizes="%s"' % (src, small, src, PRODUCT_SIZES), 1)
    parts = re.split(r'(<div class="hero-collage".*?</div>\s*</div>)', html, flags=re.S)
    return "".join(part if part.startswith('<div class="hero-collage"') else
                   re.sub(r'<img src="(/assets/img/products/[^"]+(?<!-500)\.webp)"[^>]*>', add, part)
                   for part in parts)


def read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read()


def between(text, start, end):
    a = text.index(start)
    return text[a:text.index(end, a)]


def tag(view, name, key=None):
    """Return (key, inner_html) of the first <name data-i18n=…> in view (optionally with a given key)."""
    pattern = r'<%s\b[^>]*data-i18n="(%s)"[^>]*>(.*?)</%s>' % (name, re.escape(key) if key else "[^\"]+", name)
    m = re.search(pattern, view, re.S)
    if not m:
        raise ValueError("missing <%s> %s" % (name, key or ""))
    return m.group(1), m.group(2).strip()


def build_service_view(page, view):
    route, anchor, cols = page["route"], page["anchor"], page["cols"]

    crumb = re.search(r'<nav class="breadcrumb".*?</nav>', view, re.S).group(0)
    h1_id, = re.search(r'<h1 id="([^"]+)"', view).groups()
    h1_key, h1 = tag(view, "h1")
    hero = between(view, '<div class="page-hero', '<div class="section">')
    lead_key, lead = tag(hero, "p")
    cta_key, cta = re.search(r'<a class="btn btn-primary"[^>]*><span data-i18n="([^"]+)">(.*?)</span>', hero).groups()

    services_block = between(view, '<div class="section">', '<div class="section section-alt">')
    s_eyebrow_key, s_eyebrow = tag(services_block, "p")
    s_title_key, s_title = tag(services_block, "h2")
    cards = re.findall(
        r'<article class="card">\s*<span class="card-icon"><svg class="icon"><use href="#([^"]+)"/></svg></span>\s*'
        r'<h3 data-i18n="([^"]+)">(.*?)</h3>\s*<p data-i18n="([^"]+)">(.*?)</p>\s*</article>', services_block, re.S)
    extra_link = re.search(r'<p class="center section-link">(.*?)</p>', services_block, re.S)

    process_block = between(view, '<div class="section section-alt">', '<div class="cta-band">')
    p_eyebrow_key, p_eyebrow = tag(process_block, "p")
    p_title_key, p_title = tag(process_block, "h2")
    steps = re.findall(r'<li><h3 data-i18n="([^"]+)">(.*?)</h3><p data-i18n="([^"]+)">(.*?)</p></li>', process_block)

    band = view[view.index('<div class="cta-band">'):]
    b_title_key, b_title = tag(band, "h2")
    b_text_key, b_text = tag(band, "p")

    assert cards and steps, route

    index_items = "\n".join(
        '                <li><a href="#%s-%d"><svg class="icon"><use href="#%s"/></svg>'
        '<span data-i18n="%s">%s</span><svg class="icon page-index-go"><use href="#i-arrow"/></svg></a></li>'
        % (anchor, i, icon, tkey, title) for i, (icon, tkey, title, _, _) in enumerate(cards, 1))

    card_items = "\n".join(
        '            <article class="svc" id="%s-%d">\n'
        '              <span class="svc-icon"><svg class="icon"><use href="#%s"/></svg></span>\n'
        '              <h3 data-i18n="%s">%s</h3>\n'
        '              <p data-i18n="%s">%s</p>\n'
        '            </article>' % (anchor, i, icon, tkey, title, dkey, desc)
        for i, (icon, tkey, title, dkey, desc) in enumerate(cards, 1))

    step_items = "\n".join(
        '            <li class="step"><span class="step-num" aria-hidden="true">%02d</span>'
        '<h3 data-i18n="%s">%s</h3><p data-i18n="%s">%s</p></li>' % (i, tk, t, dk, d)
        for i, (tk, t, dk, d) in enumerate(steps, 1))

    extra = ""
    if extra_link:
        extra = '\n          <p class="section-cta">%s</p>' % extra_link.group(1)
    gallery = build_gallery(route)

    return f'''<!-- view:{route} -->
    <section class="view" data-view="{route}" aria-labelledby="{h1_id}">

      <div class="page-hero">
        <div class="container page-hero-inner">
          <div class="page-hero-copy">
            {crumb}
            <h1 id="{h1_id}" data-i18n="{h1_key}">{h1}</h1>
            <p class="lead" data-i18n="{lead_key}">{lead}</p>
            <div class="hero-actions">
              <a class="btn btn-primary" href="#lien-he"><span data-i18n="{cta_key}">{cta}</span> <svg class="icon"><use href="#i-arrow"/></svg></a>
              <a class="btn btn-ghost" href="tel:+84963345099"><svg class="icon"><use href="#i-phone"/></svg> 0963.345.099</a>
            </div>
          </div>
          <nav class="page-index" aria-labelledby="{route}-index-title">
            <p class="page-index-title" id="{route}-index-title" data-i18n="{s_eyebrow_key}">{s_eyebrow}</p>
            <ol>
{index_items}
            </ol>
          </nav>
        </div>
      </div>
{gallery}
      <div class="section">
        <div class="container">
          <div class="section-head-split">
            <div>
              <h2 data-i18n="{s_title_key}">{s_title}</h2>
            </div>
          </div>
          <div class="svc-grid svc-grid-{cols}">
{card_items}
          </div>{extra}
        </div>
      </div>

      <div class="section section-sand">
        <div class="container">
          <div class="section-head-split">
            <div>
              <h2 data-i18n="{p_title_key}">{p_title}</h2>
            </div>
          </div>
          <ol class="steps">
{step_items}
          </ol>
        </div>
      </div>

      <div class="section">
        <div class="container">
          <div class="cta-band">
            <div>
              <h2 data-i18n="{b_title_key}">{b_title}</h2>
              <p data-i18n="{b_text_key}">{b_text}</p>
            </div>
            <a class="btn btn-light" href="#lien-he"><span data-i18n="cta.contactNow">Liên hệ ngay</span> <svg class="icon"><use href="#i-arrow"/></svg></a>
          </div>
        </div>
      </div>
    </section>
    '''


# Photos of finished interiors supplied by the user (2026-10-28), retouched and stored in /assets/img/cong-trinh/
# with a 600px copy. Not in site-goc: check_pages.py skips the block between the gallery comments.
# Each photo links to its large file; main.js opens it in a zoomable viewer instead (the link still works without JS).
# (file, width, height, VI alt, EN alt, VI caption, EN caption); captions stay short so they fit on a phone tile.
# The first photo is the tall one.
PROJECT_PHOTOS = {
    "noi-that": {
        "title": ("int.gallery.title", "Không gian đã hoàn thiện"),
        "lead": ("int.gallery.lead", "Một số hình ảnh thực tế các hạng mục tủ bếp, phòng khách, phòng ngủ và phòng tắm."),
        "photos": [
            ("bep-chu-l", 760, 904, "Tủ bếp chữ L, mặt đá tối màu và quầy bar bo tròn",
             "L-shaped kitchen with dark stone worktops and a rounded breakfast bar",
             "Tủ bếp chữ L & quầy bar", "L-shaped kitchen & bar"),
            ("phong-ngu-master", 1136, 768, "Phòng ngủ master, vách ốp và tủ áo kịch trần",
             "Master bedroom with a panelled wall and full-height wardrobe", "Phòng ngủ master", "Master bedroom"),
            ("phong-khach-ke-tivi", 900, 990, "Kệ tivi phòng khách, vách đá có đèn hắt",
             "Living-room TV unit with a backlit stone panel", "Kệ tivi phòng khách", "Living-room TV unit"),
            ("phong-ngu-ban-hoc", 1200, 844, "Phòng ngủ có bàn học và kệ sách", "Bedroom with a study desk and bookshelves",
             "Phòng ngủ & bàn học", "Bedroom & desk"),
            ("phong-ngu-tu-ao", 1200, 844, "Phòng ngủ với giường bọc nệm và tủ áo",
             "Bedroom with an upholstered bed and wardrobe", "Phòng ngủ & tủ áo", "Bedroom & wardrobe"),
        ],
        # Bathrooms: four portrait photos (3:4) in one even row under the grid above
        "row": [
            ("phong-tam-gach-xanh", 888, 1184, "Phòng tắm ốp gạch vảy cá xanh, lavabo đá và sen tắm đen",
             "Bathroom with green scallop wall tiles, a stone basin and a black shower set",
             "Phòng tắm gạch xanh", "Green-tile bathroom"),
            ("phong-tam-vach-da-xanh", 900, 1200, "Phòng tắm với vách đá xanh, gương tròn có đèn và lavabo đặt bàn",
             "Bathroom with a blue stone feature wall, a round backlit mirror and a countertop basin",
             "Phòng tắm đá xanh", "Blue-stone bathroom"),
            ("phong-tam-da-xam", 900, 1200, "Phòng tắm ốp gạch vân đá xám, gương đèn LED và lavabo treo",
             "Bathroom in grey stone-look tiles with an LED mirror and a wall-hung basin",
             "Phòng tắm đá xám", "Grey-stone bathroom"),
            ("phong-tam-lavabo-treo", 900, 1200, "Góc lavabo treo, gương viền vàng và bồn cầu một khối",
             "Wall-hung basin, brass-framed mirror and one-piece toilet",
             "Lavabo & gương vàng", "Basin & brass mirror"),
        ],
    },
}


def build_gallery(route):
    spec = PROJECT_PHOTOS.get(route)
    if not spec:
        return ""
    def item(photo, sizes):
        name, w, h, alt_vi, alt_en, vi, en = photo
        src = "/assets/img/cong-trinh/%s" % name
        return ('            <li><figure><a class="project-zoom" href="%s.webp" data-zoom>'
                '<img src="%s.webp" srcset="%s-600.webp 600w, %s.webp %dw" sizes="%s" width="%d" height="%d" '
                'alt="%s" data-en-alt="%s" loading="lazy" decoding="async"></a>'
                '<figcaption data-en="%s">%s</figcaption></figure></li>'
                % (src, src, src, src, w, sizes, w, h, alt_vi, alt_en, en, vi))

    grid = [item(p, "(max-width: 760px) 100vw, 420px" if i == 0 else "(max-width: 760px) 50vw, 420px")
            for i, p in enumerate(spec["photos"])]
    row = [item(p, "(max-width: 760px) 50vw, 300px") for p in spec.get("row", [])]
    row_html = ('\n          <ul class="project-grid project-row">\n%s\n          </ul>' % "\n".join(row)) if row else ""
    (t_key, title), (l_key, lead) = spec["title"], spec["lead"]
    return '''
      <!-- gallery -->
      <div class="section section-sand">
        <div class="container project-gallery">
          <div class="section-head section-head-split">
            <div>
              <h2 data-i18n="%s">%s</h2>
            </div>
            <p data-i18n="%s">%s</p>
          </div>
          <ul class="project-grid">
%s
          </ul>%s
        </div>
      </div>
      <!-- /gallery -->
''' % (t_key, title, l_key, lead, "\n".join(grid), row_html)


CATEGORY_PHOTOS = {
    "thiet-bi-ve-sinh": "thiet-bi-ve-sinh/toto-bon-cau-washlet-s7.webp",
    "bon-nuoc-may-nuoc-nong": "bon-nuoc-may-nuoc-nong/tan-a-dai-thanh-may-nuoc-nong-nlmt.webp",
    "thiet-bi-dien": "thiet-bi-dien/sino-aptomat-ps45n.webp",
    "den-trang-tri": "den-trang-tri/rang-dong-den-ban-rl38.webp",
    "nha-thong-minh": "nha-thong-minh/fpt-smart-home-cong-tac-athena.webp",
}


def build_products_view(page, view):
    route = page["route"]

    hero = between(view, '<div class="page-hero', '<div class="section">')
    crumb = re.search(r'<nav class="breadcrumb".*?</nav>', hero, re.S).group(0)
    h1_id, = re.search(r'<h1 id="([^"]+)"', hero).groups()
    h1_key, h1 = tag(hero, "h1")
    lead_key, lead = tag(hero, "p")
    jumps = re.findall(r'<li><a href="#([^"]+)"><svg class="icon"><use href="#([^"]+)"/></svg>'
                       r'<span data-i18n="([^"]+)">(.*?)</span></a></li>', hero)

    categories = []
    for m in re.finditer(r'<article class="category" id="([^"]+)" aria-labelledby="([^"]+)">(.*?)</article>', view, re.S):
        cid, labelled, body = m.groups()
        head = between(body, '<header class="category-head">', "</header>")
        cols = re.findall(r'<h3 data-i18n="([^"]+)">([^<]*)</h3>\s*<ul class="([^"]+)">(.*?)</ul>', body, re.S)
        assert len(cols) == 2, cid
        categories.append({
            "id": cid, "labelled": labelled,
            "icon": re.search(r'<use href="#([^"]+)"/>', head).group(1),
            "h2": tag(head, "h2"), "desc": tag(head, "p"),
            "gallery_title": tag(body, "h3", "prod.gallery"),
            "figures": re.findall(r'<figure class="product">.*?</figure>', body, re.S),
            "types": cols[0], "side": cols[1],
        })

    svc_block = between(view, '<div class="section section-alt">\n        <div class="container">\n          <div class="section-head">',
                        '<div class="container narrow">')
    svc_eyebrow = tag(svc_block, "p")
    svc_title = tag(svc_block, "h2")
    features = re.findall(r'<div class="feature">\s*<svg class="icon icon-lg"><use href="#([^"]+)"/></svg>\s*'
                          r'<h3 data-i18n="([^"]+)">(.*?)</h3>\s*<p data-i18n="([^"]+)">(.*?)</p>', svc_block, re.S)

    faq_block = between(view, '<div class="container narrow">', '<div class="cta-band">')
    faq_eyebrow = tag(faq_block, "p")
    faq_title = tag(faq_block, "h2")
    details = re.findall(r'<details>.*?</details>', faq_block, re.S)
    disclaimer = re.search(r'<p class="disclaimer".*?</p>', faq_block, re.S).group(0)

    band = view[view.index('<div class="cta-band">'):]
    b_title = tag(band, "h2")
    b_text = tag(band, "p")

    assert len(jumps) == len(categories) == 5 and features and details, route

    # Category cards show one product photo each (decorative: the category name is the link text)
    index_items = "\n".join(
        '                <li><a href="#%s"><span class="page-index-thumb"><img src="/assets/img/products/%s" alt="" '
        'width="800" height="800" loading="lazy" decoding="async"></span><svg class="icon"><use href="#%s"/></svg>'
        '<span data-i18n="%s">%s</span><svg class="icon page-index-go"><use href="#i-arrow"/></svg></a></li>'
        % (anchor, CATEGORY_PHOTOS[anchor], icon, key, text) for anchor, icon, key, text in jumps)

    cat_sections = []
    for i, c in enumerate(categories, 1):
        types_key, types_title, _, types_items = c["types"]
        side_key, side_title, side_class, side_items = c["side"]
        side_class = "cat-styles" if "brands-soft" in side_class else "cat-brands"
        figures = "\n".join("              " + f for f in c["figures"])
        cat_sections.append(f'''      <div class="section cat-section{' section-sand' if i % 2 == 0 else ''}">
        <div class="container">
          <article class="category" id="{c["id"]}" aria-labelledby="{c["labelled"]}">
            <header class="category-head">
              <div class="category-title">
                <span class="category-icon"><svg class="icon"><use href="#{c["icon"]}"/></svg></span>
                <h2 id="{c["labelled"]}" data-i18n="{c["h2"][0]}">{c["h2"][1]}</h2>
              </div>
              <p data-i18n="{c["desc"][0]}">{c["desc"][1]}</p>
            </header>
            <div class="gallery">
              <h3 class="label" data-i18n="{c["gallery_title"][0]}">{c["gallery_title"][1]}</h3>
              <div class="gallery-grid">
{figures}
              </div>
            </div>
            <div class="category-body">
              <div class="category-card">
                <h3 class="label" data-i18n="{types_key}">{types_title}</h3>
                <ul class="checklist">{types_items}</ul>
              </div>
              <div class="category-card">
                <h3 class="label" data-i18n="{side_key}">{side_title}</h3>
                <ul class="{side_class}">{side_items}</ul>
              </div>
            </div>
          </article>
        </div>
      </div>
''')

    feature_items = "\n".join(
        '            <article class="svc">\n'
        '              <span class="svc-icon"><svg class="icon"><use href="#%s"/></svg></span>\n'
        '              <h3 data-i18n="%s">%s</h3>\n'
        '              <p data-i18n="%s">%s</p>\n'
        '            </article>' % (icon, tk, t, dk, d) for icon, tk, t, dk, d in features)
    faq_items = "\n".join("            " + d for d in details)

    return f'''<!-- view:{route} -->
    <section class="view" data-view="{route}" aria-labelledby="{h1_id}">

      <div class="page-hero page-hero-split">
        <div class="container page-hero-inner">
          <div class="page-hero-copy">
            {crumb}
            <h1 id="{h1_id}" data-i18n="{h1_key}">{h1}</h1>
            <p class="lead" data-i18n="{lead_key}">{lead}</p>
            <div class="hero-actions">
              <a class="btn btn-primary" href="#lien-he"><span data-i18n="cta.contactNow">Liên hệ ngay</span> <svg class="icon"><use href="#i-arrow"/></svg></a>
              <a class="btn btn-ghost" href="tel:+84963345099"><svg class="icon"><use href="#i-phone"/></svg> 0963.345.099</a>
            </div>
          </div>
          <div class="hero-collage" aria-hidden="true">
            <div><img src="/assets/img/products/bon-nuoc-may-nuoc-nong/tan-a-dai-thanh-may-nuoc-nong-nlmt.webp" alt="" width="800" height="800"><span>Tân Á Đại Thành</span></div>
            <div><img src="/assets/img/products/thiet-bi-ve-sinh/toto-bon-cau-washlet-s7.webp" alt="" width="800" height="800"><span>TOTO</span></div>
            <div><img src="/assets/img/products/nha-thong-minh/aqara-hub-m3.webp" alt="" width="800" height="800"><span>Aqara</span></div>
          </div>
          <nav class="page-index" aria-labelledby="{route}-index-title">
            <p class="page-index-title" id="{route}-index-title" data-i18n="prod.jump">Danh mục sản phẩm</p>
            <ol>
{index_items}
            </ol>
          </nav>
        </div>
      </div>

{"".join(cat_sections)}
      <div class="section section-dark">
        <div class="container">
          <div class="section-head-split">
            <div>
              <h2 data-i18n="{svc_title[0]}">{svc_title[1]}</h2>
            </div>
          </div>
          <div class="svc-grid svc-grid-4">
{feature_items}
          </div>
        </div>
      </div>

      <div class="section">
        <div class="container faq-layout">
          <div class="faq-head">
            <h2 data-i18n="{faq_title[0]}">{faq_title[1]}</h2>
            {disclaimer}
          </div>
          <div class="faq">
{faq_items}
          </div>
        </div>
      </div>

      <div class="section">
        <div class="container">
          <div class="cta-band">
            <div>
              <h2 data-i18n="{b_title[0]}">{b_title[1]}</h2>
              <p data-i18n="{b_text[0]}">{b_text[1]}</p>
            </div>
            <a class="btn btn-light" href="#lien-he"><span data-i18n="cta.contactNow">Liên hệ ngay</span> <svg class="icon"><use href="#i-arrow"/></svg></a>
          </div>
        </div>
      </div>
    </section>
    '''


def build_brand_view(page, view):
    route = page["route"]

    hero = between(view, '<div class="page-hero', '<div class="section">')
    crumb = re.search(r'<nav class="breadcrumb".*?</nav>', hero, re.S).group(0)
    h1 = re.search(r'<h1 .*?</h1>', hero, re.S).group(0)
    h1_id, = re.search(r'<h1 id="([^"]+)"', h1).groups()
    lead = re.search(r'<p class="lead".*?</p>', hero, re.S).group(0)
    actions = re.search(r'<div class="hero-actions">.*?</a></div>', hero, re.S).group(0).replace("btn btn-outline", "btn btn-ghost")
    logo = re.search(r'<div class="brand-hero-logo">(.*?)</div>', hero, re.S)
    name = re.search(r'<span aria-current="page">([^<]+)</span>', crumb).group(1)
    logo_html = logo.group(1).strip() if logo else '<span class="brand-wordmark">%s</span>' % name

    content = view[view.index('<div class="container narrow-wide">') + len('<div class="container narrow-wide">'):]
    content = content[:content.rindex("</div>", 0, content.rindex("</div>"))]
    parts = [p for p in re.split(r'(?=<h2 )', content.strip()) if p.strip()]
    assert len(parts) == 5 and all(p.startswith("<h2 ") for p in parts), route
    about, products, why, faq, others = parts

    def head_and_rest(part):
        h2 = re.search(r'<h2 .*?</h2>', part, re.S).group(0)
        return h2, part[len(h2):].strip()

    about_h2, about_body = head_and_rest(about)
    prod_h2, prod_body = head_and_rest(products)
    prod_list = re.search(r'<ul class="checklist checklist-cols">.*?</ul>', prod_body, re.S).group(0)
    gallery = re.search(r'<div class="gallery">(.*?)<p class="gallery-note"', prod_body, re.S)
    gallery_html = ""
    if gallery:
        g_title = re.search(r'<h3 data-i18n="prod.gallery">[^<]*</h3>', gallery.group(1)).group(0).replace("<h3 ", '<h3 class="label" ', 1)
        figures = re.findall(r'<figure class="product">.*?</figure>', gallery.group(1), re.S)
        gallery_html = ('\n            <div class="gallery">\n              %s\n              <div class="gallery-grid brand-gallery">\n%s\n              </div>\n            </div>'
                        % (g_title, "\n".join("                " + f for f in figures)))

    why_h2, why_body = head_and_rest(why)
    reasons = re.findall(r'<li (data-en="[^"]*")>(.*?)</li>', why_body, re.S)
    reason_items = "\n".join(
        '              <li><span %s>%s</span></li>' % (attr, text)
        for attr, text in reasons)

    faq_h2, faq_body = head_and_rest(faq)
    others_h2, others_body = head_and_rest(others)
    links = re.search(r'<ul class="brands brand-links">(.*?)</ul>', others_body, re.S).group(1)
    more = re.search(r'<p class="section-link">(.*?)</p>', others_body, re.S).group(1).replace("btn btn-outline", "btn btn-light btn-sm", 1)
    disclaimer = re.search(r'<p class="disclaimer".*?</p>', others_body, re.S).group(0)
    assert reasons and "<details>" in faq_body, route

    return f'''<!-- view:{route} -->
    <section class="view" data-view="{route}" aria-labelledby="{h1_id}">

      <div class="page-hero">
        <div class="container page-hero-inner brand-hero">
          <div class="page-hero-copy">
            {crumb}
            {h1}
            {lead}
            {actions}
          </div>
          <div class="brand-logo-card" aria-hidden="true">
            <svg class="hex-lines" viewBox="0 0 200 230" fill="none">
              <path d="M100 6l88 50v118l-88 50-88-50V56z"/>
              <path d="M100 30l67 38v94l-67 38-67-38V68z"/>
            </svg>
            {logo_html}
          </div>
        </div>
      </div>

      <div class="section brand-section">
        <div class="container brand-layout">
          <div class="brand-main">
            <div class="brand-block">
              {about_h2}
              {about_body}
            </div>

            <div class="brand-block">
              {prod_h2}
              <div class="category-card">{prod_list}</div>{gallery_html}
            </div>

            <div class="brand-block">
              {why_h2}
              <ol class="reasons">
{reason_items}
              </ol>
            </div>

            <div class="brand-block">
              {faq_h2}
              {faq_body}
            </div>
          </div>

          <aside class="brand-aside">
            <div class="aside-card">
              {others_h2}
              <ul class="brand-links">{links}</ul>
              {more}
            </div>
            {disclaimer}
          </aside>
        </div>
      </div>
    </section>
    '''


def build_privacy_view(page, view):
    """The policy text is legal content: both language blocks are copied byte for byte, only the hero and
    the surrounding section are new (the look comes from CSS)."""
    route = page["route"]

    hero = between(view, '<div class="page-hero', '<div class="section">')
    crumb = re.search(r'<nav class="breadcrumb".*?</nav>', hero, re.S).group(0)
    h1 = re.search(r'<h1 .*?</h1>', hero, re.S).group(0)
    h1_id, = re.search(r'<h1 id="([^"]+)"', h1).groups()
    updated = re.search(r'<p class="lead".*?</p>', hero, re.S).group(0).replace('class="lead"', 'class="policy-updated"', 1)

    start = view.index("<!-- Vietnamese version -->")
    # the last </div> closes the section around both blocks, the one before it closes the English block
    end = view.rindex("</div>", 0, view.rindex("</div>")) + len("</div>")
    policy = view[start:end]
    assert policy.count('class="container privacy"') == 2, route

    return f'''<!-- view:{route} -->
    <section class="view" data-view="{route}" aria-labelledby="{h1_id}">

      <div class="page-hero policy-hero">
        <div class="container">
          {crumb}
          {h1}
          {updated}
        </div>
      </div>

      <div class="section policy-section">
        {policy}
      </div>
    </section>
    '''


def build(page):
    original = read(GOC, page["path"], "index.html")
    shell = read(MOI, "index.html")
    route = page["route"]

    head = original[:original.index("<body")]
    for old, new in [(FONTS_OLD, FONTS_NEW), ("/assets/css/styles.css", page["css"]),
                     ('<meta name="theme-color" content="#B5651D">', '<meta name="theme-color" content="#1C1814">')]:
        assert old in head, old
        head = head.replace(old, new)
    # iOS Safari otherwise turns the tax ID and phone numbers in plain text into blue links
    viewport = '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    assert viewport in head
    head = head.replace(viewport, viewport + '  <meta name="format-detection" content="telephone=no">\n', 1)

    body = shell[shell.index("<body"):]
    body = body.replace('<body data-route="trang-chu">', '<body data-route="%s">' % route)
    # the logo is the link home; only the homepage marks it as the current page
    body = body.replace('data-route="trang-chu" aria-current="page"', 'data-route="trang-chu"', 1)
    # Brand pages highlight "Thiết bị & Thương hiệu" in the menu
    nav = page.get("nav", {"route": route, "path": page["path"]})
    if nav:
        link = 'href="/%s/" data-route="%s"' % (nav["path"], nav["route"])
        assert link in body, route
        body = body.replace(link, link + ' class="active" aria-current="page"', 1)

    view = between(original, "<!-- view:%s -->" % route, "<!-- /view:%s -->" % route)
    new_view = page["builder"](page, view)
    a = body.index("<!-- view:trang-chu -->")
    b = body.index("<!-- /view:trang-chu -->")
    body = body[:a] + new_view + body[b:].replace("<!-- /view:trang-chu -->", "<!-- /view:%s -->" % route, 1)
    body = body.replace("<!-- ===================== TRANG CHỦ ===================== -->",
                        "<!-- ===================== %s ===================== -->" % page["label"], 1)

    out = os.path.join(MOI, page["path"], "index.html")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(head + responsive_imgs(body))
    print("wrote", os.path.relpath(out, ROOT))


PAGES = [
    {"route": "cong-nghe", "path": "cong-nghe", "label": "CÔNG NGHỆ", "anchor": "cn", "cols": 3, "builder": build_service_view},
    {"route": "noi-that", "path": "noi-that", "label": "NỘI THẤT", "anchor": "nt", "cols": 4, "builder": build_service_view},
    {"route": "thiet-bi", "path": "thiet-bi", "label": "THIẾT BỊ & THƯƠNG HIỆU", "builder": build_products_view},
    {"route": "chinh-sach-bao-mat", "path": "chinh-sach-bao-mat", "label": "CHÍNH SÁCH BẢO MẬT",
     "builder": build_privacy_view},
] + [
    {"route": "brand-" + slug, "path": "thuong-hieu/" + slug, "label": "THƯƠNG HIỆU " + slug.upper(),
     "nav": {"route": "thiet-bi", "path": "thiet-bi"}, "builder": build_brand_view}
    for slug in sorted(os.listdir(os.path.join(GOC, "thuong-hieu")))
]

if __name__ == "__main__":
    href = stamp_homepage()
    for p in PAGES:
        p["css"] = href
        build(p)
