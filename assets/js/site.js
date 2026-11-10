/* HD Hope Hair Salon — 前端互動
   無第三方追蹤、無外部請求；所有狀態僅存在於瀏覽器。 */
(function () {
  "use strict";

  var doc = document;
  var root = doc.documentElement;
  root.classList.remove("no-js");

  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------------------------------------------------- 選單 drawer */
  var drawer = doc.getElementById("drawer");
  var lastFocus = null;

  function openDrawer(trigger) {
    if (!drawer) return;
    lastFocus = trigger || doc.activeElement;
    if (typeof drawer.showModal === "function") {
      try { drawer.showModal(); } catch (e) { drawer.setAttribute("open", "open"); }
    } else {
      drawer.setAttribute("open", "open");
    }
    drawer.classList.add("is-open");
    doc.body.style.overflow = "hidden";
    var first = drawer.querySelector(".drawer__close");
    if (first) first.focus({ preventScroll: true });
  }

  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove("is-open");
    if (typeof drawer.close === "function" && drawer.open) {
      drawer.close();
    } else {
      drawer.removeAttribute("open");
    }
    doc.body.style.overflow = "";
    if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
    lastFocus = null;
  }

  doc.addEventListener("click", function (e) {
    var open = e.target.closest("[data-drawer-open]");
    if (open) {
      e.preventDefault();
      openDrawer(open);
      open.setAttribute("aria-expanded", "true");
      return;
    }
    var close = e.target.closest("[data-drawer-close]");
    if (close) {
      e.preventDefault();
      var trigger = doc.querySelector("[data-drawer-open]");
      if (trigger) trigger.setAttribute("aria-expanded", "false");
      closeDrawer();
    }
  });

  doc.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && drawer && drawer.open) {
      closeDrawer();
    }
  });

  /* ---------------------------------------------------------- 作品篩選 */
  doc.querySelectorAll("[data-filter-scope]").forEach(function (scope) {
    var group = scope.querySelector("[data-filter-group]");
    var items = scope.querySelectorAll("[data-filter-item]");
    var counter = scope.querySelector("[data-filter-count]");
    if (!group) return;
    var chips = group.querySelectorAll("[data-filter]");
    var tpl = counter ? (counter.getAttribute("data-template") || "{n}") : "";

    function apply(cat) {
      var shown = 0;
      items.forEach(function (el) {
        var ok = cat === "all" || el.getAttribute("data-cat") === cat;
        if (ok) { el.removeAttribute("hidden"); shown++; }
        else { el.setAttribute("hidden", "hidden"); }
      });
      chips.forEach(function (c) {
        var on = c.getAttribute("data-filter") === cat;
        c.setAttribute("aria-pressed", on ? "true" : "false");
      });
      if (counter) counter.textContent = tpl.replace("{n}", String(shown));
    }

    group.addEventListener("click", function (e) {
      var chip = e.target.closest("[data-filter]");
      if (!chip || !group.contains(chip)) return;
      apply(chip.getAttribute("data-filter"));
    });

    apply("all");
  });

  /* ---------------------------------------------------------- 預約訊息產生 */
  var form = doc.querySelector("[data-booking]");
  if (form) {
    var errBox = doc.querySelector("[data-booking-error]");
    var outBox = doc.querySelector("[data-booking-output]");
    var outText = doc.querySelector("[data-booking-text]");
    var copyBtn = doc.querySelector("[data-booking-copy]");

    var REQUIRED = ["name", "service", "time"];

    function field(name) {
      return form.querySelector('[name="' + name + '"]');
    }

    function setError(name, on) {
      var input = field(name);
      if (!input) return;
      var wrap = input.closest(".field");
      if (!wrap) return;
      if (on) wrap.classList.add("field--invalid");
      else wrap.classList.remove("field--invalid");
      input.setAttribute("aria-invalid", on ? "true" : "false");
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var bad = [];
      REQUIRED.forEach(function (n) {
        var input = field(n);
        var empty = !input || !String(input.value || "").trim();
        setError(n, empty);
        if (empty) bad.push(n);
      });
      if (bad.length) {
        if (errBox) errBox.removeAttribute("hidden");
        var firstBad = field(bad[0]);
        if (firstBad) firstBad.focus({ preventScroll: false });
        if (outBox) outBox.setAttribute("hidden", "hidden");
        return;
      }
      if (errBox) errBox.setAttribute("hidden", "hidden");

      var data = {
        name: field("name").value.trim(),
        phone: (field("phone") || {}).value ? field("phone").value.trim() : "",
        service: field("service").value,
        stylist: (field("stylist") || {}).value ? field("stylist").value.trim() : "",
        time: field("time").value.trim(),
        note: (field("note") || {}).value ? field("note").value.trim() : ""
      };

      var lines = [
        "你好，我想預約 HD Hope Hair Salon。",
        "姓名：" + data.name,
        "想做的服務：" + data.service
      ];
      if (data.stylist) lines.push("指定設計師：" + data.stylist);
      lines.push("希望時段：" + data.time);
      if (data.phone) lines.push("聯絡電話：" + data.phone);
      if (data.note) lines.push("其他需求：" + data.note);
      lines.push("（此訊息由網頁產生，請複製後貼到官方 LINE 送出。）");

      if (outText) outText.textContent = lines.join("\n");
      if (outBox) outBox.removeAttribute("hidden");
      if (copyBtn) copyBtn.focus({ preventScroll: true });
    });

    form.addEventListener("input", function (e) {
      var t = e.target;
      if (t && t.name) setError(t.name, false);
    });

    if (copyBtn) {
      copyBtn.addEventListener("click", function () {
        var text = outText ? outText.textContent : "";
        var done = function () {
          copyBtn.textContent = "已複製";
          window.setTimeout(function () { copyBtn.textContent = "複製訊息"; }, 2000);
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done, function () { fallback(text, done); });
        } else {
          fallback(text, done);
        }
      });
    }

    function fallback(text, done) {
      var ta = doc.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      doc.body.appendChild(ta);
      ta.select();
      try { doc.execCommand("copy"); } catch (e) {}
      doc.body.removeChild(ta);
      done();
    }
  }

  /* ---------------------------------------------------------- 曝光追蹤（僅本機） */
  doc.addEventListener("click", function (e) {
    var el = e.target.closest("[data-track]");
    if (!el) return;
    var payload = {
      event: "cta_click",
      cta: el.getAttribute("data-track"),
      label: el.getAttribute("data-track-label") || "",
      path: window.location.pathname
    };
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(payload);
  });

  /* ---------------------------------------------------------- 進場動畫 */
  var reveals = doc.querySelectorAll(".reveal");
  if (reduce || !("IntersectionObserver" in window)) {
    reveals.forEach(function (el) { el.classList.add("is-in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add("is-in");
          io.unobserve(en.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });
    reveals.forEach(function (el) { io.observe(el); });
  }
})();
