import Button from "@/components/ui/Button";
import styles from "./Network.module.css";
import useStore from "@/store";

export default function NetworkBar() {
  const cy = useStore((s) => s.cy);
  const saveNetwork = useStore((s) => s.saveNetwork);

  const predicted = useStore((s) => s.data.output.metadata.predicted);
  const known = useStore((s) => s.data.output.metadata.known);

  const handleZoom = (level) => {
    const selected = cy.$(":selected");
    const target = selected.nonempty() ? selected : undefined;
    cy.animate({ center: { eles: target }, zoom: level }, { duration: 250 });
  };

  const downloadPNG = () => {
    if (!cy) return;

    const blob = cy.png({ output: "blob", full: false, scale: 2, bg: "#FFF" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "network.png";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={styles.toolbar}>
      <div className="buttonArea">
        <Button
          onClick={() => cy.layout({ name: "cose" }).run().fit(undefined, 40)}
          variant="primary"
          tooltip="Redraws the network based on current clusters"
        >
          Redraw
        </Button>
      </div>
      <div className="buttonArea">
        <Button
          onClick={() => cy.fit(undefined, 40)}
          variant="zoom"
          tooltip="Refits the cluster to the canvas"
        >
          Fit
        </Button>
        <Button onClick={() => handleZoom(2)} tooltip="Zoom 2X">
          2X
        </Button>
        <Button onClick={() => handleZoom(5)} tooltip="Zoom 5X">
          5X
        </Button>
      </div>
      <div className="buttonArea">
        <Button onClick={downloadPNG} tooltip="Save the current view to PNG">
          ↓ PNG
        </Button>
        <Button
          onClick={() => saveNetwork()}
          tooltip="Save the data to recreate the network"
        >
          ↓ Save
        </Button>
      </div>
      <div className="flexRowMedium alignRight">
        {known > 0 && (
          <div className="flexRowSmall">
            <div className={styles.knownSwatch}></div>
            <div>Known peptides ({known})</div>
          </div>
        )}
        {predicted > 0 && (
          <div className="flexRowSmall">
            <div className={styles.predictedSwatch}></div>
            <div>Predicted peptides: ({predicted})</div>
          </div>
        )}
      </div>
    </div>
  );
}
