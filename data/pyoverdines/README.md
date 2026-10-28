# Pyoverdines

Lists of pyoverdine peptide chains and genomic sequences used in the study. The
sidereophore example of Peptorama can be recreated by uploading
`pyoverdine_known_cluster.csv` and `antiSMASH_predicted_peptides.csv` to the
known and unknown sections of the upload panel, respectively.

## File overview

| File                               | Description                                                                                        |
| ---------------------------------- | -------------------------------------------------------------------------------------------------- |
| `antiSMASH_predicted_peptides.csv` | Peptides predicted using antiSMASH from 30 environmentally isolated bacteria. One peptide per row. |
| `pyoverdine_known_cluster.csv`     | Genomes that match known pyoverdines. One genome per row.                                          |
| `pyoverdine_peptide_chains.csv`    | One row per pyoverdine peptide chain. See https://github.com/MarkCalcott/pyoverdine_review         |

## Column descriptions

### For `antiSMASH_predicted_peptides.csv`

| Column    | Type   | Description                                                                                                                                | Example                                     |
| --------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------- |
| `peptide` | string | The sequence of the peptide chain predicted from analysis of the antiSMASH results                                                         | `D-Ser-L-Lys-L-Xxx-L-Ser-L-Orn-D-Ser-L-Xxx` |
| `genome`  | string | Name of the environmental isolate.                                                                                                         | `KP_3_w_a`                                  |
| `region`  | string | Region, defined in antiSMASH, in which the peptide was found. Numeric except letter codes, `a` and `b`, added for manually split peptides. | `4a`                                        |

### For `pyoverdine_known_cluster.csv`

| Column         | Type   | Description                                                                                  | Example                                                         |
| -------------- | ------ | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `strain`       | string | Species for which the known pyoverdine comes from.                                           | `P. protegens Pf-5`                                             |
| `genome match` | string | Yes if the genome matches the strain. Otherwise the strain for which the genome was sourced. | `yes`                                                           |
| `genome`       | string | GenBank accession number for the genome.                                                     | `CP000076`                                                      |
| `peptide`      | string | The sequence of the peptide chain for the known pyoverdine                                   | `L-Asp-D-Fo-OH-Orn-L-Lys-(L-Thr-L-Ala-D-Ala-D-Fo-OH-Orn-L-Lys)` |
| `predicted`    | string | The sequence of the peptide chain predicted from analysis of the antiSMASH results           | `L-Asp-D-Fo-OH-Orn-L-Lys-L-Thr-L-Ala-D-Ala-D-Fo-OH-Orn-L-Lys`   |
