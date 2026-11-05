import MonomersCard from "@/components/features/monomers/MonomersCard";
import MetadataCard from "@/components/features/metadata/MetadataCard";
import AlignmentCard from "@/components/features/alignment/AlignmentCard";
import SelectionCard from "@/components/features/selection/SelectionCard";
import ErrorBoundary from "../components/ErrorBoundary";

export default function RightPanel() {
  return (
    <div>
      <ErrorBoundary
        fallback={<p>Alignment panel did not load. Try refreshing page.</p>}
      >
        <AlignmentCard />
      </ErrorBoundary>

      <ErrorBoundary
        fallback={<p>Selection panel did not load. Try refreshing page.</p>}
      >
        <SelectionCard />
      </ErrorBoundary>
      <ErrorBoundary
        fallback={<p>Monomers panel did not load. Try refreshing page.</p>}
      >
        <MonomersCard />
      </ErrorBoundary>

      <ErrorBoundary
        fallback={<p>Metadata panel did not load. Try refreshing page.</p>}
      >
        <MetadataCard />
      </ErrorBoundary>
    </div>
  );
}
