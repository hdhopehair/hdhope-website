# -*- coding: utf-8 -*-
"""pages_b — 設計師團隊 / 髮型作品集 / 顧客評價"""
from site_parts import *  # noqa: F401,F403
from site_parts import (PAGES, SITE, WORKS, WORK_CATS, WORK_BY_SLUG, STYLISTS,
                        REVIEWS, ARTICLES, ARTICLE_BY_SLUG, PRICING, DOMAIN,
                        SALON_LD, PHONE, PHONE_LINK, LINE_URL, IG_URL, IG_HANDLE,
                        esc, href, photo, btn, line_btn, sec_head, page_head, page,
                        breadcrumb, breadcrumb_ld, notice, empty_state, work_card,
                        stylist_card, stylist_slot, article_row, status_badge, jsonld)
from pages_a import img_path  # noqa: F401


def _tags(items, cls="chip"):
    return "".join('<span class="%s">%s</span>' % (cls, esc(t)) for t in (items or []))


def cta_band(title, body, depth=0, secondary=None):
    """深色結尾帶：主要 CTA 一律 LINE，次要可帶一個文字按鈕。"""
    sec = ""
    if secondary:
        sec = btn(secondary[0], secondary[1], depth, kind="btn--outline-light")
    return ('<section class="sect bg-ink"><div class="wrap split split--7-5">'
            '<div class="reveal"><span class="eyebrow eyebrow--on-dark">BOOK</span>'
            '<h2 class="mt-2 serif" style="font-size:var(--step-3)">%s</h2></div>'
            '<div class="reveal"><p style="max-width:32em;color:#D6D9DA;line-height:1.95">%s</p>'
            '<div class="hero__cta">%s%s</div>'
            '<p class="small mt-2" style="color:#A9ADB0">電話亦可預約：'
            '<a href="%s" data-track="tel" style="color:#D6D9DA">%s</a></p>'
            '</div></div></section>'
            % (esc(title), esc(body), line_btn(depth, kind="btn--light"),
               (" " + sec) if sec else "", esc(PHONE_LINK), esc(PHONE)))


def build_stylists_index():
    pg = PAGES["stylistsPage"]
    d = 1
    crumbs = [("首頁", "/"), ("設計師團隊", None)]
    items = STYLISTS["items"]
    cards = "".join(stylist_card(s, d) for s in items)
    slots = "".join(stylist_slot(n, d, pg["slotLabel"])
                   for n in range(len(items) + 1, max(STYLISTS.get("slots", 7), len(items)) + 1))
    body = (page_head(pg, d, crumbs)
            + '<section class="sect"><div class="wrap">'
            + '<div class="grid g-3">%s</div>' % cards
            + '<div class="notice mt-5">%s</div>' % notice(STYLISTS["capacityNote"], title="名單擴充")[len(''):].replace('<div class="notice">', '').replace('</div>', '', 1)
            + '</div></section>'
            + '<section class="sect bg-2"><div class="wrap">'
            + sec_head("OPEN SLOTS", pg["slotsTitle"], pg["slotsNote"], "Team")
            + '<div class="grid g-4 mt-5">%s</div>' % slots
            + '</div></section>'
            + cta_band("想看某位設計師的作品？", "把你的需求（例如：想剪短、想漂淺、想解決自然捲）傳到 LINE，我們會依髮況推薦適合的設計師。",
                       d, secondary=("預約與聯絡", "/contact/")))
    ld = {"@context": "https://schema.org", "@type": "ItemList",
          "name": "HD Hope Hair Salon 設計師團隊",
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": s["name"],
                               "url": "%s/stylists/%s/" % (DOMAIN, s["slug"])}
                              for i, s in enumerate(items)]}
    page("/stylists/", "設計師團隊｜HD Hope Hair Salon 桃園", "HD Hope Hair Salon 的設計師團隊：每位設計師都有獨立的個人頁面、專長、價目與預約入口。設計師名單與個人資料待店家提供，目前頁面為可運作的範本。",
         body, d, current="/stylists/", priority="0.8",
         blocks=[SALON_LD, ld, breadcrumb_ld(crumbs)])

# ---------------------------------------------------------------- stylist detail
def build_stylist_detail(s):
    d = 2
    demo = s.get("status") == "sample"
    if s.get("lineUrl"):
        line_cta = btn("LINE 預約這位設計師", s["lineUrl"], d, track="line")
    else:
        line_cta = line_btn(d, "LINE 洽詢預約")
    works = [WORK_BY_SLUG[x] for x in (s.get("workSlugs") or []) if x in WORK_BY_SLUG]
    arts = [ARTICLE_BY_SLUG[x] for x in (s.get("articleSlugs") or []) if x in ARTICLE_BY_SLUG]
    crumbs = [("首頁", "/"), ("設計師團隊", "/stylists/"), (s["name"], None)]

    works_html = ('<div class="grid g-3">%s</div>' % "".join(work_card(w, d) for w in works)) if works \
        else notice("這位設計師的作品照尚未上傳。作品僅在店家提供、且顧客同意刊登後才會上線，不以示意圖或生成影像代替真實作品。",
                    title="作品待補")
    arts_html = ('<div class="article-list">%s</div>' % "".join(article_row(a, d) for a in arts)) if arts \
        else notice("這位設計師的專業文章尚在撰寫中。文章會由設計師本人或店家內容團隊提供後發布。", title="文章待補")

    rows = [
        ("職稱", esc(s.get("title", ""))),
        ("年資", esc(s.get("experience", "待補"))),
        ("擅長", _tags(s.get("specialties"), "chip") or '<span class="small muted">待補</span>'),
        ("風格", _tags(s.get("styles"), "chip") or '<span class="small muted">待補</span>'),
    ]
    if s.get("igUrl"):
        rows.append(("Instagram", '<a href="%s" target="_blank" rel="noopener nofollow" data-track="ig" data-track-label="stylist-ig">%s</a>'
                     % (esc(s["igUrl"]), esc(s["igUrl"].replace("https://www.instagram.com/", "@").strip("/")))))
    elif s.get("instagram"):
        rows.append(("Instagram", '<a href="https://www.instagram.com/%s/" target="_blank" rel="noopener nofollow" data-track="ig">@%s</a>'
                     % (esc(s["instagram"]), esc(s["instagram"]))))
    else:
        rows.append(("Instagram", '<span class="small muted">個人帳號待補</span>'))

    info = "".join('<div class="info-row"><div class="info-row__k">%s</div><div class="info-row__v">%s</div></div>' % (k, v)
                   for k, v in rows)

    intro = "".join("<p>%s</p>" % esc(p) for p in (s.get("intro") or []))

    body = []
    body.append('<section class="sect"><div class="wrap">')
    body.append(breadcrumb(crumbs, d))
    body.append('<header class="stylist-hero mt-4 reveal">')
    body.append('<div class="stylist-hero__photo">%s</div>'
                % photo(s.get("photo", ""), "%s 形象照" % s["name"], "設計師形象照待補",
                        s.get("photoNote", ""), d, ratio="4-5"))
    body.append('<div class="stylist-hero__body">')
    body.append('<span class="eyebrow">STYLIST · 設計師個人頁</span>')
    body.append('<h1 class="mt-2">%s</h1>' % esc(s["name"]))
    body.append('<p class="h4 muted mt-1">%s</p>' % esc(s.get("title", "")))
    body.append('<div class="filters mt-2">%s%s</div>' % (_tags(s.get("tags"), "chip"), status_badge(s.get("status", ""))))
    body.append('<p class="serif mt-3" style="font-size:1.16rem;line-height:1.8;max-width:30em">%s</p>'
                % esc(s.get("philosophy", "")))
    body.append('<div class="btn-row mt-3">%s%s</div>'
                % (line_cta, btn("預約說明", "/contact/", d, kind="btn--ghost")))
    body.append('<p class="small muted mt-1">%s</p>' % esc(s.get("bookingNote", "")))
    body.append('</div></header>')
    body.append('</div></section>')

    body.append('<section class="sect sect--tight"><div class="wrap split split--7-5">')
    body.append('<div class="reveal"><span class="eyebrow">ABOUT</span><h2 class="mt-2" style="font-size:var(--step-2)">關於 %s</h2>'
                '<div class="prose mt-3">%s</div></div>' % (esc(s["name"]), intro))
    body.append('<div class="article-side">')
    body.append('<div class="plain-card reveal"><span class="eyebrow eyebrow--ink">PROFILE</span>'
                '<div class="info-list mt-3">%s</div></div>' % info)
    body.append('<div class="plain-card reveal"><h3 class="h4">預約方式</h3>'
                '<p class="small muted mt-1">指定設計師請在 LINE 訊息中註明姓名或直接使用個人預約連結；時段以現場回覆為準。</p>'
                '<div class="btn-row mt-2">%s</div></div>' % line_cta)
    body.append('</div></div></section>')

    body.append('<section class="sect sect--tight"><div class="wrap">')
    body.append(sec_head("PRICE", "個人服務價目", "實際價格依髮長、髮量與髮況調整；此表為設計師個人價目，尚未經店家核准前一律標示待確認。", "Price"))
    body.append('<div class="mt-4">%s</div>' % price_table(s.get("prices") or [], caption="%s・個人價目" % s["name"]))
    body.append('</div></section>')

    body.append('<section class="sect bg-2"><div class="wrap">')
    body.append(sec_head("WORKS", "%s 的作品" % s["name"], "每一件作品都會標記服務類別與髮況說明，方便你判斷是否適合自己。", "Portfolio"))
    body.append('<div class="mt-4">%s</div>' % works_html)
    body.append('<div class="btn-row mt-3">%s</div>' % btn("看全部作品集", "/gallery/", d, kind="btn--ghost"))
    body.append('</div></section>')

    body.append('<section class="sect"><div class="wrap">')
    body.append(sec_head("JOURNAL", "專業文章", "由設計師撰寫的髮況說明與整理建議。", "Notes"))
    body.append('<div class="mt-4">%s</div>' % arts_html)
    body.append('</div></section>')

    body.append(cta_band("想預約 %s？" % s["name"], "用 LINE 告訴我們想做的樣子與方便時段，我們會回覆可預約的時間。",
                         d, secondary=("回設計師團隊", "/stylists/")))

    blocks = [SALON_LD, breadcrumb_ld(crumbs)]
    if not demo:
        blocks.append({"@context": "https://schema.org", "@type": "Person", "name": s["name"],
                       "jobTitle": s.get("title", ""), "description": s.get("seoDesc", ""),
                       "url": "%s/stylists/%s/" % (DOMAIN, s["slug"]),
                       "worksFor": {"@id": DOMAIN + "/#salon"}})
    page("/stylists/%s/" % s["slug"], s["seoTitle"], s["seoDesc"], "".join(body), d,
         blocks=blocks, current="/stylists/", noindex=demo,
         priority=("0.4" if demo else "0.8"), changefreq="monthly")
# ---------------------------------------------------------------- gallery index
def build_gallery_index():
    g = PAGES["gallery"]
    d = 1
    chips = ['<button class="chip" type="button" data-filter="all" aria-pressed="true">%s</button>'
             % esc(g.get("filterAll", "全部作品"))]
    for key in WORK_CATS:
        chips.append('<button class="chip" type="button" data-filter="%s" aria-pressed="false">%s</button>'
                     % (esc(key), esc(WORK_CATS[key])))
    count = ('<span class="filter-count" data-filter-count data-template="{n} %s"></span>'
             % esc(g.get("countLabel", "件作品")))
    cards = "".join(work_card(w, d) for w in WORKS["items"])

    body = []
    body.append('<section class="sect"><div class="wrap">')
    body.append(page_head(g, d, [("首頁", "/"), ("髮型作品集", None)], wrap=False))
    body.append('<div class="mt-2">%s</div>' % notice(g.get("note", ""), title="作品照片待補"))
    body.append('<div data-filter-scope class="mt-4">')
    body.append('<div class="filters" data-filter-group>%s%s</div>' % ("".join(chips), count))
    body.append('<div class="grid g-3">%s</div>' % cards)
    body.append('</div>')
    body.append('<div class="notice mt-5"><div class="notice__body"><h3>怎麼看這些作品</h3>'
                '<p>每件作品都標記服務類別、髮況與設計師，方便你判斷「這個顏色／這個長度」是否適合自己。'
                '照片上線後，作品頁會同步顯示使用的服務與可預約的設計師。</p></div></div>')
    body.append('</div></section>')
    body.append(cta_band("想做出你在作品集裡看到的樣子？",
                         "把你想參考的照片直接傳到 LINE，我們會依你的髮況告訴你可行的程度、需要幾次療程與大約時間。",
                         d, secondary=("看專業服務", "/services/")))
    page("/gallery/",
         "髮型作品集｜染髮・漂髮・燙髮・縮毛矯正・男士造型",
         "HD Hope Hair Salon 髮型作品集：依染髮、漂髮、燙髮、縮毛矯正與男士造型分類，每件作品標記服務項目、髮況說明與負責設計師。作品照片由店家與顧客授權後陸續上線。",
         "".join(body), d, current="/gallery/", noindex=True, priority="0.5",
         blocks=[SALON_LD, breadcrumb_ld([("首頁", "/"), ("髮型作品集", "/gallery/")])])


# ---------------------------------------------------------------- work detail
def build_work_detail(w):
    d = 2
    svc = SERVICE_BY_SLUG.get(w.get("serviceSlug") or "")
    st = STYLIST_BY_SLUG.get(w.get("stylistSlug") or "")
    cat = WORK_CATS.get(w.get("category", ""), "")
    crumbs = [("首頁", "/"), ("髮型作品集", "/gallery/"), (w["title"], None)]
    photos = w.get("photos") or []

    hero = photo(photos[0] if photos else "", w.get("alt", w["title"]),
                 "作品照片待補", w.get("photoNote", ""), d, ratio="4-5")
    rows = []
    if svc:
        rows.append(("服務項目", '<a href="%s">%s</a>' % (esc(href("/services/" + svc["slug"] + "/", d)), esc(svc["name"]))))
    rows.append(("作品分類", esc(cat)))
    if st:
        rows.append(("負責設計師", '<a href="%s">%s</a>' % (esc(href("/stylists/" + st["slug"] + "/", d)), esc(st["name"]))))
    else:
        rows.append(("負責設計師", '<span class="small muted">未指定・待店家補登</span>'))
    if w.get("colorDesc"):
        rows.append(("髮色說明", esc(w["colorDesc"])))
    if w.get("bleached"):
        rows.append(("漂髮狀況", esc(w["bleached"])))
    rows.append(("完成日期", esc(w.get("completedAt") or "待店家提供")))
    rows.append(("刊登狀態", status_badge(w.get("status", "")) or '<span class="small muted">—</span>'))
    info = "".join('<div class="info-row"><div class="info-row__k">%s</div><div class="info-row__v">%s</div></div>' % r for r in rows)

    sibs = [x for x in WORKS["items"] if x.get("category") == w.get("category") and x["slug"] != w["slug"]][:3]
    sib_html = ('<div class="grid g-3">%s</div>' % "".join(work_card(x, d) for x in sibs)) if sibs \
        else notice("同類作品尚待補登。", title="更多作品")

    body = []
    body.append('<section class="sect"><div class="wrap">')
    body.append(breadcrumb(crumbs, d))
    body.append('<div class="split split--7-5 mt-4">')
    body.append('<div class="reveal">%s</div>' % hero)
    body.append('<div class="article-side"><div class="plain-card reveal">'
                '<span class="eyebrow eyebrow--ink">WORK</span><h1 class="mt-2" style="font-size:var(--step-2)">%s</h1>'
                '<p class="muted mt-2">%s</p><div class="info-list mt-4">%s</div>'
                '<div class="btn-row mt-4">%s</div></div></div>'
                % (esc(w["title"]), esc(w.get("desc", "")), info, line_btn(d)))
    body.append('</div>')
    body.append('</div></section>')

    extra = photos[1:]
    if extra:
        body.append('<section class="sect sect--tight"><div class="wrap">')
        body.append(sec_head("DETAIL", "更多照片", "同一次服務的其他角度與髮況紀錄。", "More photos"))
        body.append('<div class="grid g-2 mt-4">%s</div>' % "".join(
            '<div class="reveal">%s</div>' % photo(x, w.get("alt", w["title"]), "", depth=d, ratio="4-5")
            for x in extra))
        body.append('</div></section>')

    body.append('<section class="sect sect--tight"><div class="wrap">')
    body.append(sec_head("RELATED", "同類作品", "依分類整理，方便比較不同髮況與處理方式。", "More works"))
    body.append('<div class="mt-4">%s</div>' % sib_html)
    body.append('</div></section>')
    body.append(cta_band("想把這個樣子放到自己身上？",
                         "作品照只能參考。實際能不能做到、需要幾次、要留多長，都要看你的髮況。先用 LINE 傳照片，我們會給你直接的判斷。",
                         d, secondary=("回到作品集", "/gallery/")))

    page("/gallery/%s/" % w["slug"], w.get("seoTitle") or ("%s｜髮型作品" % w["title"]),
         w.get("seoDesc") or "HD Hope Hair Salon 髮型作品說明。",
         "".join(body), d, current="/gallery/", noindex=True, priority="0.3",
         og_type="article",
         blocks=[breadcrumb_ld(crumbs)])


# ---------------------------------------------------------------- reviews
def build_reviews_page():
    pg = PAGES["reviews"]
    d = 1
    howto = REVIEWS.get("howTo") or []
    lis = []
    for i, x in enumerate(howto, start=1):
        text = x.get("t", "") if isinstance(x, dict) else str(x)
        desc = x.get("d", "") if isinstance(x, dict) else ""
        lis.append("<li><strong>%02d</strong> %s%s</li>" % (i, esc(text),
                   ('<span class="small muted"> %s</span>' % esc(desc)) if desc else ""))
    pol = "".join("<li>%s</li>" % esc(x) for x in (pg.get("policy") or []))
    body = []
    body.append('<section class="sect"><div class="wrap">')
    body.append(page_head(pg, d, [("首頁", "/"), ("顧客評價", None)],
                          aside=REVIEWS.get("note", ""), wrap=False))
    body.append('<div class="mt-4">%s</div>' % empty_state(pg.get("emptyTitle", "尚未串接 Google 評論"),
                                                          pg.get("emptyBody", ""),
                                                          note="狀態：待串接（pending integration）"))
    body.append('</div></section>')
    body.append('<section class="sect sect--tight bg-2"><div class="wrap split split--7-5">')
    body.append('<div class="reveal"><span class="eyebrow">HOW IT WORKS</span>'
                '<h2 class="mt-2" style="font-size:var(--step-2)">%s</h2>'
                '<ol class="prose mt-3" style="list-style:decimal;padding-left:1.2em">%s</ol></div>'
                % (esc(pg.get("howToTitle", "開通步驟")), "".join(lis)))
    body.append('<div class="reveal plain-card"><span class="eyebrow eyebrow--ink">POLICY</span>'
                '<h3 class="h4 mt-2">我們的評價原則</h3><ul class="prose mt-3" style="list-style:disc;padding-left:1.2em">%s</ul>'
                '<p class="small muted mt-3">這一頁不會出現示範用的星等或評論數量。只有在取得可追溯來源後，才會顯示真實評分。</p></div>'
                % pol)
    body.append('</div></section>')
    body.append(cta_band("想了解實際的服務感受？",
                         "歡迎直接看 Google 商家檔案上的公開評論，或到店諮詢時詢問設計師過去處理過的類似髮況。",
                         d, secondary=("聯絡與交通資訊", "/contact/")))
    page("/reviews/",
         "顧客評價｜真實評論與服務回饋",
         "HD Hope Hair Salon 顧客評價頁。我們只顯示可追溯來源的真實評論；在取得店家授權與 Google 商家評論串接完成前，本頁維持空白，不以虛構姓名、星等或評論數量填充。",
         "".join(body), d, current="/reviews/", priority="0.7",
         blocks=[SALON_LD, breadcrumb_ld([("首頁", "/"), ("顧客評價", "/reviews/")])])
