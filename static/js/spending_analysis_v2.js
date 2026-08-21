const formatCurrency = (value) => {
  return '₹' + value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

// Distinct colors for the donut chart as per specification
const chartColors = ['#3b82f6', '#f97316', '#22c55e', '#ef4444', '#a855f7', '#06b6d4', '#eab308', '#64748b'];

async function refreshSpendingAnalytics() {
  try {
    const timeWindow = document.getElementById('time-window-select')?.value || 'MTD';
    const response = await fetch(`/api/spending-analysis/data?time_window=${timeWindow}`);
    if (!response.ok) throw new Error('Failed to fetch data');
    const data = await response.json();

    // 1. Populate Headers
    const valTotalExpenses = document.getElementById('val-total-expenses');
    if (valTotalExpenses) {
      valTotalExpenses.innerText = formatCurrency(data.total_expenses || 0);
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
        textinfo: 'none', // Hide text on the chart itself
        hoverinfo: 'label+percent+value',
        marker: {
          colors: chartColors
        }
      }];

      const layout = {
        showlegend: false, // We'll build a custom HTML legend
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
              <div class="legend-amount">${formatCurrency(item.amount)}</div>
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

  } catch (error) {
    console.error("Error loading spending analysis data:", error);
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
