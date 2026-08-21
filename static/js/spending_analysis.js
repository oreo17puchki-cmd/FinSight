// spending_analysis.js

document.addEventListener("DOMContentLoaded", () => {
  const formatCurrency = (value) => {
    return '₹' + value.toLocaleString('en-IN');
  };

  try {
    const charts = [];

    // 1. Spend by Category (Donut Chart exactly matching screenshot)
    const catChartDom = document.getElementById('chart-category');
    if (catChartDom) {
      const catChart = echarts.init(catChartDom);
      charts.push(catChart);
      
      const pieData = [
        { name: 'Food', value: 12500, percentage: 35, itemStyle: { color: '#3b82f6' } },
        { name: 'Shopping', value: 8000, percentage: 22, itemStyle: { color: '#22c55e' } },
        { name: 'Bills', value: 6500, percentage: 18, itemStyle: { color: '#f59e0b' } },
        { name: 'Transport', value: 5000, percentage: 15, itemStyle: { color: '#ef4444' } }
      ];
      
      catChart.setOption({
        tooltip: {
          trigger: 'item',
          formatter: (info) => `${info.name}: ${formatCurrency(info.value)} (${info.data.percentage}%)`
        },
        legend: {
          orient: 'vertical',
          right: '8%',
          top: 'center',
          itemGap: 25,
          itemWidth: 20,
          itemHeight: 10,
          icon: 'roundRect',
          formatter: function (name) {
            let item = pieData.find(i => i.name === name);
            return `{name|${name}}  {percent|${item ? item.percentage : 0}%}  {value|${formatCurrency(item ? item.value : 0)}}`;
          },
          textStyle: {
            rich: {
              name: { width: 75, color: '#475569', fontSize: 13, fontWeight: 500 },
              percent: { width: 35, color: '#94a3b8', fontSize: 13 },
              value: { color: '#1e293b', fontSize: 13, fontWeight: 700 }
            }
          }
        },
        series: [{
          type: 'pie',
          radius: ['40%', '75%'],
          center: ['28%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 0,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: { show: false },
          data: pieData
        }]
      });
    }

    // 2. Income vs Expenses (Trend Chart matching screenshot)
    const trendChartDom = document.getElementById('chart-trend');
    if (trendChartDom) {
      const trendChart = echarts.init(trendChartDom);
      charts.push(trendChart);
      
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
      const income = [5000, 6200, 7000, 6800, 7600, 8200];
      const expenses = [3000, 4200, 4500, 4100, 4900, 5400];
      
      trendChart.setOption({
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(30, 41, 59, 0.9)',
          textStyle: { color: '#fff' },
          formatter: function(params) {
            let tooltip = `<strong>${params[0].name}</strong><br/>`;
            params.forEach(p => {
              tooltip += `<span style="display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:${p.color}"></span>`;
              tooltip += `${p.seriesName}: ${formatCurrency(p.value)}<br/>`;
            });
            return tooltip;
          }
        },
        xAxis: {
          type: 'category',
          data: months,
          boundaryGap: false,
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { color: '#94a3b8', margin: 15 }
        },
        yAxis: {
          type: 'value',
          splitLine: { show: false },
          axisLabel: {
            color: '#94a3b8',
            formatter: (value) => '₹' + (value >= 1000 ? (value/1000) + 'K' : value)
          }
        },
        series: [
          {
            name: 'Income',
            data: income,
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            itemStyle: { color: '#22c55e', borderColor: '#fff', borderWidth: 2 },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(34, 197, 94, 0.2)' },
                { offset: 1, color: 'rgba(34, 197, 94, 0.0)' }
              ])
            }
          },
          {
            name: 'Expenses',
            data: expenses,
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            itemStyle: { color: '#ef4444', borderColor: '#fff', borderWidth: 2 },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(239, 68, 68, 0.1)' },
                { offset: 1, color: 'rgba(239, 68, 68, 0.0)' }
              ])
            }
          }
        ],
        grid: { left: '10%', right: '5%', bottom: '15%', top: '10%' }
      });
    }

    // 3. Pareto Analysis
    const paretoChartDom = document.getElementById('chart-pareto');
    if (paretoChartDom) {
      const paretoChart = echarts.init(paretoChartDom);
      charts.push(paretoChart);
      
      paretoChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['Spend', 'Transactions'], bottom: 0 },
        xAxis: { type: 'category', data: ['Top 20% Txns', 'Bottom 80% Txns'], axisTick: { show: false } },
        yAxis: [
          { type: 'value', name: 'Spend', splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } } },
          { type: 'value', name: 'Count', splitLine: { show: false } }
        ],
        series: [
          { name: 'Spend', type: 'bar', data: [25600, 6400], itemStyle: { color: '#3b82f6', borderRadius: [4, 4, 0, 0] }, barWidth: '40%' },
          { name: 'Transactions', type: 'line', yAxisIndex: 1, data: [15, 60], itemStyle: { color: '#f59e0b' }, symbolSize: 8, smooth: true }
        ],
        grid: { left: '10%', right: '10%', bottom: '15%', top: '15%' }
      });
    }

    // 4. Spend by Region
    const regionChartDom = document.getElementById('chart-region');
    if (regionChartDom) {
      const regionChart = echarts.init(regionChartDom);
      charts.push(regionChart);
      const regions = ["Middle East", "Latin America", "Asia Pacific", "Europe", "North America"];
      const regionAmts = [2500, 3500, 6000, 8000, 12000];
      
      regionChart.setOption({
        tooltip: { trigger: 'axis', valueFormatter: formatCurrency },
        xAxis: { type: 'value', show: false },
        yAxis: { type: 'category', data: regions, axisTick: { show: false }, axisLine: { show: false } },
        series: [{ type: 'bar', data: regionAmts, label: { show: true, position: 'right', formatter: (p) => formatCurrency(p.value), color: '#64748b' }, itemStyle: { color: '#0ea5e9', borderRadius: [0, 4, 4, 0] }, barWidth: '50%' }],
        grid: { left: '30%', right: '25%', bottom: '5%', top: '5%' }
      });
    }

    // 5. Spend by Supplier
    const supplierChartDom = document.getElementById('chart-supplier');
    if (supplierChartDom) {
      const supplierChart = echarts.init(supplierChartDom);
      charts.push(supplierChart);
      const suppliers = ["TechCorp", "OfficeDepot", "CloudServices", "TravelAgency", "LocalVendor", "Consulting"];
      const supplierAmts = [8000, 5000, 7500, 3200, 2100, 6200];
      
      supplierChart.setOption({
        tooltip: { trigger: 'axis', valueFormatter: formatCurrency },
        xAxis: { type: 'category', data: suppliers, axisLabel: { interval: 0, rotate: 25, color: '#64748b' }, axisTick: { show: false } },
        yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } }, axisLabel: { color: '#94a3b8', formatter: (value) => '₹' + (value/1000) + 'K' } },
        series: [{ type: 'bar', data: supplierAmts, itemStyle: { color: '#10b981', borderRadius: [4, 4, 0, 0] }, barWidth: '40%' }],
        grid: { left: '15%', right: '5%', bottom: '25%', top: '10%' }
      });
    }

    // 6. Spend by Contract
    const contractChartDom = document.getElementById('chart-contract');
    if (contractChartDom) {
      const contractChart = echarts.init(contractChartDom);
      charts.push(contractChart);
      
      contractChart.setOption({
        tooltip: { trigger: 'item', valueFormatter: formatCurrency },
        legend: { bottom: '0%', itemGap: 20 },
        color: ['#8b5cf6', '#f59e0b'],
        series: [{
          type: 'pie',
          radius: ['45%', '75%'],
          itemStyle: { borderColor: '#fff', borderWidth: 2 },
          label: { show: false },
          data: [
            { value: 20800, name: 'Contracted' },
            { value: 11200, name: 'Non-Contracted' }
          ]
        }]
      });
    }

    // Handle Window Resize
    window.addEventListener('resize', () => {
      charts.forEach(chart => chart.resize());
    });

  } catch (error) {
    console.error("Error loading spending analysis data:", error);
  }
});
