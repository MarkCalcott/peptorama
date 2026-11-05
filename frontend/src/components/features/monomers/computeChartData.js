const STEREO_COLORS = { L: "#2dd4bf", D: "#fb923c", flat: "#64748b" };

const isInbuilt = (m) => m.known === "Inbuilt";
const isUserDefined = (m) => m.known === "User-defined";
const isUnknown = (m) => !isInbuilt(m) && !isUserDefined(m);

function getGroupKey(m, groupBy) {
  if (groupBy === "exact") return m.exact;
  if (groupBy === "category") return m.category || "Uncategorized";
  return m.base || m.exact;
}

export function computeChartData(monomers, opts) {
  const {
    groupBy,
    splitBy,
    inbuiltVisible,
    userdefinedVisible,
    unknownVisible,
    stereoVisible,
  } = opts;

  if (splitBy === "none") {
    const groups = {};
    monomers.forEach((m) => {
      if (isInbuilt(m) && !inbuiltVisible) return;
      if (isUserDefined(m) && !userdefinedVisible) return;
      if (isUnknown(m) && !unknownVisible) return;
      const k = getGroupKey(m, groupBy);
      groups[k] = (groups[k] || 0) + m.count;
    });
    const sorted = Object.entries(groups).sort((a, b) => b[1] - a[1]);

    const groupStatus = (groupKey) => {
      const gm = monomers.filter((m) => getGroupKey(m, groupBy) === groupKey);
      if (gm.some(isUnknown)) return "unknown";
      if (gm.some(isUserDefined)) return "user-defined";
      return "inbuilt";
    };
    const colorFor = (status) =>
      status === "unknown"
        ? "rgba(248,113,113,1)"
        : status === "user-defined"
          ? "rgba(245,158,11,1)"
          : "rgba(56,189,248,1)";

    return {
      labels: sorted.map((e) => e[0]),
      datasets: [
        {
          label: "Count",
          data: sorted.map((e) => e[1]),
          backgroundColor: sorted.map((e) => colorFor(groupStatus(e[0]))),
          borderColor: sorted.map((e) => colorFor(groupStatus(e[0]))),
          borderWidth: 1,
          borderRadius: 3,
          barPercentage: 0.7,
        },
      ],
    };
  }
  const groups = {};
  monomers.forEach((m) => {
    const k = getGroupKey(m, groupBy);
    if (!groups[k]) groups[k] = { L: 0, D: 0, flat: 0 };
    groups[k][m.stereochemistry || "flat"] += m.count;
  });
  const sorted = Object.entries(groups).sort(
    (a, b) => b[1].L + b[1].D + b[1].flat - (a[1].L + a[1].D + a[1].flat),
  );
  const datasets = [];
  ["L", "D", "flat"].forEach((s) => {
    if (stereoVisible[s]) {
      datasets.push({
        label: s === "flat" ? "Flat" : s,
        data: sorted.map((e) => e[1][s]),
        backgroundColor: STEREO_COLORS[s],
        borderColor: STEREO_COLORS[s],
        borderWidth: 1,
        borderRadius: 3,
        barPercentage: 0.8,
        categoryPercentage: 0.7,
      });
    }
  });
  return { labels: sorted.map((e) => e[0]), datasets };
}
