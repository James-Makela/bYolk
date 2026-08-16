function renderIncomeChart(dates, titles, amounts, totalSpend, hideValues = false) {
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

  series.push({
    name: 'Total Income',
    type: 'area',
    color: '#33cc44',
    data: totalData
  });

  series.push({
    name: 'Total Spend',
    type: 'area',
    color: '#ff2222',
    data: totalSpend
  });

  series.unshift({
    name: 'Cash Flow',
    type: 'column',
    data: delta
  });

  const options = {
    series: series,
    chart: {
      height: 350,
      type: 'line',
      zoom: {
        enabled: false
      },
      toolbar: {
        show: false
      },
      background: 'transparent',
      sparkline: false,
    },
    theme: {
      mode: 'dark'
    },
    stroke: {
      curve: series.map(s => (s.type === 'column' ? 'straight' : 'smooth')),
      width: series.map(s => (s.type === 'column' ? 0 : s.type === 'line' ? 2 : 1))
    },
    fill: {
      opacity: series.map(s => {
        if (s.type === 'line') return 1;
        if (s.type === 'area') return 0.15;
        if (s.type === 'column') return 1;
        return 1;
      })
    },
    plotOptions: {
      bar: {
        columnWidth: '50%',
        colors: {
          ranges: [
            {
              from: -1000000,
              to: -0.01,
              color: '#EF4444'
            },
            {
              from: 0,
              to: 1000000,
              color: '#10B981'
            },
          ]
        }
      }
    },
    dataLabels: {
      enabled: false,
    },
    xaxis: {
      type: 'datetime',
      categories: dates,
    },
    yaxis: {
      labels: {
        formatter: function (val) {
          return formatCurrency(`${val ? Number(val).toFixed(2) : '0.00'}`)
        },
      },
      forceNiceScale: true,
      tickAmount: 10,
      axisTicks: {
        show: true,
        color: 'rgba(255, 255, 255, 0.15)'
      },
      axisBorder: {
        show: true,
        color: 'rgba(255, 255, 255, 0.15)'
      }
    },
    grid: {
      show: true,
      borderColor: 'rgba(255, 255, 255, 0.08)',
      strokeDashArray: 0,
      xaxis: {
        lines: {
          show: true
        }
      },
      yaxis: {
        lines: {
          show: true
        }
      }
    },
    tooltip: {
      x: {
        format: 'dd MMM yyyy',
      },
    },
  };

  var chart = new ApexCharts(document.querySelector("#income-area-chart"), options);
  chart.render();
}
