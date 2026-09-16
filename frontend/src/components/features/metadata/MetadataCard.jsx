import Card from "@/components/ui/Card";
import useStore from "@/store";
import MetadataGraphs from "./MetadataGraphs";

export default function MetadataCard() {
  const data = useStore((s) => s.data.output.peptides);

  const count = Object.keys(data ?? {}).length;

  return (
    <Card id="metadata" title="Metadata">
      <section className="card">
        {count === 0 && (
          <div>
            <p>Extract monomers or submit job to view metadata</p>
          </div>
        )}
        {count > 0 && (
          <>
            <MetadataGraphs data={data} />
          </>
        )}
      </section>
    </Card>
  );
}
