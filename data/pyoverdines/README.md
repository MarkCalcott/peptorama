# Pyoverdines

A list of manually curated pyoverdines in which pyoverdine structures have been checked against the corresponding papers. The data is a compilation from existing lists and manual searches. It represents the known peptides when we compared known with unknown pyovedines.

## File overview

| File                            | Description                               |
| ------------------------------- | ----------------------------------------- |
| `pyoverdine_peptide_chains.csv` | One row per pyoverdine peptide chain      |
| `references.md`                | Full citations for the `reference` column |

## Column descriptions

| Column      | Type                   | Description                                                                                                                                                                                                                     | Example                      |
| ----------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `peptide`   | string                 | Amino acid sequence of the peptide chain, N- to C-terminus                                                                                                                                                                      | `Ala-Lys-Gly-Gly-OH-Asp-...` |
| `species`   | string                 | Producing species as reported in the source                                                                                                                                                                                     | `P. fluorescens`             |
| `strain`    | string                 | Strain designation as reported in the source                                                                                                                                                                                    | `ATCC 17400`                 |
| `group`     | integer                | Grouping according to ref 1. Pyoverdines with a cylcic terminal homoserine (Hse) residue have been added to group 1, and pyoverdines with intramolecular cyclisation with a ornithine (Orn) residue have been added to group 2. | `1`                          |
| `class`     | string (Roman numeral) | Classification according to ref 2                                                                                                                                                                                               | `II`                         |
| `reference` | integer                | ID of the source publication; see `references.csv`                                                                                                                                                                              | `3`                          |

## Peptide notation

See paper for nomenclature.

## References

| ID  | Citation                                                                                                                                                          | DOI                               |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| 1   | Fuchs, R., Schäfer, M., Geoffroy, V. & Meyer, J. M. (2001). Siderotyping - a powerful tool for the characterization of pyoverdines. _Curr Top Med Chem_ 1: 31-57. | 10.2174/1568026013395542          |
| 2   | Cézard, C., Farvacques, N., & Sonnet, P. (2015). Chemistry and biology of pyoverdines, Pseudomonas primary siderophores. _Curr Med Chem_, 22(2): 165-186.         | 10.2174/0929867321666141011194624 |
