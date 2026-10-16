/* gx-datav 展示站 —— 组件网格 + 详情弹层。
   零依赖：读 docs/components.json（由 scripts/gen-site-data.py 从源码注释生成）。 */

(async function () {
  "use strict";

  const grid = document.getElementById("grid");
  const filters = document.getElementById("filters");
  const modal = document.getElementById("modal");
  const modalBody = modal.querySelector(".modal-body");

  let data;
  try {
    const res = await fetch("components.json");
    if (!res.ok) throw new Error(res.status + " " + res.statusText);
    data = await res.json();
  } catch (err) {
    grid.innerHTML =
      '<p style="color:var(--bad)">组件数据加载失败：' + err.message +
      '<br><br>本站用 <code>fetch()</code> 读 components.json —— 直接双击打开 ' +
      'index.html（file:// 协议）会被浏览器拦下。请起个本地服务：' +
      '<br><code>python3 -m http.server -d docs 8080</code></p>';
    return;
  }

  /* ── 分组筛选 ─────────────────────────────────────────── */
  let active = "全部";
  const groups = ["全部"].concat(data.groups);

  function renderFilters() {
    filters.innerHTML = "";
    for (const g of groups) {
      const b = document.createElement("button");
      b.textContent = g;
      b.className = g === active ? "on" : "";
      b.addEventListener("click", () => {
        active = g;
        renderFilters();
        renderGrid();
      });
      filters.appendChild(b);
    }
  }

  /* ── 组件卡片 ─────────────────────────────────────────── */
  function renderGrid() {
    const list = data.components.filter(
      (c) => active === "全部" || c.group === active
    );
    grid.innerHTML = "";
    for (const c of list) {
      const tile = document.createElement("button");
      tile.className = "tile";
      tile.type = "button";
      tile.innerHTML =
        '<div class="tile-shot"><img src="' + c.shot + '" alt="' +
        c.name + '" loading="lazy" onerror="this.style.opacity=.15"></div>' +
        '<div class="tile-meta">' +
          '<div class="name">' + c.name + "</div>" +
          '<div class="short">' + c.short + "</div>" +
          '<span class="group">' + c.group + "</span>" +
        "</div>";
      tile.addEventListener("click", () => openModal(c));
      grid.appendChild(tile);
    }
  }

  /* ── 详情弹层 ─────────────────────────────────────────── */
  function openModal(c) {
    let html = "<h3>" + c.name + "</h3>";
    html += '<p class="m-short">' + c.short + " · " + c.group + "</p>";
    html += '<img class="shot" src="' + c.shot + '" alt="' + c.name + '">';
    html += '<p class="m-desc">' + c.desc + "</p>";

    if (c.props && c.props.length) {
      html += "<table class='props'><thead><tr><th>prop</th><th>说明</th></tr></thead><tbody>";
      for (const p of c.props) {
        html += "<tr><td>" + esc(p.name) + "</td><td>" + inlineCode(p.desc) + "</td></tr>";
      }
      html += "</tbody></table>";
      if (c.propsSource === "readme") {
        html += '<p class="src-note">※ 该组件的 props 表来自 README（源码注释里没有 ' +
                "props 段），已与实现逐项核对。</p>";
      }
    } else {
      html += '<p class="src-note">未解析到 props 说明，请查阅源码或 README。</p>';
    }

    modalBody.innerHTML = html;
    modal.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = "";
  }

  modal.querySelector(".modal-close").addEventListener("click", closeModal);
  modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !modal.hidden) closeModal(); });

  /* ── 复制按钮 ─────────────────────────────────────────── */
  for (const btn of document.querySelectorAll(".copy")) {
    btn.addEventListener("click", async () => {
      const text = btn.dataset.copy;
      try {
        await navigator.clipboard.writeText(text);
      } catch {
        // 剪贴板 API 在非 https / 老浏览器下会拒，退化成选中文本
        const el = btn.previousElementSibling;
        const r = document.createRange();
        r.selectNodeContents(el);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(r);
      }
      btn.textContent = "已复制";
      btn.classList.add("done");
      setTimeout(() => { btn.textContent = "复制"; btn.classList.remove("done"); }, 1400);
    });
  }

  /* ── 小工具 ───────────────────────────────────────────── */
  function esc(s) {
    return String(s).replace(/[&<>"]/g, (m) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m]));
  }
  // props 说明里的字段名/默认值用 <code> 点出来，读起来更清楚。
  // 注意**先转义再插标签**：先 esc 拿到纯文本，再对安全模式替换。
  function inlineCode(s) {
    return esc(s).replace(/(缺省\s*[\w."\/-]+|"[^"]*"|\[[\d,\s]+\])/g,
      (m) => "<code>" + m + "</code>");
  }

  renderFilters();
  renderGrid();
})();
