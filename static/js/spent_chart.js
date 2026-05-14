function renderChart(chartID, color, title, amounts, dates, budgetedAmount) {
  const hasBudget = budgetedAmount > 0;
  const maxActual = Math.max(...amounts.filter(a => a > 0), 0);
  const max = hasBudget ? Math.max(maxActual, budgetedAmount) : maxActual;
  const stub = hasBudget ? budgetedAmount * 0.03 : maxActual * 0.03;
  const displayAmounts = amounts.map(a => a === 0 ? stub : a);
  const isStub = amounts.map(a => a === 0);

  var options = {
    series: [{
      name: title,
      data: displayAmounts,
    }],
    chart: {
      height: 250,
      type: 'bar',
      parentHeightOffset: 0,
      toolbar: {
        show: false,
      },
    },
    grid: {
      show: false,
    },
    tooltip: {
      y: {
        formatter: (val, opts) => isStub[opts.dataPointIndex] ? "$0.00" : `$${val.toFixed(2)}`
      },
      theme: 'dark',
    },

    colors:  [
      function(context) {
        if (isStub[context.dataPointIndex]) return color;
        if (!hasBudget) return color;
        return context.value <= budgetedAmount ? color : '#ff0000';
      }
    ],
    plotOptions: {
      bar: {
        minHeight: 10,
        borderRadius: 5,
        dataLabels: {
          position: 'top', // top, center, bottom
        },
      }
    },
    dataLabels: {
      enabled: false,
      formatter: function (val) {
        return "$" + val;
      },
      style: {
        fontSize: '12px',
        colors: ["#304758"]
      }
    },
    annotations: {
      yaxis: hasBudget ? [{
        y: budgetedAmount,
        label: {
          text: `$${budgetedAmount.toFixed(2)}`,
          position: 'left',
          borderWidth: 0,
          style: {
            background: 'transparent',
            color: '#ffffff',
          },
        },
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
          return "$" + val;
        },
      }
    },
  };

  var chart = new ApexCharts(document.querySelector("#chart-" + chartID), options);
  chart.render();
}
