import InfoCard from "@/components/features/info/InfoCard";
import NodeCard from "@/components/features/nodes/NodeCard";
import EdgeCard from "@/components/features/edges/EdgeCard";
import ErrorBoundary from "../components/ErrorBoundary";

export default function LeftPanel() {
  return (
    <div>
      <ErrorBoundary
        fallback={<p>Info panel did not load. Try refreshing page.</p>}
      >
        <InfoCard />
      </ErrorBoundary>

      <ErrorBoundary
        fallback={<p>Node panel did not load. Try refreshing page.</p>}
      >
        <NodeCard />
      </ErrorBoundary>

      <ErrorBoundary
        fallback={<p>Edge panel did not load. Try refreshing page.</p>}
      >
        <EdgeCard />
      </ErrorBoundary>
    </div>
  );
}
