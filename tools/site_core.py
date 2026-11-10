# -*- coding: utf-8 -*-
"""site_core — 共用資料、常數與基礎元件（header / footer / JSON-LD）"""
import json, os, pathlib

ROOT = pathlib.Path(
    os.environ.get("SITE_ROOT") or pathlib.Path(__file__).resolve().parent.parent
).resolve()
DATA_DIR = ROOT / "data"
BUILD_DATE = "2026-11-10"


def load(name):
    with open(DATA_DIR / ("%s.json" % name), encoding="utf-8") as f:
        return json.load(f)


SITE = load("site")
PAGES = load("pages")
SERVICES = load("services")
ARTICLES = load("articles")
STYLISTS = load("stylists")
WORKS = load("works")
NEWS = load("news")
REVIEWS = load("reviews")

BRAND = SITE["brand"]
CONTACT = SITE["contact"]
SEO = SITE["seo"]
PRICING = SITE["pricing"]
IMAGES = SITE.get("images") or {}
DOMAIN = BRAND.get("domain", "https://hdhopehair.com").rstrip("/")
LINE_URL = CONTACT.get("lineUrl", "")
LINE_ID = CONTACT.get("lineId", "")
IG_URL = CONTACT.get("igUrl", "")
IG_HANDLE = CONTACT.get("igHandle", "")
PHONE = CONTACT.get("phoneDisplay", "")
PHONE_LINK = CONTACT.get("phoneLink", "")
LINE_BTN = "LINE 預約諮詢"

SERVICE_BY_SLUG = {x["slug"]: x for x in SERVICES["items"]}
ARTICLE_BY_SLUG = {x["slug"]: x for x in ARTICLES["items"]}
STYLIST_BY_SLUG = {x["slug"]: x for x in STYLISTS["items"]}
WORK_BY_SLUG = {x["slug"]: x for x in WORKS["items"]}

WORK_CATS = WORKS.get("categories") or {
    "color": "染髮", "bleach": "漂髮", "perm": "燙髮",
    "straightening": "縮毛矯正", "mens": "男士造型",
}
ARTICLE_CATS = {
    "color": "染髮", "bleach": "漂髮", "straightening": "縮毛矯正",
    "perm": "燙髮", "care": "護髮", "mens": "男士造型", "basics": "基礎知識",
}
NEWS_CATS = {
    "announcement": "公告", "hours": "營業時間調整", "event": "活動",
    "career": "徵才", "promo": "優惠",
}

NAV = [
    {"label": "首頁", "url": "/"},
    {"label": "關於 HD Hope", "url": "/about/"},
    {"label": "專業服務", "url": "/services/", "children": [
        {"label": "%s %s" % (s["num"], s["name"]), "url": "/services/%s/" % s["slug"]}
        for s in SERVICES["items"]
    ]},
    {"label": "設計師團隊", "url": "/stylists/"},
    {"label": "髮型作品集", "url": "/gallery/"},
    {"label": "美髮知識", "url": "/journal/"},
    {"label": "顧客評價", "url": "/reviews/"},
    {"label": "聯絡與預約", "url": "/contact/"},
]


# ---------------------------------------------------------------- 基礎工具
def esc(v):
    if v is None:
        return ""
    return (str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def depth_of(url):
    return len([x for x in url.strip("/").split("/") if x])


def _prefix(depth):
    return "./" if depth <= 0 else "../" * depth


def href(url, depth=0):
    if not url:
        return "#"
    if url.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return url
    if url == "line":
        return LINE_URL
    if url == "tel":
        return PHONE_LINK
    p = url.strip("/")
    if not p:
        return _prefix(depth) + "index.html"
    # 靜態資產（含副檔名）直接回傳，不接 index.html
    if "." in p.rsplit("/", 1)[-1]:
        return _prefix(depth) + p
    return _prefix(depth) + "%s/index.html" % p


def root_abs(url):
    """絕對網址（canonical / OG 用）"""
    if url.startswith(("http://", "https://")):
        return url
    return DOMAIN + (url if url != "/" else "/")


def exists(path):
    if not path:
        return False
    return (ROOT / path.lstrip("/")).exists()


def badge(text, kind=""):
    cls = "badge" + (" badge--%s" % kind if kind else "")
    return '<span class="%s">%s</span>' % (cls, esc(text))


STATUS_MAP = {
    "draft": ("草稿・待確認", "draft"),
    "placeholder": ("範本・資料待補", "pending"),
    "sample": ("範本頁面・資料待補", "sample"),
    "pending-integration": ("待串接", "pending"),
    "pending-upload": ("待上傳", "pending"),
    "published": ("已發布", "ok"),
}


def status_badge(status):
    if not status or status not in STATUS_MAP:
        return ""
    text, kind = STATUS_MAP[status]
    return badge(text, kind)


def jsonld(obj):
    return '<script type="application/ld+json">%s</script>' % json.dumps(obj, ensure_ascii=False)


# ---------------------------------------------------------------- 元件
def photo(src, alt, txt, note="", depth=0, wrap="", ratio="4-5", eager=False):
    """媒體版位：檔案存在才輸出 <img>，否則顯示明確標示的佔位（不生成假照片）。"""
    src_path = src or ""
    has = bool(src_path) and exists(src_path)
    cls = "media-slot ratio-%s" % ratio + ("" if has else " is-missing")
    inner = []
    if has:
        inner.append('<img src="%s" alt="%s"%s%s>'
                     % (esc(href(src_path, depth)), esc(alt),
                        "" if eager else ' loading="lazy"',
                        ' decoding="async"'))
    inner.append('<div class="slot-ph" aria-hidden="true">'
                 '<span class="slot-ph__mark">HD</span>'
                 '<span class="slot-ph__txt">%s</span>%s</div>'
                 % (esc(txt or "照片待補"),
                    ('<span class="slot-ph__note">%s</span>' % esc(note)) if note else ""))
    html = '<div class="%s"%s>%s</div>' % (cls, (' aria-label="%s"' % esc(txt)) if not has else "",
                                           "".join(inner))
    if wrap:
        return '<div class="%s">%s</div>' % (wrap, html)
    return html


def btn(label, url, depth=0, kind="", track="", extra=""):
    cls = "btn" + (" " + kind if kind else "")
    tk = (' data-track="%s"' % esc(track)) if track else ""
    return ('<a class="%s" href="%s"%s%s>%s</a>'
            % (cls, esc(href(url, depth)), tk, (" " + extra) if extra else "", esc(label)))


def line_btn(depth, label=LINE_BTN, kind="", block=False):
    k = kind or ""
    if block:
        k = (k + " btn--block").strip()
    return btn(label, LINE_URL, 0, k, track="line")


def sec_head(eyebrow, title, aside="", en=""):
    h = ['<div class="sec-head reveal">', '<div class="sec-head__left">',
         '<span class="eyebrow">%s</span>' % esc(eyebrow),
         '<h2 class="sec-head__title">%s</h2>' % esc(title)]
    if en:
        h.append('<span class="sec-head__en">%s</span>' % esc(en))
    h.append('</div>')
    if aside:
        h.append('<p class="sec-head__aside">%s</p>' % esc(aside))
    h.append('</div>')
    return "".join(h)


def page_head(pg, depth, crumbs, aside="", wrap=True):
    h = ['<div class="page-head reveal">']
    if wrap:
        h.append('<div class="wrap">')
    h.append(breadcrumb(crumbs, depth))
    h.append('<div class="page-head__grid mt-3">')
    h.append('<div>')
    h.append('<span class="eyebrow">%s</span>' % esc(pg.get("eyebrow", "")))
    h.append('<h1 class="mt-2">%s</h1>' % esc(pg.get("h1", "")))
    h.append('</div>')
    lead = pg.get("lead", "")
    if lead or aside:
        h.append('<div class="page-head__aside">')
        if lead:
            h.append('<p class="lead">%s</p>' % esc(lead))
        if aside:
            h.append('<p class="small muted mt-2">%s</p>' % esc(aside))
        h.append('</div>')
    h.append('</div>')
    if wrap:
        h.append('</div>')
    h.append('</div>')
    return "".join(h)


def breadcrumb(items, depth=0):
    lis = []
    for i, (label, url) in enumerate(items):
        last = i == len(items) - 1
        if url and not last:
            lis.append('<li><a href="%s">%s</a></li>' % (esc(href(url, depth)), esc(label)))
        else:
            lis.append('<li aria-current="page">%s</li>' % esc(label))
    return '<nav class="breadcrumb" aria-label="麵包屑"><ul>%s</ul></nav>' % "".join(lis)


def breadcrumb_ld(items):
    return jsonld({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": label,
             "item": root_abs(url) if url else root_abs(root_abs_placeholder)}
            for i, (label, url) in enumerate(items)
        ],
    }) if False else jsonld({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            dict({"@type": "ListItem", "position": i + 1, "name": label},
                 **({"item": root_abs(url)} if url else {}))
            for i, (label, url) in enumerate(items)
        ],
    })


SALON_LD = {
    "@context": "https://schema.org",
    "@type": "HairSalon",
    "@id": DOMAIN + "/#salon",
    "name": BRAND["name"],
    "alternateName": BRAND.get("nameZh", ""),
    "url": DOMAIN + "/",
    "image": root_abs(SEO.get("ogImage", "")),
    "description": BRAND.get("intro", ""),
    "slogan": BRAND.get("slogan", ""),
    "telephone": CONTACT.get("phoneLink", "").replace("tel:", ""),
    "address": {
        "@type": "PostalAddress",
        "streetAddress": CONTACT.get("streetAddress", ""),
        "addressLocality": CONTACT.get("addressLocality", ""),
        "addressRegion": CONTACT.get("addressRegion", ""),
        "addressCountry": CONTACT.get("addressCountry", ""),
    },
    "openingHoursSpecification": [{
        "@type": "OpeningHoursSpecification",
        "dayOfWeek": ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "opens": CONTACT.get("opens", "12:00"),
        "closes": CONTACT.get("closes", "20:00"),
    }],
    "sameAs": [x for x in [IG_URL] if x],
}

WEBSITE_LD = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "@id": DOMAIN + "/#website",
    "url": DOMAIN + "/",
    "name": BRAND["name"],
    "inLanguage": BRAND.get("locale", "zh-Hant-TW"),
    "publisher": {"@id": DOMAIN + "/#salon"},
}


def brand_mark(depth, cls=""):
    logo = BRAND.get("logo") or {}
    has_logo = bool(logo.get("path")) and exists(logo.get("path"))
    mark = ('<img src="%s" alt="%s" width="40" height="40">' % (esc(href(logo["path"], depth)), esc(BRAND["name"]))
            if has_logo else '<span class="brand__mark--missing" aria-hidden="true">HD</span>')
    return ('<a class="brand %s" href="%s" aria-label="%s 首頁">%s'
            '<span class="brand__name">%s<span class="brand__sub">%s</span></span></a>'
            % (cls, esc(href("/", depth)), esc(BRAND["name"]), mark,
               esc(BRAND.get("nameShort", BRAND["name"])), esc("HAIR SALON")))


def header_html(current="/", depth=0):
    items = []
    for it in NAV:
        kids = it.get("children")
        active = " is-active" if current == it["url"] else ""
        if kids:
            sub = "".join('<li><a href="%s"%s>%s</a></li>'
                          % (esc(href(k["url"], depth)),
                             ' aria-current="page"' if current == k["url"] else "", esc(k["label"]))
                          for k in kids)
            items.append('<li class="nav-drop%s"><a href="%s"%s>%s<span class="nav-drop__caret">▾</span></a>'
                         '<div class="nav-drop__panel"><ul>%s</ul></div></li>'
                         % (active, esc(href(it["url"], depth)), "", esc(it["label"]), sub))
        else:
            items.append('<li><a href="%s"%s>%s</a></li>'
                         % (esc(href(it["url"], depth)),
                            ' aria-current="page"' if current == it["url"] else "", esc(it["label"])))

    drawer_links = "".join('<li><a href="%s">%s</a></li>'
                           % (esc(href(it["url"], depth)), esc(it["label"])) for it in NAV)

    return "".join([
        '<div class="utility"><div class="wrap wrap--wide">'
        '<span class="utility__left">%s</span>'
        '<span class="utility__right"><a href="%s" data-track="tel" data-track-label="utility-tel">%s</a>'
        '<span class="utility__sep">·</span>%s<span class="utility__sep">·</span>%s</span>'
        '</div></div>' % (esc(BRAND.get("enLine", "")), esc(PHONE_LINK), esc(PHONE),
                          esc(CONTACT.get("hoursDisplay", "")), esc(CONTACT.get("closedDay", "") + "公休")),
        '<header class="site-header"><div class="wrap wrap--wide site-header__inner">',
        brand_mark(depth),
        '<nav class="nav" aria-label="主要導覽"><ul>%s</ul></nav>' % "".join(items),
        '<div class="header-actions">',
        '<a class="header-phone" href="%s" data-track="tel" data-track-label="header-tel">%s</a>'
        % (esc(PHONE_LINK), esc(PHONE)),
        btn("LINE 預約", LINE_URL, 0, "btn--sm", track="line"),
        '<button class="burger" type="button" data-drawer-open aria-label="開啟選單" aria-expanded="false">'
        '<span></span><span></span><span></span></button>',
        '</div></div></header>',
        '<dialog class="drawer" id="drawer">',
        '<div class="drawer__panel">',
        '<div class="drawer__top">%s<button class="drawer__close" type="button" data-drawer-close '
        'aria-label="關閉選單">×</button></div>' % brand_mark(depth),
        '<ul class="drawer__links">%s</ul>' % drawer_links,
        '<div class="drawer__cta">%s%s</div>'
        % (line_btn(depth, "LINE 預約諮詢", block=True),
           btn("撥打電話 %s" % PHONE, PHONE_LINK, 0, "btn--ghost btn--block", track="tel")),
        '<p class="small muted mt-3">%s<br>%s</p>'
        % (esc(CONTACT.get("addressFull", "")), esc(CONTACT.get("hoursDisplay", "") + "｜" + CONTACT.get("closedDay", "") + "公休")),
        '</div><div class="drawer__scrim" data-drawer-close></div></dialog>',
        '<div class="mobile-bar">',
        '<a href="%s" data-track="tel" data-track-label="mobilebar-tel"><span>電話</span>%s</a>' % (esc(PHONE_LINK), esc(PHONE)),
        '<a href="%s" target="_blank" rel="noopener" data-track="line" data-track-label="mobilebar-line" '
        'class="mobile-bar__line"><span>LINE</span>預約</a>' % esc(LINE_URL),
        '</div>',
    ])


def footer_html(depth=0):
    svc = "".join('<li><a href="%s">%s</a></li>'
                  % (esc(href("/services/%s/" % s["slug"], depth)), esc(s["name"]))
                  for s in SERVICES["items"])
    site_links = [("關於 HD Hope", "/about/"), ("設計師團隊", "/stylists/"),
                  ("髮型作品集", "/gallery/"), ("美髮知識", "/journal/"),
                  ("最新消息", "/news/"), ("顧客評價", "/reviews/")]
    sl = "".join('<li><a href="%s">%s</a></li>' % (esc(href(u, depth)), esc(t)) for t, u in site_links)
    help_links = [("常見問題", "/faq/"), ("聯絡與預約", "/contact/"),
                  ("徵才招募", "/careers/"), ("隱私權與資料使用", "/privacy/"),
                  ("網站地圖", "/sitemap/")]
    hl = "".join('<li><a href="%s">%s</a></li>' % (esc(href(u, depth)), esc(t)) for t, u in help_links)
    return "".join([
        '<footer class="site-footer"><div class="wrap wrap--wide">',
        '<div class="site-footer__grid">',
        '<div class="site-footer__brand">%s' % brand_mark(depth),
        '<p class="site-footer__intro mt-3">%s</p>' % esc(BRAND.get("intro", "")),
        '<p class="serif site-footer__slogan">%s</p>' % esc(BRAND.get("slogan", "")),
        '<div class="site-footer__social mt-3">',
        '<a href="%s" target="_blank" rel="noopener" data-track="ig" data-track-label="footer-ig">Instagram @%s</a>'
        % (esc(IG_URL), esc(IG_HANDLE)),
        '<a href="%s" target="_blank" rel="noopener" data-track="line" data-track-label="footer-line">LINE %s</a>'
        % (esc(LINE_URL), esc(LINE_ID)),
        '</div></div>',
        '<div class="site-footer__col"><h3>專業服務</h3><ul>%s</ul></div>' % svc,
        '<div class="site-footer__col"><h3>認識我們</h3><ul>%s</ul></div>' % sl,
        '<div class="site-footer__col"><h3>資訊與協助</h3><ul>%s</ul></div>' % hl,
        '<div class="site-footer__col site-footer__contact"><h3>店家資訊</h3>',
        '<p>%s</p><p>%s</p>' % (esc(CONTACT.get("addressFull", "")), esc(CONTACT.get("floorNote", ""))),
        '<p><a href="%s" data-track="tel" data-track-label="footer-tel">%s</a></p>' % (esc(PHONE_LINK), esc(PHONE)),
        '<p>%s<br>%s公休</p>' % (esc(CONTACT.get("hoursDisplay", "")), esc(CONTACT.get("closedDay", ""))),
        '<p><a href="%s">交通與地圖</a></p>' % esc(href("/contact/", depth)),
        '</div></div>',
        '<div class="site-footer__bottom">',
        '<p>© %s %s。All rights reserved.</p>' % (BUILD_DATE[:4], esc(BRAND["name"])),
        '<p class="small">本站照片與文字版權屬店家所有。頁面狀態：第一版建置・部分資料待店家提供。</p>',
        '</div></div></footer>',
    ])


# --------------------------------------------------------------- image codes
IMG_CODE = {"store-01": "storeEntrance", "store-02": "storeReception"}


def img_path(code):
    """資料檔用 store-01 / store-02 代碼指向實體照片；回傳站內路徑（無檔則空字串）。"""
    if not code:
        return ""
    info = IMAGES.get(IMG_CODE.get(code, code)) or {}
    return info.get("path", "") or ""
