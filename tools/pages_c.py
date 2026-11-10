# -*- coding: utf-8 -*-
"""pages_c — 美髮知識 / 最新消息 / 徵才 / FAQ / 聯絡預約 / 隱私權 / 網站地圖 / 404"""
from site_parts import *  # noqa: F401,F403
from site_parts import (PAGES, ARTICLES, NEWS, REVIEWS, SERVICES, STYLISTS, PRICING,
                        ARTICLE_BY_SLUG, SERVICE_BY_SLUG, ARTICLE_CATS, CONTACT,
                        esc, href, photo, btn, line_btn, notice, empty_state, sec_head,
                        page_head, breadcrumb, breadcrumb_ld, page, prose, toc,
                        article_row, faq_list, faq_ld, status_badge)
from pages_a import img_path
from pages_b import cta_band
from urllib.parse import quote


def draft_note(kind="文章"):
    return notice(("本%s目前為草稿，內容尚待店家確認，因此未列入 Sitemap，也不會被搜尋引擎索引。"
               "確認後於後台改為「已發布」，再重新產生網站即可公開。" % kind),
              title="草稿狀態說明", kind="draft")


# ---------------------------------------------------------------- journal index
def build_journal_index():
    pg = PAGES["journal"]
    d = 1
    rows = "".join(article_row(a, d) for a in ARTICLES["items"])
    body = ('<section class="sect"><div class="wrap">'
            + page_head(pg, d, [("首頁", "/"), ("美髮知識", None)], wrap=False)
            + '<div class="mt-2">%s</div>' % draft_note("文章")
            + '<div class="article-list mt-5">%s</div>' % rows
            + '<div class="notice mt-5"><div class="notice__body"><h3>我們怎麼寫這些文章</h3>'
              '<p>文章由店家與設計師提供實務經驗，內容團隊整理成可以閱讀的說明。'
              '涉及藥劑、漂染與矯正的內容會標明限制與風險，不以「保證」或「一次見效」的說法書寫。</p>'
              '</div></div>'
            + '</div></section>')
    page("/journal/", "美髮知識｜染髮・漂髮・縮毛矯正・燙髮的專業說明",
         "HD Hope Hair Salon 美髮知識專欄：霧感染髮、漂染與特殊色、縮毛矯正、燙髮與染後維護的專業說明，內容由桃園店內設計師撰寫與校訂。",
         body, d, current="/journal/", noindex=True, priority="0.5",
         blocks=[breadcrumb_ld([("首頁", "/"), ("美髮知識", "/journal/")])])


# ---------------------------------------------------------------- article detail
def build_article(a):
    d = 2
    cat = ARTICLE_CATS.get(a.get("category", ""), "")
    crumb = [("首頁", "/"), ("美髮知識", "/journal/"), (a["title"], None)]
    hero = photo(img_path(a.get("heroImage")), a["title"], "文章配圖待補",
                 a.get("heroNote", ""), d, ratio="16-9")
    svc_chips = "".join(
        '<a class="chip" href="%s">%s</a>' % (esc(href("/services/" + s["slug"] + "/", d)), esc(s["name"]))
        for s in [SERVICE_BY_SLUG[x] for x in (a.get("relatedServices") or []) if x in SERVICE_BY_SLUG])
    rel = [ARTICLE_BY_SLUG[x] for x in (a.get("relatedArticles") or []) if x in ARTICLE_BY_SLUG]
    related_html = ('<div class="article-list">%s</div>' % "".join(article_row(x, d) for x in rel)) if rel \
        else notice("相關文章整理中。", title="延伸閱讀")

    body = []
    body.append('<section class="sect"><div class="wrap">')
    body.append(breadcrumb(crumb, d))
    body.append('<div class="mt-4">%s%s</div>' % (draft_note("文章") if a.get("status") == "draft" else "", hero))
    body.append('<div class="split split--7-5 mt-5">')
    body.append('<div><span class="eyebrow">%s</span>' % esc(cat))
    body.append('<h1 class="mt-2" style="font-size:var(--step-3)">%s</h1>' % esc(a["h1"]))
    body.append('<div class="article-row__meta mt-2" style="border:0;padding:0"><span>%s</span>'
                '<span>%s</span><span>%s</span>%s</div>'
                % (esc(a.get("author", "")), esc(a.get("draftDate", "")),
                   esc(a.get("readingTime", "")), status_badge(a.get("status", ""))))
    body.append('<p class="lead mt-3">%s</p>' % esc(a.get("excerpt", "")))
    body.append(prose(a["body"]))
    body.append('<div class="rule mt-5"></div>')
    body.append('<p class="small muted mt-2">本文由 %s 撰寫，內容以店內實務經驗整理；'
                '個人髮況差異大，實際處理方式仍以現場諮詢為準。</p>' % esc(a.get("author", "HD Hope 內容團隊")))
    body.append('</div>')
    body.append('<aside class="article-side">')
    body.append(toc(a["body"]))
    if svc_chips:
        body.append('<div class="plain-card"><span class="eyebrow eyebrow--ink">SERVICES</span>'
                    '<h3 class="h4 mt-2">相關服務</h3><div class="filters mt-2">%s</div></div>' % svc_chips)
    body.append('<div class="plain-card"><h3 class="h4">想直接問比較快？</h3>'
                '<p class="small muted mt-2">把照片傳到 LINE，我們會依你的髮況告訴你可行程度與需要多長時間。</p>'
                '<div class="btn-row mt-3">%s</div></div>' % line_btn(d))
    body.append('</aside></div>')
    body.append('</div></section>')

    body.append('<section class="sect bg-2"><div class="wrap">')
    body.append(sec_head("MORE", "延伸閱讀", "把相關的觀念一起讀完，會比只看一篇更清楚。", "Read on"))
    body.append('<div class="mt-4">%s</div>' % related_html)
    body.append('</div></section>')

    page("/journal/%s/" % a["slug"], a["seoTitle"], a["seoDesc"], "".join(body), d,
         current="/journal/", noindex=True, priority="0.3", og_type="article",
         blocks=[breadcrumb_ld(crumb)])


# ---------------------------------------------------------------- news index
def build_news_index():
    pg = NEWS["intro"]
    d = 1
    items = NEWS.get("items") or []
    cards = "".join(
        '<a class="card card--flat reveal" href="%s"><div class="card__body">'
        '<span class="card__meta">%s · %s</span><h3>%s</h3><p>%s</p>'
        '<div class="card__foot"><span class="small muted">%s</span>%s</div></div></a>'
        % (esc(href("/news/" + n["slug"] + "/", d)), esc(n.get("date", "")),
           esc(NEWS_CATS.get(n.get("category", ""), n.get("category", ""))), esc(n["title"]),
           esc(n.get("excerpt", "")), esc(n.get("date", "")), status_badge(n.get("status", "")))
        for n in items)
    if not cards:
        cards = empty_state("目前沒有已發布的公告",
                            "營業時間調整、活動與徵才資訊都會公布在這裡。正式公告確認後才會上線。")
    body = ('<section class="sect"><div class="wrap">'
            + page_head(pg, d, [("首頁", "/"), ("最新消息", None)], wrap=False)
            + '<div class="mt-2">%s</div>' % draft_note("公告")
            + '<div class="grid g-2 mt-5">%s</div>' % cards
            + '</div></section>'
            + cta_band("想收到第一手消息？", "營業時間異動與臨時公告會優先發在官方 LINE，建議把帳號加入好友。", d,
                       secondary=("聯絡與預約", "/contact/")))
    page("/news/", "最新消息｜營業時間・活動公告・徵才資訊",
         "HD Hope Hair Salon 最新消息：營業時間調整、活動公告與徵才資訊。臨時異動以官方 LINE 公告為準。",
         body, d, current="/news/", noindex=True, priority="0.4",
         blocks=[breadcrumb_ld([("首頁", "/"), ("最新消息", "/news/")])])


def build_news_detail(n):
    d = 2
    crumb = [("首頁", "/"), ("最新消息", "/news/"), (n["title"], None)]
    body = []
    body.append('<section class="sect"><div class="wrap wrap--narrow">')
    body.append(breadcrumb(crumb, d))
    body.append('<div class="mt-4">%s</div>' % draft_note("公告"))
    body.append('<span class="eyebrow mt-4">%s</span>' % esc(NEWS_CATS.get(n.get("category", ""), n.get("category", ""))))
    body.append('<h1 class="mt-2" style="font-size:var(--step-3)">%s</h1>' % esc(n["title"]))
    body.append('<div class="article-row__meta mt-2" style="border:0;padding:0"><span>%s</span>%s</div>'
                % (esc(n.get("date", "")), status_badge(n.get("status", ""))))
    body.append('<div class="mt-4">%s</div>' % prose(n.get("body") or []))
    body.append('<div class="rule mt-5"></div>')
    body.append('<div class="btn-row mt-3">%s%s</div>'
                % (btn("回最新消息", "/news/", d, kind="btn--ghost"),
                   btn("聯絡與預約", "/contact/", d, kind="btn--ghost")))
    body.append('</div></section>')
    page("/news/%s/" % n["slug"], n.get("seoTitle") or ("%s｜最新消息" % n["title"]),
         n.get("seoDesc") or "HD Hope Hair Salon 最新消息。",
         "".join(body), d, current="/news/", noindex=True, priority="0.3",
         blocks=[breadcrumb_ld(crumb)])


# ---------------------------------------------------------------- careers
def build_careers():
    pg = PAGES["careers"]
    d = 1
    crumb = [("首頁", "/"), ("徵才招募", None)]
    why = pg["why"]
    offer = pg["offer"]
    roles = pg["roles"]
    ap = pg["apply"]

    offer_cards = "".join(
        '<div class="plain-card reveal"><h3 class="h4">%s</h3><p class="small muted mt-2">%s</p></div>'
        % (esc(i["t"]), esc(i["d"])) for i in offer.get("items") or [])

    role_html = ('<div class="grid g-2">%s</div>' % "".join(
        '<div class="plain-card reveal"><h3 class="h4">%s</h3><p class="small muted mt-2">%s</p></div>'
        % (esc(r.get("t", "")), esc(r.get("d", ""))) for r in roles.get("items") or [])
    ) if roles.get("items") else empty_state("目前沒有公開的職缺", roles.get("empty", ""),
                                             "職缺確認後會公布在這裡，也會同步發在官方 LINE。")

    body = []
    body.append('<section class="sect"><div class="wrap">')
    body.append(page_head(pg, d, crumb, wrap=False))
    body.append('</div></section>')

    body.append('<section class="sect sect--tight bg-2"><div class="wrap split split--5-7">')
    body.append('<div class="reveal"><span class="eyebrow">WHY</span><h2 class="mt-2" style="font-size:var(--step-2)">%s</h2></div>'
                % esc(why["h2"]))
    body.append('<div class="reveal">%s</div>' % "".join(
        '<p style="max-width:34em;color:var(--ink-3);line-height:2">%s</p>' % esc(x) for x in why["paras"]))
    body.append('</div></section>')

    body.append('<section class="sect"><div class="wrap">')
    body.append(sec_head("BENEFITS", offer["h2"], "制度內容尚待店家確認，確認後會更新這一區，不先列出未定案的數字。", "What we offer"))
    body.append('<div class="grid g-2 mt-4">%s</div>' % offer_cards)
    body.append('<div class="mt-3">%s</div>' % notice(offer.get("note", ""), title="制度內容待確認"))
    body.append('</div></section>')

    body.append('<section class="sect sect--tight"><div class="wrap">')
    body.append(sec_head("ROLES", roles["h2"], "", "Open positions"))
    body.append('<div class="mt-4">%s</div>' % role_html)
    body.append('</div></section>')

    body.append('<section class="sect bg-ink"><div class="wrap split split--5-7">')
    body.append('<div class="reveal"><span class="eyebrow eyebrow--on-dark">APPLY</span>'
                '<h2 class="mt-2" style="font-size:var(--step-2)">%s</h2>'
                '<p class="small" style="color:#B9BDBF;margin-top:1rem">%s</p></div>' % (esc(ap["h2"]), esc(ap["body"])))
    body.append('<div class="reveal"><div class="info-list">'
                '<div class="info-row" style="border-color:#3A3C3E"><div class="info-row__k" style="color:#8E9295">LINE</div>'
                '<div class="info-row__v" style="color:#E7E9EA">%s</div></div>'
                '<div class="info-row" style="border-color:#3A3C3E"><div class="info-row__k" style="color:#8E9295">電話</div>'
                '<div class="info-row__v" style="color:#E7E9EA"><a href="%s" style="color:#E7E9EA">%s</a></div></div>'
                '</div><div class="hero__cta">%s%s</div>'
                '<p class="small mt-2" style="color:#9BA0A2">%s</p></div>'
                % (esc(ap["line"]), PHONE_LINK, esc(ap["phone"]),
                   line_btn(d, kind="btn--light"), btn("查看隱私權政策", "/privacy/", d, kind="btn--outline-light"),
                   esc(ap["note"])))
    body.append('</div></section>')
    page("/careers/", "徵才招募｜設計師與助理職缺｜HD Hope Hair Salon 桃園",
         "HD Hope Hair Salon 桃園店徵才：我們重視判斷、說明與對顧客的耐心。職缺與制度內容陸續更新，歡迎透過官方 LINE 或電話與我們聯繫。",
         "".join(body), d, current="/careers/", priority="0.6",
         blocks=[SALON_LD, breadcrumb_ld([("首頁", "/"), ("徵才招募", "/careers/")])])


# ---------------------------------------------------------------- FAQ
def build_faq():
    pg = PAGES["faq"]
    d = 1
    crumb = [("首頁", "/"), ("常見問題", None)]
    all_items = []
    blocks = []
    for g in pg.get("groups") or []:
        start = len(all_items) + 1
        blocks.append('<h2 class="h2 mt-5">%s</h2>' % esc(g["h2"]))
        blocks.append('<div class="mt-3">%s</div>' % faq_list(g.get("items") or [], start=start))
        all_items.extend(g.get("items") or [])
    tail = pg.get("tail") or {}
    blocks.append('<div class="plain-card center mt-5 reveal"><h2 class="h2">%s</h2>'
                  '<p class="muted mt-2">%s</p><div class="btn-row center mt-3">%s%s</div>'
                  '<p class="small muted mt-2">%s・%s</p></div>'
                  % (esc(tail.get("t", "")), esc(tail.get("p", "")), line_btn(d),
                     btn(tail.get("phone", "電話聯絡"), PHONE_LINK, d, kind="btn--ghost",
                         track="phone"),
                     esc(tail.get("line", "")), esc(tail.get("phone", ""))))
    body = ('<section class="sect"><div class="wrap">'
            + page_head(pg, d, crumb, wrap=False)
            + '<div class="wrap--narrow" style="margin-inline:auto;padding-left:0;padding-right:0">'
            + "".join(blocks)
            + '</div></div></section>'
            + cta_band("問題還是沒被回答到？",
                       "直接在 LINE 說明你的髮況與想做的事，我們會給你比較直接的答案，而不是制式的說明。",
                       d, secondary=("看專業服務", "/services/")))
    page("/faq/", "常見問題｜預約・價格・服務流程",
         "HD Hope Hair Salon 常見問題：預約方式、營業時間與公休日、價格計算方式、染燙間隔、縮毛矯正與離子燙的差異、到店與停車資訊。",
         body, d, current="/faq/", priority="0.7",
         blocks=[SALON_LD, faq_ld(all_items) if all_items else None,
                 breadcrumb_ld([("首頁", "/"), ("常見問題", "/faq/")])])


# ---------------------------------------------------------------- contact
HREF_MAP = {"tel": PHONE_LINK, "ig": IG_URL, "line": LINE_URL}


def _field(name, spec, kind="text", options=None):
    label = esc(spec.get("label", name))
    req = '<span class="req" aria-hidden="true">*</span>' if spec.get("req") else ""
    hint = ('<div class="field__hint">%s</div>' % esc(spec["hint"])) if spec.get("hint") else ""
    err = '<div class="field__error">請填寫%s</div>' % esc(spec.get("label", name))
    req_attr = " required" if spec.get("req") else ""
    if kind == "select":
        opts = "".join('<option value="%s">%s</option>' % (esc(o), esc(o)) for o in (options or []))
        ctrl = ('<select id="f-%s" name="%s"%s><option value="">請選擇</option>%s</select>'
                % (name, name, req_attr, opts))
    elif kind == "textarea":
        ctrl = ('<textarea id="f-%s" name="%s" rows="4" placeholder="%s"%s></textarea>'
                % (name, name, esc(spec.get("ph", "")), req_attr))
    else:
        ctrl = ('<input id="f-%s" name="%s" type="%s" placeholder="%s"%s>'
                % (name, name, kind, esc(spec.get("ph", "")), req_attr))
    return ('<div class="field"><label for="f-%s">%s%s</label>%s%s%s</div>'
            % (name, label, req, ctrl, hint, err))


def build_contact():
    pg = PAGES["contact"]
    d = 1
    crumb = [("首頁", "/"), ("聯絡與預約", None)]
    rows = []
    for r in pg.get("rows") or []:
        v = esc(r.get("v", ""))
        if r.get("href") in HREF_MAP:
            extra = ' target="_blank" rel="noopener"' if r["href"] in ("ig", "line") else ""
            v = ('<a href="%s"%s data-track="%s" data-track-label="%s">%s</a>'
                 % (esc(HREF_MAP[r["href"]]), extra, esc(r["href"]), esc(r.get("k", "")), v))
        rows.append('<div class="info-row"><div class="info-row__k">%s</div>'
                    '<div class="info-row__v">%s</div></div>' % (esc(r.get("k", "")), v))
    notes = "".join("<li>%s</li>" % esc(x) for x in pg.get("notes") or [])
    f = pg["form"]
    fs = f["fields"]
    service_opts = f.get("serviceOptions") or []
    stylist_opts = f.get("stylistOptions") or []
    fields = "".join([
        _field("name", fs["name"], "text"),
        _field("phone", fs["phone"], "tel"),
        _field("service", fs["service"], "select", service_opts),
        _field("stylist", fs["stylist"], "select", stylist_opts),
        _field("time", fs["time"], "text"),
        _field("note", fs["note"], "textarea"),
    ])
    consent = ('<div class="field"><label class="small" style="display:flex;gap:.6em;align-items:flex-start">'
               '<input type="checkbox" name="consent" style="margin-top:.35em">'
               '<span>%s</span></label></div>' % esc(f.get("consent", "")))

    map_q = quote(CONTACT["addressFull"])
    map_html = ('<div class="map-frame reveal"><iframe title="HD Hope Hair Salon 位置地圖" '
                'src="https://maps.google.com/maps?q=%s&output=embed" loading="lazy" '
                'referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>'
                '<p class="small mt-2"><a href="https://www.google.com/maps/search/?api=1&query=%s" '
                'target="_blank" rel="noopener">在 Google 地圖開啟（地圖載入較慢時可用）</a></p>' % (map_q, map_q))

    body = ('<section class="sect"><div class="wrap">'
            + page_head(pg, d, crumb, wrap=False)
            + '<div class="contact-grid mt-5">'
            + '<div class="reveal"><div class="info-list">%s</div>' % "".join(rows)
            + '<ul class="prose small muted mt-4" style="padding-left:1.1em">%s</ul>' % notes
            + '</div>'
            + '<div class="reveal">%s<p class="small muted mt-2">%s</p>'
              '<div class="btn-row mt-3">%s%s</div></div>'
            % (map_html, esc(CONTACT.get("floorNote", "")),
               line_btn(d), btn("電話預約", PHONE_LINK, d, kind="btn--ghost", track="phone"))
            + '</div></div></section>'
            + '<section class="sect bg-2"><div class="wrap split split--7-5">'
            + '<div class="reveal"><span class="eyebrow">BOOK</span><h2 class="h2 mt-2">%s</h2>'
              '<p class="muted mt-2">%s</p>'
              '<form data-booking class="mt-4" novalidate>%s%s'
              '<div class="notice mt-3" data-booking-error hidden><div class="notice__body">'
              '<p>請先填寫標有＊的必填欄位，再產生訊息。</p></div></div>'
              '<div class="btn-row mt-4"><button class="btn" type="submit">產生預約訊息</button>%s</div>'
              '<p class="small muted mt-2">%s</p></form>'
            % (esc(f["h2"]), esc(f.get("lead", "")),
               fields, consent,
               '<a class="btn btn--ghost" href="%s" target="_blank" rel="noopener" data-track="line">直接開 LINE</a>' % esc(LINE_URL),
               esc(f.get("note", "")))
            + '</div>'
            + '<aside class="article-side"><div class="notice reveal" data-booking-output hidden>'
              '<div class="notice__body"><h3>你的預約訊息</h3>'
              '<pre data-booking-text class="small" style="white-space:pre-wrap;word-break:break-word;'
              'font-family:inherit;margin:.4rem 0 0"></pre>'
              '<div class="btn-row mt-3"><button class="btn btn--sm" type="button" data-booking-copy>複製訊息</button>'
              '</div></div></div>'
              '<div class="plain-card reveal"><h3 class="h4">預約前先看一下</h3>'
              '<p class="small muted mt-2">染、燙、漂建議提前幾天詢問，設計師需要依髮況安排足夠的時段。'
              '若你曾經漂過、燙過或染黑，請先告知，這會影響當天能做的項目。</p>'
              '<div class="btn-row mt-3">%s</div></div></aside>'
            % btn("先看常見問題", "/faq/", d, kind="btn--ghost")
            + '</div></section>')
    page("/contact/", "聯絡與預約｜桃園成功路一段・LINE 預約",
         "HD Hope Hair Salon 聯絡資訊與預約方式：桃園市桃園區成功路一段12號3樓，電話 03-333-0671，營業時間 12:00–20:00（週一公休），官方 LINE @877onqgo 預約。",
         body, d, current="/contact/", priority="0.9",
         blocks=[SALON_LD, breadcrumb_ld([("首頁", "/"), ("聯絡與預約", "/contact/")])])


# ---------------------------------------------------------------- privacy
def build_privacy():
    pg = PAGES["privacy"]
    d = 1
    crumb = [("首頁", "/"), ("隱私權政策", None)]
    blocks = []
    for i, s in enumerate(pg["sections"], start=1):
        paras = "".join("<p>%s</p>" % esc(x) for x in (s.get("paras") or []))
        lis = "".join("<li>%s</li>" % esc(x) for x in (s.get("list") or []))
        ul = '<ul class="mt-2" style="padding-left:1.1em">%s</ul>' % lis if lis else ""
        blocks.append('<section class="mt-5 reveal"><h2 id="s%d" style="font-size:var(--step-1)">%s</h2>'
                      '<div class="prose mt-2">%s%s</div></section>'
                      % (i, esc(s["h2"]), paras, ul))

    body = ('<section class="sect"><div class="wrap">'
            + page_head(pg, d, crumb, wrap=False)
            + '<div class="wrap--narrow" style="margin-inline:auto;padding-left:0;padding-right:0">'
            + '<p class="small muted mt-5">最後更新：%s</p>' % esc(pg.get("updated", ""))
            + "".join(blocks)
            + '<div class="mt-5">%s</div>' % notice(pg.get("note", ""), title="提醒")
            + '<div class="btn-row mt-4">%s</div>'
              % btn("聯絡與預約", "/contact/", d, kind="btn--ghost")
            + '</div></div></section>')
    page("/privacy/", "隱私權政策｜資料蒐集與使用說明｜HD Hope Hair Salon",
         "HD Hope Hair Salon 官方網站隱私權政策：說明預約聯繫、服務諮詢與招募評估時的資料蒐集目的、項目、利用期間與你的權利。第一版網站未啟用會員、金流或追蹤碼。",
         body, d, current="/privacy/", priority="0.3", changefreq="yearly",
         blocks=[breadcrumb_ld([("首頁", "/"), ("隱私權政策", "/privacy/")])])


# ---------------------------------------------------------------- sitemap page
def build_sitemap_page():
    pg = PAGES["sitemapPage"]
    d = 1

    def group(title, links, note=""):
        lis = "".join('<li><a href="%s">%s</a></li>' % (esc(href(u, d)), esc(l)) for l, u in links)
        n = ('<p class="small muted">%s</p>' % esc(note)) if note else ""
        return ('<section class="mt-5 reveal"><h2 style="font-size:var(--step-1)">%s</h2>%s'
                '<ul class="mt-2" style="padding-left:1.1em;columns:2;column-gap:2rem">%s</ul></section>'
                % (esc(title), n, lis))

    groups = []
    groups.append(group("主要頁面", [("首頁", "/"), ("品牌故事", "/about/"), ("專業服務", "/services/"),
                                 ("設計師團隊", "/stylists/"), ("顧客評價", "/reviews/"),
                                 ("徵才招募", "/careers/"), ("常見問題", "/faq/"),
                                 ("聯絡與預約", "/contact/")]))
    svc_links = [(("%s %s" % (s.get("num", ""), s["name"])).strip(), "/services/%s/" % s["slug"])
                 for s in SERVICES["items"]]
    groups.append(group("專業服務", svc_links))
    st_links = [("%s（%s）" % (s["name"], s.get("title", "")), "/stylists/%s/" % s["slug"]) for s in STYLISTS["items"]]
    groups.append(group("設計師個人頁", st_links, "目前僅有可直接運作的範本頁；正式設計師名單待店家提供。"))
    groups.append(group("髮型作品集", [("作品集首頁", "/gallery/")] +
                        [("%s（%s）" % (w["title"], WORK_CATS.get(w.get("category", ""), "")),
                          "/gallery/%s/" % w["slug"]) for w in WORKS["items"]],
                        "作品照片與資料待補，以下頁面目前為 noindex，不會出現在搜尋結果。"))
    groups.append(group("美髮知識", [("文章列表", "/journal/")] +
                        [("%s（草稿）" % a["title"], "/journal/%s/" % a["slug"]) for a in ARTICLES["items"]],
                        "文章為草稿狀態，未列入 Sitemap，也不會被搜尋引擎索引。"))
    groups.append(group("最新消息", [("消息列表", "/news/")] +
                        [("%s（草稿）" % n["title"], "/news/%s/" % n["slug"]) for n in NEWS["items"]],
                        "目前僅有後台範本項目，尚未發布。"))
    groups.append(group("其他", [("隱私權政策", "/privacy/"), ("網站地圖", "/sitemap/"),
                               ("後台管理（僅供店家使用）", "/admin/")]))

    body = ('<section class="sect"><div class="wrap">'
            + page_head(pg, d, [("首頁", "/"), ("網站地圖", None)], wrap=False)
            + "".join(groups)
            + '<div class="mt-5">%s</div>' % notice("標示為草稿的頁面已設為 noindex，也不會寫入 sitemap.xml。"
                                                    "資料補齊後於後台改為發布，重新產生網站即可。", title="關於索引狀態")
            + '</div></section>')
    page("/sitemap/", "網站地圖｜全站頁面一覽｜HD Hope Hair Salon",
         "HD Hope Hair Salon 網站地圖：一次瀏覽品牌故事、七項專業服務、設計師團隊、髮型作品集、美髮知識、最新消息與聯絡預約等所有頁面。",
         body, d, current="/sitemap/", priority="0.2", changefreq="weekly",
         blocks=[breadcrumb_ld([("首頁", "/"), ("網站地圖", "/sitemap/")])])


# ---------------------------------------------------------------- 404
def build_404():
    pg = PAGES["notFound"]
    d = 0
    links = "".join('<li><a href="%s">%s</a></li>' % (esc(href(x["url"], d)), esc(x["label"]))
                    for x in pg.get("links") or [])
    body = ('<section class="sect"><div class="wrap center" style="max-width:44em">'
            '<span class="eyebrow">404</span><h1 class="mt-2" style="font-size:var(--step-3)">%s</h1>'
            '<p class="lead mt-3">%s</p>'
            '<ul class="prose mt-4" style="padding-left:1.1em;text-align:left;display:inline-block">%s</ul>'
            '<div class="btn-row center mt-4">%s</div></div></section>'
            % (esc(pg["h1"]), esc(pg["lead"]), links, line_btn(d)))
    tmp = page("/404/", "找不到頁面｜HD Hope Hair Salon", pg["lead"], body, d,
               noindex=True, priority="0.0")
    # 直接輸出為 /404.html（單一檔案，符合主機 404 慣例）
    from shutil import move
    dest = ROOT / "404.html"
    move(str(tmp), str(dest))
    try:
        tmp.parent.rmdir()
    except OSError:
        pass
    PAGES_OUT[:] = [p for p in PAGES_OUT if p["url"] != "/404/"]
    return dest
