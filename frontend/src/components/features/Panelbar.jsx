import useStore from "../../store";
import Button from "../ui/Button";
import styles from "./Panelbar.module.css";

function PanelToggle({ id }) {
  const visible = useStore((s) =>
    Object.values(s.panels).some((panel) => panel[id]),
  );
  const toggleCard = useStore((s) => s.toggleCard);

  return (
    <Button
      label={id.charAt(0).toUpperCase() + id.slice(1)}
      variant="toggle"
      active={visible}
      onClick={() => toggleCard(id)}
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
    <div className={styles.toolbar}>
      <h2>Panels</h2>
      {buttonGroups.map((group, i) => (
        <div key={i} className="toggleButtonArea">
          {group.map((id) => (
            <PanelToggle key={id} id={id} />
          ))}
        </div>
      ))}
    </div>
  );
}
