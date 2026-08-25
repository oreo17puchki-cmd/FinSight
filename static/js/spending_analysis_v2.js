const formatCurrency = (value) => {
  return '₹' + Math.round(value).toLocaleString('en-IN');
};

const formatCurrencyDetailed = (value) => {
  return '₹' + Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

// Distinct colors for the donut chart as per specification
const chartColors = ['#3b82f6', '#f97316', '#22c55e', '#ef4444', '#a855f7', '#06b6d4', '#eab308', '#64748b'];

function updateBurnRateModule(burnRate) {
  if (!burnRate || !burnRate.phases || burnRate.phases.length < 3) return;

  const [p1, p2, p3] = burnRate.phases;

  const phases = [
    "Phase 1 (Days 1-10)<br>Post-Payday Surge",
    "Phase 2 (Days 11-20)<br>Mid-Month Baseline",
    "Phase 3 (Days 21-End)<br>Month-End Frugality"
  ];
  const values  = [p1.daily_avg, p2.daily_avg, p3.daily_avg];
  const colors  = ['#941334', '#E5A93C', '#3E8299'];
  const halfH   = Math.max(p1.daily_avg, p2.daily_avg, p3.daily_avg) * 0.065; // ~6.5% of max as half-height
  const gap     = halfH * 0.08; // tiny white gap between upper & lower half

  const traces = [];

  // For each phase: lower half (base = val - halfH, height = halfH - gap/2)
  //                 upper half (base = val + gap/2,  height = halfH - gap/2)
  phases.forEach((label, i) => {
    const val  = values[i];
    const col  = colors[i];
    const lo   = halfH - gap / 2;

    // Lower half — starts at (val - halfH), rises to center
    traces.push({
      x: [label], y: [lo],
      base: val - halfH,
      type: 'bar',
      width: [1.0],
      marker: { color: col, line: { width: 0 } },
      showlegend: false,
      hovertemplate: `<b>${label.replace('<br>', ' ')}</b><br>Daily Burn Rate: ₹${Math.round(val).toLocaleString('en-IN')}/day<extra></extra>`
    });

    // Upper half — starts just above center, same height
    traces.push({
      x: [label], y: [lo],
      base: val + gap / 2,
      type: 'bar',
      width: [1.0],
      marker: { color: col, line: { width: 0 } },
      showlegend: false,
      hoverinfo: 'skip'
    });
  });

  const maxVal = Math.max(...values);
  const tickVals = [0, p3.daily_avg, p2.daily_avg, p1.daily_avg];
  const tickText = tickVals.map((v, i) =>
    i === 0
      ? '₹0'
      : `₹${Math.round(v).toLocaleString('en-IN')}/day`
  );

  const layout = {
    height: 340,
    barmode: 'overlay',
    bargap: 0,
    bargroupgap: 0,
    plot_bgcolor: '#FFFFFF',
    paper_bgcolor: '#FFFFFF',
    margin: { l: 110, r: 20, t: 16, b: 140 },
    yaxis: {
      tickvals: tickVals,
      ticktext: tickText,
      range: [-(maxVal * 0.12), maxVal * 1.18],
      gridcolor: '#E2E8F0',
      gridwidth: 1,
      zeroline: true,
      zerolinecolor: '#CBD5E1',
      zerolinewidth: 1.5,
      tickfont: { family: 'Manrope, Inter, sans-serif', size: 13, color: '#1E293B' },
      showgrid: true
    },
    xaxis: {
      showgrid: false,
      zeroline: false,
      tickangle: -40,
      tickfont: { family: 'Manrope, Inter, sans-serif', size: 12, color: '#1E293B' },
      automargin: true
    }
  };

  const config = { responsive: true, displayModeBar: false };
  Plotly.newPlot('plotly-burn-rate-chart', traces, layout, config);

  // Update Alert Box
  const alertBox     = document.getElementById('burn-alert-box');
  const alertHeading = document.getElementById('burn-alert-heading');
  const alertP1      = document.getElementById('burn-alert-p1');
  const alertP2      = document.getElementById('burn-alert-p2');

  if (alertBox) alertBox.className = `burn-alert-box alert-${burnRate.alert_theme || 'warning'}`;
  if (alertHeading) alertHeading.textContent = burnRate.alert_title || 'Post-Payday Surge Detected:';
  if (alertP1) {
    alertP1.innerHTML = (burnRate.status === 'surge' && burnRate.multiplier > 1.0)
      ? `Your daily spending in Days 1-10 is <span class="highlight-val">${burnRate.multiplier.toFixed(1)}x higher</span> than Month-End.`
      : burnRate.alert_line_1;
  }
  if (alertP2) {
    alertP2.innerHTML = (burnRate.status === 'surge')
      ? `<span class="highlight-val">${burnRate.phase_1_percentage.toFixed(1)}%</span> of total monthly expenses occurred in the first 10 days.`
      : burnRate.alert_line_2;
  }
}

async function refreshSpendingAnalytics() {
  try {
    const timeWindow = document.getElementById('time-window-select')?.value || 'MTD';
    const response = await fetch(`/api/spending-analysis/data?time_window=${timeWindow}`);
    if (!response.ok) throw new Error('Failed to fetch data');
    const data = await response.json();

    // 1. Populate Headers
    const valTotalExpenses = document.getElementById('val-total-expenses');
    if (valTotalExpenses) {
      valTotalExpenses.innerText = formatCurrencyDetailed(data.total_expenses || 0);
    }
    
    const valDateRange = document.getElementById('val-date-range');
    if (valDateRange) {
      valDateRange.innerText = data.date_range;
    }

    // 2. Populate Assist Beta Card
    if (data.assist_insights) {
      const assistSummary = document.getElementById('assist-summary');
      if (assistSummary) {
        assistSummary.innerText = data.assist_insights.summary;
      }

      const assistTop = document.getElementById('assist-top-spending');
      if (assistTop) {
        assistTop.innerHTML = data.assist_insights.top_spending
          .map(item => `<div>${item}</div>`)
          .join('');
      }
    }

    // 3. Render Plotly Donut Chart and Legend
    if (data.spend_by_category && data.spend_by_category.length > 0) {
      const labels = data.spend_by_category.map(item => item.category);
      const values = data.spend_by_category.map(item => item.amount);
      
      const plotData = [{
        values: values,
        labels: labels,
        type: 'pie',
        hole: 0.6,
        textinfo: 'none',
        hoverinfo: 'label+percent+value',
        marker: {
          colors: chartColors
        }
      }];

      const layout = {
        showlegend: false,
        margin: { t: 10, b: 10, l: 10, r: 10 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)'
      };

      const config = { responsive: true, displayModeBar: false };

      Plotly.newPlot('plotly-donut-chart', plotData, layout, config);

      // 4. Build Custom HTML Legend
      const legendGrid = document.getElementById('category-legend-grid');
      if (legendGrid) {
        let legendHTML = '';
        data.spend_by_category.forEach((item, index) => {
          const color = chartColors[index % chartColors.length];
          legendHTML += `
            <div class="legend-item">
              <div class="legend-title">
                <div class="legend-color" style="background-color: ${color}"></div>
                <span>${item.category}</span>
              </div>
              <div class="legend-amount">${formatCurrencyDetailed(item.amount)}</div>
            </div>
          `;
        });
        legendGrid.innerHTML = legendHTML;
      }
    } else {
      // Handle empty state
      document.getElementById('plotly-donut-chart').innerHTML = '<p style="color:#94a3b8; text-align:center; padding-top:40px;">No spending data found.</p>';
      document.getElementById('category-legend-grid').innerHTML = '';
    }

    // 5. Render Burn Rate Module
    if (data.burn_rate) {
      updateBurnRateModule(data.burn_rate);
    }

    // 6. Render Labor Equivalency Module
    if (data.labor_equivalency) {
      updateLaborEquivalencyModule(data.labor_equivalency);
    }

  } catch (error) {
    console.error("Error loading spending analysis data:", error);
  }
}

function updateLaborEquivalencyModule(labor) {
  if (!labor) return;

  const fmt = (n) => '₹' + Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  // Header badge
  const badge = document.getElementById('labor-rate-badge');
  if (badge) badge.textContent = `(Based on ₹${Math.round(labor.hourly_rate).toLocaleString('en-IN')}/hr • ${labor.work_hours_per_month} hrs/mo)`;

  const cats = labor.categories || [];
  const shop = cats.find(c => c.key === 'shopping')    || {};
  const dine = cats.find(c => c.key === 'dining')      || {};
  const ent  = cats.find(c => c.key === 'entertainment') || {};

  // Shopping column
  const el = (id) => document.getElementById(id);
  if (el('labor-shop-amount')) el('labor-shop-amount').textContent = fmt(shop.amount || 0);
  if (el('labor-shop-hrs'))    el('labor-shop-hrs').textContent    = shop.hours ?? 0;
  if (el('labor-shop-days'))   el('labor-shop-days').textContent   = shop.days  ?? 0;

  // Dining column
  if (el('labor-dine-amount')) el('labor-dine-amount').textContent = fmt(dine.amount || 0);
  if (el('labor-dine-hrs'))    el('labor-dine-hrs').textContent    = dine.hours ?? 0;
  if (el('labor-dine-days'))   el('labor-dine-days').textContent   = dine.days  ?? 0;

  // Entertainment column
  if (el('labor-ent-amount')) el('labor-ent-amount').textContent = fmt(ent.amount || 0);
  if (el('labor-ent-hrs'))    el('labor-ent-hrs').textContent    = ent.hours ?? 0;
  if (el('labor-ent-days'))   el('labor-ent-days').textContent   = ent.days  ?? 0;

  // Totals & callout
  if (el('labor-total-hrs'))  el('labor-total-hrs').textContent  = labor.total_hours ?? 0;
  if (el('labor-total-days')) el('labor-total-days').textContent = labor.total_days  ?? 0;
  if (el('labor-callout-text')) {
    el('labor-callout-text').innerHTML =
      `You worked <strong>${labor.total_hours}</strong> hours ` +
      `(~<strong>${labor.total_days}</strong> working days) this month ` +
      `solely to fund discretionary lifestyle purchases.`;
  }
}

window.refreshSpendingAnalytics = refreshSpendingAnalytics;

document.addEventListener("DOMContentLoaded", () => {
  refreshSpendingAnalytics();
  
  const timeSelect = document.getElementById('time-window-select');
  if (timeSelect) {
    timeSelect.addEventListener('change', refreshSpendingAnalytics);
  }
});
