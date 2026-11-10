/* HD Hope Hair Salon — CMS V2（Supabase 版）
 * 資料存於 Supabase Postgres，登入由 Supabase Auth 伺服器驗證，
 * 圖片存於 Supabase Storage；本檔不含任何密碼或服務金鑰。 */
(function () {
  "use strict";

  var CFG = window.HD_CONFIG || {};
  var SB = (CFG.SUPABASE_URL || "").replace(/\/$/ ,"");
  var KEY = CFG.SUPABASE_ANON_KEY || "";
  var SITE = CFG.SITE_BASE || "";
  var SESSION_KEY = "hd_cms_session_v2";

  var S = { token: null, refresh: null, email: "", uid: null, view: "dash", stylists: [], works: [] };

  /* ------------------------------------------------------------------ 小工具 */
  function $(id) { return document.getElementById(id); }
  function el(tag, cls, html) { var n = document.createElement(tag); if (cls) n.className = cls; if (html != null) n.innerHTML = html; return n; }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]; }); }
  function toast(msg, kind) {
    var t = el("div", "toast" + (kind ? " " + kind : ""), esc(msg));
    $("toasts").appendChild(t);
    setTimeout(function () { t.style.opacity = "0"; t.style.transition = "opacity .3s"; }, 3200);
    setTimeout(function () { t.remove(); }, 3700);
  }
  function fmtDate(iso) { if (!iso) return "—"; var d = new Date(iso); return isNaN(d) ? "—" : d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); }
  function slugify(s) {
    return String(s || "").toLowerCase().trim()
      .replace(/[^a-z0-9\u4e00-\u9fff -]/g, "")
      .replace(/[\u4e00-\u9fff]+/g, "")
      .replace(/\s+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "").slice(0, 40);
  }
  function configured() { return !!(SB && KEY); }

  /* ------------------------------------------------------------------ 連線層 */
  function authHeaders(extra) {
    var h = { apikey: KEY, Authorization: "Bearer " + (S.token || KEY) };
    if (extra) for (var k in extra) h[k] = extra[k];
    return h;
  }

  async function refreshSession() {
    if (!S.refresh) return false;
    var r = await fetch(SB + "/auth/v1/token?grant_type=refresh_token", {
      method: "POST", headers: { apikey: KEY, "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: S.refresh })
    });
    if (!r.ok) return false;
    var j = await r.json();
    applySession(j);
    return true;
  }

  function applySession(j) {
    S.token = j.access_token; S.refresh = j.refresh_token || S.refresh;
    S.email = (j.user && j.user.email) || S.email; S.uid = (j.user && j.user.id) || S.uid;
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({ access_token: S.token, refresh_token: S.refresh, email: S.email, uid: S.uid }));
  }

  async function api(path, opt) {
    opt = opt || {};
    var tries = 0, res, body = opt.body;
    var clean = String(path).replace(/^\/rest\/v1\//, "").replace(/^\/+/, "");
    var extra = opt.headers || {};
    if (opt.prefer) extra.Prefer = opt.prefer;
    var payload;
    if (body !== undefined) payload = typeof body === "string" ? body : JSON.stringify(body);
    while (tries < 2) {
      res = await fetch(SB + "/rest/v1/" + clean, {
        method: opt.method || "GET",
        headers: authHeaders(Object.assign({ "Content-Type": "application/json" }, extra)),
        body: payload
      });
      if (res.status === 401 && tries === 0) { tries++; if (await refreshSession()) continue; }
      break;
    }
    if (!res.ok) {
      var txt = ""; try { txt = await res.text(); } catch (e) {}
      throw new Error(restError(res.status, txt));
    }
    if (res.status === 204) return null;
    var ct = res.headers.get("content-type") || "";
    return ct.indexOf("json") >= 0 ? res.json() : res.text();
  }
  function restError(code, txt) {
    if (code === 401 || code === 403) return "沒有權限：請確認登入帳號已被加入 admins 名單。";
    if (code === 409) return "Slug 或唯一欄位重複，請換一個。";
    if (code === 400) return "資料格式有誤：" + String(txt).slice(0, 160);
    return "儲存失敗（" + code + "）" + (txt ? "：" + String(txt).slice(0, 160) : "");
  }

  async function uploadBlob(path, blob) {
    var r = await fetch(SB + "/storage/v1/object/media/" + path, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "image/webp", "x-upsert": "true", "cache-control": "3600" }),
      body: blob
    });
    if (!r.ok) throw new Error("圖片上傳失敗（" + r.status + "）請確認 storage 桶與權限已建立。");
    return publicUrl(path);
  }
  function publicUrl(path) { return SB + "/storage/v1/object/public/media/" + path; }

  /* ------------------------------------------------------------------ 圖片處理 */
  function readFile(file) {
    return new Promise(function (res, rej) {
      var fr = new FileReader();
      fr.onload = function () { res(fr.result); };
      fr.onerror = function () { rej(new Error("讀取檔案失敗")); };
      fr.readAsDataURL(file);
    });
  }
  function loadImage(src) {
    return new Promise(function (res, rej) {
      var im = new Image();
      im.onload = function () { res(im); };
      im.onerror = function () { rej(new Error("這個檔案不是可讀取的圖片")); };
      im.src = src;
    });
  }
  async function shrink(file, maxEdge, quality) {
    var dataUrl = await readFile(file);
    var img = await loadImage(dataUrl);
    var w = img.naturalWidth, h = img.naturalHeight;
    var scale = Math.min(1, maxEdge / Math.max(w, h));
    var cw = Math.round(w * scale), ch = Math.round(h * scale);
    var cv = document.createElement("canvas");
    cv.width = cw; cv.height = ch;
    var ctx = cv.getContext("2d");
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, cw, ch);
    ctx.drawImage(img, 0, 0, cw, ch);
    var blob = await new Promise(function (res) { cv.toBlob(res, "image/webp", quality); });
    if (!blob) throw new Error("這個瀏覽器無法轉存圖片，請改用 Chrome 或 Safari 最新版。");
    return { blob: blob, w: cw, h: ch };
  }
  function uniqueName(prefix) {
    var d = new Date();
    var stamp = d.getFullYear() + ("0" + (d.getMonth() + 1)).slice(-2) + ("0" + d.getDate()).slice(-2);
    return prefix + "-" + stamp + "-" + Math.random().toString(36).slice(2, 8);
  }
  async function uploadImage(file, folder, alt) {
    var big = await shrink(file, 1600, 0.84);
    var sm = await shrink(file, 640, 0.8);
    var name = uniqueName(folder || "img");
    var path = name + ".webp";
    await uploadBlob(path, big.blob);
    await uploadBlob(name + "-thumb.webp", sm.blob);
    var row = await api("/rest/v1/media", {
      method: "POST", body: {
        storage_path: path, filename: file.name || path, mime: "image/webp",
        size_bytes: big.blob.size, width: big.w, height: big.h, alt: alt || ""
      },
      headers: { Prefer: "return=representation" }
    });
    return { path: path, thumb: name + "-thumb.webp", url: publicUrl(path), thumbUrl: publicUrl(name + "-thumb.webp"), row: (row && row[0]) || null };
  }

  /* ------------------------------------------------------------------ 共用畫面元件 */
  function statusPill(s) {
    var map = { published: ["p-published", "已發布"], draft: ["p-draft", "草稿"], hidden: ["p-hidden", "已隱藏"] };
    var m = map[s] || ["", s || "—"];
    return '<span class="pill ' + m[0] + '">' + m[1] + "</span>";
  }
  function photoURL(path, thumb) {
    if (!path) return "";
    if (/^https?:/.test(path)) return path;
    var p = thumb && /\.webp$/.test(path) ? path.replace(/\.webp$/, "-thumb.webp") : path;
    return publicUrl(p);
  }
  function confirmBox(msg) { return window.confirm(msg); }
  function busy(btn, on, label) {
    if (!btn) return;
    if (on) { btn.dataset.label = btn.textContent; btn.textContent = label || "處理中…"; btn.disabled = true; }
    else { btn.textContent = btn.dataset.label || btn.textContent; btn.disabled = false; }
  }

  /* ------------------------------------------------------------------ 資料讀寫 */
  async function loadStylists() {
    S.stylists = await api("/rest/v1/stylists?select=*&order=sort_order.asc,created_at.asc") || [];
    return S.stylists;
  }
  async function loadWorks() {
    S.works = await api("/rest/v1/works?select=*&order=sort_order.asc,created_at.desc") || [];
    return S.works;
  }
  async function countOf(table, query) {
    var r = await fetch(SB + "/rest/v1/" + table + "?select=id" + (query || ""), {
      headers: authHeaders({ Prefer: "count=exact", Range: "0-0" })
    });
    var cr = r.headers.get("content-range") || "";
    var n = cr.split("/")[1];
    return n && n !== "*" ? Number(n) : 0;
  }
  function services() {
    return [["hair-color", "染髮"], ["bleach-color", "漂髮"], ["hair-straightening", "縮毛矯正"],
      ["perm", "燙髮"], ["haircut", "剪髮"], ["hair-care", "護髮"], ["mens-hair", "男士造型"]];
  }
  function categories() {
    return [["color", "染髮"], ["bleach", "漂髮"], ["straightening", "縮毛矯正"],
      ["perm", "燙髮"], ["cut", "剪髮"], ["treatment", "護髮"], ["mens", "男士造型"]];
  }

  /* ------------------------------------------------------------------ 導覽／路由 */
  var NAV = [
    ["dash", "總覽"], ["stylists", "設計師"], ["works", "作品集"],
    ["media", "媒體庫"], ["settings", "網站設定"], ["account", "帳號"], ["phase2", "第二階段"]
  ];

  function buildNav() {
    var nav = $("nav");
    nav.innerHTML = "";
    NAV.forEach(function (n) {
      var b = el("button", "nav", "<span>" + n[1] + "</span>");
      b.type = "button";
      b.dataset.view = n[0];
      if (n[0] === "phase2") b.dataset.phase = "1";
      b.addEventListener("click", function () { setView(n[0]); sideClose(); });
      nav.appendChild(b);
    });
  }

  function navBadge(key, num) {
    NAV.forEach(function (n) {
      var b = document.querySelector('.nav[data-view="' + n[0] + '"]');
      if (!b) return;
      var old = b.querySelector(".badge-n");
      if (old) old.remove();
      if (n[0] === key && num != null) b.appendChild(el("span", "badge-n", String(num)));
    });
  }

  function setView(k, skipHash) {
    if (!NAV.some(function (n) { return n[0] === k; })) k = "dash";
    S.view = k;
    Array.prototype.forEach.call(document.querySelectorAll(".nav"), function (b) {
      b.setAttribute("aria-current", b.dataset.view === k ? "true" : "false");
    });
    var m = NAV.filter(function (n) { return n[0] === k; })[0];
    $("crumb").textContent = k === "dash" ? "DASHBOARD" : "CMS";
    $("pageTitle").textContent = m ? m[1] : "總覽";
    if (!skipHash) { try { history.replaceState(null, "", "#" + k); } catch (e) {} }
    closeDrawer();
    renderView();
  }

  function renderView() {
    var v = $("view");
    v.innerHTML = '<div class="empty">載入中…</div>';
    var fn = { dash: viewDash, stylists: viewStylists, works: viewWorks, media: viewMedia,
      settings: viewSettings, account: viewAccount, phase2: viewPhase2 }[S.view] || viewDash;
    fn(v);
  }

  function fail(v, e) {
    v.innerHTML = '<div class="empty"><b>讀取失敗</b>' + esc(e && e.message ? e.message : "請重新整理頁面") + "</div>";
  }

  /* ------------------------------------------------------------------ 抽屜 */
  function openDrawer(title, build) {
    var ed = $("editor");
    ed.innerHTML = "";
    var eh = el("div", "eh", '<h2 id="edTitle">' + esc(title) + "</h2>");
    var x = el("button", "x", "✕");
    x.type = "button"; x.setAttribute("aria-label", "關閉"); x.addEventListener("click", closeDrawer);
    eh.appendChild(x);
    var eb = el("div", "eb"), ef = el("div", "ef");
    ed.appendChild(eh); ed.appendChild(eb); ed.appendChild(ef);
    ed.classList.add("on"); ed.setAttribute("aria-hidden", "false");
    $("drawerBg").classList.add("on");
    document.body.style.overflow = "hidden";
    if (build) build(eb, ef);
  }
  function closeDrawer() {
    var ed = $("editor");
    ed.classList.remove("on"); ed.setAttribute("aria-hidden", "true");
    $("drawerBg").classList.remove("on");
    document.body.style.overflow = "";
  }
  function sideClose() { $("side").classList.remove("open"); }

  /* ------------------------------------------------------------------ 表單小元件 */
  function inp(id, label, value, type, tip) {
    return '<div class="field"><label for="' + id + '">' + esc(label) + '</label><input type="' +
      (type || "text") + '" id="' + id + '" value="' + esc(value == null ? "" : value) + '">' +
      (tip ? '<div class="tip">' + esc(tip) + "</div>" : "") + "</div>";
  }
  function txa(id, label, value, tip, rows) {
    return '<div class="field"><label for="' + id + '">' + esc(label) + '</label><textarea id="' + id +
      '" rows="' + (rows || 4) + '">' + esc(value == null ? "" : value) + "</textarea>" +
      (tip ? '<div class="tip">' + esc(tip) + "</div>" : "") + "</div>";
  }
  function sel(id, label, value, opts, tip) {
    var o = opts.map(function (p) {
      return '<option value="' + esc(p[0]) + '"' + (String(p[0]) === String(value) ? " selected" : "") + ">" + esc(p[1]) + "</option>";
    }).join("");
    return '<div class="field"><label for="' + id + '">' + esc(label) + '</label><select id="' + id + '">' + o + "</select>" +
      (tip ? '<div class="tip">' + esc(tip) + "</div>" : "") + "</div>";
  }
  function v(id) { var n = $(id); return n ? String(n.value).trim() : ""; }
  function lines(s) { return String(s || "").split(/\n/).map(function (x) { return x.trim(); }).filter(Boolean); }
  function num(vv, d) { var n = parseInt(vv, 10); return isNaN(n) ? d : n; }

  /* ------------------------------------------------------------------ 總覽 */
  async function viewDash(v) {
    try {
      var both = await Promise.all([loadStylists(), loadWorks(), countOf("media")]);
      var st = both[0], wk = both[1], mediaN = both[2];
      var stPub = st.filter(function (x) { return x.status === "published"; }).length;
      var wkPub = wk.filter(function (x) { return x.status === "published"; }).length;
      var recent = st.map(function (x) { return { t: "設計師", n: x.name || x.slug, s: x.status, d: x.updated_at, id: x.id }; })
        .concat(wk.map(function (x) { return { t: "作品", n: x.title || x.slug, s: x.status, d: x.updated_at, id: x.id }; }))
        .sort(function (a, b) { return String(b.d).localeCompare(String(a.d)); }).slice(0, 6);

      v.innerHTML =
        '<div class="stats">' +
          stat("設計師", st.length, stPub + " 已發布 · " + (st.length - stPub) + " 未發布") +
          stat("作品", wk.length, wkPub + " 已發布 · " + (wk.length - wkPub) + " 未發布") +
          stat("媒體庫", mediaN, "圖片數量") +
          stat("官網頁面", "34", "設計師頁與作品頁自動產生") +
        "</div>" +
        '<div class="card"><h2>快速操作</h2><div class="toolbar" style="margin-top:.8rem">' +
          '<button class="btn btn--sm" data-go="stylists">新增設計師</button>' +
          '<button class="btn btn--sm" data-go="works">新增作品</button>' +
          '<button class="btn btn--ghost btn--sm" data-go="media">上傳圖片</button>' +
          '<button class="btn btn--ghost btn--sm" data-go="settings">網站文案</button>' +
        "</div></div>" +
        '<div class="card"><h2>最近更新</h2><div style="margin-top:.6rem">' +
          (recent.length ? '<table class="list"><tbody>' + recent.map(function (r) {
            return "<tr><td class=\"num\">" + esc(r.t) + '</td><td class="cell-title">' + esc(r.n) +
              "</td><td>" + statusPill(r.s) + '</td><td class="num">' + fmtDate(r.d) + "</td></tr>";
          }).join("") + "</tbody></table>"
          : '<div class="empty"><b>還沒有資料</b>新增第一位設計師或第一件作品後，這裡會顯示更新紀錄。</div>') +
        "</div></div>" +
        '<div class="card"><h2>發布方式</h2><p class="hint">' +
          "後台儲存後，官網由 GitHub Actions 每 15 分鐘自動重建；若已在 config.js 設定 PUBLISH_WEBHOOK，" +
          "按下儲存會立刻觸發重建。未設定時請等待自動排程。<br>" +
          "</p></div>";

      Array.prototype.forEach.call(v.querySelectorAll("[data-go]"), function (b) {
        b.addEventListener("click", function () { setView(b.dataset.go); });
      });
    } catch (e) { fail(v, e); }
  }
  function stat(k, num, sub) {
    return '<div class="stat"><div class="k">' + esc(k) + '</div><div class="v">' + esc(num) + '</div><div class="s">' + esc(sub) + "</div></div>";
  }

  /* ------------------------------------------------------------------ 設計師列表 */
  async function viewStylists(v) {
    try {
      await loadStylists();
      var list = S.stylists;
      v.innerHTML =
        '<div class="card"><div class="toolbar">' +
          '<div><h2 style="margin:0">設計師</h2><p class="hint" style="margin:0">每位設計師儲存後，官網會自動產生一個個人頁（/stylists/代稱）。</p></div>' +
          '<div class="grow"></div>' +
          '<button class="btn btn--sm" id="newSty">新增設計師</button>' +
        '</div></div>' +
        '<div class="card">' +
          (list.length ? '<table class="list"><thead><tr><th>照片</th><th>名字</th><th>職稱</th><th>狀態</th><th>排序</th><th>更新</th><th></th></tr></thead><tbody>' +
            list.map(function (s) {
              return "<tr>" +
                '<td><img class="thumb" loading="lazy" alt="" src="' + esc(photoURL(s.photo_path, true)) + '" onerror="this.style.visibility=\'hidden\'"></td>' +
                '<td class="cell-title">' + esc(s.name || "（未命名）") + '<div class="num">' + esc(s.slug) + "</div></td>" +
                "<td>" + esc(s.title || "—") + "</td>" +
                "<td>" + statusPill(s.status) + "</td>" +
                '<td class="num">' + esc(s.sort_order) + "</td>" +
                '<td class="num">' + fmtDate(s.updated_at) + "</td>" +
                '<td><button class="btn btn--ghost btn--sm" data-ed="' + esc(s.id) + '">編輯</button></td>' +
              "</tr>";
            }).join("") + "</tbody></table>"
          : '<div class="empty"><b>尚無設計師</b>按下「新增設計師」建立第一位，填好資料、上傳照片後把狀態改為「已發布」就會出現在官網。</div>') +
        "</div>";

      $("newSty").addEventListener("click", function () { editStylist(null); });
      Array.prototype.forEach.call(v.querySelectorAll("[data-ed]"), function (b) {
        b.addEventListener("click", function () { editStylist(S.stylists.filter(function (x) { return x.id === b.dataset.ed; })[0]); });
      });
    } catch (e) { fail(v, e); }
  }

  /* ------------------------------------------------------------------ 設計師表單欄位 */
  function stylistFields(d) {
    var tagsNote = "一行一個，或用逗號分隔";
    return '<div class="sect-label">照片</div>' +
      '<div class="photo-edit">' +
        '<div><div class="frame" id="stFrame"></div>' +
          '<div class="btn-row" style="margin-top:8px">' +
            '<button class="btn btn--ghost btn--sm" type="button" id="stPick">選擇照片</button>' +
            '<button class="btn btn--ghost btn--sm" type="button" id="stClear">移除</button>' +
          '</div>' +
        '</div>' +
        '<div>' +
          '<div class="drop" id="stDrop">點這裡選照片，或把檔案拖進來<br><span class="tip">JPG／PNG／WebP，上限 12MB；系統自動轉 WebP（主圖 1600px、縮圖 640px）</span></div>' +
          txa("f_photo_note", "照片說明", d.photo_note, "例如「攝影：店內自然光」，沒有就留白。") +
        '</div>' +
      '</div>' +
      '<div class="sect-label">基本資料</div>' +
      '<div class="grid2">' +
        inp("f_name", "名字（必填）", d.name) +
        inp("f_nameEn", "英文名字", d.name_en, "text", "顯示在名字下方，例如 RYAN。") +
      '</div>' +
      '<div class="grid2">' +
        inp("f_title", "職稱", d.title, "text", "例如「店長／資深設計師」。") +
        inp("f_slug", "網址代稱（英文）", d.slug, "text", "官網個人頁網址：/stylists/代稱。中文名字請自行填英文拼音。") +
      '</div>' +
      '<div class="grid3">' +
        sel("f_status", "狀態", d.status, [["draft", "草稿"], ["published", "已發布"], ["hidden", "已隱藏"]], "只有「已發布」會出現在官網。") +
        inp("f_sort", "排序", d.sort_order, "number", "數字小的排前面。") +
        inp("f_exp", "經歷", d.experience, "text", "例如「入行 12 年」。") +
      '</div>' +
      '<div class="sect-label">介紹內容</div>' +
      txa("f_paras", "介紹段落", (d.paragraphs || []).join("\n\n"), "一行一段，空行分段；官網會依序輸出。", 6) +
      txa("f_philosophy", "設計理念", d.philosophy, "一段話，會出現在個人頁引言區。", 3) +
      '<div class="grid2">' +
        txa("f_specialties", "擅長技術", (d.specialties || []).join("\n"), tagsNote, 4) +
        txa("f_styles", "風格標籤", (d.styles || []).join("\n"), tagsNote, 4) +
      '</div>' +
      txa("f_tags", "其他標籤", (d.tags || []).join("\n"), tagsNote, 3) +
      '<div class="sect-label">價格與連結</div>' +
      '<div class="field"><label>價目（名稱／價格／備註）</label><div class="repeatable" id="priceRows"></div>' +
        '<div class="tip">價格未確認時，價格欄可填「待店家確認」。空白列儲存時會自動忽略。</div></div>' +
      '<div class="btn-row"><button class="btn btn--ghost btn--sm" type="button" id="addPrice">＋ 新增一列價目</button></div>' +
      '<div class="grid2">' +
        inp("f_ig", "Instagram 網址", d.instagram_url, "url") +
        inp("f_line", "LINE 網址", d.line_url, "url") +
      '</div>' +
      '<div class="sect-label">SEO</div>' +
      '<div class="grid2">' +
        inp("f_seo_t", "頁面標題", d.seo_title, "text", "留白會自動用「名字｜HD Hope」.") +
        inp("f_seo_d", "頁面描述", d.seo_desc, "text", "建議 60–120 字。") +
      '</div>';
  }

  function blankStylist() {
    return { slug: "", status: "draft", sort_order: 0, name: "", name_en: "", title: "", photo_path: "",
      photo_note: "", paragraphs: [], philosophy: "", specialties: [], styles: [], experience: "",
      tags: [], instagram_url: "", line_url: "", prices: [], seo_title: "", seo_desc: "" };
  }

  function editStylist(row) {
    var d = row ? JSON.parse(JSON.stringify(row)) : blankStylist();
    var picked = null;
    openDrawer(row ? "編輯設計師" : "新增設計師", function (eb, ef) {
      eb.innerHTML = stylistFields(d);
      var frame = $("stFrame");
      function paint() {
        var src = picked ? URL.createObjectURL(picked) : photoURL(d.photo_path);
        frame.innerHTML = src ? '<img src="' + esc(src) + '" alt="">'
          : '<div class="ph">尚未上傳照片<br>官網會顯示「待補」佔位</div>';
      }
      var fileIn = el("input");
      fileIn.type = "file"; fileIn.accept = "image/jpeg,image/png,image/webp"; fileIn.style.display = "none";
      eb.appendChild(fileIn);
      function take(f) { if (!f) return; picked = f; paint(); }
      fileIn.addEventListener("change", function () { take(fileIn.files[0]); });
      paint();
      $("stPick").addEventListener("click", function () { fileIn.click(); });
      $("stClear").addEventListener("click", function () { picked = null; d.photo_path = ""; paint(); });
      var drop = $("stDrop");
      drop.addEventListener("click", function () { fileIn.click(); });
      drop.addEventListener("dragover", function (e) { e.preventDefault(); drop.classList.add("hot"); });
      drop.addEventListener("dragleave", function () { drop.classList.remove("hot"); });
      drop.addEventListener("drop", function (e) {
        e.preventDefault(); drop.classList.remove("hot");
        if (e.dataTransfer.files && e.dataTransfer.files[0]) take(e.dataTransfer.files[0]);
      });

      var priceWrap = $("priceRows");
      function addPrice(p) {
        p = p || {};
        var r = el("div", "row");
        r.style.gridTemplateColumns = "1fr 1fr 1fr auto";
        r.innerHTML = '<input type="text" placeholder="項目（剪髮）" value="' + esc(p.name || "") + '">' +
          '<input type="text" placeholder="價格（800 起／待店家確認）" value="' + esc(p.val || "") + '">' +
          '<input type="text" placeholder="備註" value="' + esc(p.note || "") + '">' +
          '<button class="btn btn--ghost btn--sm" type="button">移除</button>';
        r.querySelector("button").addEventListener("click", function () { r.remove(); });
        priceWrap.appendChild(r);
      }
      (d.prices || []).forEach(addPrice);
      $("addPrice").addEventListener("click", function () { addPrice({}); });

      ef.innerHTML = '<button class="btn btn--ghost btn--sm" type="button" id="stCancel">取消</button>' +
        (row && row.id ? '<button class="btn btn--danger btn--sm" type="button" id="stDel">刪除</button>' : "") +
        '<button class="btn" type="button" id="stSave">儲存</button>';
      $("stCancel").addEventListener("click", closeDrawer);
      if (row && row.id) $("stDel").addEventListener("click", function () { removeStylist(row); });
      $("stSave").addEventListener("click", function () { saveStylist(row, d, picked, this); });
    });
  }

  function collectPrices() {
    var rows = Array.prototype.map.call(document.querySelectorAll("#priceRows .row"), function (r) {
      var i = r.querySelectorAll("input");
      return { name: i[0].value.trim(), val: i[1].value.trim(), note: i[2].value.trim() };
    });
    return rows.filter(function (p) { return p.name || p.val || p.note; });
  }

  function pickSlug(row, d, type) {
    var s = d.slug || "";
    s = s.toLowerCase().replace(/[^a-z0-9-]/g, "").replace(/-+/g, "-").replace(/^-|-$/g, "");
    if (s.length < 2) {
      s = slugify(d.nameEn || d.nameEn || "") || slugify(d.name || "") || "";
    }
    if (!s || s.length < 2) {
      s = (type === "work" ? "work-" : "stylist-") + Math.random().toString(36).slice(2, 7);
    }
    return s.slice(0, type === "work" ? 60 : 40);
  }

  async function saveStylist(row, d, picked, btn) {
    var name = v("f_name");
    if (!name) { toast("請先填名字", "err"); return; }
    var body = {
      slug: pickSlug(row, { slug: v("f_slug") }, "stylist"),
      status: v("f_status") || "draft",
      sort_order: num(v("f_sort"), 0),
      name: name,
      name_en: v("f_nameEn"),
      title: v("f_title"),
      photo_note: v("f_photo_note"),
      paragraphs: String($("f_paras").value).split(/\n\s*\n/).map(function (x) { return x.replace(/\n/g, " ").trim(); }).filter(Boolean),
      philosophy: v("f_philosophy"),
      specialties: lines($("f_specialties").value.replace(/，/g, "\n")),
      styles: lines($("f_styles").value.replace(/，/g, "\n")),
      tags: lines($("f_tags").value.replace(/，/g, "\n")),
      experience: v("f_exp"),
      instagram_url: v("f_ig"),
      line_url: v("f_line"),
      prices: collectPrices(),
      seo_title: v("f_seo_t"),
      seo_desc: v("f_seo_d"),
      photo_path: d.photo_path || ""
    };
    busy(btn, true, "儲存中…");
    try {
      if (picked) {
        var up = await uploadImage(picked, "stylists", name);
        body.photo_path = up.path;
      }
      var q = "/stylists" + (row && row.id ? "?id=eq." + encodeURIComponent(row.id) : "");
      var saved = await api(q, {
        method: row && row.id ? "PATCH" : "POST",
        prefer: "return=representation",
        body: body
      });
      var got = (saved && saved[0]) || {};
      toast(row && row.id ? "已儲存設計師資料" : "已新增設計師", "ok");
      closeDrawer();
      await loadStylists();
      triggerPublish(got.status === "published" || body.status === "published");
      setView("stylists");
    } catch (e) {
      toast(e.message, "err");
    } finally { busy(btn, false); }
  }

  async function removeStylist(row) {
    if (!confirmBox("確定刪除「" + (row.name || row.slug) + "」？\n這個動作無法復原，該設計師的個人頁也會從官網移除。")) return;
    try {
      await api("/stylists?id=eq." + encodeURIComponent(row.id), { method: "DELETE" });
      toast("已刪除設計師", "ok");
      closeDrawer();
      await loadStylists();
      triggerPublish(false);
      setView("stylists");
    } catch (e) { toast(e.message, "err"); }
  }

  /* ------------------------------------------------------------------ 作品列表 */
  async function viewWorks(v) {
    try {
      await Promise.all([loadWorks(), S.stylists.length ? null : loadStylists()]);
      var list = S.works;
      v.innerHTML =
        '<div class="card"><div class="toolbar">' +
          '<div><h2 style="margin:0">作品集</h2><p class="hint" style="margin:0">每件作品儲存後，官網會自動產生作品頁，並自動歸類到對應的療程分類。</p></div>' +
          '<div class="grow"></div>' +
          '<button class="btn btn--sm" id="newWork">新增作品</button>' +
        '</div></div>' +
        '<div class="card">' +
          (list.length ? '<table class="list"><thead><tr><th>封面</th><th>標題</th><th>分類</th><th>設計師</th><th>狀態</th><th>日期</th><th></th></tr></thead><tbody>' +
            list.map(function (w) {
              var ph = (w.photos && w.photos[0] && (w.photos[0].path || w.photos[0])) || "";
              var photo = ph ? publicUrl(String(ph)) : "";
              var catName = (categories().filter(function (c) { return c[0] === w.category; })[0] || [w.category, w.category])[1];
              var st = S.stylists.filter(function (s) { return s.id === w.stylist_id; })[0];
              return "<tr>" +
                '<td>' + (photo ? '<img class="thumb" loading="lazy" alt="" src="' + esc(photo) + '" onerror="this.style.visibility=\'hidden\'">' : '<span class="pill">無圖</span>') + "</td>" +
                '<td class="cell-title">' + esc(w.title || "（未命名）") + '<div class="num">' + esc(w.slug) + "</div></td>" +
                "<td>" + esc(catName) + "</td>" +
                "<td>" + esc(st ? (st.name || st.slug) : "—") + "</td>" +
                "<td>" + statusPill(w.status) + "</td>" +
                '<td class="num">' + esc(w.completed_at || "—") + "</td>" +
                '<td><button class="btn btn--ghost btn--sm" data-ed="' + esc(w.id) + '">編輯</button></td>' +
              "</tr>";
            }).join("") + "</tbody></table>"
          : '<div class="empty"><b>尚無作品</b>按下「新增作品」建立第一件，上傳照片並選擇分類，狀態改為「已發布」就會出現在作品集。</div>') +
        "</div>";

      $("newWork").addEventListener("click", function () { editWork(null); });
      Array.prototype.forEach.call(v.querySelectorAll("[data-ed]"), function (b) {
        b.addEventListener("click", function () { editWork(S.works.filter(function (x) { return x.id === b.dataset.ed; })[0]); });
      });
    } catch (e) { fail(v, e); }
  }

  /* ------------------------------------------------------------------ 作品表單 */
  function workFields(d) {
    var styOpts = [["", "未指定"]].concat(S.stylists.map(function (s) { return [s.id, (s.name || s.slug) + (s.status === "published" ? "" : "（未發布）")]; }));
    return '<div class="sect-label">照片（第一張為封面）</div>' +
      '<div class="thumbs" id="wThumbs"></div>' +
      '<div class="btn-row">' +
        '<button class="btn btn--ghost btn--sm" type="button" id="wAdd">＋ 上傳照片</button>' +
        '<span class="tip">JPG／PNG／WebP，可多選；系統自動轉 WebP。點縮圖右上角可移除，第一張就是封面。</span>' +
      '</div>' +
      txa("f_photo_note", "照片說明", d.photo_note, "例如「攝影：店內自然光」，可不填。", 2) +
      '<div class="sect-label">作品資料</div>' +
      '<div class="grid2">' +
        inp("f_title", "作品標題（必填）", d.title, "text", "例如「奶茶棕漸層染」。") +
        inp("f_slug", "網址代稱（英文）", d.slug, "text", "作品頁網址：/works/代稱。") +
      '</div>' +
      '<div class="grid2">' +
        sel("f_cat", "分類", d.category, categories(), "決定作品會出現在哪個療程篩選。") +
        sel("f_stylist", "設計師", d.stylist_id || "", styOpts, "指定後作品會同時出現在該設計師的個人頁。") +
      '</div>' +
      '<div class="grid3">' +
        sel("f_status", "狀態", d.status, [["draft", "草稿"], ["published", "已發布"], ["hidden", "已隱藏"]]) +
        inp("f_date", "完成日期", d.completed_at, "date") +
        inp("f_sort", "排序", d.sort_order, "number", "數字小的排前面。") +
      '</div>' +
      '<div class="sect-label">說明</div>' +
      txa("f_desc", "作品描述", d.description, "2–4 句說明染燙過程、髮質狀況與結果。", 5) +
      '<div class="grid2">' +
        inp("f_color", "染劑／色號", d.color_desc, "text", "例如「7 度奶茶棕 + 冷調灰」。漂染類才需要。") +
        inp("f_bleach", "漂髮次數", d.bleached, "text", "例如「漂 2 次」。未漂髮可留白。") +
      '</div>' +
      inp("f_alt", "圖片 ALT 文字", d.alt, "text", "給搜尋引擎與螢幕閱讀器用，描述照片內容。") +
      '<div class="sect-label">SEO</div>' +
      '<div class="grid2">' +
        inp("f_seo_t", "頁面標題", d.seo_title) +
        inp("f_seo_d", "頁面描述", d.seo_desc, "text", "建議 60–120 字。") +
      '</div>';
  }

  function blankWork() {
    return { slug: "", status: "draft", sort_order: 0, title: "", category: "color", stylist_id: null,
      service_slug: "", photos: [], alt: "", color_desc: "", bleached: "", completed_at: null,
      description: "", photo_note: "", seo_title: "", seo_desc: "" };
  }

  function editWork(row) {
    var d = row ? JSON.parse(JSON.stringify(row)) : blankWork();
    if (!Array.isArray(d.photos)) d.photos = [];
    openDrawer(row ? "編輯作品" : "新增作品", function (eb, ef) {
      eb.innerHTML = workFields(d);
      var wrap = $("wThumbs");

      function paintThumbs() {
        wrap.innerHTML = "";
        if (!d.photos.length) {
          wrap.innerHTML = '<div class="empty" style="grid-column:1/-1;padding:18px"><b>還沒有照片</b>按「上傳照片」加入，第一張會當封面。</div>';
        }
        d.photos.forEach(function (p, i) {
          var path = typeof p === "string" ? p : (p.path || "");
          var src = /^blob:|^https?:/.test(path) ? path : publicUrl(path);
          var card = el("div", "thumb-card");
          card.innerHTML = '<img src="' + esc(src) + '" alt="" loading="lazy">' +
            (i === 0 ? '<span class="cover-flag">封面</span>' : "") +
            '<div class="cap"><span>第 ' + (i + 1) + " 張</span></div>" +
            '<button class="x" type="button" aria-label="移除">✕</button>';
          card.querySelector(".x").addEventListener("click", function () {
            d.photos.splice(i, 1); paintThumbs();
          });
          wrap.appendChild(card);
        });
      }
      paintThumbs();

      var fileIn = el("input");
      fileIn.type = "file"; fileIn.multiple = true;
      fileIn.accept = "image/jpeg,image/png,image/webp"; fileIn.style.display = "none";
      eb.appendChild(fileIn);
      $("wAdd").addEventListener("click", function () { fileIn.click(); });
      fileIn.addEventListener("change", async function () {
        var files = Array.prototype.slice.call(fileIn.files || []);
        if (!files.length) return;
        var btn = $("wAdd");
        busy(btn, true, "上傳中…");
        for (var i = 0; i < files.length; i++) {
          try {
            var up = await uploadImage(files[i], "works", d.title || v("f_title"));
            d.photos.push({ path: up.path, alt: d.alt || "", crop: "" });
          } catch (e) { toast(e.message, "err"); }
        }
        busy(btn, false); fileIn.value = ""; paintThumbs();
      });

      ef.innerHTML = '<button class="btn btn--ghost btn--sm" type="button" id="wCancel">取消</button>' +
        (row && row.id ? '<button class="btn btn--danger btn--sm" type="button" id="wDel">刪除</button>' : "") +
        '<button class="btn" type="button" id="wSave">儲存</button>';
      $("wCancel").addEventListener("click", closeDrawer);
      if (row && row.id) $("wDel").addEventListener("click", function () { removeWork(row); });
      $("wSave").addEventListener("click", function () { saveWork(row, d, this); });
    });
  }

  function catService(cat) {
    var c = { color: "hair-color", bleach: "bleach-color", straightening: "hair-straightening",
      perm: "perm", cut: "haircut", treatment: "hair-care", mens: "mens-hair" };
    return c[cat] || "";
  }

  async function saveWork(row, d, btn) {
    var title = v("f_title");
    if (!title) { toast("請先填作品標題", "err"); return; }
    var cat = v("f_cat") || "color";
    var body = {
      slug: pickSlug(row, { slug: v("f_slug") }, "work"),
      status: v("f_status") || "draft",
      sort_order: num(v("f_sort"), 0),
      title: title,
      category: cat,
      service_slug: catService(cat),
      stylist_id: v("f_stylist") || null,
      photos: d.photos,
      alt: v("f_alt"),
      color_desc: v("f_color"),
      bleached: v("f_bleach"),
      completed_at: v("f_date") || null,
      description: v("f_desc"),
      photo_note: v("f_photo_note"),
      seo_title: v("f_seo_t"),
      seo_desc: v("f_seo_d")
    };
    if (!body.photos.length) { toast("請至少上傳一張照片", "err"); return; }
    busy(btn, true, "儲存中…");
    try {
      var q = "/works" + (row && row.id ? "?id=eq." + encodeURIComponent(row.id) : "");
      await api(q, { method: row && row.id ? "PATCH" : "POST", prefer: "return=representation", body: body });
      toast(row && row.id ? "已儲存作品" : "已新增作品", "ok");
      closeDrawer();
      await loadWorks();
      triggerPublish(body.status === "published");
      setView("works");
    } catch (e) { toast(e.message, "err"); } finally { busy(btn, false); }
  }

  async function removeWork(row) {
    if (!confirmBox("確定刪除「" + (row.title || row.slug) + "」？\n作品頁會從官網移除，圖片仍留在媒體庫。")) return;
    try {
      await api("/works?id=eq." + encodeURIComponent(row.id), { method: "DELETE" });
      toast("已刪除作品", "ok");
      closeDrawer();
      await loadWorks();
      triggerPublish(false);
      setView("works");
    } catch (e) { toast(e.message, "err"); }
  }

  /* 發布：有設 webhook 就立刻重建，沒設就等排程 */
  async function triggerPublish(live) {
    if (!CFG.PUBLISH_WEBHOOK) {
      if (live) toast("已儲存。官網會在 15 分鐘內自動重建上線。", "ok");
      return;
    }
    try {
      await fetch(CFG.PUBLISH_WEBHOOK, { method: "POST" });
      if (live) toast("已觸發官網重建，約 1–2 分鐘後生效。", "ok");
    } catch (e) { toast("重建通知送出失敗，請稍後由排程自動重建。", "err"); }
  }

  /* ------------------------------------------------------------------ 媒體庫 */
  async function viewMedia(v) {
    try {
      var rows = (await api("/media?select=*&order=created_at.desc&limit=300")) || [];
      v.innerHTML =
        '<div class="card"><div class="toolbar"><div><h2 style="margin:0">媒體庫</h2>' +
          '<p class="hint" style="margin:0">圖片存在 Supabase Storage 的 media 桶；作品與設計師照片都從這裡取用。</p></div>' +
          '<div class="grow"></div><button class="btn btn--sm" id="mAdd">上傳圖片</button></div>' +
          '<div class="drop" id="mDrop" style="margin-top:14px">點這裡或把圖片拖進來（可多選）<br>' +
          '<span class="tip">JPG／PNG／WebP，單張上限 12MB；自動轉 WebP 並產生 640px 縮圖。</span></div>' +
        '</div>' +
        '<div class="card"><div class="toolbar" style="margin-bottom:.8rem"><h2 style="margin:0">全部圖片</h2>' +
          '<span class="badge-n">' + rows.length + '</span><div class="grow"></div>' +
          '<input type="text" id="mSearch" placeholder="搜尋檔名或 ALT" style="max-width:240px">' +
        '</div><div class="thumbs" id="mGrid"></div></div>';

      var fileIn = el("input");
      fileIn.type = "file"; fileIn.multiple = true;
      fileIn.accept = "image/jpeg,image/png,image/webp"; fileIn.style.display = "none";
      v.appendChild(fileIn);

      function paint(list) {
        var grid = $("mGrid");
        grid.innerHTML = "";
        if (!list.length) {
          grid.innerHTML = '<div class="empty" style="grid-column:1/-1"><b>還沒有圖片</b>用上面的上傳區加入第一批照片。</div>';
          return;
        }
        list.forEach(function (m) {
          var card = el("div", "thumb-card");
          card.innerHTML = '<img loading="lazy" alt="" src="' + esc(photoURL(m.storage_path, true)) + '">' +
            '<div class="cap"><span title="' + esc(m.filename || m.storage_path) + '">' +
              esc((m.filename || m.storage_path || "").slice(0, 22)) + '</span>' +
              '<button class="btn btn--ghost btn--sm" type="button" data-cp="' + esc(m.storage_path) + '">複製路徑</button></div>' +
            '<div class="cap"><input type="text" data-alt="' + esc(m.id) + '" value="' + esc(m.alt || "") + '" placeholder="ALT 說明">' +
              '<button class="btn btn--danger btn--sm" type="button" data-del="' + esc(m.id) + '">刪除</button></div>';
          var altIn = card.querySelector("[data-alt]");
          altIn.addEventListener("change", async function () {
            try { await api("/media?id=eq." + encodeURIComponent(m.id), { method: "PATCH", body: { alt: altIn.value.trim() } }); toast("已更新 ALT", "ok"); }
            catch (e) { toast(e.message, "err"); }
          });
          card.querySelector("[data-cp]").addEventListener("click", function () {
            copyText(m.storage_path);
          });
          card.querySelector("[data-del]").addEventListener("click", function () { removeMedia(m); });
          grid.appendChild(card);
        });
      }
      paint(rows);

      $("mSearch").addEventListener("input", function () {
        var q = this.value.trim().toLowerCase();
        paint(rows.filter(function (m) { return !q || ((m.filename || "") + " " + (m.alt || "") + " " + m.storage_path).toLowerCase().indexOf(q) >= 0; }));
      });

      async function upload(files) {
        var arr = Array.prototype.slice.call(files || []);
        if (!arr.length) return;
        var btn = $("mAdd");
        busy(btn, true, "上傳中…");
        var ok = 0;
        for (var i = 0; i < arr.length; i++) {
          try {
            var up = await uploadImage(arr[i], "library", "");
            rows.unshift({ id: "tmp", storage_path: up.path, filename: arr[i].name, alt: "" });
            ok++;
          } catch (e) { toast(e.message, "err"); }
        }
        busy(btn, false); fileIn.value = "";
        if (ok) { toast("已上傳 " + ok + " 張圖片", "ok"); setView("media"); }
      }

      $("mAdd").addEventListener("click", function () { fileIn.click(); });
      fileIn.addEventListener("change", function () { upload(fileIn.files); });
      var drop = $("mDrop");
      drop.addEventListener("click", function () { fileIn.click(); });
      drop.addEventListener("dragover", function (e) { e.preventDefault(); drop.classList.add("hot"); });
      drop.addEventListener("dragleave", function () { drop.classList.remove("hot"); });
      drop.addEventListener("drop", function (e) {
        e.preventDefault(); drop.classList.remove("hot");
        upload(e.dataTransfer.files);
      });
    } catch (e) { fail(v, e); }
  }

  function copyText(t) {
    function done() { toast("已複製：" + t, "ok"); }
    function legacy() {
      try {
        var ta = el("textarea");
        ta.value = t; ta.style.position = "fixed"; ta.style.top = "-1000px"; ta.style.opacity = "0";
        document.body.appendChild(ta); ta.focus(); ta.select();
        var ok = document.execCommand("copy");
        document.body.removeChild(ta);
        if (ok) { done(); return true; }
      } catch (e) { /* ignore */ }
      return false;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(t).then(done, function () { if (!legacy()) toast("複製失敗，請手動選取路徑", "err"); });
    } else if (!legacy()) {
      toast("這個瀏覽器不支援自動複製，請手動選取路徑", "err");
    }
  }

  async function removeMedia(m) {
    try {
      var used = [];
      var wk = await api("/works?select=title,photos");
      (wk || []).forEach(function (w) {
        var ps = (w.photos || []).map(function (p) { return typeof p === "string" ? p : (p && p.path) || ""; });
        if (ps.indexOf(m.storage_path) >= 0) used.push("作品「" + (w.title || "未命名") + "」");
      });
      var st = await api("/stylists?select=name,photo_path");
      (st || []).forEach(function (s) {
        if (s.photo_path === m.storage_path) used.push("設計師「" + (s.name || "未命名") + "」的個人照片");
      });
      if (used.length) {
        toast("這張圖片正被使用中，請先更換：" + used.join("、"), "err");
        return;
      }
      if (!confirmBox("刪除這張圖片？\n" + m.storage_path + "\n刪除後無法復原。")) return;
      var del = await fetch(SB + "/storage/v1/object/media/" + m.storage_path, { method: "DELETE", headers: authHeaders() });
      if (!del.ok && del.status !== 404) throw new Error("圖片檔刪除失敗（" + del.status + "）");
      await api("/media?id=eq." + encodeURIComponent(m.id), { method: "DELETE" });
      toast("已刪除圖片", "ok");
      setView("media");
    } catch (e) { toast(e.message, "err"); }
  }

  /* ------------------------------------------------------------------ 網站設定 */
  var SETTING_DEFAULTS = {
  "brand": {
    "name": "HD Hope Hair Salon",
    "nameShort": "HD Hope",
    "nameZh": "HD Hope 髮廊",
    "slogan": "細節成就美感，讓美好從希望開始。",
    "enLine": "HIGH DEFINITION · HOPE · BEAUTY",
    "intro": "以專業技術與溫暖服務，成就每一次美好的改變。",
    "positioning": "高質感但親切、專業且有溫度的桃園美髮沙龍。",
    "domain": "https://hdhopehair.com",
    "locale": "zh-Hant-TW",
    "logo": {
      "path": "/assets/img/logo.png",
      "note": "正式 HD 字母交錯 Logo 原圖（透明 PNG／SVG 優先）。未上傳前顯示中性佔位，不以 AI 重繪。",
      "status": "pending-upload"
    }
  },
  "contact": {
    "phoneDisplay": "03-333-0671",
    "phoneLink": "tel:+88633330671",
    "addressFull": "桃園市桃園區成功路一段12號3樓",
    "streetAddress": "成功路一段12號3樓",
    "addressLocality": "桃園區",
    "addressRegion": "桃園市",
    "addressCountry": "TW",
    "floorNote": "位於 3 樓，入口請由成功路一段進入",
    "hoursDisplay": "12:00–20:00",
    "opens": "12:00",
    "closes": "20:00",
    "closedDay": "每週一",
    "closedNote": "每週一公休；國定假日與臨時調整依官方 LINE 公告為準。",
    "igHandle": "hd_hope_hair",
    "igUrl": "https://www.instagram.com/hd_hope_hair/",
    "lineId": "@877onqgo",
    "lineUrl": "https://line.me/R/ti/p/@877onqgo",
    "lineStatus": "standard-format-unverified",
    "lineNote": "此連結依 LINE 官方帳號 ID 的標準加好友網址格式產生，上線前請由店家實際點擊驗證一次。",
    "googleBusinessUrl": "",
    "googleBusinessNote": "Google 商家網址尚未提供，取得後填入即可啟用評論模組與地圖按鈕。"
  },
  "seo": {
    "defaultTitleSuffix": "HD Hope Hair Salon｜桃園美髮沙龍",
    "defaultDescription": "HD Hope Hair Salon 位於桃園市桃園區成功路一段，提供霧感染髮、漂染特殊色、縮毛矯正、燙髮、護髮與男士剪燙。以專業技術與溫暖服務，成就每一次美好的改變。",
    "ogImage": "/assets/img/og-default.jpg",
    "keywordsLocal": [
      "桃園髮廊",
      "桃園染髮",
      "桃園漂髮",
      "桃園霧感染髮",
      "桃園特殊色",
      "桃園縮毛矯正",
      "桃園燙髮",
      "桃園護髮",
      "桃園男士剪髮"
    ]
  }
};

  var SETTING_KEYS = [
    ["brand", "品牌資訊", "店名、地址、電話、營業時間與社群連結。會寫回網站的 brand 設定，所有頁尾與聯絡區塊同步更新。"],
    ["contact", "聯絡與預約", "電話、地址、公休日、IG 與 LINE 連結。會寫回網站的 contact 設定，用於聯絡頁、頁尾與結構化資料。"],
    ["seo", "SEO 預設", "全站預設標題、描述與社群分享文字。會寫回網站的 seo 設定。"]
  ];

  async function viewSettings(v) {
    try {
      var rows = (await api("/settings?select=*")) || [];
      var byKey = {};
      rows.forEach(function (r) { byKey[r.key] = r; });
      v.innerHTML = '<div class="card"><h2>網站設定</h2><p class="hint">' +
        "這裡的文字會直接寫進官網。內容以 JSON 儲存，格式必須是物件（大括號）；" +
        "儲存後若設定正確，官網重建時會套用。欄位名稱請沿用原本的鍵，不要自行改名。</p></div>" +
        SETTING_KEYS.map(function (k) {
          var row = byKey[k[0]];
          var val = JSON.stringify((row && row.value) || SETTING_DEFAULTS[k[0]] || {}, null, 2);
          return '<div class="card"><h2>' + esc(k[1]) + ' <span class="pill">' + esc(k[0]) + "</span></h2>" +
            '<p class="hint">' + esc(k[2]) + "</p>" +
            '<textarea id="set_' + k[0] + '" rows="12" spellcheck="false" style="font-family:ui-monospace,Menlo,monospace;font-size:.78rem">' +
            esc(val) + "</textarea>" +
            '<div class="btn-row" style="margin-top:10px">' +
            '<button class="btn btn--sm" type="button" data-save="' + k[0] + '">儲存' + esc(k[1]) + "</button>" +
            '<button class="btn btn--ghost btn--sm" type="button" data-check="' + k[0] + '">檢查格式</button>' +
            '<span class="tip" id="setok_' + k[0] + '"></span></div></div>';
        }).join("");

      Array.prototype.forEach.call(v.querySelectorAll("[data-check]"), function (b) {
        b.addEventListener("click", function () {
          var msg = $("setok_" + b.dataset.check);
          try { JSON.parse($("set_" + b.dataset.check).value); msg.textContent = "格式正確"; msg.style.color = "#3C5A3C"; }
          catch (e) { msg.textContent = "JSON 格式錯誤：" + e.message; msg.style.color = "#8C5A48"; }
        });
      });
      Array.prototype.forEach.call(v.querySelectorAll("[data-save]"), function (b) {
        b.addEventListener("click", async function () {
          var k = b.dataset.save, txt = $("set_" + k).value;
          var parsed;
          try { parsed = JSON.parse(txt); } catch (e) { toast("JSON 格式錯誤：" + e.message, "err"); return; }
          if (typeof parsed !== "object" || Array.isArray(parsed) || parsed === null) { toast("最外層必須是大括號物件", "err"); return; }
          busy(b, true, "儲存中…");
          try {
            await api("/settings?on_conflict=key", {
              method: "POST", prefer: "resolution=merge-duplicates,return=representation",
              body: { key: k, value: parsed }
            });
            toast("已儲存" + SETTING_KEYS.filter(function (x) { return x[0] === k; })[0][1], "ok");
            triggerPublish(true);
          } catch (e) { toast(e.message, "err"); } finally { busy(b, false); }
        });
      });
    } catch (e) { fail(v, e); }
  }

  /* ------------------------------------------------------------------ 帳號 */
  async function viewAccount(v) {
    v.innerHTML =
      '<div class="card"><h2>登入帳號</h2><p class="hint">登入與密碼由 Supabase Auth 管理，這個網站不含任何密碼。</p>' +
        '<table class="list" style="margin-top:.8rem"><tbody>' +
          "<tr><td>電子郵件</td><td class=\"cell-title\">" + esc(S.email || "—") + "</td></tr>" +
          "<tr><td>權限</td><td>" + (S.token ? statusPill("published").replace(/已發布/, "管理員") : "—") + "</td></tr>" +
        "</tbody></table>" +
        '<div class="btn-row" style="margin-top:14px">' +
          '<button class="btn btn--ghost btn--sm" type="button" id="pwReset">寄送重設密碼信</button>' +
          '<button class="btn btn--danger btn--sm" type="button" id="logout2">登出</button>' +
        "</div></div>" +
      '<div class="card"><h2>新增管理員</h2><p class="hint">' +
        "後台採白名單制。步驟：<br>" +
        "1. 在 Supabase 後台 Authentication → Users 建立使用者（設定密碼）。<br>" +
        "2. 在 SQL Editor 執行：<code>insert into public.admins(user_id,email) values ('使用者 UID','email');</code><br>" +
        "3. 沒加入 admins 的帳號即使登入成功也讀不到資料。" +
      "</p></div>";

    $("pwReset").addEventListener("click", async function () {
      var btn = this;
      busy(btn, true, "寄送中…");
      try {
        var r = await fetch(SB + "/auth/v1/recover", {
          method: "POST", headers: { apikey: KEY, "Content-Type": "application/json" },
          body: JSON.stringify({ email: S.email })
        });
        if (!r.ok) throw new Error("寄送失敗（" + r.status + "），請確認 Supabase 的寄信服務已設定。");
        toast("已寄出重設密碼信到 " + S.email, "ok");
      } catch (e) { toast(e.message, "err"); } finally { busy(btn, false); }
    });
    $("logout2").addEventListener("click", logout);
  }

  /* ------------------------------------------------------------------ 第二階段 */
  var PHASE2 = [
    ["服務與價格", "各療程頁的價目表與服務說明改由後台維護（目前寫在 JSON，需重新建置）。"],
    ["Journal 文章", "文章新增、編輯、分類與封面圖；目前文章由設計師提供、由工程端加入。"],
    ["最新消息", "公告與活動上稿、置頂與到期自動下架。"],
    ["線上預約", "預約表單、時段容量與通知信；需搭配 Supabase Edge Function 或外部表單服務。"],
    ["顧客評價", "評價審核與顯示；官網目前維持設計過的空狀態，不放假評價。"],
    ["SEO 與頁面文案", "逐頁 title／description／OG 圖設定，取代目前的 config 檔。"]
  ];

  function viewPhase2(v) {
    v.innerHTML =
      '<div class="card"><h2>第二階段模組</h2><p class="hint">' +
        "第一階段已完成：總覽、設計師管理（含自動個人頁）、作品集管理（含自動同步）、媒體庫、登入權限。" +
        "以下模組尚未實作，因此沒有提供按鈕，避免誤按。<br>" +
        "這些內容目前寫在網站的 JSON 設定檔，需要修改時請聯絡維護人員重建官網。" +
      "</p></div>" +
      '<div class="card"><table class="list"><thead><tr><th>模組</th><th>說明</th><th>狀態</th></tr></thead><tbody>' +
        PHASE2.map(function (m) {
          return "<tr><td class=\"cell-title\">" + esc(m[0]) + "</td><td>" + esc(m[1]) +
            '</td><td><span class="pill p-hidden">第二階段</span></td></tr>';
        }).join("") +
      "</tbody></table></div>";
  }

  /* ------------------------------------------------------------------ 登入／啟動 */
  function showApp() {
    $("login").hidden = true;
    $("app").hidden = false;
    $("whoEmail").textContent = S.email || "—";
    $("whoMeta").textContent = "管理員";
    buildNav();
    var h = (location.hash || "").replace("#", "");
    setView(h || "dash", true);
  }

  function showLogin() {
    $("app").hidden = true;
    $("login").hidden = false;
    S.token = null; S.refresh = null;
    try { sessionStorage.removeItem(SESSION_KEY); } catch (e) {}
  }

  function loginErr(msg) {
    var n = $("loginErr");
    if (!msg) { n.hidden = true; n.textContent = ""; return; }
    n.hidden = false; n.textContent = msg;
  }

  async function doLogin(e) {
    if (e) e.preventDefault();
    loginErr("");
    var email = $("email").value.trim(), pw = $("password").value;
    if (!email || !pw) { loginErr("請填電子郵件與密碼"); return; }
    var btn = $("loginBtn");
    busy(btn, true, "登入中…");
    try {
      var r = await fetch(SB + "/auth/v1/token?grant_type=password", {
        method: "POST", headers: { apikey: KEY, "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, password: pw })
      });
      var j = await r.json().catch(function () { return {}; });
      if (!r.ok) throw new Error(r.status === 400 || r.status === 401 ? "電子郵件或密碼不正確" : "登入失敗（" + r.status + "）");
      applySession(j);
      $("password").value = "";
      await bootCheck(true);
    } catch (err) { loginErr(err.message); }
    finally { busy(btn, false); }
  }

  async function doForgot() {
    var email = $("email").value.trim();
    if (!email) { loginErr("請先在上方填入電子郵件，再按忘記密碼。"); return; }
    loginErr("");
    try {
      var r = await fetch(SB + "/auth/v1/recover", {
        method: "POST", headers: { apikey: KEY, "Content-Type": "application/json" },
        body: JSON.stringify({ email: email })
      });
      if (!r.ok) throw new Error("寄送失敗（" + r.status + "）");
      loginErr("已寄出重設密碼信，請收信並依連結設定新密碼。");
    } catch (e) { loginErr(e.message + "：請確認 Supabase 的寄信服務已設定。"); }
  }

  async function logout() {
    try {
      await fetch(SB + "/auth/v1/logout", { method: "POST", headers: authHeaders() });
    } catch (e) {}
    showLogin();
    toast("已登出", "ok");
  }

  async function bootCheck(afterLogin) {
    if (!configured()) { $("setupNote").hidden = false; $("loginBtn").disabled = true; return; }
    if (!S.token) { showLogin(); return; }
    var r = await fetch(SB + "/auth/v1/user", { headers: authHeaders() });
    if (r.status === 401 && S.refresh) { if (await refreshSession()) r = await fetch(SB + "/auth/v1/user", { headers: authHeaders() }); }
    if (!r.ok) { showLogin(); if (afterLogin) loginErr("登入成功但無法取得使用者資料，請確認金鑰是否正確。"); return; }
    var u = await r.json().catch(function () { return {}; });
    S.email = (u && u.email) || S.email;
    S.uid = (u && u.id) || S.uid;
    applySession({ access_token: S.token, refresh_token: S.refresh, user: { email: S.email, id: S.uid } });
    showApp();
  }

  function restore() {
    try {
      var raw = sessionStorage.getItem(SESSION_KEY);
      if (!raw) return false;
      var j = JSON.parse(raw);
      S.token = j.access_token || null; S.refresh = j.refresh_token || null;
      S.email = j.email || ""; S.uid = j.uid || null;
      return !!S.token;
    } catch (e) { return false; }
  }

  /* ------------------------------------------------------------------ 啟動 */
  function wire() {
    $("loginForm").addEventListener("submit", doLogin);
    $("forgotBtn").addEventListener("click", doForgot);
    $("logoutBtn").addEventListener("click", logout);
    $("burgerBtn").addEventListener("click", function () { $("side").classList.toggle("open"); });
    $("drawerBg").addEventListener("click", closeDrawer);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeDrawer(); });
    window.addEventListener("hashchange", function () {
      if ($("app").hidden) return;
      setView((location.hash || "").replace("#", "") || "dash", true);
    });
  }

  function start() {
    wire();
    if (!configured()) {
      $("setupNote").hidden = false;
      $("loginBtn").disabled = true;
      loginErr("");
      return;
    }
    if (restore()) bootCheck(false); else showLogin();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
