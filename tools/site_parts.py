# -*- coding: utf-8 -*-
"""site_parts — 頁面外殼 page() 與內容元件"""
import pathlib
from site_core import *  # noqa: F401,F403

PAGES_OUT = []

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    'family=Cormorant+Garamond:wght@300;400;500&'
    'family=Noto+Sans+TC:wght@300;400;500&display=swap" rel="stylesheet">'
)


def page(url, title, desc, body, depth, blocks=None, current=None, noindex=False,
         priority="0.6", changefreq="monthly", og_image=None, og_type="website",
         extra_head=""):
    if "HD Hope" not in title:
        title = "%s｜%s" % (title, SEO["defaultTitleSuffix"])
    canon = root_abs(url)
    og = root_abs(og_image or SEO.get("ogImage") or "")
    ga = (SITE.get("analytics") or {}).get("ga4Id") or ""
    gsv = (SITE.get("analytics") or {}).get("searchConsoleVerification") or ""
    analytics = ""
    if ga:
        analytics = ('<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>'
                     '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
                     'gtag("js",new Date());gtag("config","%s");</script>' % (esc(ga), esc(ga)))
    robots = "noindex, follow" if noindex else "index, follow"
    css_href = href("/assets/css/style.css", depth)
    js_href = href("/assets/js/site.js", depth)
    head = []
    head.append('<!DOCTYPE html><html lang="zh-Hant-TW" class="no-js"><head>')
    head.append('<meta charset="utf-8">')
    head.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    head.append('<title>%s</title>' % esc(title))
    head.append('<meta name="description" content="%s">' % esc(desc))
    head.append('<meta name="robots" content="%s">' % robots)
    head.append('<link rel="canonical" href="%s">' % esc(canon))
    head.append('<meta property="og:type" content="%s">' % esc(og_type))
    head.append('<meta property="og:site_name" content="%s">' % esc(BRAND["name"]))
    head.append('<meta property="og:title" content="%s">' % esc(title))
    head.append('<meta property="og:description" content="%s">' % esc(desc))
    head.append('<meta property="og:url" content="%s">' % esc(canon))
    head.append('<meta property="og:locale" content="zh_TW">')
    if og:
        head.append('<meta property="og:image" content="%s">' % esc(og))
    head.append('<meta name="twitter:card" content="summary_large_image">')
    head.append('<meta name="theme-color" content="#FAFAF9">')
    if gsv:
        head.append('<meta name="google-site-verification" content="%s">' % esc(gsv))
    head.append(FONTS)
    head.append('<link rel="icon" href="%s" type="image/svg+xml">' % href("/assets/img/favicon.svg", depth))
    head.append('<link rel="stylesheet" href="%s">' % css_href)
    if extra_head:
        head.append(extra_head)
    head.append('</head><body>')
    head.append('<a class="skip-link" href="#main">跳至主要內容</a>')
    head.append(header_html(current or url, depth))
    head.append('<main id="main">')
    head.append(body)
    head.append('</main>')
    head.append(footer_html(depth))
    head.append(analytics)
    head.append('<script src="%s" defer></script>' % js_href)
    if blocks:
        head.append("".join(x if isinstance(x, str) and x.lstrip().startswith("<script")
                          else jsonld(x) for x in blocks if x))
    head.append('</body></html>')
    html = "".join(head)

    p = url.strip("/")
    d = ROOT / p / "index.html" if p else ROOT / "index.html"
    d.parent.mkdir(parents=True, exist_ok=True)
    d.write_text(html, encoding="utf-8")
    PAGES_OUT.append({"url": url, "canonical": canon, "priority": priority,
                      "changefreq": changefreq, "indexable": not noindex,
                      "title": title})
    return d


def notice(text, title="", kind=""):
    t = ""
    if title:
        t = '<strong>%s</strong><br>' % esc(title)
    return '<div class="notice notice--%s"><div class="notice__body">%s%s</div></div>' % (
        esc(kind or "info"), t, esc(text))


def empty_state(title, body, note="", stars=False):
    star_row = '<div class="empty-state__stars">★★★★★</div>' if stars else ""
    n = '<p class="small muted">%s</p>' % esc(note) if note else ""
    return ('<div class="empty-state reveal">%s<h3 class="h3">%s</h3><p class="muted">%s</p>%s</div>'
            % (star_row, esc(title), esc(body), n))


def prose(blocks):
    out = []
    i = 0
    for b in blocks or []:
        if "h2" in b:
            i += 1
            out.append('<h2 id="s%d">%s</h2>' % (i, esc(b["h2"])))
        elif "h3" in b:
            out.append('<h3>%s</h3>' % esc(b["h3"]))
        elif "p" in b:
            out.append('<p>%s</p>' % esc(b["p"]))
        elif "ul" in b:
            out.append('<ul>%s</ul>' % "".join("<li>%s</li>" % esc(x) for x in b["ul"]))
        elif "ol" in b:
            out.append('<ol>%s</ol>' % "".join("<li>%s</li>" % esc(x) for x in b["ol"]))
        elif "quote" in b:
            out.append('<blockquote class="quote">%s</blockquote>' % esc(b["quote"]))
        elif "img" in b:
            out.append('<figure class="figure">%s</figure>' % esc(b["img"]))
    return '<div class="prose">%s</div>' % "".join(out)


def toc(blocks):
    items = [b["h2"] for b in (blocks or []) if "h2" in b]
    if not items:
        return ""
    lis = "".join('<li><a href="#s%d">%s</a></li>' % (i, esc(t)) for i, t in enumerate(items, start=1))
    return ('<div class="plain-card toc"><span class="eyebrow eyebrow--ink">CONTENTS</span>'
            '<h3 class="h4 mt-2">本文目錄</h3><ol class="toc__list mt-2">%s</ol></div>' % lis)


# ---------------------------------------------------------------- 卡片元件
def service_tile(s, depth=0):
    return ('<a class="svc-tile reveal" href="%s">'
            '<div class="svc-tile__media">%s</div>'
            '<div class="svc-tile__body"><span class="svc-tile__num">%s</span>'
            '<h3>%s</h3><p class="small muted">%s</p>'
            '<span class="svc-tile__go">看服務說明 →</span></div></a>'
            % (href("/services/%s/" % s["slug"], depth),
               photo(s.get("heroImage", "") and img_path(s.get("heroImage", "")) or "",
                     "%s 示意" % s["name"], "服務示意照待補", "", depth, ratio="3-2"),
               esc(s.get("num", "")), esc(s.get("name", "")), esc(s.get("cardDesc", ""))))


def work_card(w, depth=0):
    cat = WORK_CATS.get(w.get("category", ""), "")
    photos = w.get("photos") or []
    return ('<article class="card reveal" data-filter-item data-cat="%s">'
            '<a class="card__media" href="%s">%s</a>'
            '<div class="card__body"><div class="card__meta">%s</div>'
            '<h3 class="h4"><a href="%s">%s</a></h3>'
            '<p class="small muted">%s</p>'
            '<div class="card__foot">%s</div></div></article>'
            % (esc(w.get("category", "")), href("/gallery/%s/" % w["slug"], depth),
               photo(photos[0] if photos else "", w.get("alt", w["title"]),
                     "作品照片待補", w.get("photoNote", ""), depth, ratio="4-5"),
               esc(cat), href("/gallery/%s/" % w["slug"], depth), esc(w["title"]),
               esc(w.get("desc", "")), status_badge(w.get("status", ""))))


def article_row(a, depth=0):
    cat = ARTICLE_CATS.get(a.get("category", ""), "")
    return ('<article class="article-row reveal">'
            '<div class="article-row__thumb">%s</div>'
            '<div class="article-row__body">'
            '<div class="article-row__meta">%s<span>%s 分鐘</span>%s</div>'
            '<h3 class="h4"><a href="%s">%s</a></h3>'
            '<p class="small muted">%s</p>'
            '<span class="article-row__go"><a class="link-arrow" href="%s">閱讀全文</a></span>'
            '</div></article>'
            % (photo(a.get("heroImage", "") and img_path(a.get("heroImage", "")) or "",
                     a["title"], "封面照待補", a.get("heroNote", ""), depth, ratio="4-3"),
               esc(cat), esc(a.get("readingTime", "")), status_badge(a.get("status", "")),
               href("/journal/%s/" % a["slug"], depth), esc(a.get("title", "")),
               esc(a.get("excerpt", "")), href("/journal/%s/" % a["slug"], depth)))


def stylist_card(s, depth=0):
    return ('<article class="stylist-card reveal">'
            '<div class="stylist-card__photo">%s</div>'
            '<div class="stylist-card__body"><h3 class="h4"><a href="%s">%s</a></h3>'
            '<p class="small muted">%s</p>'
            '<div class="stylist-card__tags">%s</div>'
            '<p class="small">%s</p>'
            '<div class="btn-row mt-2">%s</div></div></article>'
            % (photo(s.get("photo", ""), "%s 形象照" % s.get("name", ""), "設計師形象照待補",
                     s.get("photoNote", ""), depth, ratio="4-5"),
               href("/stylists/%s/" % s["slug"], depth), esc(s.get("name", "")),
               esc(s.get("title", "")),
               "".join('<span class="chip">%s</span>' % esc(t) for t in (s.get("specialties") or [])[:3]),
               esc(s.get("philosophy", "")),
               btn("看個人頁", "/stylists/%s/" % s["slug"], depth, kind="btn--ghost btn--sm")))


def stylist_slot(n, depth=0, label="版位待補"):
    return ('<article class="stylist-card stylist-card--slot reveal">'
            '<div class="stylist-card__photo is-missing">%s</div>'
            '<div class="stylist-card__body"><span class="eyebrow">SLOT %02d</span>'
            '<h3 class="h4 mt-1">%s</h3>'
            '<p class="small muted">此版位保留給尚未提供資料的設計師。新增資料後會自動產生個人頁，不需修改程式。</p>'
            '</div></article>'
            % (photo("", "設計師形象照待補", "設計師形象照待補", "", depth, ratio="4-5"), n, esc(label)))


def price_table(prices, caption="", note=""):
    rows = []
    for p in prices:
        rows.append('<div class="price-row"><div><div class="price-row__name">%s</div>%s</div>'
                    '<div class="price-row__val">%s</div></div>'
                    % (esc(p.get("name", "")),
                       ('<div class="price-row__note">%s</div>' % esc(p["note"])) if p.get("note") else "",
                       esc(p.get("val", ""))))
    head = ('<div class="price-table"><div class="price-row price-row--head"><div>%s</div>'
            '<div>價格</div></div>%s</div>' % (esc(caption or "項目"), "".join(rows)))
    if not PRICING.get("confirmedByOwner"):
        head += '<p class="price-note">%s</p>' % esc(PRICING.get("publicNote", ""))
    elif note:
        head += '<p class="price-note">%s</p>' % esc(note)
    return head


def faq_list(items, start=1):
    out = ['<div class="faq-list">']
    for i, q in enumerate(items, start=start):
        out.append('<div class="faq-item reveal"><h3 class="faq-item__q">'
                   '<span class="faq-item__num">%02d</span>%s</h3>'
                   '<div class="faq-item__a">%s</div></div>'
                   % (i, esc(q.get("q", "")), esc(q.get("a", ""))))
    out.append('</div>')
    return "".join(out)


def faq_ld(items):
    return jsonld({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q.get("q", ""),
                        "acceptedAnswer": {"@type": "Answer", "text": q.get("a", "")}}
                       for q in items],
    })
