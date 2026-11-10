# -*- coding: utf-8 -*-
"""build.py — 由 data/*.json 產生整站靜態 HTML（重建即發布，無後端）

用法：
    SITE_ROOT=/path/to/site python3 tools/build.py
"""
import shutil
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import site_core as C           # noqa: E402
import site_parts as SP         # noqa: E402
import pages_a as A             # noqa: E402
import pages_b as B             # noqa: E402
import pages_c as PC            # noqa: E402

ROOT = C.ROOT
DOMAIN = C.DOMAIN


def build_pages():
    A.build_home()
    A.build_about()
    A.build_services_index()
    for s in C.SERVICES["items"]:
        A.build_service_detail(s)
    B.build_stylists_index()
    for s in C.STYLISTS["items"]:
        B.build_stylist_detail(s)
    B.build_gallery_index()
    for w in C.WORKS["items"]:
        B.build_work_detail(w)
    B.build_reviews_page()
    PC.build_journal_index()
    for a in C.ARTICLES["items"]:
        PC.build_article(a)
    PC.build_news_index()
    for n in C.NEWS["items"]:
        PC.build_news_detail(n)
    PC.build_careers()
    PC.build_faq()
    PC.build_contact()
    PC.build_privacy()
    PC.build_sitemap_page()
    PC.build_404()


def write_robots():
    txt = ("User-agent: *\n"
           "Allow: /\n"
           "Disallow: /admin/\n"
           "Disallow: /404.html\n"
           "\n"
           "Sitemap: %s/sitemap.xml\n" % DOMAIN)
    (ROOT / "robots.txt").write_text(txt, encoding="utf-8")


def write_sitemap():
    from xml.sax.saxutils import escape
    rows = []
    pages = sorted([p for p in SP.PAGES_OUT if p.get("indexable")],
                   key=lambda p: (p["url"].count("/"), p["url"]))
    for p in pages:
        rows.append("<url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq>"
                    "<priority>%s</priority></url>"
                    % (escape(p["canonical"]), C.BUILD_DATE,
                       p.get("changefreq", "monthly"), p.get("priority", "0.6")))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  '
           + "\n  ".join(rows) + "\n</urlset>\n")
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")


FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" '
           'aria-label="HD Hope">'
           '<rect width="64" height="64" rx="4" fill="#202123"/>'
           '<text x="32" y="41" text-anchor="middle" font-family="Georgia,serif" '
           'font-size="24" letter-spacing="2" fill="#EDEEEF">HD</text></svg>')

IMG_README = """HD Hope Hair Salon — 圖片素材放置說明
====================================

此資料夾目前沒有任何實際照片。網站以「版位待補」明確標示，不以生成影像冒充店內實照或顧客作品。
請將下列檔案放入本資料夾（assets/img/），檔名需完全一致，重新產生網站後即會自動顯示：

必要（會影響首頁與品牌頁）
  logo.png                 店家 Logo（透明背景 PNG 或有底色方形皆可，建議 512×512 以上）
  store-01-entrance.jpg    店面／入口實照（首頁主視覺，建議 1600×2000 以上，直式）
  store-02-reception.jpg   櫃台／空間實照（品牌頁與首頁哲學區，建議 1600×2000 直式）
  og-default.jpg           社群分享預覽圖（1200×630）

選用（有就先上，沒有不影響上線）
  stylist-template.jpg     設計師形象照（新增設計師時，每位一張）
  works/*.jpg              作品照（需顧客同意刊登；於後台逐筆指定檔名）

注意事項
  1. 作品照一律需取得顧客同意，並去除可辨識身分的資訊（車牌、姓名、孩童等）。
  2. 店內照若拍到顧客，需確認對方同意；否則請以空景或局部特寫代替。
  3. 圖片建議先壓縮（長邊 2000px、JPEG 品質 80），單張控制在 400KB 以內以維持載入速度。
  4. 檔名請使用英文小寫與連字號，不要使用中文或空格，避免部分主機的檔名編碼問題。
"""


def write_assets():
    img = ROOT / "assets" / "img"
    img.mkdir(parents=True, exist_ok=True)
    (img / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    (img / "README.txt").write_text(IMG_README, encoding="utf-8")


def prune_stale():
    """後台刪掉的設計師／作品／文章，對應的舊頁面要一起移除，避免已下架的內容還留在網站上。"""
    groups = [
        ("gallery", [w.get("slug") for w in C.WORKS["items"]]),
        ("stylists", [s.get("slug") for s in C.STYLISTS["items"]]),
        ("journal", [a.get("slug") for a in C.ARTICLES["items"]]),
        ("news", [n.get("slug") for n in C.NEWS["items"]]),
    ]
    gone = []
    for folder, slugs in groups:
        base = ROOT / folder
        if not base.is_dir():
            continue
        for sub in sorted(base.iterdir()):
            if not sub.is_dir() or sub.name in slugs or not (sub / "index.html").exists():
                continue
            shutil.rmtree(sub)
            gone.append("%s/%s" % (folder, sub.name))
    if gone:
        print("removed stale pages: %d" % len(gone))
        for g in gone:
            print("  - " + g)


def main():
    build_pages()
    prune_stale()
    write_robots()
    write_sitemap()
    write_assets()
    pages = [p for p in SP.PAGES_OUT]
    html_files = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("index.html"))
    print("pages built: %d" % len(pages))
    print("indexable: %d" % sum(1 for p in pages if p["indexable"]))
    print("html files: %d" % len(html_files))
    for f in html_files:
        print("  " + f)


if __name__ == "__main__":
    main()
