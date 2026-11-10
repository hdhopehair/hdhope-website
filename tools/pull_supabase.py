#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 Supabase 上的內容拉下來，寫成 data/*.json，再重建官網。

    SUPABASE_URL=https://xxxx.supabase.co SUPABASE_ANON_KEY=eyJ... \
        python3 tools/pull_supabase.py

參數：
    --force       重新下載已存在的圖片
    --skip-build  只更新 JSON 與圖片，不重建網站
    --dry-run     只檢查連線與筆數，不寫入任何檔案

設定也可寫在專案根目錄的 .env（SUPABASE_URL / SUPABASE_ANON_KEY）。
GitHub Actions 以 Secrets 注入同名環境變數，不需要 .env。
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IMG = ROOT / "assets" / "img"

SERVICE_BY_CAT = {
    "color": "hair-color",
    "bleach": "bleach-color",
    "straightening": "hair-straightening",
    "perm": "perm",
    "cut": "haircut",
    "treatment": "hair-care",
    "mens": "mens-hair",
}

CATEGORY_LABELS = {
    "color": "染髮",
    "bleach": "漂髮",
    "straightening": "縮毛矯正",
    "perm": "燙髮",
    "cut": "剪髮",
    "treatment": "護髮",
    "mens": "男士造型",
}

BOOKING_NOTE = "指定設計師請在 LINE 訊息中註明設計師姓名；實際可預約時段以店家回覆為準。"
TIMEOUT = 30


def die(msg):
    print("\n[失敗] " + msg, file=sys.stderr)
    sys.exit(1)


def note(msg):
    print("[pull] " + msg)


def load_env():
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def need(key):
    v = (os.environ.get(key) or "").strip()
    if not v:
        die("缺少環境變數 %s。請在專案根目錄建立 .env 或設定 GitHub Secrets（見交付說明_V2.md）。" % key)
    return v.rstrip("/")


def http_json(url, headers, label):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        die("%s 讀取失敗（HTTP %s）：%s\n網址：%s" % (label, e.code, detail or e.reason, url))
    except urllib.error.URLError as e:
        die("%s 連線失敗：%s\n網址：%s" % (label, e.reason, url))
    try:
        return json.loads(body.decode("utf-8"))
    except Exception as e:
        die("%s 回傳的不是 JSON（%s），請確認 SUPABASE_URL 是否正確。" % (label, e))


def select(base, key, table, query):
    url = "%s/rest/v1/%s?%s" % (base, table, query)
    rows = http_json(url, {"apikey": key, "Authorization": "Bearer " + key,
                           "Accept": "application/json"}, "資料表 " + table)
    if not isinstance(rows, list):
        die("資料表 %s 回傳格式異常（預期陣列）。" % table)
    return rows


import urllib.parse


def as_list(v):
    """jsonb 欄位可能是陣列、換行字串或空值，一律轉成乾淨的 list。"""
    if isinstance(v, list):
        return [x for x in v if x not in (None, "", "null")]
    if isinstance(v, str):
        return [x.strip() for x in v.split("\n") if x.strip()]
    return []


def rel(dest):
    return "/" + str(dest.relative_to(ROOT)).replace(os.sep, "/")


def fetch_public(base, key, storage_path, dest, force=False, optional=False):
    """把 media 桶裡的公開檔案下載到 dest。已存在就跳過（可重複執行）。"""
    if not storage_path:
        return ""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0 and not force:
        return rel(dest)
    url = "%s/storage/v1/object/public/media/%s" % (base, urllib.parse.quote(storage_path))
    req = urllib.request.Request(url, headers={"apikey": key})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            blob = r.read()
    except urllib.error.HTTPError as e:
        if optional:
            note("圖片不存在，略過：%s（HTTP %s）" % (storage_path, e.code))
            return ""
        die("圖片下載失敗（HTTP %s）：%s\n網址：%s" % (e.code, storage_path, url))
    except urllib.error.URLError as e:
        if optional:
            note("圖片下載失敗，略過：%s" % storage_path)
            return ""
        die("圖片下載失敗：%s\n網址：%s" % (getattr(e, "reason", e), url))
    if not blob:
        if optional:
            note("圖片是空檔，略過：%s" % storage_path)
            return ""
        die("圖片下載回來是 0 bytes：%s" % storage_path)
    dest.write_bytes(blob)
    return rel(dest)


def stylist_item(r, work_slugs, base, key, force):
    slug = (r.get("slug") or "").strip()
    if not slug:
        die("有一筆設計師資料沒有 slug（網址代稱），請先在後台補上。")
    sp = r.get("photo_path") or ""
    photo = fetch_public(base, key, sp, IMG / "stylists" / (slug + ".webp"), force, optional=True)
    if sp:
        fetch_public(base, key, Path(sp).stem + "-thumb.webp",
                     IMG / "stylists" / (slug + "-thumb.webp"), force, optional=True)
    prices = []
    for p in (r.get("prices") or []):
        if isinstance(p, dict):
            prices.append({"name": p.get("name", ""), "val": p.get("val", "") or "待店家確認",
                           "note": p.get("note", "")})
    return {
        "slug": slug,
        "status": "live" if r.get("status") == "published" else (r.get("status") or "draft"),
        "name": r.get("name") or slug,
        "nameEn": r.get("name_en") or "",
        "title": r.get("title") or "",
        "photo": photo,
        "photoNote": r.get("photo_note") or "",
        "intro": as_list(r.get("paragraphs")),
        "philosophy": r.get("philosophy") or "",
        "specialties": as_list(r.get("specialties")),
        "styles": as_list(r.get("styles")),
        "experience": r.get("experience") or "",
        "tags": as_list(r.get("tags")),
        "igUrl": r.get("instagram_url") or "",
        "lineUrl": r.get("line_url") or "",
        "bookingNote": BOOKING_NOTE,
        "prices": prices,
        "workSlugs": work_slugs,
        "articleSlugs": [],
        "seoTitle": r.get("seo_title") or "",
        "seoDesc": r.get("seo_desc") or "",
    }


def work_item(r, stylist_slug, base, key, force):
    slug = (r.get("slug") or "").strip()
    if not slug:
        die("有一件作品沒有 slug（網址代稱），請先在後台補上。")
    plist = [p for p in (r.get("photos") or []) if p]
    paths = []
    for i, p in enumerate(plist):
        sp = p.get("path") if isinstance(p, dict) else p
        if not sp:
            continue
        paths.append(fetch_public(base, key, sp,
                                  IMG / "works" / ("%s-%02d.webp" % (slug, i + 1)), force, optional=True))
    paths = [p for p in paths if p]
    cat = r.get("category") or "color"
    if cat not in SERVICE_BY_CAT:
        note("作品 %s 的分類「%s」不在名單內，改用 color。" % (slug, cat))
        cat = "color"
    published = r.get("status") == "published"
    if published and not paths:
        status = "placeholder"
    elif published:
        status = "live"
    else:
        status = r.get("status") or "draft"
    return {
        "slug": slug,
        "title": r.get("title") or slug,
        "category": cat,
        "serviceSlug": r.get("service_slug") or SERVICE_BY_CAT[cat],
        "stylistSlug": stylist_slug,
        "status": status,
        "photos": paths,
        "photoNote": r.get("photo_note") or "",
        "colorDesc": r.get("color_desc") or "",
        "bleached": r.get("bleached") or "",
        "completedAt": (r.get("completed_at") or "")[:10],
        "desc": r.get("description") or "",
        "alt": r.get("alt") or (r.get("title") or slug),
        "seoTitle": r.get("seo_title") or "",
        "seoDesc": r.get("seo_desc") or "",
    }


def deep_merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            deep_merge(dst[k], v)
        else:
            dst[k] = v


def read_json(name):
    p = DATA / name
    if not p.exists():
        die("找不到 data/%s，請確認程式是在官網專案目錄裡執行。" % name)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        die("data/%s 格式錯誤：%s" % (name, e))


def write_json(name, obj):
    DATA.mkdir(parents=True, exist_ok=True)
    p = DATA / name
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)


def apply_settings(site, rows):
    """只覆蓋 brand / contact / seo 三個區塊；其他鍵一律忽略並提醒。"""
    seen = []
    for r in rows:
        k = r.get("key")
        v = r.get("value")
        if k not in ("brand", "contact", "seo"):
            note("設定鍵 %s 不是官網用的區塊，已忽略。" % k)
            continue
        if not isinstance(v, dict) or not v:
            note("設定 %s 是空值或格式錯誤，保留原本內容。" % k)
            continue
        site.setdefault(k, {})
        deep_merge(site[k], v)
        seen.append(k)
    if seen:
        note("已套用網站設定：%s" % "、".join(seen))


def main():
    ap = argparse.ArgumentParser(description="從 Supabase 拉內容 → data/*.json → 重建官網")
    ap.add_argument("--force", action="store_true", help="重新下載已存在的圖片")
    ap.add_argument("--skip-build", action="store_true", help="只更新資料與圖片，不重建網站")
    ap.add_argument("--dry-run", action="store_true", help="只檢查連線與筆數，不寫入任何檔案")
    args = ap.parse_args()

    load_env()
    base = need("SUPABASE_URL")
    key = need("SUPABASE_ANON_KEY")
    note("來源：%s" % base)

    stylists = select(base, key, "stylists",
                      "select=*&status=eq.published&order=sort_order.asc,created_at.asc")
    works = select(base, key, "works",
                   "select=*&status=eq.published&order=sort_order.asc,created_at.desc")
    settings = select(base, key, "settings", "select=key,value")
    note("讀到 %d 位已發布設計師、%d 件已發布作品、%d 筆網站設定"
         % (len(stylists), len(works), len(settings)))

    if args.dry_run:
        note("dry-run：只檢查連線，未寫入任何檔案。")
        return

    site = read_json("site.json")
    apply_settings(site, settings)
    write_json("site.json", site)

    id2slug = {}
    for s in stylists:
        if s.get("id") and (s.get("slug") or "").strip():
            id2slug[s["id"]] = s["slug"].strip()
    works_by_stylist = {}
    for w in works:
        slug = id2slug.get(w.get("stylist_id") or "")
        if slug and w.get("slug"):
            works_by_stylist.setdefault(slug, []).append(w["slug"])

    wd = read_json("works.json")
    if works:
        wd["items"] = [work_item(w, id2slug.get(w.get("stylist_id") or "", ""), base, key, args.force)
                       for w in works]
        wd["categories"] = dict(CATEGORY_LABELS)
        write_json("works.json", wd)
        note("寫入 data/works.json：%d 件作品。" % len(wd["items"]))
    else:
        note("沒有已發布作品，保留現有 data/works.json 內容。")

    sd = read_json("stylists.json")
    if stylists:
        sd["items"] = [stylist_item(s, works_by_stylist.get(s["slug"].strip(), []), base, key, args.force)
                       for s in stylists]
        sd["slots"] = max(7, len(sd["items"]) + 2)
        write_json("stylists.json", sd)
        note("寫入 data/stylists.json：%d 位設計師。" % len(sd["items"]))
    else:
        note("沒有已發布設計師，保留現有 data/stylists.json 內容。")

    if args.skip_build:
        note("已跳過重建（--skip-build）。")
        return

    import subprocess
    note("執行 tools/build.py …")
    rc = subprocess.run([sys.executable, str(ROOT / "tools" / "build.py")], cwd=str(ROOT)).returncode
    if rc != 0:
        die("官網重建失敗（build.py 結束碼 %s）。資料已更新，但網站沒有重建，請看上面的錯誤訊息。" % rc)
    note("完成：官網已重建。")


if __name__ == "__main__":
    main()
