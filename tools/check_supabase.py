#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上線前的連線檢查：確認「網站建置程式」用 anon key 就能讀到需要的資料。

    SUPABASE_URL=https://xxxx.supabase.co SUPABASE_ANON_KEY=eyJ... \
        python3 tools/check_supabase.py

會檢查四件事：
  1. 網址與金鑰可用（能連上 Supabase REST API）
  2. stylists / works 的已發布資料讀得到（RLS 沒有擋掉公開讀取）
  3. settings 讀得到（網站設定）
  4. 設計師照片的公開網址抓得到（Storage 桶是 public）

任何一項「失敗」都會以非 0 結束，讓 GitHub Actions 停下來，
不會把空網站或壞網站部署出去。回傳 0 代表可以放心拉資料。
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TIMEOUT = 30
ok_n = 0
warn_n = 0


def env(name):
    v = os.environ.get(name)
    if v:
        return v.strip()
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, val = line.split("=", 1)
            if k.strip() == name:
                return val.strip().strip('"').strip("'")
    return ""


def ok(msg):
    global ok_n
    ok_n += 1
    print("[ok]   " + msg)


def warn(msg):
    global warn_n
    warn_n += 1
    print("[警告] " + msg)


def fail(msg):
    print("\n[失敗] " + msg, file=sys.stderr)
    sys.exit(1)


def get_json(url, key, label):
    req = urllib.request.Request(url, headers={
        "apikey": key, "Authorization": "Bearer " + key, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:260]
        if e.code in (401, 403):
            fail("%s 被拒絕（HTTP %s）。這通常是 anon key 填錯，或 RLS 沒有開放公開讀取。\n回應：%s"
                 % (label, e.code, detail))
        fail("%s 讀取失敗（HTTP %s）：%s" % (label, e.code, detail or e.reason))
    except urllib.error.URLError as e:
        fail("%s 連線失敗：%s\n請確認 SUPABASE_URL（形如 https://xxxx.supabase.co，結尾不要有斜線）"
             % (label, getattr(e, "reason", e)))


def head(url, key):
    req = urllib.request.Request(url, headers={"apikey": key}, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except urllib.error.URLError:
        return 0


def main():
    base = env("SUPABASE_URL")
    key = env("SUPABASE_ANON_KEY")
    if not base:
        fail("沒有設定 SUPABASE_URL（環境變數或專案根目錄的 .env）")
    if not key:
        fail("沒有設定 SUPABASE_ANON_KEY（環境變數或專案根目錄的 .env）")
    base = base.rstrip("/")
    if "service_role" in key:
        fail("這個金鑰看起來是 service_role（後台專用、權限極大）。網站建置請改用 anon public key。")

    print("檢查 Supabase：%s\n" % base)

    # 1. 連線
  get_json(base + "/rest/v1/stylists?select=id&limit=1", key, "Supabase REST API")
    ok("網址與 anon key 可以連線")

    # 2. 已發布資料
    stylists = get_json(base + "/rest/v1/stylists?select=id,slug,status,photo_path"
                        "&status=eq.published&order=sort_order.asc", key, "stylists")
    works = get_json(base + "/rest/v1/works?select=id,slug,status,photos"
                     "&status=eq.published&order=sort_order.asc", key, "works")
    if len(stylists) == 0:
        warn("沒有任何「已發布」設計師。官網會保留現有內容，不會被清空。")
    else:
        ok("讀到 %d 位已發布設計師（RLS 允許公開讀取）" % len(stylists))
    if len(works) == 0:
        warn("沒有任何「已發布」作品。官網會保留現有內容。")
    else:
        ok("讀到 %d 件已發布作品（RLS 允許公開讀取）" % len(works))

    missing_slug = [r.get("id") for r in stylists if not (r.get("slug") or "").strip()]
    if missing_slug:
        fail("有 %d 位設計師沒有填「網址代稱」，建置會失敗。請在後台補上。" % len(missing_slug))

    # 3. 網站設定
    settings = get_json(base + "/rest/v1/settings?select=key,value", key, "settings")
    keys = [r.get("key") for r in settings if isinstance(r, dict)]
    used = [k for k in keys if k in ("brand", "contact", "seo")]
    if used:
        ok("讀到網站設定：%s" % "、".join(used))
    else:
        warn("settings 沒有 brand / contact / seo，官網會沿用 data/site.json 的現有值。")

    # 4. 圖片公開網址
    paths = []
    for r in stylists:
        sp = (r.get("photo_path") or "").strip()
        if sp:
            paths.append(sp)
    for w in works:
        for p in (w.get("photos") or []):
            sp = (p.get("path") if isinstance(p, dict) else p) or ""
            if sp:
                paths.append(sp)
    if not paths:
        warn("目前沒有任何圖片路徑可檢查（設計師與作品都還沒有照片）。")
    else:
        checked = paths[:3]
        bad = []
        for sp in checked:
            code = head("%s/storage/v1/object/public/media/%s" % (base, urllib.parse.quote(sp)), key)
            if code not in (200, 206):
                bad.append("%s（HTTP %s）" % (sp, code))
        if bad:
            fail("圖片公開網址抓不到：%s\n請確認 Storage 的 media 桶是 public，且檔案真的上傳成功。" % "、".join(bad))
        ok("圖片公開網址正常（抽查 %d 個）" % len(checked))

    print("\n[完成] 共 %d 項通過、%d 項警告。可以執行 tools/pull_supabase.py。"
          % (ok_n, warn_n))


if __name__ == "__main__":
    main()
