# -*- coding: utf-8 -*-
"""pages_a — 首頁 / 品牌故事 / 專業服務（索引 + 七項詳情）"""
from site_parts import *  # noqa: F401,F403
from site_parts import (PAGES, SITE, SERVICES, WORKS, STYLISTS, REVIEWS, ARTICLES,
                        PRICING, DOMAIN, SERVICE_BY_SLUG, WORK_BY_SLUG,
                        esc, href, photo, btn, line_btn, sec_head, page_head, page,
                        breadcrumb, breadcrumb_ld, notice, empty_state, service_tile,
                        work_card, stylist_card, stylist_slot, article_row, SALON_LD,
                        status_badge)


def hero_media(src, alt, txt, note, depth, cls="hero__media"):
    """首頁視覺：有圖就顯示，沒有就以標示清楚的版位呈現。"""
    ok = bool(src) and exists(src)
    inner = ('<img src="%s" alt="%s" loading="eager" decoding="async">' % (esc(href(src, depth)), esc(alt))
             if ok else "")
    miss = "" if ok else " is-missing"
    ph = ("" if ok else
          '<div class="slot-ph"><span class="slot-ph__mark">HD</span>'
          '<span class="slot-ph__txt">%s</span><span class="slot-ph__note">%s</span></div>'
          % (esc(txt), esc(note)))
    return '<div class="%s%s%s">%s%s</div>' % (cls, " media-slot", miss, inner, ph)


def build_home():
    h = PAGES["home"]
    hv = h["hero"]
    meta = "".join('<div class="info-row"><span class="info-row__k">%s</span>'
                   '<span class="info-row__v">%s</span></div>' % (esc(m["k"]), esc(m["v"]))
                   for m in hv["meta"])
    hero = f'''<section class="hero"><div class="hero__inner">
<div class="hero__copy">
<span class="hero__kicker">{esc(hv["kicker"])}</span>
<h1 class="h1 mt-2">{esc(hv["h1_pre"])}<em class="serif" style="font-style:normal;color:var(--ink-2)">{esc(hv["h1_em"])}</em></h1>
<span class="hero__en en-serif mt-2">{esc(hv["en"])}</span>
<p class="hero__intro lead mt-3">{esc(hv["intro"])}</p>
<div class="hero__cta mt-4">{btn(hv["primary"]["label"], hv["primary"]["url"], 0)}{line_btn(0, block=False)}</div>
<div class="hero__meta mt-4">{meta}</div>
</div>
{hero_media(hv.get("image", ""), hv.get("imageAlt", ""), hv.get("slotTxt", "店面實照待上傳"), hv.get("slotNote", ""), 0)}
</div></section>'''

    ph = h["philosophy"]
    phil = f'''<section class="sect"><div class="wrap split split--5-7">
<div class="reveal">{hero_media(ph.get("image", ""), ph.get("imageAlt", ""), ph.get("slotTxt", "空間實照待上傳"), ph.get("slotNote", ""), 0, cls="media-slot")}</div>
<div class="reveal"><span class="eyebrow">{esc(ph["eyebrow"])}</span>
<h2 class="serif mt-2" style="font-size:var(--step-3)">{esc(ph["title"])}</h2>
{''.join('<p class="mt-3" style="color:var(--ink-2);line-height:2">%s</p>' % esc(p) for p in ph["paras"])}
<div class="mt-4"><a class="link-arrow" href="%s">%s →</a></div></div>
</div></section>''' % (esc(href(ph["link"]["url"], 0)), esc(ph["link"]["label"]))

    pi = h["pillars"]
    pits = "".join(f'''<div class="reveal"><span class="eyebrow">{esc(x["no"])}</span>
<h3 class="mt-2">{esc(x["t"])}</h3>
<p class="small mt-2" style="color:var(--ink-2);line-height:1.95">{esc(x["d"])}</p></div>'''
                   for x in pi["items"])
    pillars = f'''<section class="sect sect--tight bg-2"><div class="wrap">
{sec_head(pi["eyebrow"], pi["title"], "三件我們在諮詢時一定會先做的事。", "How we work")}
<div class="grid g-3 mt-5">{pits}</div></div></section>'''

    sv = h["services"]
    tiles = "".join(service_tile(s, 0) for s in SERVICES["items"][:6])
    services = f'''<section class="sect"><div class="wrap">
{sec_head(sv["eyebrow"], sv["title"], sv["aside"], "Services")}
<div class="grid g-3 mt-5">{tiles}</div>
<div class="btn-row mt-5">{btn("看全部七項服務", "/services/", 0, kind="btn--ghost")}</div>
</div></section>'''

    ga = h["gallery"]
    gal = f'''<section class="sect bg-2"><div class="wrap">
{sec_head(ga["eyebrow"], ga["title"], ga["aside"], "Portfolio")}
<div class="notice mt-4">{esc(PAGES["gallery"].get("note", ""))}</div>
<div class="grid g-3 mt-4">{"".join(work_card(w, 0) for w in WORKS["items"][:3])}</div>
<div class="btn-row mt-4">{btn("看全部作品集", "/gallery/", 0, kind="btn--ghost")}</div>
</div></section>'''

    st = h["stylists"]
    cards = "".join(stylist_card(s, 0) for s in STYLISTS["items"]) + "".join(
        stylist_slot(n, 0, PAGES["stylistsPage"].get("slotLabel", "版位待補")) for n in range(2, 4))
    stylists = f'''<section class="sect"><div class="wrap">
{sec_head(st["eyebrow"], st["title"], st["aside"], "Stylists")}
<div class="grid g-3 mt-5">{cards}</div>
<div class="btn-row mt-5">{btn("看設計師團隊", "/stylists/", 0, kind="btn--ghost")}</div>
</div></section>'''

    rv = h["reviews"]
    reviews = f'''<section class="sect sect--tight bg-2"><div class="wrap">
{sec_head(rv["eyebrow"], rv["title"], rv["aside"], "Reviews")}
<div class="mt-4">{empty_state(PAGES["reviews"].get("emptyTitle", "尚未串接 Google 評論"),
                              PAGES["reviews"].get("emptyBody", ""), note="狀態：待串接")}</div>
<div class="btn-row mt-3">{btn("評價與開通說明", "/reviews/", 0, kind="btn--ghost")}</div>
</div></section>'''

    jo = h["journal"]
    rows = "".join(article_row(a, 0) for a in ARTICLES["items"][:3])
    journal = f'''<section class="sect"><div class="wrap">
{sec_head(jo["eyebrow"], jo["title"], jo["aside"], "Journal")}
<div class="article-list mt-4">{rows}</div>
<div class="btn-row mt-4">{btn("看全部文章", "/journal/", 0, kind="btn--ghost")}</div>
</div></section>'''

    cc = h["contactCta"]
    cta = f'''<section class="sect bg-ink"><div class="wrap split split--5-7">
<div class="reveal"><span class="eyebrow eyebrow--on-dark">{esc(cc["eyebrow"])}</span>
<h2 class="mt-2" style="font-size:var(--step-3)">{esc(cc["title"])}</h2>
<p class="small mt-3" style="color:#AEB2B4">{esc(cc["note"])}</p></div>
<div class="reveal"><p style="color:#D6D9DA;line-height:2;max-width:32em">{esc(cc["body"])}</p>
<div class="hero__cta">{line_btn(0, kind="btn--light")}{btn("聯絡與交通資訊", "/contact/", 0, kind="btn--outline-light")}</div></div>
</div></section>'''

    page("/", "HD Hope Hair Salon｜桃園美髮沙龍・霧感染髮・縮毛矯正・燙髮",
         "HD Hope Hair Salon 位於桃園市桃園區成功路一段，提供霧感染髮、漂染特殊色、縮毛矯正、燙髮、護髮與男士剪燙。以專業技術與溫暖服務，成就每一次美好的改變。營業時間 12:00–20:00，每週一公休。",
         hero + phil + pillars + services + gal + stylists + reviews + journal + cta,
         0, current="/", priority="1.0", changefreq="weekly",
         blocks=[SALON_LD, {"@context": "https://schema.org", "@type": "WebSite",
                            "name": "HD Hope Hair Salon", "url": DOMAIN + "/",
                            "inLanguage": "zh-Hant-TW"}])


def build_about():
    a = PAGES["about"]
    img1 = SITE["images"].get("storeEntrance") or {}
    img2 = SITE["images"].get("storeReception") or {}
    crumbs = [("首頁", "/"), ("品牌故事", None)]
    out = [page_head(a, 1, crumbs)]

    sec_imgs = [img1, img2, img1]
    rows = []
    for i, s in enumerate(a["sections"]):
        im = sec_imgs[i] if i < len(sec_imgs) else {}
        media = photo(im.get("path", ""), im.get("alt", "店內空間照（待上傳）"),
                      "店內實照待上傳", im.get("note", "將以店家提供的實拍照片呈現，不使用生成影像。"),
                      1, wrap="media-slot", ratio="4-5")
        text = (f'<div class="reveal"><span class="eyebrow">{esc(s["eyebrow"])}</span>'
                f'<h2 class="mt-2 serif" style="font-size:var(--step-3)">{esc(s["h2"])}</h2>'
                + "".join(f'<p class="mt-3" style="color:var(--ink-2);line-height:2">{esc(p)}</p>' for p in s["paras"])
                + '</div>')
        body = f'<div class="wrap split split--7-5">{text}<div class="reveal">{media}</div></div>'
        if i % 2 == 1:
            body = f'<div class="wrap split split--5-7"><div class="reveal">{media}</div>{text}</div>'
        bg = " bg-2" if i % 2 == 1 else ""
        rows.append(f'<section class="sect{bg}" id="{esc(s["id"])}">{body}</section>')
    out.append("".join(rows))

    pr = a["process"]
    steps = "".join(
        f'<div class="reveal"><div class="eyebrow">{esc(x["no"])}</div>'
        f'<h3 class="mt-2">{esc(x["t"])}</h3>'
        f'<p class="mt-2 small" style="color:var(--ink-2);line-height:1.9">{esc(x["d"])}</p></div>'
        for x in pr["steps"])
    out.append(f'''<section class="sect bg-2"><div class="wrap">
{sec_head(pr["eyebrow"], pr["h2"], pr["lead"])}
<div class="grid g-3 mt-5" style="row-gap:clamp(28px,4vw,48px)">{steps}</div></div></section>''')

    va = a["values"]
    vals = "".join(f'<div class="plain-card reveal"><h3>{esc(x["t"])}</h3>'
                   f'<p class="small mt-2" style="color:var(--ink-2)">{esc(x["d"])}</p></div>'
                   for x in va["items"])
    out.append(f'''<section class="sect"><div class="wrap">{sec_head(va["eyebrow"], va["h2"])}
<div class="grid g-2 mt-5">{vals}</div></div></section>''')

    tn = a["teamNote"]
    out.append(f'''<section class="sect bg-2"><div class="wrap"><div class="notice reveal">
<div class="notice__body"><h3>{esc(tn["t"])}</h3><p>{esc(tn["p"])}</p>
<div class="mt-3"><a class="link-arrow" href="{esc(href(tn["link"]["url"], 1))}">{esc(tn["link"]["label"])} →</a></div>
</div></div></div></section>''')

    ac = a["access"]
    info = "".join(f'<div class="info-row"><span class="info-row__k">{esc(r["k"])}</span>'
                   f'<span class="info-row__v">{esc(r["v"])}</span></div>' for r in ac["rows"])
    out.append(f'''<section class="sect"><div class="wrap split split--7-5">
<div class="reveal"><span class="eyebrow">{esc(ac["eyebrow"])}</span>
<h2 class="mt-2" style="font-size:var(--step-3)">{esc(ac["h2"])}</h2>
<p class="mt-3 small muted">{esc(ac["note"])}</p></div>
<div class="reveal info-list">{info}</div></div></section>''')

    page("/about/", "品牌故事｜HD Hope Hair Salon 桃園髮廊",
         "HD Hope Hair Salon 的品牌故事：HD 代表 High Definition 的細節講究，Hope 代表希望與療癒。位於桃園市桃園區成功路一段，以冷白與銀灰的空間、專業技術與溫暖服務，成就每一次美好的改變。",
         "".join(out), 1, current="/about/", priority="0.8",
         blocks=[SALON_LD, breadcrumb_ld(crumbs)])


def build_services_index():
    intro = SERVICES.get("intro") or {}
    ic = {"eyebrow": intro.get("eyebrow", "SERVICES"), "h1": intro.get("h1", "專業服務"),
          "lead": intro.get("lead", ""), "note": intro.get("note", "")}
    crumbs = [("首頁", "/"), ("專業服務", None)]
    tiles = "".join(service_tile(s, 1) for s in SERVICES["items"])
    list_ld = {"@context": "https://schema.org", "@type": "ItemList",
               "name": "HD Hope Hair Salon 專業服務",
               "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": s["name"],
                                    "url": DOMAIN + "/services/" + s["slug"] + "/"}
                                   for i, s in enumerate(SERVICES["items"])]}
    body = (page_head(ic, 1, crumbs)
            + f'''<section class="sect"><div class="wrap">
<div class="grid g-3">{tiles}</div>
<div class="notice mt-5"><div class="notice__body"><h3>價格說明</h3>
<p>{esc(PRICING["publicNote"])}各服務頁的價目表目前皆標示「待店家確認」，正式價目表核准後會同步更新。</p>
</div></div></div></section>'''
            + f'''<section class="sect bg-ink"><div class="wrap split split--5-7">
<div class="reveal"><span class="eyebrow eyebrow--on-dark">BOOK</span>
<h2 class="mt-2" style="font-size:var(--step-3)">不確定自己適合哪一項？</h2></div>
<div class="reveal"><p style="max-width:32em;color:#D6D9DA">把你想解決的問題直接傳給我們（例如：布丁頭、自然捲、想剪短但不要塌），
我們會依髮況告訴你適合的服務項目與需要多長時間。</p>
<div class="hero__cta">{line_btn(1, kind="btn--light")}{btn("聯絡與交通資訊", "/contact/", 1, kind="btn--outline-light")}</div></div></div></section>''')
    page("/services/", "專業服務｜霧感染髮・漂染・縮毛矯正・燙髮・護髮｜HD Hope 桃園",
         "HD Hope Hair Salon 提供七項專業服務：霧感染髮、漂染與特殊色、縮毛矯正、燙髮、男士剪燙、護髮與頭皮養護、一般剪髮。每項服務皆有獨立說明頁、價目與常見問題，並可透過 LINE 預約。",
         body, 1, current="/services/", priority="0.9", changefreq="monthly",
         blocks=[SALON_LD, list_ld, breadcrumb_ld(crumbs)])


# ------------------------------------------------------------- service detail
IMG_CODE = {"store-01": "storeEntrance", "store-02": "storeReception"}


def img_path(code):
    info = SITE["images"].get(IMG_CODE.get(code, "storeEntrance")) or {}
    return info.get("path", "")


def build_service_detail(s):
    slug, depth = s["slug"], 2
    crumbs = [("首頁", "/"), ("專業服務", "/services/"), (s["name"], None)]
    pg = {"eyebrow": "SERVICE " + s["num"] + " · " + s.get("en", ""), "h1": s["name"],
          "lead": s["lead"], "note": ""}

    intro = "".join('<p class="mt-3" style="color:var(--ink-2);line-height:2">%s</p>' % esc(p) for p in s["intro"])
    hero = ('<section class="sect sect--tight"><div class="wrap split split--7-5">'
            '<div class="reveal">%s<div class="hero__cta">%s%s</div></div>'
            '<div class="reveal">%s</div></div></section>'
            % (intro, line_btn(depth), btn("看所有作品", "/gallery/?service=" + slug, depth, kind="btn--ghost"),
               photo(img_path(s.get("heroImage", "")), s["name"] + "服務示意（照片待上傳）",
                     "服務示意照待上傳", s.get("photoNote", "將以該服務的真實作品照呈現，不使用生成影像。"),
                     depth, wrap="media-slot", ratio="4-5")))

    suit = "".join('<div class="plain-card reveal"><h3 style="font-size:var(--step-1)">%s</h3>'
                   '<p class="small mt-2" style="color:var(--ink-2);line-height:1.9">%s</p></div>'
                   % (esc(x["t"]), esc(x["d"])) for x in s["suitableFor"])
    suit_html = ('<section class="sect bg-2"><div class="wrap">%s<div class="grid g-3 mt-5">%s</div></div></section>'
                 % (sec_head("WHO IT IS FOR", "適合這樣的你"), suit))

    steps = "".join('<div class="reveal"><div class="eyebrow">%02d</div>'
                    '<h3 class="mt-2">%s</h3><p class="small mt-2" style="color:var(--ink-2)">%s</p></div>'
                    % (i + 1, esc(x["t"]), esc(x["d"])) for i, x in enumerate(s["process"]))
    steps_html = ('<section class="sect"><div class="wrap">%s<div class="grid g-3 mt-5">%s</div></div></section>'
                  % (sec_head("HOW IT WORKS", "施作流程", "流程固定，時間與內容會依你的髮況調整。"), steps))

    price = price_table(s["prices"], caption=s["name"] + "價目（" + s.get("en", "") + "）")
    price_html = ('<section class="sect bg-2" id="price"><div class="wrap split split--7-5">'
                  '<div class="reveal"><span class="eyebrow">PRICE</span>'
                  '<h2 class="mt-2" style="font-size:var(--step-3)">價目與計價方式</h2>'
                  '<p class="mt-3 small" style="color:var(--ink-2);line-height:1.9">髮長、髮量與是否需要'
                  '前置處理都會影響價格。施作前我們會先報價，確認後才開始。</p>'
                  '<p class="mt-3 small muted">正式價目表由店家核准後更新，未定案項目一律標示「待店家確認」，'
                  '不自行推算金額。</p></div><div class="reveal">%s</div></div></section>'
                  % (price,))

    ws = [w for w in WORKS["items"] if w.get("serviceSlug") == slug]
    if ws:
        works = '<div class="grid g-3 mt-5">%s</div>' % "".join(work_card(w, depth) for w in ws)
    else:
        works = ('<div class="mt-5">%s</div>' % notice(
            "此服務的作品照片尚未取得授權，因此先以空白版位呈現，不以生成影像代替顧客案例。",
            "作品照片待補"))
    works_html = ('<section class="sect"><div class="wrap">%s%s'
                  '<div class="mt-4"><a class="link-arrow" href="%s">看更多作品 →</a></div></div></section>'
                  % (sec_head("WORKS", s["name"] + "作品", "照片與髮況說明待店家提供授權後上傳。"),
                     works, esc(href("/gallery/", depth))))

    sty = [t for t in STYLISTS["items"] if s["name"] in (t.get("specialties") or [])]
    if sty:
        sty_html = ('<section class="sect bg-2"><div class="wrap">%s<div class="grid g-3 mt-5">%s</div></div></section>'
                    % (sec_head("STYLISTS", "提供此服務的設計師"), "".join(stylist_card(t, depth) for t in sty)))
    else:
        sty_html = ('<section class="sect bg-2"><div class="wrap">%s<div class="mt-5">%s</div>'
                    '<div class="mt-4"><a class="link-arrow" href="%s">設計師團隊與個人頁 →</a></div></div></section>'
                    % (sec_head("STYLISTS", "提供此服務的設計師"),
                       notice("設計師名單與個人資料尚待店家提供。系統已建好可擴充的個人頁範本，"
                              "資料填入後就會列出實際提供此服務的設計師。", "設計師資料待補"),
                       esc(href("/stylists/", depth))))

    faq = ('<section class="sect"><div class="wrap split split--5-7">'
           '<div class="reveal"><span class="eyebrow">FAQ</span>'
           '<h2 class="mt-2" style="font-size:var(--step-3)">%s 常見問題</h2>'
           '<p class="mt-3 small muted">沒有列到的問題，直接傳 LINE 給我們。</p>'
           '<div class="mt-4">%s</div></div><div class="reveal">%s</div></div></section>'
           % (esc(s["name"]), line_btn(depth, kind="btn--ghost"), faq_list(s["faq"])))

    rel = "".join('<a class="chip" href="%s">%s</a>' % (esc(href("/services/" + r + "/", depth)),
                                                        esc(SERVICE_BY_SLUG[r]["name"]))
                  for r in s.get("related", []) if r in SERVICE_BY_SLUG)
    arts = [ARTICLE_BY_SLUG[a] for a in s.get("relatedArticles", []) if a in ARTICLE_BY_SLUG]
    art_html = "".join(article_row(a, depth) for a in arts)
    rel_html = ('<section class="sect bg-2"><div class="wrap">%s'
                '<div class="filters mt-3" style="border:0;padding:0">%s</div>'
                '<div class="article-list mt-5">%s</div></div></section>'
                % (sec_head("RELATED", "相關服務與文章"), rel, art_html))

    cta = ('<section class="sect bg-ink"><div class="wrap split split--5-7">'
           '<div class="reveal"><span class="eyebrow eyebrow--on-dark">BOOK</span>'
           '<h2 class="mt-2" style="font-size:var(--step-3)">預約 %s</h2></div>'
           '<div class="reveal"><p style="color:#D6D9DA;max-width:32em">告訴我們你現在的髮況與想要的結果，'
           '我們會回覆建議的做法、需要時間與費用。</p>'
           '<div class="hero__cta">%s%s</div></div></div></section>'
           % (esc(s["name"]), line_btn(depth, kind="btn--light"),
              btn("電話 " + PHONE, "tel", depth, kind="btn--outline-light", track="phone")))

    body = (page_head(pg, depth, crumbs) + hero + suit_html + steps_html + price_html
            + works_html + sty_html + faq + rel_html + cta)
    page("/services/" + slug + "/", s["seoTitle"], s["seoDesc"], body, depth,
         current="/services/", priority="0.8",
         blocks=[SALON_LD, faq_ld(s["faq"]), breadcrumb_ld(crumbs),
                 {"@context": "https://schema.org", "@type": "Service",
                  "name": s["name"], "serviceType": s["name"], "description": s["seoDesc"],
                  "provider": {"@id": DOMAIN + "/#salon"},
                  "areaServed": {"@type": "City", "name": "桃園市"},
                  "url": DOMAIN + "/services/" + slug + "/"}])
