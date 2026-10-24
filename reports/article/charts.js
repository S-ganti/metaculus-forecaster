(function () {
  "use strict";
  const D = window.ARTICLE_DATA;
  const NS = "http://www.w3.org/2000/svg";
  const START = new Date(Date.UTC(2026, 9, 16));
  const pct = (v, d = 0) => (v * 100).toFixed(d) + "%";
  const pctS = (v) => (v < 0.01 && v > 0 ? (v * 100).toFixed(1) : (v * 100).toFixed(v < 0.1 ? 1 : 0)) + "%";
  const logit = (p) => Math.log(p / (1 - p));
  const expit = (x) => 1 / (1 + Math.exp(-x));
  const cal = (m) => {
    const d = new Date(START.getTime() + m * 30.44 * 86400000);
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
  };

  function el(tag, attrs, parent, text) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs || {}) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  }
  const lin = (d0, d1, r0, r1) => (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);

  // ---- tooltip: one per figure body, positioned inside it
  function tipFor(host) {
    let t = host.querySelector(".tip");
    if (!t) { t = document.createElement("div"); t.className = "tip"; t.hidden = true; host.appendChild(t); }
    return {
      show(html, clientX, clientY) {
        const r = host.getBoundingClientRect();
        t.innerHTML = html; t.hidden = false;
        let x = clientX - r.left + host.scrollLeft;
        const half = t.offsetWidth / 2 + 4;
        x = Math.max(half, Math.min(host.scrollWidth - half, x));
        t.style.left = x + "px";
        t.style.top = Math.max(t.offsetHeight + 6, clientY - r.top) + "px";
      },
      hide() { t.hidden = true; },
    };
  }
  function svgPoint(svg, evt) {
    const p = svg.createSVGPoint(); p.x = evt.clientX; p.y = evt.clientY;
    return p.matrixTransform(svg.getScreenCTM().inverse());
  }

  // ---- generic line chart
  function lineChart(host, c) {
    const W = c.W || 720, H = c.H || 320;
    const m = Object.assign({ t: 18, r: 110, b: 46, l: 56 }, c.m || {});
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": c.aria || "" }, host);
    if (c.narrow) svg.style.minWidth = "0";
    const sx = lin(c.xd[0], c.xd[1], m.l, W - m.r), sy = lin(c.yd[0], c.yd[1], H - m.b, m.t);
    const g = el("g", {}, svg);
    (c.bands || []).forEach((b) => el("rect", { x: sx(b.x0 ?? c.xd[0]), width: sx(b.x1 ?? c.xd[1]) - sx(b.x0 ?? c.xd[0]),
      y: sy(b.y1), height: sy(b.y0) - sy(b.y1), class: b.cls, style: b.style || "" }, g));
    const grid = el("g", { class: "grid" }, g), ax = el("g", { class: "ax" }, g);
    c.yTicks.forEach((v) => {
      el("line", { x1: m.l, x2: W - m.r, y1: sy(v), y2: sy(v) }, grid);
      el("text", { x: m.l - 8, y: sy(v) + 4, "text-anchor": "end" }, ax, (c.yFmt || String)(v));
    });
    el("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b }, ax);
    c.xTicks.forEach((v) => {
      el("line", { x1: sx(v), x2: sx(v), y1: H - m.b, y2: H - m.b + 5 }, ax);
      el("text", { x: sx(v), y: H - m.b + 18, "text-anchor": "middle" }, ax, (c.xFmt || String)(v));
    });
    if (c.xTitle) el("text", { class: "axtitle", x: m.l, y: H - 6 }, g, c.xTitle);
    if (c.yTitle) el("text", { class: "axtitle", x: m.l, y: m.t - 6 }, g, c.yTitle);
    (c.hlines || []).forEach((h) => {
      el("line", { x1: m.l, x2: W - m.r, y1: sy(h.y), y2: sy(h.y), class: h.cls }, g);
      if (h.label) el("text", { class: "lbl", x: W - m.r + 6, y: sy(h.y) + 4 }, g, h.label);
    });
    (c.vlines || []).forEach((v, i) => {
      el("line", { x1: sx(v.x), x2: sx(v.x), y1: m.t, y2: H - m.b, class: "vmark" }, g);
      el("text", { class: "vmark-t", x: sx(v.x) + 4, y: m.t + 10 + (v.row || 0) * 13 }, g, v.label);
    });
    const lines = el("g", {}, svg);
    c.series.forEach((s) => {
      const pts = c.x.map((xv, i) => (s.y[i] == null ? null : `${sx(xv).toFixed(1)},${sy(s.y[i]).toFixed(1)}`)).filter(Boolean);
      el("polyline", { points: pts.join(" "), class: `ln ${s.cls}`, style: s.style || "",
        "stroke-dasharray": s.dash || "", "stroke-width": s.w || 2 }, lines);
    });
    // direct end labels with simple collision avoidance
    const ends = c.series.filter((s) => s.end).map((s) => ({ s, y: sy(s.y[s.y.length - 1]) }))
      .sort((a, b) => a.y - b.y);
    for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 13) ends[i].y = ends[i - 1].y + 13;
    ends.forEach((e) => el("text", { class: "endlbl", x: W - m.r + 6, y: e.y + 4 }, svg, e.s.end));
    (c.marks || []).forEach((k) => {
      el("circle", { cx: sx(k.x), cy: sy(k.y), r: 4.5, class: k.cls || "facc" }, svg);
      if (k.label) el("text", { class: "endlbl", x: sx(k.x) + (k.dx ?? 8), y: sy(k.y) + (k.dy ?? -8),
        "text-anchor": k.anchor || "start" }, svg, k.label);
    });
    // hover layer
    if (c.tip !== false) {
      const tip = tipFor(host.closest(".fig-body") || host);
      const cross = el("line", { y1: m.t, y2: H - m.b, class: "cross", visibility: "hidden" }, svg);
      const hit = el("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, class: "hit" }, svg);
      const move = (evt) => {
        const p = svgPoint(svg, evt);
        let i = 0, best = Infinity;
        c.x.forEach((xv, k) => { const dd = Math.abs(sx(xv) - p.x); if (dd < best) { best = dd; i = k; } });
        cross.setAttribute("x1", sx(c.x[i])); cross.setAttribute("x2", sx(c.x[i]));
        cross.setAttribute("visibility", "visible");
        tip.show(c.tipHtml(i), evt.clientX, evt.clientY);
      };
      hit.addEventListener("pointermove", move);
      hit.addEventListener("pointerdown", move);
      hit.addEventListener("pointerleave", () => { cross.setAttribute("visibility", "hidden"); tip.hide(); });
    }
    return { svg, sx, sy, m, W, H };
  }
  const sw = (v) => `<i style="background:var(${v})"></i>`;

  // =================================================================== Fig 3 influence
  (function () {
    const h = D.h_curve;
    lineChart(document.getElementById("fig-h"), {
      aria: "Influence function: zero inside the dead-band, rising and saturating outside it.",
      H: 300, x: h.d, xd: [-0.4, 0.4], yd: [-1, 1],
      xTicks: [-0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4], yTicks: [-1, -0.5, 0, 0.5, 1],
      xFmt: (v) => (v > 0 ? "+" : "") + v.toFixed(1), yFmt: (v) => (v > 0 ? "+" : "") + v,
      xTitle: "distance from normal, d", yTitle: "influence passed on",
      bands: [{ x0: -h.deadband, x1: h.deadband, y0: -1, y1: 1, cls: "", style: "fill:var(--panel)" }],
      hlines: [{ y: 0, cls: "zero", label: "dead-band ±0.05" }],
      series: [{ y: h.sharp2, cls: "c1", end: "sharp 2" }, { y: h.sharp4, cls: "c2", end: "sharp 4" }],
      tipHtml: (i) => `d = ${h.d[i].toFixed(2)}<br>${sw("--s1")}sharp 2: ${h.sharp2[i].toFixed(3)}<br>${sw("--s2")}sharp 4: ${h.sharp4[i].toFixed(3)}`,
    });
  })();

  // =================================================================== Fig 4 order of breakage
  (function () {
    const a = D.all_shocks;
    const nodes = ["security", "access", "food", "purchasing", "nutrition", "survival"];
    const vars = ["--s1", "--s2", "--s3", "--s4", "--s5", "--s6"];
    document.getElementById("lg-order").innerHTML = nodes.map((n, i) => `<span>${sw(vars[i])}${n}</span>`).join("")
      + `<span><i style="background:var(--ipc5);opacity:.4"></i>below famine line</span>`;
    lineChart(document.getElementById("fig-order"), {
      aria: "Six domains falling over six months after all shocks hit; survival is the last to cross the famine line.",
      H: 330, m: { r: 24 }, x: a.t, xd: [0, 6], yd: [0, 0.3],
      xTicks: [0, 1, 2, 3, 4, 5, 6], yTicks: [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3],
      xFmt: (v) => v + " mo", yFmt: (v) => v.toFixed(2),
      xTitle: "months after 16 October 2026", yTitle: "domain health x",
      bands: [{ y0: 0, y1: 0.15, cls: "famine-band" }],
      hlines: [{ y: 0.15, cls: "famine-line" }],
      vlines: [{ x: 1.5, label: "1 Dec" }, { x: 2.5, label: "1 Jan" }, { x: D.famine_time_all, label: "famine conditions", row: 1 }],
      series: nodes.map((n, i) => ({ y: a[n], cls: "c" + (i + 1) })),
      tipHtml: (i) => `<b>${a.t[i].toFixed(1)} mo · ${cal(a.t[i])}</b><br>` + nodes.map((n, k) => `${sw(vars[k])}${n} ${a[n][i].toFixed(3)}`).join("<br>"),
    });
    const tb = document.querySelector("#tbl-order tbody");
    nodes.map((n) => [n, D.order_all[n]]).sort((p, q) => (p[1] ?? 99) - (q[1] ?? 99)).forEach(([n, t]) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${n}</td><td class="num">${t === 0 ? "already below" : t == null ? "does not cross" : t.toFixed(2)}</td>
        <td>${t === 0 ? "wasting is past the threshold today" : t == null ? "" : cal(t)}</td>`;
      tb.appendChild(tr);
    });
  })();

  // =================================================================== Fig 5 loops table
  (function () {
    const tb = document.querySelector("#tbl-loops tbody");
    D.loops.forEach((L) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${L.nodes.concat(L.nodes[0]).join(" → ")}</td><td>${L.kind}</td>
        <td class="num">${L.gain.toFixed(2)}</td><td class="num">${L.lag.toFixed(2)}</td>`;
      tb.appendChild(tr);
    });
  })();

  // =================================================================== Fig 6 set point
  (function () {
    const s = D.setpoint, last = s.x.length - 1;
    lineChart(document.getElementById("fig-setpoint"), {
      aria: "A camp's set point drifts from 0.5 down to about 0.38 over two years and the state follows it.",
      H: 290, x: s.t, xd: [0, 24], yd: [0.25, 0.55],
      xTicks: [0, 4, 8, 12, 16, 20, 24], yTicks: [0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55],
      xFmt: (v) => v + " mo", yFmt: (v) => v.toFixed(2),
      xTitle: "months", yTitle: "camp level",
      hlines: [{ y: 0.5, cls: "zero", label: "old normal 0.50" }, { y: 0.3, cls: "vmark", label: "neighbours 0.30" }],
      series: [{ y: s.x, cls: "c1", end: `settles ${s.x[last].toFixed(2)}` }, { y: s.s, cls: "c2", dash: "6 4" }],
      tipHtml: (i) => `<b>month ${s.t[i]}</b><br>${sw("--s1")}state ${s.x[i].toFixed(3)}<br>${sw("--s2")}set point ${s.s[i].toFixed(3)}`,
    });
  })();

  // =================================================================== Fig 7 kick vs driver
  (function () {
    const host = document.getElementById("fig-kick");
    host.style.display = "grid";
    host.style.gridTemplateColumns = "repeat(auto-fit, minmax(17rem, 1fr))";
    host.style.gap = "1rem";
    [["kick", "One-off kick to food"], ["driver", "Driver node keeps pushing"]].forEach(([k, title]) => {
      const box = document.createElement("div");
      box.style.minWidth = "0";
      const h = document.createElement("div"); h.className = "label"; h.textContent = title; h.style.marginBottom = "0.3rem";
      box.appendChild(h); host.appendChild(box);
      const d = D.kick_vs_driver[k];
      lineChart(box, {
        narrow: true, W: 380, H: 270, m: { r: 70, l: 46 }, x: d.t, xd: [0, 6], yd: [0, 0.3],
        xTicks: [0, 2, 4, 6], yTicks: [0, 0.1, 0.2, 0.3], xFmt: (v) => v + " mo", yFmt: (v) => v.toFixed(1),
        bands: [{ y0: 0, y1: 0.15, cls: "famine-band" }], hlines: [{ y: 0.15, cls: "famine-line" }],
        series: [{ y: d.food, cls: "c1", end: "food" }, { y: d.survival, cls: "c3", end: "survival" }],
        tipHtml: (i) => `<b>${d.t[i].toFixed(1)} mo</b><br>${sw("--s1")}food ${d.food[i].toFixed(3)}<br>${sw("--s3")}survival ${d.survival[i].toFixed(3)}`,
      });
    });
    host.closest(".fig-body").style.overflowX = "visible";
  })();

  // =================================================================== Fig 9 fan
  (function () {
    const f = D.fan, n = f.runs.length;
    const famineRuns = f.runs.filter((r) => r.famine != null).length;
    const chart = lineChart(document.getElementById("fig-fan"), {
      aria: `Survival paths for ${n} simulated runs; many fall below the famine line, almost none before December.`,
      H: 340, m: { r: 24 }, x: f.t, xd: [0, 6], yd: [0, 0.3],
      xTicks: [0, 1, 2, 3, 4, 5, 6], yTicks: [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3],
      xFmt: (v) => v + " mo", yFmt: (v) => v.toFixed(2),
      xTitle: "months after 16 October 2026", yTitle: "survival (death-rate health)",
      bands: [{ y0: 0, y1: 0.15, cls: "famine-band" }], hlines: [{ y: 0.15, cls: "famine-line" }],
      vlines: [{ x: 1.5, label: "1 Dec" }, { x: 2.5, label: "1 Jan" }],
      series: f.runs.map((r) => ({ y: r.survival, cls: r.famine != null ? "cacc" : "cink",
        style: `opacity:${r.famine != null ? 0.55 : 0.28}`, w: 1.2 })),
      tipHtml: (i) => {
        const below = f.runs.filter((r) => r.survival[i] <= 0.15).length;
        const fam = f.runs.filter((r) => r.famine != null && r.famine <= f.t[i] + 1e-9).length;
        return `<b>${f.t[i].toFixed(1)} mo · ${cal(f.t[i])}</b><br>survival below line: ${below} of ${n}<br>`
          + `famine conditions reached: ${fam} of ${n}`;
      },
    });
    el("text", { class: "endlbl", x: chart.W - 30, y: chart.sy(0.285), "text-anchor": "end" }, chart.svg,
      `${famineRuns} of ${n} runs reach famine conditions within 6 months`);
  })();

  // =================================================================== Fig 11 horizon
  (function () {
    const H = D.horizon, g = H.grid;
    const at = (arr, m) => arr[g.findIndex((v) => Math.abs(v - m) < 1e-6)];
    const S = [
      { k: "all", label: "all runs", short: "all runs", cls: "cink", v: "--ink", w: 3 },
      { k: "displacement_only", label: "displacement surge only", short: "surge", cls: "c1", v: "--s1" },
      { k: "conflict_only", label: "siege only", short: "siege", cls: "c2", v: "--s2" },
      { k: "none", label: "no new shock", short: "no shock", cls: "c3", v: "--s3" },
      { k: "two_plus", label: "two or more shocks", short: "2+ shocks", cls: "c4", v: "--s4" },
    ];
    document.getElementById("lg-horizon").innerHTML = S.map((s) =>
      `<span><i style="background:var(${s.v});${s.w ? "height:4px" : ""}"></i>${s.label} (n=${H[s.k].n})</span>`).join("");
    lineChart(document.getElementById("fig-horizon"), {
      aria: "Cumulative probability of famine conditions by month: near zero until late December, rising to about 60% by April.",
      H: 340, m: { r: 108 }, x: g, xd: [0, 6], yd: [0, 1],
      xTicks: [0, 1, 2, 3, 4, 5, 6], yTicks: [0, 0.2, 0.4, 0.6, 0.8, 1],
      xFmt: (v) => v + " mo", yFmt: (v) => pct(v),
      xTitle: "months after 16 October 2026", yTitle: "share of runs with famine conditions",
      bands: [{ x0: 0, x1: 1.5, y0: 0, y1: 1, cls: "", style: "fill:var(--panel)" }],
      vlines: [{ x: 1.5, label: "1 Dec" }, { x: 2.5, label: "1 Jan" }],
      series: S.map((s) => ({ y: H[s.k].p, cls: s.cls, w: s.w, end: `${s.short} ${pct(H[s.k].p[H[s.k].p.length - 1])}` })),
      tipHtml: (i) => `<b>${g[i]} mo · ${cal(g[i])}</b><br>` + S.map((s) => `${sw(s.v)}${s.label}: ${pctS(H[s.k].p[i])}`).join("<br>"),
    });
    const tiles = [["By 1 December", 1.5, "the real deadline"], ["By 1 January", 2.5, "question closes"],
      ["By mid-January", 3.0, "after it closes"], ["By March", 4.5, "lean season"]];
    document.getElementById("verdict-horizon").innerHTML = tiles.map(([t, mo, sub], i) =>
      `<div class="${i === 0 ? "main" : ""}"><span class="label">${t}</span><b>${pctS(at(H.all.p, mo))}</b><small>${sub}</small></div>`).join("");
  })();

  // =================================================================== Fig 12 lag sensitivity
  (function () {
    const host = document.getElementById("fig-lag");
    const L = D.lag_sensitivity, W = 720, Hh = 290, m = { t: 22, r: 20, b: 50, l: 56 };
    const svg = el("svg", { viewBox: `0 0 ${W} ${Hh}`, role: "img",
      "aria-label": "Bar chart: probability by 1 December stays under 1% for every lag setting; by mid-January it ranges from 4% to 38%." }, host);
    const yMax = 0.4, sy = lin(0, yMax, Hh - m.b, m.t);
    const grid = el("g", { class: "grid" }, svg), ax = el("g", { class: "ax" }, svg);
    [0, 0.1, 0.2, 0.3, 0.4].forEach((v) => {
      el("line", { x1: m.l, x2: W - m.r, y1: sy(v), y2: sy(v) }, grid);
      el("text", { x: m.l - 8, y: sy(v) + 4, "text-anchor": "end" }, ax, pct(v));
    });
    el("line", { x1: m.l, x2: W - m.r, y1: sy(0), y2: sy(0) }, ax);
    el("text", { class: "axtitle", x: m.l, y: m.t - 8 }, svg, "P(famine conditions)");
    const gw = (W - m.l - m.r) / L.length, bw = 34;
    const tip = tipFor(host);
    L.forEach((r, i) => {
      const cx = m.l + gw * (i + 0.5);
      el("text", { class: "lbl", x: cx, y: Hh - m.b + 18, "text-anchor": "middle" }, svg,
        `lags ×${r.scale}${r.scale === 1 ? " (used)" : ""}`);
      [["p15", "f1", "by 1 Dec", "--s1"], ["p30", "f2", "by mid-Jan", "--s2"]].forEach(([k, cls, name, v], j) => {
        const x = cx + (j === 0 ? -bw - 1 : 1), y = sy(r[k]), hgt = Math.max(sy(0) - y, 1.5);
        const rect = el("rect", { x, y: sy(0) - hgt, width: bw, height: hgt, class: cls, rx: 2 }, svg);
        el("text", { class: "lbl", x: x + bw / 2, y: sy(0) - hgt - 5, "text-anchor": "middle" }, svg, pctS(r[k]));
        const hit = el("rect", { x: x - 2, y: m.t, width: bw + 4, height: sy(0) - m.t, class: "hit" }, svg);
        const show = (e) => { rect.style.opacity = 0.75; tip.show(`${sw(v)}${name}, lags ×${r.scale}<br><b>${pctS(r[k])}</b> of 600 runs`, e.clientX, e.clientY); };
        hit.addEventListener("pointermove", show); hit.addEventListener("pointerdown", show);
        hit.addEventListener("pointerleave", () => { rect.style.opacity = 1; tip.hide(); });
      });
    });
  })();

  // =================================================================== Fig 13 ledger waterfall
  (function () {
    const host = document.getElementById("fig-ledger");
    const Lg = D.ledger, items = Lg.items;
    const rows = [{ kind: "start", label: "Base rate (3 of 12 quarters)", from: logit(Lg.prior), to: logit(Lg.prior) }];
    let cum = logit(Lg.prior);
    items.forEach((it) => { rows.push({ kind: it.shift >= 0 ? "yes" : "no", label: it.what, it, from: cum, to: cum + it.shift }); cum += it.shift; });
    rows.push({ kind: "end", label: "Inside view", from: cum, to: cum });
    const W = 760, rh = 34, m = { t: 30, r: 70, b: 40, l: 300 }, Hh = m.t + rows.length * rh + m.b;
    const svg = el("svg", { viewBox: `0 0 ${W} ${Hh}`, role: "img",
      "aria-label": `Evidence waterfall from a ${pct(Lg.prior, 1)} base rate to a ${pct(Lg.posterior, 1)} inside view.` }, host);
    const vals = rows.flatMap((r) => [r.from, r.to]);
    const lo = Math.min(...vals) - 0.25, hi = Math.max(...vals) + 0.25;
    const sx = lin(lo, hi, m.l, W - m.r);
    const grid = el("g", { class: "grid" }, svg), ax = el("g", { class: "ax" }, svg);
    [0.08, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4].filter((p) => logit(p) > lo && logit(p) < hi).forEach((p) => {
      el("line", { x1: sx(logit(p)), x2: sx(logit(p)), y1: m.t - 6, y2: Hh - m.b }, grid);
      el("text", { x: sx(logit(p)), y: Hh - m.b + 18, "text-anchor": "middle" }, ax, pct(p));
    });
    el("text", { class: "axtitle", x: m.l, y: Hh - 6 }, svg, "probability (log-odds scale)");
    const tip = tipFor(host);
    rows.forEach((r, i) => {
      const y = m.t + i * rh, cy = y + rh / 2;
      const short = r.label.length > 42 ? r.label.slice(0, 40) + "…" : r.label;
      el("text", { class: "lbl", x: m.l - 10, y: cy + 4, "text-anchor": "end",
        style: r.kind === "start" || r.kind === "end" ? "fill:var(--ink);font-weight:500" : "" }, svg, short);
      if (r.kind === "start" || r.kind === "end") {
        el("circle", { cx: sx(r.to), cy, r: 6, class: "fink" }, svg);
        el("text", { class: "endlbl", x: sx(r.to) + 11, y: cy + 4 }, svg, pct(expit(r.to), 1));
      } else {
        const x0 = Math.min(r.from, r.to), x1 = Math.max(r.from, r.to);
        const rect = el("rect", { x: sx(x0), y: cy - 9, width: Math.max(sx(x1) - sx(x0), 2), height: 18, rx: 2,
          class: r.kind === "yes" ? "fyes" : "fno" }, svg);
        el("text", { class: "lbl", x: (r.kind === "yes" ? sx(x1) + 5 : sx(x0) - 5), y: cy + 4,
          "text-anchor": r.kind === "yes" ? "start" : "end" }, svg, `×${r.it.lr.toFixed(2)}`);
        const hit = el("rect", { x: 0, y, width: W, height: rh, class: "hit" }, svg);
        const show = (e) => { rect.style.opacity = 0.75; tip.show(`<b>${r.it.what}</b><br>${r.it.source} · ${r.it.date}<br>LR ${r.it.lr.toFixed(2)} × reliability ${r.it.rel} → ${pct(expit(r.from), 1)} to ${pct(expit(r.to), 1)}`, e.clientX, e.clientY); };
        hit.addEventListener("pointermove", show); hit.addEventListener("pointerdown", show);
        hit.addEventListener("pointerleave", () => { rect.style.opacity = 1; tip.hide(); });
      }
      if (i < rows.length - 1) el("line", { x1: sx(r.to), x2: sx(r.to), y1: cy + 9, y2: cy + rh - 9, class: "cross",
        "stroke-dasharray": "2 2" }, svg);
    });
    const tb = document.querySelector("#tbl-ledger tbody");
    items.forEach((it) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${it.what}</td><td>${it.source}, ${it.date}</td><td class="num">${it.lr.toFixed(2)} ${it.lr > 1 ? "↑" : "↓"}</td><td class="num">${it.rel.toFixed(1)}</td>`;
      tb.appendChild(tr);
    });
    const s = D.sentiment;
    document.getElementById("sent-line").textContent =
      `On 16 October the scorer read ${s.n} news headlines and Reddit posts: ${s.stance.yes} leaned YES, ${s.stance.no} leaned NO, average tone ${s.polarity.toFixed(2)} (strongly negative, as you would expect for this subject and uninformative for the question).`;
  })();

  // =================================================================== Fig 14 fusion
  (function () {
    const F = D.fusion;
    const rows = [
      { label: "Base rate", sub: "3 of 12 quarters since the war began", p: D.ledger.prior, cls: "fink3" },
      { label: "Inside view", sub: "base rate + evidence ledger", p: F.inside, cls: "fink", w: F.w_inside },
      { label: "Metaculus community", sub: `${F.n_forecasters} forecasters`, p: F.community, cls: "f2", w: F.w_comm },
      { label: "Forecast, slope 1.0", sub: "fused, no extra shrink", p: F.slope10.p, lo: F.slope10.lo, hi: F.slope10.hi, cls: "f1" },
      { label: "Forecast, pre-registered", sub: "fused, slope 0.9", p: F.slope09.p, lo: F.slope09.lo, hi: F.slope09.hi, cls: "facc", bold: true },
    ];
    const host = document.getElementById("fig-fusion");
    const W = 720, rh = 46, m = { t: 14, r: 30, b: 40, l: 210 }, Hh = m.t + rows.length * rh + m.b;
    const svg = el("svg", { viewBox: `0 0 ${W} ${Hh}`, role: "img",
      "aria-label": `Dot plot: base rate ${pct(rows[0].p)}, inside view ${pct(F.inside)}, community ${pct(F.community)}, forecast ${pct(F.slope09.p, 1)}.` }, host);
    const sx = lin(0, 0.5, m.l, W - m.r);
    const grid = el("g", { class: "grid" }, svg), ax = el("g", { class: "ax" }, svg);
    [0, 0.1, 0.2, 0.3, 0.4, 0.5].forEach((v) => {
      el("line", { x1: sx(v), x2: sx(v), y1: m.t, y2: Hh - m.b }, grid);
      el("text", { x: sx(v), y: Hh - m.b + 18, "text-anchor": "middle" }, ax, pct(v));
    });
    el("text", { class: "axtitle", x: m.l, y: Hh - 6 }, svg, "probability of YES");
    const tip = tipFor(host);
    rows.forEach((r, i) => {
      const cy = m.t + i * rh + rh / 2;
      el("text", { class: "lbl", x: m.l - 12, y: cy - 2, "text-anchor": "end",
        style: `fill:var(--ink);${r.bold ? "font-weight:600" : ""}` }, svg, r.label);
      el("text", { class: "lbl", x: m.l - 12, y: cy + 12, "text-anchor": "end", style: "font-size:10px" }, svg, r.sub);
      if (r.lo != null) {
        el("line", { x1: sx(r.lo), x2: sx(r.hi), y1: cy, y2: cy, class: "cross", "stroke-width": 2 }, svg);
        [r.lo, r.hi].forEach((v) => el("line", { x1: sx(v), x2: sx(v), y1: cy - 5, y2: cy + 5, class: "cross", "stroke-width": 2 }, svg));
      }
      el("circle", { cx: sx(r.p), cy, r: r.bold ? 8 : 6.5, class: r.cls, stroke: "var(--sheet)", "stroke-width": 2 }, svg);
      el("text", { class: "endlbl", x: sx(r.lo != null ? r.hi : r.p) + 12, y: cy + 4,
        style: r.bold ? "font-weight:600" : "" }, svg, pct(r.p, 1) + (r.w ? ` · weight ${r.w}` : ""));
      const hit = el("rect", { x: 0, y: cy - rh / 2, width: W, height: rh, class: "hit" }, svg);
      const show = (e) => tip.show(`<b>${r.label}</b><br>${pct(r.p, 1)}${r.lo != null ? `<br>90% interval ${pct(r.lo)}–${pct(r.hi)}` : ""}${r.w ? `<br>fusion weight ${r.w}` : ""}`, e.clientX, e.clientY);
      hit.addEventListener("pointermove", show); hit.addEventListener("pointerdown", show);
      hit.addEventListener("pointerleave", () => tip.hide());
    });
    document.getElementById("verdict-final").innerHTML =
      `<div class="main"><span class="label">Forecast · pre-registered</span><b>${pct(F.slope09.p, 1)}</b><small>90% interval ${pct(F.slope09.lo)}–${pct(F.slope09.hi)}</small></div>`
      + `<div><span class="label">With slope 1.0</span><b>${pct(F.slope10.p, 1)}</b><small>90% interval ${pct(F.slope10.lo)}–${pct(F.slope10.hi)}</small></div>`
      + `<div><span class="label">Community</span><b>${pct(F.community)}</b><small>${F.n_forecasters} forecasters</small></div>`
      + `<div><span class="label">Inside view</span><b>${pct(F.inside, 1)}</b><small>base rate ${pct(D.ledger.prior, 1)} + evidence</small></div>`;
    document.getElementById("alt-forecast").textContent = `${pct(F.slope10.p, 1)} (interval ${pct(F.slope10.lo)}–${pct(F.slope10.hi)})`;
    document.getElementById("fc-sudan").textContent = pct(F.slope09.p, 1);
  })();
})();
