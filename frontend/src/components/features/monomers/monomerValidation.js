const DISALLOWED_TEXT = /[#$%&@!?{}\\|~`"\'<>^,]/;
const DISALLOWED_SMILES = /[^A-Za-z0-9#=\-\(\)\[\]\.@\/\\%\*+~:]/;

const RULES = {
  code: [
    [(v) => DISALLOWED_TEXT.test(v), "Contains a disallowed character"],
    [(v) => /\s/.test(v), "Code can't contain spaces"],
  ],
  name: [[(v) => DISALLOWED_TEXT.test(v), "Contains a disallowed character"]],
  category: [
    [(v) => DISALLOWED_TEXT.test(v), "Contains a disallowed character"],
  ],
  base: [
    [(v) => DISALLOWED_TEXT.test(v), "Contains a disallowed character"],
    [(v) => v.includes("-"), "Base can't contain a hyphen"],
    [(v) => /\s/.test(v), "Code can't contain spaces"],
  ],
  exact: [
    [(v) => DISALLOWED_TEXT.test(v), "Contains a disallowed character"],
    [(v) => /\s/.test(v), "Code can't contain spaces"],
  ],
  smiles: [
    [(v) => DISALLOWED_SMILES.test(v), "SMILES contains invalid charcters"],
  ],
};

export function validateMonomer(draft) {
  const errors = {};
  if (!draft) return errors;

  if (!(draft.code ?? "").trim()) errors.code = "Code is required"; // Sanity check

  for (const [field, checks] of Object.entries(RULES)) {
    if (errors[field]) continue;
    const value = draft[field] ?? "";
    if (!value) continue;
    const failed = checks.find(([test]) => test(value));
    if (failed) errors[field] = failed[1];
  }
  return errors;
}
