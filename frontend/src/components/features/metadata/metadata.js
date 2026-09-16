export function computeFieldChart(
  peptides,
  fields,
  subset,
  subsetField = "origin",
) {
  const peptideSubset = peptides.filter((p) => p?.[subsetField] === subset);

  // Fix to return a dicitionary with correct fields
  // Fix to ensure labels and values match

  return Object.fromEntries(
    fields.map((field) => {
      const counts = {};
      for (const p of peptideSubset) {
        const value = String(p["metadata"][field]);
        counts[value] = (counts[value] ?? 0) + 1;
      }
      const entries = Object.entries(counts);
      const chartFormat = {
        labels: entries.map(([label]) => label),
        datasets: [{ label: field, data: entries.map(([, count]) => count) }],
      };
      return [field, chartFormat];
    }),
  );
}
