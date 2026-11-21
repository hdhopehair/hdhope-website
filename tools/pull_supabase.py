        "status": status,
        "featured_status": r.get("featured_status") or "none",
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
    # 即使所有作品都已下架，也必須清空輸出，避免保留上一版的公開作品。
    wd["items"] = [work_item(w, id2slug.get(w.get("stylist_id") or "", ""), base, key, args.force)
                   for w in works]
    wd["categories"] = dict(CATEGORY_LABELS)
    write_json("works.json", wd)
    note("寫入 data/works.json：%d 件作品。" % len(wd["items"]))

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
