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

  const xAnnotationOne = new Date(dates[dates.length - 1]).getTime();
  const xAnnotationTwo = new Date(dates[dates.length - 2]).getTime();

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
      width: '100%',
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
        inverseColors: true,
        shadeIntensity: 0.8,
        gradientToColors: undefined,
        colorStops: [
          [
            { offset: 0, color: '#33cc44', opacity: 0.5 },
            { offset: 100, color: '#33cc44', opacity: 0.04 },
          ],
          [
            { offset: 0, color: '#ff2222', opacity: 0.04 },
            { offset: 100, color: '#ff2222', opacity: 0.5 },
          ],
        ]
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
    annotations: {
      xaxis: [
        {
          x: xAnnotationOne,
          x2: xAnnotationTwo,
          fillColor: isDark ? 'rgb(255, 255, 255)' :  'rgb(0, 0, 0)',
          opacity: 0.03,
        },
      ],
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
      padding: {
        ignoreBarPad: true,
      },
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

  const chart = new ApexCharts(document.querySelector("#cashflow-chart"), options);
  // Works to ensure the chart is the correct size on load - while preserving the animation
  requestAnimationFrame(() => {
    chart.render().then(() => {
      preserveZeroLabel();
    });
  });

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
