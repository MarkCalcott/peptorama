# Why these 6 genomes are excluded from the analyses

**Six accessions are excluded, and they are the six specified:**
`LT629746`, `CP176771`, `GCA_000730605`, `AP039450`, `CP028517`, `CP023269`.

`CP034337` (*Pseudomonas* sp. IB3) and `CP011835` (*Azomonas macrocytogenes*)
are **analysed, not excluded**. The former is a declared surrogate genome,
which warrants caution in interpreting its structure comparison but is not a
reason to withhold it from clustering. The latter has no pyoverdine locus and
is represented by its azotobactin cluster, which shares the pyoverdine
chromophore, entering the comparison as a near-miss outgroup.

Evidence drawn from `pyoverdine_paper_provenance.tsv` and
`pyoverdine_structure_comparison.tsv`. Per-accession detail with every field
is in `why_excluded_6.tsv` beside this note.

**The prediction is not what failed in any of these six.** The structure
in the workbook is real and comes from a paper; the *genome* attached to it
belongs to a different strain. So the row pairs a published structure with a
different organism's BGC, and a disagreement between them measures a curation
defect, not the accuracy of BGC-based structure prediction. Scoring the
benchmark on those rows would penalise the method for something the method
did not do.

The records are staged in `bigscape/excluded/` and
`discern/known_excluded/` so this can be checked rather than taken on trust.

## Four surrogate genomes — the cited genome is a different strain

| accession | structure measured in | genome actually is | marker identity | resolved identity |
|---|---|---|---|---|
| `LT629746` | *Pseudomonas* sp. 3D19 | *P. lini* BS3782 | 97.76 % | 14.3 % |
| `CP176771` | *Pseudomonas* sp. 6.10 | *Pseudomonas* sp. MPB23 | 91.69 / 99.38 % | 18.2 % |
| `AP039450` | *Pseudomonas* sp. LBSA1 | *P. allii* To-1 | 99.5 % | 30.0 % |
| `CP028517` | *P. fluorescens* PL7 | *P. fluorescens* PsChi | 99.12 % | 37.5 % |

None of these four is flagged as a surrogate in the workbook. The
substitution was found by checking each accession's organism against the
strain its paper names. (`CP034337`, which the workbook *does* flag, is not
excluded — see above.)

Marker-gene identity of 91–99.5 % is species-level or close, but it is not the
same strain, and pyoverdine peptide chains differ between strains of one
species. `AP039450` at 99.5 % and `CP028517` at 99.12 % still disagree, which
is the point: high marker identity does not license substituting a genome.

## One unexplained strain mismatch

`CP023269` — the paper measured *P. putida* 9AW / 9BW; the accession is
*Pseudomonas* sp. MYb193. Resolved identity 42.9 %. The workbook's own curator
note on this row reads "Different pyoverdine".

## One unresolved, and fragmented as well

`GCA_000730605` — the paper measured *P. monteilii* Lille 1; the accession
resolves to *P. monteilii* NBRC 103158. Its locus is also split across contig
edges, so the prediction is inconclusive independently of the strain question
(7 residues predicted against 9 curated, 25.0 % resolved identity).
