function renderChart(chartID, color, title, amounts, dates, budgetedAmount, hideValues = false, theme) {
  const isDark = theme.includes('dark');
  const hasBudget = budgetedAmount > 0;
  const maxActual = Math.max(...amounts.filter(a => a > 0), 0);
  const max = hasBudget ? Math.max(maxActual, budgetedAmount) : maxActual;
  const stub = Math.max(maxActual, budgetedAmount) * 0.02;
  const displayAmounts = amounts.map(a => a === 0 ? stub : a);
  const isStub = amounts.map(a => a === 0);
  const formatCurrency = (val) => {
    if (hideValues) return "$x.xx";
    return typeof val === 'number' ? `$${val.toFixed(2)}` : `$${val}`;
  };

  const options = {
    series: [{
      name: title,
      data: displayAmounts,
    }],
    chart: {
      height: 200,
      width: '100%',
      type: 'bar',
      parentHeightOffset: 0,
      background: 'transparent',
      toolbar: {
        show: false,
      },
    },
    theme: {
      mode: isDark ? 'dark' : 'light',
    },
    grid: {
      show: false,
      padding: {
        left: -10,
        right: 0,
        top: 0,
        bottom: 0,
      },
    },
    tooltip: {
      y: {
        formatter: (val, opts) => isStub[opts.dataPointIndex] ? "$0.00" : formatCurrency(`${val.toFixed(2)}`)
      },
      theme: isDark ? 'dark' : 'light',
    },

    colors:  [
      function(context) {
        const isLast = context.dataPointIndex === context.w.config.series[context.seriesIndex].data.length - 1;

        if (isStub[context.dataPointIndex]) return isLast ? color + '80' : color;
        if (!hasBudget) return isLast ? color + '80' : color;
        return context.value <= budgetedAmount ? (isLast ? color + '80' : color) : (isLast ? '#ff000080' : '#ff0000');
      }
    ],
    plotOptions: {
      bar: {
        minHeight: 10,
        borderRadius: 2,
        dataLabels: {
          position: 'top', // top, center, bottom
        },
      }
    },
    dataLabels: {
      enabled: false,
    },
    annotations: {
      yaxis: hasBudget ? [{
        y: budgetedAmount,
        strokeDashArray: 0,
        borderWidth: 0.5,
        opacity: 0.08,
      }] : [],
    },

    xaxis: {
      categories: dates,
      crosshairs: {
        show: false
      },
      position: 'bottom',
      labels: {
        show: false,
        rotate: 0,
        offsetY: 0,
      },
      lines: {
        show: false
      },
      axisBorder: {
        show: false
      },
      axisTicks: {
        show: false
      },
      tooltip: {
        enabled: false,
        theme: 'dark',
      }
    },
    yaxis: {
      min: 0,
      max: max * 1.1,
      axisBorder: {
        show: false
      },
      lines: {
        show: false
      },
      axisTicks: {
        show: false,
      },
      labels: {
        show: false,
        formatter: function (val) {
          formatCurrency(val);
        },
      }
    },
  };

  setTimeout(() => {
    var chart = new ApexCharts(
      document.querySelector('#chart-' + chartID),
      options
    );
    chart.render();
    ChartManager.register(chart, '#chart-' + chartID);
  }, 0);
}
