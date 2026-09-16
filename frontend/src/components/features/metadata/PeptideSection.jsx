import { useMemo } from "react";
import { PeptWorkChart } from "@/lib/charts/PeptWorkChart";
import { computeFieldChart } from "./metadata";

export default function PeptideSection({ data, fields }) {
  const peptides = useMemo(() => Object.values(data ?? {}), [data]);

  return (
    <>
      Hello
      {fields.map((field) => (
        <IndividualGraph key={field} peptides={peptides} field={field} />
      ))}
    </>
  );
}

function IndividualGraph(peptides, field) {
  const chartData = useMemo(
    () => computeFieldChart(peptides, field),
    [peptides, field],
  );

  return (
    <>
      <PeptWorkChart
        type="bar"
        data={chartData}
        options={{ yAxisLabel: "Peptide count" }}
      />
    </>
  );
}
