import { useMemo, useState } from "react";
import { PeptWorkChart } from "@/lib/charts/PeptworkChart";
import { computeChartData } from "./computeChartData";
import Button from "@/components/ui/Button";
import styles from "./Monomers.module.css";

export default function MonomerGraph({ data }) {
  // Chart controls
  const [groupBy, setGroupBy] = useState("base");
  const [splitBy, setSplitBy] = useState("none");
  const [inbuiltVisible, setInbuiltVisible] = useState(true);
  const [userdefinedVisible, setUserdefinedVisible] = useState(true);
  const [unknownVisible, setUnknownVisible] = useState(true);
  const [stereoVisible, setStereoVisible] = useState({
    L: true,
    D: true,
    flat: true,
  });

  const monomers = useMemo(() => Object.values(data ?? {}), [data]);

  const chartData = useMemo(
    () =>
      computeChartData(monomers, {
        groupBy,
        splitBy,
        inbuiltVisible,
        userdefinedVisible,
        unknownVisible,
        stereoVisible,
      }),
    [
      monomers,
      groupBy,
      splitBy,
      inbuiltVisible,
      userdefinedVisible,
      unknownVisible,
      stereoVisible,
    ],
  );

  return (
    <>
      <div className={styles.legendControls}>
        {/* Chart controls */}
        <div className="flexRowMedium">
          <div className="flexRowMedium">
            <span className={styles.toolbarLegend}>GROUP</span>
            <div>
              {["Base", "Exact", "Category"].map((g) => (
                <Button
                  key={g}
                  variant="toggle"
                  active={groupBy === g.toLowerCase()}
                  onClick={() => setGroupBy(g.toLowerCase())}
                >
                  {g}
                </Button>
              ))}
            </div>
          </div>

          <div className="flexRowMedium">
            <span className={styles.toolbarLegend}>SPLIT</span>
            <div>
              {[
                ["none", "Pooled"],
                ["stereochemistry", "Stereo"],
              ].map(([val, label]) => (
                <Button
                  key={val}
                  variant="toggle"
                  active={splitBy === val}
                  onClick={() => setSplitBy(val)}
                >
                  {label}
                </Button>
              ))}
            </div>
          </div>
        </div>

        {/* Legends */}
        {splitBy === "none" && (
          <div className="flexRowMedium">
            <div
              onClick={() => setInbuiltVisible((v) => !v)}
              className={`${styles.legendItem} ${inbuiltVisible ? "" : styles.disabled}`}
            >
              <div
                className={`${styles.legendSwatch} ${styles.swatchCyan}`}
              ></div>
              <span>Inbuilt</span>
            </div>
            <div
              onClick={() => setUserdefinedVisible((v) => !v)}
              className={`${styles.legendItem} ${userdefinedVisible ? "" : styles.disabled}`}
            >
              <div
                className={`${styles.legendSwatch} ${styles.swatchAmber}`}
              ></div>
              <span>User-defined</span>
            </div>
            <div
              onClick={() => setUnknownVisible((v) => !v)}
              className={`${styles.legendItem} ${unknownVisible ? "" : styles.disabled}`}
            >
              <div
                className={`${styles.legendSwatch} ${styles.swatchRed}`}
              ></div>
              <span>Unknown</span>
            </div>
          </div>
        )}
        {splitBy === "stereochemistry" && (
          <div className="flexRowMedium">
            {["L", "D", "flat"].map((ch) => (
              <div
                key={ch}
                className={`${styles.legendItem} ${stereoVisible[ch] ? "" : styles.disabled}`}
                onClick={() =>
                  setStereoVisible((s) => ({ ...s, [ch]: !s[ch] }))
                }
              >
                <div
                  className={`${styles.legendSwatch} ${ch === "L" ? styles.swatchTeal : ch === "D" ? styles.swatchAmber : styles.swatchGrey}`}
                ></div>
                <span>{ch}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Chart (lazy-loads Chart.js, updates in place on data change) */}
      <PeptWorkChart
        type="bar"
        data={chartData}
        options={{ yAxisLabel: "Monomer count" }}
        exportName={`monomer_chart_${groupBy}${splitBy !== "none" ? `_${splitBy}` : ""}`}
      />
    </>
  );
}
