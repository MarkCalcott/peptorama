import { useEffect, useState } from "react";

let chartPromise = null;
function loadChart() {
  if (!chartPromise) {
    chartPromise = import("chart.js/auto").then((m) => m.default ?? m.Chart);
  }
  return chartPromise;
}

export function useChartJs() {
  const [Chart, setChart] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    loadChart()
      .then((C) => active && setChart(() => C))
      .catch((e) => active && setError(e));
    return () => {
      active = false;
    };
  }, []);

  return { Chart, error };
}
