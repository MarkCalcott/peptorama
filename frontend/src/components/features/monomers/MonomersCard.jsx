import MonomerGraph from "./MonomerGraph";
import MonomerTable from "./MonomerTable";
import Card from "@/components/ui/Card";
import useStore from "@/store";

export default function MonomersCard() {
  const data = useStore((s) => s.data.input.monomers);
  const setMonomers = useStore((s) => s.setMonomers);
  const count = Object.keys(data ?? {}).length;

  return (
    <Card id="monomers" title="Monomers">
      <section className="card">
        {count === 0 && (
          <div>
            <p>Extract monomers or submit job to view monomers</p>
          </div>
        )}
        {count > 0 && (
          <>
            <MonomerGraph data={data} />
            <hr />
            <MonomerTable data={data} onApply={setMonomers} />
          </>
        )}
      </section>
    </Card>
  );
}
