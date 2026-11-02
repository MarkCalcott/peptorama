import { PeptWorkChart } from "@/lib/charts/PeptworkChart";

export default function IndividualGraph({ field, data }) {
  return (
    <PeptWorkChart
      key={field}
      type="bar"
      data={data}
      exportName={field}
      options={{
        yAxisLabel: "Peptide count",
        backgroundColor: "rgba(56,189,248, 1)",
        borderColor: "#38bdf8",
      }}
    />
  );
}
