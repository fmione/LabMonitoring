const CHART_COLORS = [
  "#0ea5e9", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6",
  "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16",
];

window.__lmCharts = {};
window.__lmCards = {};

document.addEventListener("DOMContentLoaded", function () {
  setTimeout(() => {
    document.querySelectorAll("table").forEach(t => t.classList.add("lm-shown"));
  }, 250);
  bindChartResize();
});

function isSmallScreen() {
  return window.innerWidth < 768;
}

function xTickRotation() {
  return isSmallScreen() ? 90 : 0;
}



function makeDatasets(series) {
  return series.map((s, i) => {
    const style = s.style || (s.dashed ? "dashed" : "line");
    const pointsOnly = style === "dots" || style === "stars";
    const color = s.color || (pointsOnly ? "#64748b" : CHART_COLORS[i % CHART_COLORS.length]);
    return {
      label: s.label,
      data: s.points.map(p => ({ x: p[0], y: p[1] })),
      borderColor: color,
      backgroundColor: pointsOnly ? color : color + "22",
      borderWidth: 2,
      borderDash: style === "dashed" ? [6, 4] : [],
      pointStyle: style === "stars" ? "star" : "circle",
      pointRadius: style === "stars" ? 6 : pointsOnly ? 2 : 1,
      pointHoverRadius: 4,
      tension: pointsOnly ? 0 : 0.2,
      showLine: !pointsOnly,
    };
  });
}

let _fixedTooltipRegistered = false;
function ensureFixedTooltip() {
  if (_fixedTooltipRegistered || !Chart || !Chart.Tooltip || !Chart.Tooltip.positioners) return;
  _fixedTooltipRegistered = true;
  Chart.Tooltip.positioners.fixedBottomRight = function (items, eventPosition) {
    const chart = this.chart;
    return { x: chart.width - 4, y: chart.height - 4 };
  };
}

function tooltipExternal(context) {
  const { chart, tooltip } = context;
  if (!chart || !chart.canvas || !chart.canvas.parentNode) return;
  const box = chart.canvas.parentNode;
  let el = box.querySelector(".lm-tooltip");
  if (!tooltip.opacity || !tooltip.dataPoints || !tooltip.dataPoints.length) {
    if (el) el.style.display = "none";
    return;
  }
  if (!el) {
    el = document.createElement("div");
    el.className = "lm-tooltip";
    el.innerHTML = "<div class='lm-tooltip-title'></div><div class='lm-tooltip-body'></div>";
    box.appendChild(el);
  }
  el.querySelector(".lm-tooltip-title").textContent = tooltip.title && tooltip.title[0] ? tooltip.title[0] : "";
  const body = el.querySelector(".lm-tooltip-body");
  body.innerHTML = "";
  tooltip.dataPoints.forEach(dp => {
    const row = document.createElement("div");
    row.className = "lm-row";
    row.innerHTML = `<span class="lm-dot"></span><span>${dp.dataset.label}: ${Number(dp.parsed.y).toFixed(3)}</span>`;
    if (dp.dataset.borderColor) row.querySelector(".lm-dot").style.background = dp.dataset.borderColor;
    body.appendChild(row);
  });
  el.style.display = "block";
}

function buildLineChart(canvasId, series, animate = true, card = null) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  canvas.ondblclick = () => {
    const c = Chart.getChart(canvas);
    if (c) c.resetZoom();
  };
  delete window.__lmCharts[canvasId];
  const old = Chart.getChart(canvas);
  if (old) old.destroy();
  if (card) window.__lmCards[canvasId] = card;
  if (!series || series.length === 0 || series.every(s => s.points.length === 0)) return;

  const datasets = makeDatasets(series);
  ensureFixedTooltip();

  const chart = new Chart(canvas, {
    type: "line",
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: animate,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: {
          type: "linear",
          title: { display: true, text: "Tiempo (h)" },
          ticks: {
            maxTicksLimit: isSmallScreen() ? 4 : 8,
            maxRotation: xTickRotation(),
            minRotation: xTickRotation(),
            autoSkip: true,
          },
        },
        y: { beginAtZero: false, title: { display: true, text: "Valor" } },
      },
      plugins: {
        legend: { position: "right" },
        tooltip: {
          enabled: false,
          position: "fixedBottomRight",
          external: tooltipExternal,
          callbacks: {
            title: items => items.length ? `t = ${Number(items[0].parsed.x).toFixed(3)}` : "",
          },
        },
        zoom: {
          pan: { enabled: true, mode: "x", modifierKey: "shift" },
          zoom: {
            wheel: { enabled: false },
            drag: {
              enabled: true,
              mode: "xy",
              backgroundColor: "rgba(14, 165, 233, 0.12)",
              borderColor: "#0ea5e9",
              borderWidth: 1,
            },
            pinch: { enabled: true },
            mode: "xy",
          },
        },
      },
    },
  });
  window.__lmCharts[canvasId] = chart;
}

function updateLineChart(canvasId, series, chart, card, animate = true) {
  chart.options.animation = animate;
  chart.data.datasets = makeDatasets(series);
  chart.update(animate ? undefined : "none");
  if (card) {
    const n = card.querySelector(".series-count");
    if (n) n.textContent = `${series.length} series`;
  }
}

let _resizeHandler = null;
function bindChartResize() {
  if (_resizeHandler) return;
  _resizeHandler = debounce(() => {
    Object.values(window.__lmCharts).forEach(chart => {
      const scale = chart.options.scales.x;
      const rot = xTickRotation();
      scale.ticks.maxTicksLimit = isSmallScreen() ? 4 : 8;
      scale.ticks.maxRotation = rot;
      scale.ticks.minRotation = rot;
      chart.update("none");
    });
  }, 150);
  window.addEventListener("resize", _resizeHandler);
}

function debounce(fn, ms) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}