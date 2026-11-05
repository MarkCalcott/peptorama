import Card from "@/components/ui/Card";
import useStore from "@/store";
import NodeFunctions from "./NodeFunctions";

export default function NodeCard() {
  const data = useStore((s) => s.data.output);

  return (
    <Card id="nodes" title="Nodes">
      {data.metadata.known > 0 && <NodeFunctions type="known" />}
      {data.metadata.known > 0 && data.metadata.predicted > 0 && (
        <>
          <hr />
          <hr />
        </>
      )}

      {data.metadata.predicted > 0 && <NodeFunctions type="predicted" />}

      {data.edges.length === 0 && (
        <p>
          Create a network and then use this panel to highlight and search
          peptides
        </p>
      )}
    </Card>
  );
}
