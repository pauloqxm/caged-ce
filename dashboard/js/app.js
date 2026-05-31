/* Dashboard CAGED CE — app.js */

const fmt = (n) => n == null ? "—" : n.toLocaleString("pt-BR");
const fmtPct = (n) => (n >= 0 ? "+" : "") + n.toFixed(1) + "%";

const COLORS = {
  blue: "rgba(59, 130, 246, 0.85)",
  blueLight: "rgba(59, 130, 246, 0.2)",
  green: "rgba(34, 197, 94, 0.85)",
  greenLight: "rgba(34, 197, 94, 0.2)",
  orange: "rgba(245, 158, 11, 0.85)",
  red: "rgba(239, 68, 68, 0.85)",
  purple: "rgba(168, 85, 247, 0.85)",
  grid: "rgba(139, 156, 179, 0.12)",
  text: "#8b9cb3",
};

const chartDefaults = {
  responsive: true,
  maintainAspectRatio: false,
  layout: { padding: { top: 8, right: 12, bottom: 4, left: 4 } },
  plugins: {
    legend: { labels: { color: COLORS.text, font: { size: 11 } } },
  },
  scales: {
    x: { ticks: { color: COLORS.text, maxRotation: 45, autoSkip: true, maxTicksLimit: 12 }, grid: { color: COLORS.grid } },
    y: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid }, beginAtZero: true },
  },
};

let DATA = null;
let charts = {};
const renderedSections = new Set();

async function init() {
  try {
    const res = await fetch("data/emprego_ce.json");
    DATA = await res.json();
    renderKPIs();
    renderInsight();
    setupFiltroAno();
    setupNav();
    setupMobileMenu();
    setupChartResize();
    renderSectionCharts("visao-geral");
    document.getElementById("data-geracao").textContent =
      "Atualizado: " + new Date(DATA.gerado_em).toLocaleString("pt-BR");
  } catch (e) {
    document.getElementById("insight-text").textContent =
      "Erro ao carregar dados. Execute iniciar_dashboard.bat para preparar os arquivos.";
    console.error(e);
  } finally {
    document.getElementById("loading").classList.add("hidden");
    requestAnimationFrame(() => {
      requestAnimationFrame(resizeAllCharts);
    });
  }
}

function renderSectionCharts(sectionId) {
  if (!DATA) return;

  if (renderedSections.has(sectionId)) {
    requestAnimationFrame(resizeAllCharts);
    return;
  }
  renderedSections.add(sectionId);

  switch (sectionId) {
    case "visao-geral":
      renderJanAno();
      renderSaldoAnual();
      break;
    case "evolucao":
      renderEstoqueMensal(document.getElementById("filtro-ano").value);
      renderFluxoMensal(document.getElementById("filtro-ano").value);
      break;
    case "anual":
      renderAdmDesAnual();
      renderCrescAnual();
      break;
    case "municipios":
      renderTopMunicipios();
      renderTabelaMunicipios();
      break;
    case "ajuste":
      renderAjuste();
      break;
  }

  requestAnimationFrame(resizeAllCharts);
}

function renderKPIs() {
  const k = DATA.emprego.kpis;
  document.getElementById("kpi-estoque").textContent = fmt(k.estoque_atual);
  document.getElementById("kpi-mes").textContent = k.mes_atual;
  document.getElementById("kpi-cresc-2326").textContent = "+" + fmt(k.crescimento_2023_2026);
  document.getElementById("kpi-pct-2326").textContent =
    fmtPct(k.percentual_2023_2026) + " · estoque +" + fmt(k.diff_estoque_2023_2026);
  document.getElementById("kpi-cresc-2026").textContent = "+" + fmt(k.crescimento_2020_2026);
  document.getElementById("kpi-pct-2026").textContent = fmtPct(k.percentual_2020_2026) + " (jan/20 → abr/26)";
  document.getElementById("kpi-saldo-2025").textContent = "+" + fmt(k.saldo_2025);
}

function renderInsight() {
  const k = DATA.emprego.kpis;
  const saldo2023 = DATA.emprego.serie_anual.find((a) => a.ano === 2023);
  const saldo2024 = DATA.emprego.serie_anual.find((a) => a.ano === 2024);
  const saldo2025 = DATA.emprego.serie_anual.find((a) => a.ano === 2025);

  document.getElementById("insight-text").innerHTML = `
    Entre janeiro de 2023 e abril de 2026, o saldo líquido acumulado
    (admissões − desligamentos) foi de
    <strong>${fmt(k.crescimento_2023_2026)} empregos formais</strong>
    (${fmtPct(k.percentual_2023_2026)} sobre o estoque inicial), elevando o
    estoque de ${fmt(k.estoque_inicio)} para ${fmt(k.estoque_fim)} vínculos
    (variação de estoque: +${fmt(k.diff_estoque_2023_2026)}).
    Os saldos anuais foram positivos em 2023 (+${fmt(saldo2023?.saldo)}),
    2024 (+${fmt(saldo2024?.saldo)}) e 2025 (+${fmt(saldo2025?.saldo)}),
    com saldo parcial de jan–abr/2026 de +${fmt(k.saldo_2026_parcial)}.
    O mercado <strong>não estagnou</strong> — o que estabilizou foi apenas o
    ajuste cadastral entre versões antigas e novas do CAGED.
  `;
}

function destroyChart(id) {
  if (charts[id]) {
    charts[id].destroy();
    delete charts[id];
  }
}

function renderJanAno() {
  destroyChart("janAno");
  const d = DATA.emprego.jan_por_ano;
  const ctx = document.getElementById("chart-jan-ano");
  charts.janAno = new Chart(ctx, {
    type: "bar",
    data: {
      labels: d.map((x) => x.ano),
      datasets: [{
        label: "Estoque (jan)",
        data: d.map((x) => x.estoque),
        backgroundColor: COLORS.blue,
        borderRadius: 6,
      }],
    },
    options: {
      ...chartDefaults,
      plugins: {
        ...chartDefaults.plugins,
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (c) => fmt(c.raw) + " vínculos",
          },
        },
      },
      scales: {
        ...chartDefaults.scales,
        y: {
          ...chartDefaults.scales.y,
          ticks: {
            ...chartDefaults.scales.y.ticks,
            callback: (v) => (v / 1e6).toFixed(2) + " mi",
          },
        },
      },
    },
  });
}

function renderSaldoAnual() {
  destroyChart("saldoAnual");
  const d = DATA.emprego.serie_anual.filter((a) => a.ano <= 2025);
  const ctx = document.getElementById("chart-saldo-anual");
  charts.saldoAnual = new Chart(ctx, {
    type: "bar",
    data: {
      labels: d.map((x) => x.ano),
      datasets: [{
        label: "Saldo líquido",
        data: d.map((x) => x.saldo),
        backgroundColor: d.map((x) => (x.saldo >= 0 ? COLORS.green : COLORS.red)),
        borderRadius: 6,
      }],
    },
    options: {
      ...chartDefaults,
      plugins: { ...chartDefaults.plugins, legend: { display: false } },
    },
  });
}

function filtrarSerie(ano) {
  const s = DATA.emprego.serie_mensal;
  if (ano === "todos") return s;
  return s.filter((x) => x.mes_ano.endsWith("/" + ano));
}

function renderEstoqueMensal(ano) {
  destroyChart("estoqueMensal");
  const d = filtrarSerie(ano);
  const ctx = document.getElementById("chart-estoque-mensal");
  charts.estoqueMensal = new Chart(ctx, {
    type: "line",
    data: {
      labels: d.map((x) => x.label),
      datasets: [{
        label: "Estoque total",
        data: d.map((x) => x.estoque),
        borderColor: COLORS.blue,
        backgroundColor: COLORS.blueLight,
        fill: true,
        tension: 0.3,
        pointRadius: ano === "todos" ? 0 : 3,
        borderWidth: 2,
      }],
    },
    options: {
      ...chartDefaults,
      plugins: { ...chartDefaults.plugins, legend: { display: false } },
      scales: {
        ...chartDefaults.scales,
        y: {
          ...chartDefaults.scales.y,
          ticks: {
            ...chartDefaults.scales.y.ticks,
            callback: (v) => (v / 1e6).toFixed(2) + " mi",
          },
        },
      },
    },
  });
}

function renderFluxoMensal(ano) {
  destroyChart("fluxoMensal");
  const d = filtrarSerie(ano);
  const ctx = document.getElementById("chart-fluxo-mensal");
  charts.fluxoMensal = new Chart(ctx, {
    type: "line",
    data: {
      labels: d.map((x) => x.label),
      datasets: [
        {
          label: "Admissões",
          data: d.map((x) => x.admissoes),
          borderColor: COLORS.green,
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 1.5,
        },
        {
          label: "Desligamentos",
          data: d.map((x) => x.desligamentos),
          borderColor: COLORS.red,
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 1.5,
        },
      ],
    },
    options: chartDefaults,
  });
}

function renderAdmDesAnual() {
  destroyChart("admDesAnual");
  const d = DATA.emprego.serie_anual.filter((a) => a.ano <= 2025);
  const ctx = document.getElementById("chart-adm-des-anual");
  charts.admDesAnual = new Chart(ctx, {
    type: "bar",
    data: {
      labels: d.map((x) => x.ano),
      datasets: [
        {
          label: "Admissões",
          data: d.map((x) => x.admissoes),
          backgroundColor: COLORS.green,
          borderRadius: 4,
        },
        {
          label: "Desligamentos",
          data: d.map((x) => x.desligamentos),
          backgroundColor: COLORS.red,
          borderRadius: 4,
        },
      ],
    },
    options: {
      ...chartDefaults,
      scales: { ...chartDefaults.scales, x: { ...chartDefaults.scales.x, stacked: false } },
    },
  });
}

function renderCrescAnual() {
  destroyChart("crescAnual");
  const jan = DATA.emprego.jan_por_ano;
  const pct = [];
  for (let i = 1; i < jan.length; i++) {
    const prev = jan[i - 1].estoque;
    const curr = jan[i].estoque;
    pct.push({ ano: jan[i].ano, val: ((curr - prev) / prev) * 100 });
  }
  const ctx = document.getElementById("chart-cresc-anual");
  charts.crescAnual = new Chart(ctx, {
    type: "bar",
    data: {
      labels: pct.map((x) => x.ano),
      datasets: [{
        label: "Crescimento % (jan/jan)",
        data: pct.map((x) => x.val),
        backgroundColor: pct.map((x) => (x.val >= 0 ? COLORS.green : COLORS.red)),
        borderRadius: 6,
      }],
    },
    options: {
      ...chartDefaults,
      plugins: { ...chartDefaults.plugins, legend: { display: false } },
      scales: {
        ...chartDefaults.scales,
        y: {
          ...chartDefaults.scales.y,
          ticks: { ...chartDefaults.scales.y.ticks, callback: (v) => v + "%" },
        },
      },
    },
  });
}

function renderTopMunicipios() {
  destroyChart("topMuni");
  const d = DATA.emprego.top_crescimento.slice(0, 10);
  const ctx = document.getElementById("chart-top-muni");
  charts.topMuni = new Chart(ctx, {
    type: "bar",
    data: {
      labels: d.map((x) => x.municipio),
      datasets: [{
        label: "Crescimento (vínculos)",
        data: d.map((x) => x.crescimento),
        backgroundColor: COLORS.purple,
        borderRadius: 4,
      }],
    },
    options: {
      indexAxis: "y",
      ...chartDefaults,
      plugins: { ...chartDefaults.plugins, legend: { display: false } },
    },
  });
}

function renderTabelaMunicipios() {
  const tbody = document.querySelector("#tabela-municipios tbody");
  tbody.innerHTML = "";
  DATA.emprego.top_crescimento.forEach((m) => {
    const tr = document.createElement("tr");
    const cls = m.crescimento >= 0 ? "pos" : "neg";
    tr.innerHTML = `
      <td>${m.municipio}</td>
      <td class="num">${fmt(m.estoque_2023)}</td>
      <td class="num">${fmt(m.estoque_2026)}</td>
      <td class="num ${cls}">${m.crescimento >= 0 ? "+" : ""}${fmt(m.crescimento)}</td>
      <td class="num ${cls}">${fmtPct(m.percentual)}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderAjuste() {
  const aj = DATA.ajuste_cadastral;
  if (!aj || !aj.por_ano.length) {
    document.getElementById("ajuste-container").innerHTML =
      "<p class='chart-desc'>Dados de comparação mar/abri não disponíveis.</p>";
    return;
  }
  destroyChart("ajuste");
  const ctx = document.getElementById("chart-ajuste");
  charts.ajuste = new Chart(ctx, {
    type: "bar",
    data: {
      labels: aj.por_ano.map((x) => x.ano),
      datasets: [{
        label: "Soma diff estoque (abri − mar)",
        data: aj.por_ano.map((x) => x.soma_diff),
        backgroundColor: COLORS.orange,
        borderRadius: 6,
      }],
    },
    options: {
      ...chartDefaults,
      plugins: { ...chartDefaults.plugins, legend: { display: false } },
    },
  });
}

function setupNav() {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const sectionId = btn.dataset.section;
      document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".section").forEach((s) => s.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(sectionId).classList.add("active");
      closeMobileMenu();
      renderSectionCharts(sectionId);
    });
  });
}

function setupMobileMenu() {
  const toggle = document.getElementById("menu-toggle");
  const overlay = document.getElementById("sidebar-overlay");
  if (!toggle || !overlay) return;

  toggle.addEventListener("click", () => {
    const open = document.body.classList.toggle("menu-open");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Fechar menu" : "Abrir menu");
    overlay.classList.toggle("visible", open);
    overlay.setAttribute("aria-hidden", open ? "false" : "true");
  });

  overlay.addEventListener("click", closeMobileMenu);

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMobileMenu();
  });
}

function closeMobileMenu() {
  document.body.classList.remove("menu-open");
  const toggle = document.getElementById("menu-toggle");
  const overlay = document.getElementById("sidebar-overlay");
  if (toggle) {
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Abrir menu");
  }
  if (overlay) {
    overlay.classList.remove("visible");
    overlay.setAttribute("aria-hidden", "true");
  }
}

function resizeAllCharts() {
  Object.values(charts).forEach((chart) => {
    if (chart) chart.resize();
  });
}

function setupChartResize() {
  let timer;
  const onResize = () => {
    clearTimeout(timer);
    timer = setTimeout(resizeAllCharts, 150);
  };
  window.addEventListener("resize", onResize);
  window.addEventListener("orientationchange", onResize);
  if (window.ResizeObserver) {
    const ro = new ResizeObserver(onResize);
    document.querySelectorAll(".chart-wrap").forEach((el) => ro.observe(el));
  }
}

function setupFiltroAno() {
  const sel = document.getElementById("filtro-ano");
  const anos = [...new Set(DATA.emprego.serie_mensal.map((s) => s.mes_ano.split("/")[1]))];
  anos.forEach((a) => {
    const opt = document.createElement("option");
    opt.value = a;
    opt.textContent = a;
    sel.appendChild(opt);
  });
  sel.addEventListener("change", () => {
    renderEstoqueMensal(sel.value);
    renderFluxoMensal(sel.value);
  });
}

init();
