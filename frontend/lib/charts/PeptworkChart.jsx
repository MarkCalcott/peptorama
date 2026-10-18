import { useEffect, useRef, useState } from "react";
import { useChartJs } from "./useChartJs";
import { createPeptWorkChart } from "./createPeptWorkChart";
import Button from "@/components/ui/Button";
import styles from "./PeptworkChart.module.css";

function download(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function toCsv(data) {
  const header = ["Label", ...data.datasets.map((ds) => ds.label ?? "")];
  const rows = data.labels.map((l, i) => [
    l,
    ...data.datasets.map((ds) => ds.data[i] ?? ""),
  ]);
  return [header, ...rows]
    .map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(","))
    .join("\n");
}

export function PeptWorkChart({
  type = "bar",
  data,
  options = {},
  exportName = "chart",
  toolbar = true,
  whiteBg: whiteBgProp,
  onWhiteBgChange,
}) {
  const { Chart, error } = useChartJs();
  const canvasRef = useRef(null);
  const instanceRef = useRef(null);

  const [whiteBgState, setWhiteBgState] = useState(false);
  const whiteBg = whiteBgProp ?? whiteBgState;
  const setWhiteBg = (v) => {
    if (whiteBgProp === undefined) setWhiteBgState(v);
    onWhiteBgChange?.(v);
  };

  const mergedOptions = { ...options, whiteBg };
  const optionsKey = JSON.stringify(mergedOptions);

  useEffect(() => {
    if (!Chart || !canvasRef.current) return;
    instanceRef.current = createPeptWorkChart(
      Chart,
      canvasRef.current,
      type,
      data,
      mergedOptions,
    );
    return () => {
      instanceRef.current?.destroy();
      instanceRef.current = null;
    };
  }, [Chart, type, optionsKey]); // Linter gets a warning, optionsKey contains mergedOptions and don't want redraw on data change

  useEffect(() => {
    const chart = instanceRef.current;
    if (!chart) return;
    chart.data = data;
    chart.update();
  }, [data]);

  function downloadPng() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    const scale = 1;
    const tc = document.createElement("canvas");
    tc.width = w * scale;
    tc.height = h * scale;
    const cx = tc.getContext("2d");
    cx.fillStyle = whiteBg ? "#ffffff" : "#0b1120";
    cx.fillRect(0, 0, tc.width, tc.height);
    cx.drawImage(canvas, 0, 0, tc.width, tc.height);
    const a = document.createElement("a");
    a.href = tc.toDataURL("image/png");
    a.download = `${exportName}.png`;
    a.click();
  }

  if (error) {
    return <div className="chart-error">Couldn’t load the chart library.</div>;
  }

  return (
    <div className={`${styles.peptworkChart} ${whiteBg ? styles.whiteBg : ""}`}>
      {toolbar && (
        <div className={styles.chartToolbar}>
          <div className="buttonArea">
            <label className={styles.switch}>
              <input
                type="checkbox"
                checked={whiteBg}
                onChange={(e) => setWhiteBg(e.target.checked)}
              />
              <span className={styles.slider}></span>
            </label>
            <span className={styles.switchLabel}>White background</span>
          </div>
          <div className="buttonArea">
            <Button
              variant="chart"
              onClick={() =>
                download(`${exportName}.csv`, toCsv(data), "text/csv")
              }
            >
              ↓ CSV
            </Button>
            <Button variant="chart" onClick={downloadPng}>
              ↓ PNG
            </Button>
          </div>
        </div>
      )}

      <div className={styles.chartCanvasWrap}>
        {!Chart && <div className="chart-loading">Loading chart…</div>}
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
}
