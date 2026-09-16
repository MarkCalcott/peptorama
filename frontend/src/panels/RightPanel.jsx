import Card from "../components/ui/Card";
import MonomersCard from "@/components/features/monomers/MonomersCard";
import MetadataCard from "@/components/features/metadata/MetadataCard";
import AlignmentCard from "@/components/features/alignment/AlignmentCard";
import SelectionCard from "@/components/features/selection/SelectionCard";

export default function RightPanel() {
  return (
    <div>
      <AlignmentCard />

      <SelectionCard />

      <MonomersCard />

      <MetadataCard />
    </div>
  );
}
