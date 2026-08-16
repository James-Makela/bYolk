function renderChart(labels, series, colors, hideValues) {
  const formatCurrency = (val) => {
    if (hideValues) return "$x.xx";
    return typeof val === 'number' ? `$${val.toFixed(2)}` : `$${val}`;
  };
  const options = {
    chart: {
      type: 'pie',
      width: '90%',
      height: '90%',
      background: 'transparent',
      parentHeightOffset: 0
    },
    series: series,
    labels: labels,
    colors: colors,
    dataLabels: {
      enabled: false,
      formatter: function(val) {
        return `${val.toFixed(1)}%`;
      }
    },
    legend: {
      enabled: true
    },
    stroke: {
      width: 1,
      colors: ['#000000']
    },
    theme: {
      mode: 'dark'
    },
    plotOptions: {
      pie: {
        dataLabels: {
          external: {
            show: true,
            formatter: function(name, opts) {
              const amount = opts.w.globals.series[opts.seriesIndex];
              return `${name}: ${formatCurrency(amount.toFixed(2))}`;
            }
          }
        }
      }
    },
    tooltip: {
      theme: 'dark',
      fillSeriesColor: false,
      style: {
        fontSize: '13px',
        fontFamily: 'inherit'
      },
      onDatasetHover: {
        highlightDataSeries: true
      },
      marker: {
        show: true
      },
      y: {
        title: {
          formatter: (seriesName) => `${seriesName}:`
        },
        formatter: function (val, opts) {
          const seriesArr = opts && opts.w ? opts.w.config.series : series;
          const total = seriesArr.reduce((a, b) => a + b, 0);
          const percent = total > 0 ? ((val / total) * 100).toFixed(2) : '0.00';

          return `$${formatCurrency(val.toFixed(2))} (${percent}%)`;
        }
      }
    }
  };

  var chart = new ApexCharts(document.querySelector("#category-pie-chart"), options);
  chart.render();
}
