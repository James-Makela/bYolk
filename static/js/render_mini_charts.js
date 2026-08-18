document.querySelectorAll('.mini-chart-card').forEach(card => {
  const targetEl = card.querySelector('.chart-target');
  const chartId = targetEl.dataset.chartId;

  const chartData = JSON.parse(document.getElementById(chartId).textContent);

  renderChart(
    chartId,
    chartData.color,
    chartData.title,
    chartData.amounts,
    chartData.dates,
    chartData.budgeted_amount,
    targetEl.dataset.privacy === 'true',
    targetEl.dataset.theme
  );
});
