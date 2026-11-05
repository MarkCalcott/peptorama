import Card from "@/components/ui/Card";
import { MoleculeView } from "./MoleculeView";
import useStore from "@/store";
import { useMemo } from "react";
import styles from "./Selection.module.css";

export default function SelectionCard() {
  const selection = useStore((s) => s.selection);

  const handleSelection = useMemo(() => {
    if (!selection.element) return "Click nodes or edges to select";

    const nodeList =
      selection.element === "node"
        ? [selection.selected]
        : [selection.nodeNeighbours, selection.edgeNeighbours];

    const sliceLength = 10;
    const connectedNodes =
      selection.element === "node"
        ? selection.nodeNeighbours.slice(0, sliceLength)
        : [];

    return (
      <>
        {nodeList.map((node, idx) => {
          const selectedNode = useStore.getState().peptidesById[node];
          const metadataOrder =
            selectedNode.origin === "known"
              ? useStore.getState().data.output.metadata.known_order
              : useStore.getState().data.output.metadata.predicted_order;
          node;
          return (
            <div key={idx}>
              {idx > 0 && <hr />}
              <div className="flexRow">
                <h3>
                  {selectedNode.number}. {selectedNode.name}
                </h3>
                <div className="alignRight">
                  {selectedNode.origin === "known"
                    ? "Known peptide"
                    : "Predicted peptide"}
                </div>
              </div>
              <div className={styles.peptideRow}>
                <div>
                  {metadataOrder.map((key, idx) => (
                    <p key={idx}>
                      <strong>{key}</strong>: {selectedNode.metadata[key]}
                    </p>
                  ))}
                </div>
                {selectedNode.smiles && (
                  <MoleculeView smiles={selectedNode.smiles} />
                )}
              </div>
            </div>
          );
        })}
        <hr />
        {connectedNodes.length > 0 && (
          <div>
            <h4>Compounds from connected nodes</h4>
          </div>
        )}
        <div className={styles.connectedNodes}>
          {connectedNodes.map((node, idx) => {
            const selectedNode = useStore.getState().peptidesById[node];
            return (
              <div key={idx}>
                {selectedNode.smiles && (
                  <div>
                    <h5>
                      {selectedNode.number}. {selectedNode.name}
                    </h5>
                    <MoleculeView smiles={selectedNode.smiles} />
                  </div>
                )}
              </div>
            );
          })}
          {selection.nodeNeighbours.length > sliceLength && (
            <div className={styles.truncated}>
              Results truncated: Too many connected nodes
            </div>
          )}
        </div>
      </>
    );
  }, [selection]);

  return (
    <Card id="selection" title="Selection">
      {handleSelection}
    </Card>
  );
}
