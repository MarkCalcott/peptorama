import { useEffect, useMemo, useState } from "react";
import useStore from "@/store";
import styles from "./Node.module.css";

const PALETTE = [
  "#1f77b4",
  "#ff7f0e",
  "#2ca02c",
  "#d62728",
  "#9467bd",
  "#8c564b",
  "#e377c2",
  "#bcbd22",
  "#17becf",
  "#aec7e8",
  "#ffbb78",
  "#98df8a",
  "#ff9896",
  "#c5b0d5",
  "#c49c94",
  "#f7b6d2",
  "#dbdb8d",
  "#9edae5",
];
const NULL_COLOR = "#7f7f7f";
const OTHER = "(other)";

export default function NodeFunctions({ type }) {
  const cy = useStore((s) => s.cy);
  const peptidesById = useStore((s) => s.peptidesById);

  const [field, setField] = useState("");

  const known_order = useStore((s) => s.data.output.metadata.known_order);
  const predicted_order = useStore(
    (s) => s.data.output.metadata.predicted_order,
  );
  const metadataValues = type === "known" ? known_order : predicted_order;

  const { valueColors, legend } = useMemo(() => {
    if (!field) {
      if (cy) cy.fit();
      return { valueColors: {}, legend: [] };
    }

    const buckets = new Map();
    Object.values(peptidesById)
      .filter((p) => p.origin === type)
      .forEach((p) => {
        const v = p.metadata?.[field];
        const raw = v == null || v === "" ? "NA" : v;
        if (!buckets.has(raw)) buckets.set(raw, []);
        buckets.get(raw).push(p.id);
      });

    const sorted = [...buckets.entries()].sort(
      (a, b) => b[1].length - a[1].length,
    );
    const top = sorted.slice(0, PALETTE.length);
    const rest = sorted.slice(PALETTE.length);

    const colors = {};
    top.forEach(([val], i) => {
      colors[val] = val === "NA" ? NULL_COLOR : PALETTE[i % PALETTE.length];
    });

    const rows = top.map(([value, ids]) => ({
      value,
      count: ids.length,
      color: colors[value],
      ids,
    }));
    if (rest.length) {
      const otherIds = rest.flatMap(([, ids]) => ids);
      colors[OTHER] = NULL_COLOR;
      rows.push({
        value: OTHER,
        count: otherIds.length,
        color: NULL_COLOR,
        ids: otherIds,
      });
    }

    return { valueColors: colors, legend: rows };
  }, [field, peptidesById, type]);

  useEffect(() => {
    if (!cy || cy.destroyed()) return;

    const current = cy
      .nodes()
      .filter((n) => peptidesById[n.id()]?.origin === type);

    if (!field) {
      current.nodes().removeData(`highlightColor`);
      cy.style().update();
      return;
    }

    current.forEach((n) => {
      const raw = peptidesById[n.id()].metadata?.[field] ?? "NA";
      const colorMe = valueColors[raw] !== undefined;
      n.data(`highlightColor`, colorMe ? valueColors[raw] : NULL_COLOR);
    });

    return () => {
      if (!cy.destroyed()) current.nodes().removeData("highlightColor");
    };
  }, [cy, field, valueColors, peptidesById, type]);

  const selectGroup = (ids) => {
    if (!cy || cy.destroyed()) return;

    const group = cy.collection(ids.map((id) => cy.getElementById(id)));
    cy.elements().unselect();
    if (!group.length) return;
    group.select();
    cy.animate(
      { center: { eles: group }, zoom: Math.max(cy.zoom(), 1.2) },
      { duration: 250 },
    );
  };

  return (
    <>
      <h4>Highlight</h4>

      <select
        className="filterSelect"
        id="highlightSelect"
        style={{ width: "100%" }}
        onChange={(e) => {
          setField(e.target.value);
        }}
      >
        <option value="">– None –</option>
        {metadataValues.map((value) => (
          <option key={value} value={value}>
            {value}
          </option>
        ))}
      </select>

      <div className={styles.resultsList}>
        {legend.map(({ value, count, color, ids }) => (
          <div
            key={value}
            className={`flexRowMedium ${styles.searchResult}`}
            onClick={() => selectGroup(ids)}
          >
            <div
              className={styles.legendSwatch}
              style={{ background: color }}
            />
            <div title={value}>{value}</div>
            <div>({count})</div>
          </div>
        ))}
      </div>
    </>
  );
}
