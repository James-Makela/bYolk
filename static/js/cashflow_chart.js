function renderCashFlowChart(dates, titles, amounts, totalSpend, hideValues = false, theme) {
  const isDark = theme.includes('dark');
  const formatCurrency = (val) => {
    if (hideValues) return "$x.xx";
    return typeof val === 'number' ? `$${val.toFixed(2)}` : `$${val}`;
  };
  const series = titles.map((title, index) => ({
    name: title,
    type: 'line',
    data: amounts[index]
  }));

  const totalData = amounts[0].map((val, i) =>
    amounts.reduce((sum, list) => sum + (Number(list[i]) || 0), 0)
  );

  const delta = totalData.map((val, i) => Number(val) + (Number(totalSpend[i]) || 0));

  series.unshift({
    name: 'Total Income',
    type: 'area',
    color: '#33cc44',
    data: totalData,
  });

  series.unshift({
    name: 'Total Spend',
    type: 'area',
    color: '#ff2222',
    data: totalSpend,
  });

  series.unshift({
    name: 'Cash Flow',
    type: 'column',
    data: delta,
  });

  const options = {
    series: series,
    chart: {
      height: 350,
      type: 'area',
      zoom: {
        enabled: false,
      },
      toolbar: {
        show: false,
      },
      background: 'transparent',
      sparkline: false,
      events: {
        updated: function(chartContext, config) {
          preserveZeroLabel('#cashflow-chart');
        },
      },
    },
    theme: {
      mode: isDark ? 'dark' : 'light',
    },
    stroke: {
      curve: series.map(s => (s.type === 'column' ? 'straight' : 'smooth')),
      width: series.map(s => (s.type === 'column' ? 0 : s.type === 'line' ? 2.5 : 1)),
    },
    fill: {
      type: ['solid', 'gradient', 'gradient'],
      gradient: {
        shade: isDark ? 'dark' : 'light',
        shadeIntensity: 0.8,
        opacityFrom: [1, 0.3, 0.6],
        opacityTo: [1, 0.6, 0.3],
        stops: [0, 100],
      }
    },
    plotOptions: {
      bar: {
        columnWidth: '50%',
        colors: {
          ranges: [
            {
              from: -1000000,
              to: -0.01,
              color: '#EF4444',
            },
            {
              from: 0,
              to: 1000000,
              color: '#10B981',
            },
          ]
        },
      },
    },
    dataLabels: {
      enabled: false,
    },
    legend: {
      markers: {
        strokeWidth: 0,
      },
    },
    xaxis: {
      type: 'datetime',
      categories: dates,
      axisTicks: {
        show: false,
      },
      axisBorder: {
        show: false,
      },
    },
    yaxis: {
      labels: {
        show: true,
        formatter: function (val, opts) {
          return formatCurrency(val);
        },
      },
      forceNiceScale: true,
      tickAmount: 10,
      axisTicks: {
        show: false,
      },
      axisBorder: {
        show: false,
      },
    },
    grid: {
      show: true,
      borderColor: isDark ? 'rgba(255, 255, 255, 0.08)' :  'rgba(0, 0, 0, 0.08)',
      strokeDashArray: 0,
      xaxis: {
        lines: {
          show: false,
        },
      },
    },
    tooltip: {
      x: {
        format: 'dd MMM yyyy',
      },
      theme: isDark ? 'dark' : 'light',
    },
  };

  var chart = new ApexCharts(document.querySelector("#cashflow-chart"), options);
  chart.render()

  ChartManager.register(chart, '#cashflow-chart', (isDark) => {
    preserveZeroLabel('#cashflow-chart');
  });
}

function preserveZeroLabel(containerSelector = '#cashflow-chart') {
  const labels = document.querySelectorAll(`${containerSelector} .apexcharts-yaxis-label`);
  labels.forEach(label => {
    if (label.textContent.trim().startsWith('$0.00')) {
      label.classList.add('show-label');
    }
  });
}
