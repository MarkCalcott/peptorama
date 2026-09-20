# DiscERN: the 30 unknown genomes against the known pyoverdine family

DiscERN 0.1.0, commit `716e932418c30ffda587964b0d1b0edf04ade3d2`, antiSMASH
8.0.4. Run 19 Sep 2026.

    discern -a as30 -r pvd_refs_excl -o discern_k2_g30_new -k 2

    as30/            30 genomes, 424 regions, 424 knownclusterblast tables, 30 JSON
    pvd_refs_excl/   82 reference regions from 44 known-pyoverdine accessions
    discern_k2_g30_new/   this directory

## Correction to what I told you earlier

I said the `knownclusterblast` output DiscERN needs "was never there," and that
DiscERN itself had vanished. **Both were wrong.**

- Your own `run_antismash_all (1).sh` (lines 29 and 114) shows the original runs
  used `--taxon bacteria --cb-knownclusters --cb-subclusters`. The output was
  produced and then discarded by the trim-to-BiG-SCAPE-input step. It was
  regenerable from the whole-genome GenBanks you already had, which is what was
  done here — `--genefinding-tool none`, no re-annotation.
- DiscERN is at `github.com/MaxMeta/DiscERN`, per the paper's code-availability
  statement. The organisation recorded in my own provenance manifest does not
  exist on GitHub; I reported its 404 as the tool being gone instead of checking
  the publication. HEAD of the real repository is the same commit the manifest
  pinned, so the code is identical to the earlier run. It is now archived as an
  artifact.

## Inputs

**Queries.** antiSMASH 8.0.4 re-run on the 30 whole-genome GenBanks in
`Benchmarking/antismash/unknown pyoverdines raw antismash/`, with the study's
original flags. 30 genomes, 424 regions, **424 knownclusterblast tables, 30
JSON — no genome incomplete.** This also restores the `monomer_pairings` the
unknown arm was missing.

**References.** `pvd_refs` filtered to drop the excluded accessions, leaving
**82 regions from 44 accessions** — the same 44 known genomes as the BiG-SCAPE
run, so the two analyses cover identical genome sets.

Dropped: `LT629746`, `CP176771`, `GCA_000730605`, `AP039450`, `CP028517`,
`CP023269` (your six), plus `CP034337` (sp. IB3) on the earlier standing
instruction about declared surrogates. Each was verified absent by prefix match.
`.gbk`/`.txt` counts balanced at 82/82 — unbalanced counts make DiscERN print a
message and **exit 0 having done nothing**.

## Result

Both algorithms had data, and both thresholds were optimised on the reference
set rather than assumed:

| algorithm | cutoff | MCC | precision | recall |
|---|---|---|---|---|
| Pfam vector (bs) | 0.4331 | 0.943 | 0.951 | 0.939 |
| clusterblast (cb) | 0.9980 | 1.000 | 1.000 | 1.000 |

| | regions | genomes |
|---|---|---|
| clusterblast (cb) | 102 | 26 |
| Pfam vector (bs) | 43 | 22 |
| **k=2 (both agree)** | **43** | **22** |
| k=1 (one only) | 59 | 26 |

`bs` is a **strict subset** of `cb`, so the high-confidence set is set entirely
by the Pfam-vector algorithm; clusterblast adds no k=2 region of its own. Note
that `k` means "in exactly n algorithm sets", so k=1 is the symmetric
difference, not a weaker superset.

The note-1 sanity check passes: `newick_tree.txt` holds **125 leaves = 82
references + 43 hits**. A tree with only the 82 would mean the run had silently
found nothing.

### The cross-check that matters

The k=2 call was compared against the independent protein-level evidence —
`pvdA`, `pvdI/J/D`, and the chromophore pathway, from a different method with no
input in common beyond the genomes:

| protein-level call | k=2 | k=1 only | no hit |
|---|---|---|---|
| pyoverdine-positive (24) | **22** | 2 | 0 |
| pyoverdine-negative (6) | **0** | 2 | 4 |

**28 of 30 agree, and no pyoverdine-negative genome reaches a high-confidence
hit.** Two of the six negatives do surface at k=1, on clusterblast alone —
consistent with them carrying other siderophore and NRPS loci that share
architecture with pyoverdine without being pyoverdine.

The two positives that fall short of k=2, `OW_2_w_a` (3 k=1 regions) and
`OW_3_w_b` (4), are not negatives: they hit on clusterblast and miss only the
Pfam-vector threshold. They are the genomes to look at by hand.

`SN_3_w_a` has the most k=2 hits of any genome (4), which is what the
two-organisms-in-one-file finding predicts.

## Four reference regions errored

```
ERR13305467__305467_32.region001   OV986001__OV986001.1.region011
NZ_LT629699__NZ_LT629699.1.region015   ERR13305469__305469_8.region001
```

Traced rather than ignored: the message comes from
`find_conserved_features_in_ref_set` (`funcs_2.py:672`), which does
`mibig_counts[bgc]` inside a bare `try/except` and prints on `KeyError`. So
these four are missing from the feature-count dictionary and therefore did not
contribute to the **conserved-feature filter**. All four parse cleanly, carry
CDS with translations and a region feature, and have populated clusterblast
tables (16–28 hits), so the cause is not malformed input.

What this does and does not mean: conserved features are the minimum counts
across the reference set, so dropping references can only make that filter
equally or more strict — it cannot have manufactured hits. The reference
diagnostics (`bigslice_vec_check.json`, `blast_vec_check.json`) do report
reference outliers and a max distance from centroid, so references were used in
the vector stage. **I did not trace whether these four also dropped out of the
centroid computation**, so treat the conserved-feature filter as computed from
78 of 82 references rather than all 82.

## Why the queries are full regions, not the trimmed BGCs

The BiG-SCAPE run used one concatenated record per genome. That is not usable
here, for two reasons: knownclusterblast tables are written per region and keyed
to region filenames, so a concatenated record has no matching table; and
trimming drops flanking genes that the Pfam-vector and clusterblast comparisons
both read. DiscERN's natural unit is the region, and it reports per-region hits.
Results are therefore aggregated to one row per genome in
`discern_unknown_vs_known.tsv` — one comparable number per genome, without
feeding the tool an input that would invalidate its own evidence.

## Limitations

- **Region-level, not structure-level.** A k=2 hit says the region resembles the
  known pyoverdine family in Pfam content and gene homology. It is not a
  peptide prediction and not a structure match.
- **Only two of four algorithms are active.** The polymer and overlap sets
  initialise empty without `--poly_search`, so `ol_hits.json` is empty by
  construction, not by result. `-k 2` is therefore the maximum attainable k; the
  k=3 and k=4 buckets are empty for the same reason and mean nothing here.
- **The conserved-feature filter used 78 of 82 references**, as above.
- **Thresholds are fitted to this reference set.** The bs cutoff (0.4331) sits
  just below the largest reference-to-centroid distance (0.4773), so the family
  boundary is tight against its own outlier, `PHHD01000001` region012.
- **`--resmash` was not run.** It re-annotates hits and was not needed for a
  hit list.

## Reproducing

    # 1. antiSMASH: regenerate knownclusterblast + JSON (no re-annotation)
    bash run_antismash_30.sh            # 30 genomes, ~70 s each, 3 at a time

    # 2. references: filter pvd_refs to the 44 retained accessions
    #    (flat directory, equal .gbk/.txt counts - both are load-bearing)

    # 3. DiscERN
    export PYTHONPATH=discern_src
    python -c "from discern.discern import main; main()" \
        -a as30 -r pvd_refs_excl -o discern_k2_g30_new -k 2

Prerequisites that each failed loudly during setup: `PYTHONPATH` must point at a
**writable** copy of the antismash package (it caches pressed HMMs inside its
own tree); `hmmpfam2` must be on `PATH` and ships in the **discern** env, not
the antismash one; the BiG-SLiCE models must sit at
`discern_src/discern/bigslice_models` (no flag relocates them) and their md5
matches the published `aaabde911ec107d08e5c24f68aaf31d1`; and `discern.py` needs
`discern_ref_dir_patch.diff` to accept `-r <directory>` at all.
