export function mergeEditsIntoData(data, edits) {
  const merged = {};
  for (const [key, value] of Object.entries(data ?? {})) {
    merged[key] = edits[value.code]
      ? { ...value, ...edits[value.code] }
      : value;
  }
  return merged;
}

export function mergeEditsIntoList(monomers, edits) {
  return monomers.map((m) => (edits[m.code] ? { ...m, ...edits[m.code] } : m));
}
