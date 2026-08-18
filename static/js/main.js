window.ChartManager = (function () {
  const chartRegistry = [];

  window.addEventListener('themeChanged', function (e) {
    const isDark = e.detail.theme.includes('dark');

    chartRegistry.forEach(({ chart, containerId, onThemeChange }) => {
      if (!chart) return;

      chart.updateOptions({
        theme: {
          mode: isDark ? 'dark' : 'light',
        },
        grid: {
          borderColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
        },
        fill: {
          gradient: {
            shade: isDark ? 'dark' : 'light',
          },
        },
        tooltip: {
          theme: isDark ? 'dark' : 'light',
        },
      }).then(() => {
        const container = document.querySelector(containerId);
        const tooltip = container ? container.querySelector('.apexcharts-tooltip') : document.querySelector('.apexcharts-tooltip');

        if (tooltip) {
          tooltip.classList.remove('apexcharts-theme-light', 'apexcharts-theme-dark');
          tooltip.classList.add(isDark ? 'apexcharts-theme-dark' : 'apexcharts-theme-light');
        }

        if (typeof onThemeChange === 'function') {
          onThemeChange(isDark);
        }
      });
    });
  });

  return {
    register: function (chartInstance, containerId, onThemeChange = null) {
      chartRegistry.push({
        chart: chartInstance,
        containerId: containerId,
        onThemeChange: onThemeChange
      });
      return chartInstance;
    }
  };
})();
