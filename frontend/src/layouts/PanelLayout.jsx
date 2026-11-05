import styles from "./PanelLayout.module.css";

import LeftPanel from "../panels/LeftPanel";
import MiddlePanel from "../panels/MiddlePanel";
import RightPanel from "../panels/RightPanel";

import useStore from "../store";

import { useState, useRef } from "react";

export default function PanelLayout() {
  const leftVisible = useStore((s) =>
    Object.values(s.panels.left).some(Boolean),
  );
  const rightVisible = useStore((s) =>
    Object.values(s.panels.right).some(Boolean),
  );

  const layoutRef = useRef(null);
  const [widths, setWidths] = useState({ left: 380, right: 380 });
  const resizerWidth = 4;

  const buildColumns = (lv, rv, w) =>
    [
      lv ? `${w.left}px` : "0fr",
      lv ? `${resizerWidth}px` : "0px",
      "1fr",
      rv ? `${resizerWidth}px` : "0px",
      rv ? `${w.right}px` : "0fr",
    ].join(" ");

  const startDrag = (e, side) => {
    e.preventDefault();
    const layout = layoutRef.current;
    if (!layout) return;
    const startX = e.clientX;
    const startWidth = widths[side];

    const onMove = (moveEvent) => {
      const dx = moveEvent.clientX - startX;
      const newWidth =
        side === "left"
          ? Math.min(1280, startWidth + dx)
          : Math.min(1280, startWidth - dx);

      const newWidths = { ...widths, [side]: newWidth };
      layout.style.setProperty(
        "--columns",
        buildColumns(leftVisible, rightVisible, newWidths),
      );
    };

    const onUp = () => {
      const cols = getComputedStyle(layout).gridTemplateColumns.split(" ");
      setWidths({
        left: parseFloat(cols[0]) || widths.left,
        right: parseFloat(cols[4]) || widths.right,
      });
      document.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerup", onUp);
    };

    document.addEventListener("pointermove", onMove);
    document.addEventListener("pointerup", onUp);
  };

  return (
    <div
      className={styles.layout}
      ref={layoutRef}
      style={{
        "--columns": buildColumns(leftVisible, rightVisible, widths),
      }}
    >
      <div className={styles.sidepanel}>
        <LeftPanel />
      </div>

      <div
        className={`${styles.handle} ${!leftVisible ? styles.handleHidden : ""}`}
        onPointerDown={(e) => startDrag(e, "left")}
      />

      <div className={styles.centre}>
        <MiddlePanel />
      </div>

      <div
        className={`${styles.handle} ${!rightVisible ? styles.handleHidden : ""}`}
        onPointerDown={(e) => startDrag(e, "right")}
      />

      <div className={styles.sidepanel}>
        <RightPanel />
      </div>
    </div>
  );
}
