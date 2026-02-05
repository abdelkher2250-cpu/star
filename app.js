const pricingBody = document.getElementById('pricingBody');
const totalMarketsEl = document.getElementById('totalMarkets');
const lowestMonthlyEl = document.getElementById('lowestMonthly');
const highestMonthlyEl = document.getElementById('highestMonthly');
const avgHardwareEl = document.getElementById('avgHardware');
const countryFilterEl = document.getElementById('countryFilter');
const planFilterEl = document.getElementById('planFilter');

const fmtMoney = (value, currency) =>
  new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency,
    maximumFractionDigits: currency === 'JPY' || currency === 'CLP' ? 0 : 2,
  }).format(value);

const toUsd = (value, rate) => value * rate;

let allRows = [];

function buildPlanFilter(rows) {
  const plans = [...new Set(rows.map((row) => row.plan))].sort();
  for (const plan of plans) {
    const option = document.createElement('option');
    option.value = plan;
    option.textContent = plan;
    planFilterEl.appendChild(option);
  }
}

function computeSummary(rows) {
  totalMarketsEl.textContent = String(new Set(rows.map((r) => r.country)).size);
  if (!rows.length) {
    lowestMonthlyEl.textContent = '—';
    highestMonthlyEl.textContent = '—';
    avgHardwareEl.textContent = '—';
    return;
  }

  const priced = rows.map((row) => ({
    ...row,
    monthlyUsd: toUsd(row.monthly_local, row.usd_rate),
    hardwareUsd: toUsd(row.hardware_local, row.usd_rate),
  }));

  const lowest = priced.reduce((a, b) => (a.monthlyUsd < b.monthlyUsd ? a : b));
  const highest = priced.reduce((a, b) => (a.monthlyUsd > b.monthlyUsd ? a : b));
  const avgHardware = priced.reduce((sum, row) => sum + row.hardwareUsd, 0) / priced.length;

  lowestMonthlyEl.textContent = `${fmtMoney(lowest.monthlyUsd, 'USD')} (${lowest.country})`;
  highestMonthlyEl.textContent = `${fmtMoney(highest.monthlyUsd, 'USD')} (${highest.country})`;
  avgHardwareEl.textContent = fmtMoney(avgHardware, 'USD');
}

function renderRows(rows) {
  pricingBody.innerHTML = '';
  const sorted = [...rows].sort((a, b) => a.country.localeCompare(b.country));

  for (const row of sorted) {
    const tr = document.createElement('tr');
    const monthlyUsd = toUsd(row.monthly_local, row.usd_rate);
    const hardwareUsd = toUsd(row.hardware_local, row.usd_rate);
    tr.innerHTML = `
      <td>${row.country}</td>
      <td>${row.currency}</td>
      <td>${row.plan}</td>
      <td>${fmtMoney(row.monthly_local, row.currency)}</td>
      <td>${fmtMoney(monthlyUsd, 'USD')}</td>
      <td>${fmtMoney(row.hardware_local, row.currency)}</td>
      <td>${fmtMoney(hardwareUsd, 'USD')}</td>
      <td>${row.notes || ''}</td>
    `;
    pricingBody.appendChild(tr);
  }
  computeSummary(rows);
}

function applyFilters() {
  const countryNeedle = countryFilterEl.value.trim().toLowerCase();
  const planValue = planFilterEl.value;
  const filtered = allRows.filter((row) => {
    const countryMatch = !countryNeedle || row.country.toLowerCase().includes(countryNeedle);
    const planMatch = !planValue || row.plan === planValue;
    return countryMatch && planMatch;
  });
  renderRows(filtered);
}

async function init() {
  const response = await fetch('data/starlink_pricing.json');
  const payload = await response.json();
  allRows = payload.rows;
  buildPlanFilter(allRows);
  renderRows(allRows);

  countryFilterEl.addEventListener('input', applyFilters);
  planFilterEl.addEventListener('change', applyFilters);
}

init().catch((error) => {
  pricingBody.innerHTML = `<tr><td colspan="8">Failed to load data: ${error.message}</td></tr>`;
});
