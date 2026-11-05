import { useEffect, useRef } from "react";
import useStore from "../../store";
import Button from "../ui/Button";
import styles from "./Panelbar.module.css";

function PanelToggle({ id }) {
  const visible = useStore((s) =>
    Object.values(s.panels).some((panel) => panel[id]),
  );
  const toggleCard = useStore((s) => s.toggleCard);
  const pending = useRef(null);

  useEffect(() => {
    const action = pending.current;
    if (!action) return;
    pending.current = null;

    if (action === "open" && visible) {
      const el = document.getElementById(id);
      if (!el) return;
      const { top } = el.getBoundingClientRect();
      const offScreen = top < 0 || top > window.innerHeight;
      if (offScreen) {
        el.addEventListener(
          "transitionend",
          () => {
            el.scrollIntoView({ behavior: "smooth", block: "start" });
          },
          { once: true },
        );
      }
    } else if (action === "close" && !visible) {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [visible, id]);

  return (
    <Button
      label={id.charAt(0).toUpperCase() + id.slice(1)}
      variant="toggle"
      active={visible}
      onClick={() => {
        pending.current = visible ? "close" : "open";
        toggleCard(id);
      }}
    />
  );
}

export default function Panelbar() {
  const buttonGroups = [
    ["info", "nodes", "edges"],
    ["upload", "network"],
    ["alignment", "selection", "monomers", "metadata"],
  ];

  return (
    <div id="panel-bar" className={styles.panelbar}>
      <h2>Panels</h2>
      <div className={styles.panelbarButtons}>
        {buttonGroups.map((group, i) => (
          <div key={i} className="toggleButtonArea">
            {group.map((id) => (
              <PanelToggle key={id} id={id} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
