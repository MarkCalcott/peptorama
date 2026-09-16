# Pyoverdines

A list of manually curated pyoverdines in which pyoverdine structures have been checked against the corresponding papers. The data is a compilation from existing lists and manual searches. 

## File overview

| File | Description |
|------|-------------|
| `data/pyoverdine_peptide_chains.csv` | One row per pyoverdine peptide chain |
| `data/references.csv` | Full citations for the `reference` column |

## Column descriptions

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `peptide` | string | Amino acid sequence of the peptide chain, N- to C-terminus | `Ala-Lys-Gly-Gly-OH-Asp-...` |
| `species` | string | Producing species as reported in the source | `P. fluorescens` |
| `strain` | string | Strain designation as reported in the source | `ATCC 17400` |
| `group` | integer | Grouping according to [define scheme and cite it] | `1` |
| `class` | string (Roman numeral) | Classification according to [define scheme and cite it] | `II` |
| `reference` | integer | ID of the source publication; see `references.csv` | `3` |

## Peptide notation

See paper for nomenclature.

## References

| ID | Citation | DOI |
|----|----------|-----|
| 1 | Author A. et al. (Year). Title. *Journal*, vol, pages. | 10.xxxx/xxxxx |
| 2 | ... | ... |