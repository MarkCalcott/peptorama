import InfoCard from "@/components/features/info/InfoCard";
import NodeCard from "@/components/features/nodes/NodeCard";
import EdgeCard from "@/components/features/edges/EdgeCard";

export default function LeftPanel() {
  return (
    <div>
      <InfoCard />

      <NodeCard />

      <EdgeCard />
    </div>
  );
}
