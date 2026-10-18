export function createPeptWorkChart(Chart, canvas, type, data, options = {}) {
  const ctx = canvas.getContext("2d");
  const whiteBg = options.whiteBg || false;

  // Theme colors
  const gridColor = whiteBg ? "rgba(0,0,0,0.06)" : "rgba(56,189,248,0.04)";
  const tickColor = whiteBg ? "#6b7280" : "#64748b";
  const borderColor = whiteBg ? "rgba(0,0,0,0.1)" : "rgba(56,189,248,0.08)";
  const tooltipBg = whiteBg ? "#1e293b" : "#0f1729";

  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: true,
    aspectRatio: options.aspectRatio || 2.8,
    animation: { duration: 250 },
    plugins: {
      legend: { display: options.showLegend || false },
      tooltip: {
        backgroundColor: tooltipBg,
        titleFont: { family: "'IBM Plex Mono', monospace", size: 12 },
        bodyFont: { family: "'IBM Plex Mono', monospace", size: 12 },
        borderColor: "rgba(56,189,248,0.25)",
        borderWidth: 1,
        padding: 10,
        cornerRadius: 6,
        titleColor: "#e2e8f0",
        bodyColor: "#94a3b8",
      },
    },
    scales: {
      x: {
        grid: { color: gridColor, drawBorder: false },
        ticks: {
          font: { family: "'IBM Plex Mono', monospace", size: 12 },
          color: tickColor,
        },
        border: { color: borderColor },
      },
      y: {
        beginAtZero: true,
        grid: { color: gridColor, drawBorder: false },
        ticks: {
          font: { family: "'IBM Plex Mono', monospace", size: 12 },
          color: tickColor,
          stepSize: options.yStepSize || 1,
        },
        border: { display: false },
        title: {
          display: !!options.yAxisLabel,
          text: options.yAxisLabel || "",
          font: { family: "'IBM Plex Mono', monospace", size: 12 },
          color: tickColor,
        },
      },
    },
  };

  // Deep merge custom options with defaults
  const mergedOptions = { ...defaultOptions, ...options };

  return new Chart(ctx, { type, data, options: mergedOptions });
}
