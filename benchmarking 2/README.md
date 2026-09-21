# Pyoverdine BGC benchmarking

Biosynthetic gene clusters from genomes with experimentally characterised
pyoverdines (**known**) are compared against those from isolate genomes whose
pyoverdines are predicted from sequence only (**predicted**), using BiG-SCAPE
and DiscERN. This folder contains the inputs, the code and the results.

## Data

**Known arm — 52 genomes.** Seventeen were assembled from Illumina reads
deposited in ENA under study accession `PRJEB76792`; thirty-five were obtained
from NCBI under the accessions listed in `benchmark_input_manifest.tsv`. Each
has a published pyoverdine structure, which is the ground truth the benchmark
measures against.

**Predicted arm — 30 genomes.** Unpublished *Pseudomonas* and related isolates.
No public accessions exist for these; they are primary data for this study.

## What was done

**1. Annotation.** The predicted genomes were annotated with Bakta 1.12.0; the
seventeen assembled known genomes with Prokka 1.15.6. The thirty-five NCBI
genomes were supplied as sequence and gene-called by antiSMASH. All three
routes use Prodigal 2.6, so coding-sequence coordinates are comparable
throughout. Assembly and annotation are described in the Methods.

**2. Cluster detection.** antiSMASH 8.0.4 was run on all 82 genomes with
identical settings (`--genefinding-tool none --cb-knownclusters
--cb-subclusters`), yielding 1,186 regions: 762 from the known arm and 424
from the predicted arm. `--genefinding-tool none` preserves the gene calls
from step 1.

**3. Benchmark inputs.** For each genome, regions were scored for pyoverdine
chromophore markers and every NRPS was compared by BLASTP against the
*P. aeruginosa* PAO1 PvdI, PvdJ, PvdD and PvdL synthetases. Qualifying regions
were trimmed to their pyoverdine coding sequences, and where a genome's locus
spans more than one antiSMASH region — `pvdL` is typically separated from
`pvdI`/`pvdJ`/`pvdD` — the parts were concatenated into a single record, so
each genome contributes one comparable unit rather than several partial ones.
Parts are ordered identically in every genome. Domain content is unchanged by
concatenation; gene order gains one artificial adjacency per join.

This produced 77 analysed records — 46 known and 31 predicted — plus 6 held
out (below). The per-genome outcome, including every genome not staged and the
reason, is recorded in `benchmark_input_manifest.tsv`.

**4. Comparison.** BiG-SCAPE 2.0.3 clustered the records three ways (known
alone, predicted alone, and combined) in `glocal` alignment mode with
singletons retained at the default 0.30 cutoff, giving 36 families across the
77 combined records, 8 of which contain both known and predicted members.
DiscERN compared the predicted genomes against the known pyoverdine family at
`-k 2`. Both sides are the same kind of object: one condensed BGC per genome,
trimmed to the pyoverdine genes and re-run through antiSMASH so each record
carries its own clusterblast table. The reference family is 46 condensed
pyoverdine BGCs, one per known genome, labelled by accession; the query set is
31 condensed BGCs from the 30 predicted genomes. Every reference detects as
`NRP-metallophore.NRPS`, and no record was split by the condensation or lost
genes at re-detection.

A reference table computed over the untrimmed antiSMASH region cannot be
reused here, because it describes genes the condensed record no longer
contains: DiscERN's two active algorithms would then intersect evidence
measured over different footprints. Re-running detection on each condensed
record is what keeps the two sides comparable. The effect is not cosmetic --
comparing condensed queries against condensed references rather than whole
regions against them raises coverage from 15 to 19 of the 23 pyoverdine-
positive genomes and removes the one high-confidence hit in a genome with no
pyoverdine locus.

## Exclusions

Six known-arm accessions were excluded from both analyses: `LT629746`,
`CP176771`, `GCA_000730605`, `AP039450`, `CP028517` and `CP023269`. In each
case the published structure disagrees with what the genome's own cluster
encodes, because the deposited accession belongs to a different strain from
the one the pyoverdine was characterised in. Scoring these rows would penalise
the prediction for a curation error in the source record rather than for a
failure of the method. Per-accession evidence is in
`benchmark/bigscape/excluded/WHY_EXCLUDED.md`.

The excluded genomes are retained in `bigscape/excluded/` and
`discern/known_excluded/`, which no analysis script reads, so the basis for
each exclusion can be inspected. They are given the same treatment as the
analysed references -- condensed, one per genome, with their own clusterblast
tables -- so they can be judged on the same evidence: 6 excluded beside the 46
analysed, 52 known genomes in total.

## Genomes without a pyoverdine

Seven of the 83 staged records are not a pyoverdine locus. Four predicted
genomes lack a pyoverdine cluster but carry other NRPS, and are represented by
their most closely related one. `CP011835` (*Azomonas macrocytogenes*) produces
azotobactin, which shares the pyoverdine chromophore, and is represented by
that cluster as a near-miss outgroup.

`TP_1_w_a` and `TP_2_d_a` contain no NRPS at all — no condensation domain
anywhere in either genome — and `TP_2_d_a` has no siderophore synthetase of any
kind among its 3,288 coding sequences. Both are carried through so the
benchmark reports what the tools do with a genome lacking the target.
`TP_1_w_a` does possess an NRPS-independent siderophore cluster with an
IucA/IucC synthetase, which is the nearest functional analogue to a pyoverdine
and is what it contributes; `TP_2_d_a`, having no siderophore, contributes an
arylpolyene cluster as a true negative control. Both resolve as singletons:
BiG-SCAPE computed no pairwise comparison at all for `TP_1_w_a`, the only
NI-siderophore in the set, and placed `TP_2_d_a` at a nearest-neighbour
distance of 0.974 against the 0.30 cutoff. DiscERN returned no hit for
`TP_1_w_a` and a single low-confidence hit for `TP_2_d_a`.

One predicted assembly, `SN_3_w_a`, contains two chromosome-sized records each
carrying a complete pyoverdine cluster, and contributes two records.

## Reproducing

Tools are installed from bioconda; exact versions and database releases are in
`VERSIONS.txt`.

    conda create -n bigscape  -c conda-forge -c bioconda bigscape=2.0.3
    conda create -n antismash -c conda-forge -c bioconda antismash=8.0.4 hmmer2
    download-antismash-databases

    wget https://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/Pfam-A.hmm.gz
    gunzip Pfam-A.hmm.gz && hmmpress Pfam-A.hmm

`hmmer2` is required in addition to HMMER3: DiscERN's clusterblast stage calls
`hmmpfam2`. DiscERN itself is not packaged and must be patched before it will
accept a reference directory:

    git clone https://github.com/MaxMeta/DiscERN
    cd DiscERN && git checkout 716e932418c30ffda587964b0d1b0edf04ade3d2
    git apply <this folder>/benchmark/discern/discern_patches.diff
    wget https://github.com/medema-group/bigslice/releases/download/v2.0.0rc/bigslice-models.2022-11-30.tar.gz
    mkdir -p discern/bigslice_models
    tar xzf bigslice-models.2022-11-30.tar.gz -C discern/bigslice_models --strip-components=1

Then, from `benchmark/`:

    python step3_build_benchmark_input.py \
        --antismash-known ../antiSMASH/known \
        --antismash-predicted ../antiSMASH/predicted --out .
    PFAM=<Pfam-A.hmm> ./run_bigscape.sh
    python step4_build_discern_input.py --bigscape bigscape --out discern
    DISCERN_SRC=<patched DiscERN> ./run_discern.sh

Rerunning step 3 reproduces the staged records byte for byte. The scripts
resolve their tools from `PATH` and accept overrides; each checks the
conditions that otherwise fail silently, in particular DiscERN's requirement
that its reference directory be flat with equal numbers of GenBank and
clusterblast files, and the `-k 2` setting, since only two of its four
algorithms are active and at the default `-k 3` it builds trees from the
references alone while exiting successfully.

## Contents

```
README.md                 this file
PROJECT_SUMMARY.md        informal account of what was done and why
VERSIONS.txt              every tool and database version

raw/                      step1_assemble_annotate.sh
  predicted/                30 annotated genomes
  known/                    empty; see Limitations

antiSMASH/                step2_run_antismash.sh
  known/                    52 genomes, 762 regions
  predicted/                30 genomes, 424 regions, clusterblast tables, JSON

benchmark/                step3_build_benchmark_input.py   regions -> clusters
                          step4_build_discern_input.py     clusters -> DiscERN pairs
                          run_bigscape.sh, run_discern.sh
                          inline_bigscape_ui.py            one-file results viewer
                          benchmark_input_manifest.tsv
  bigscape/                 known 46, predicted 31, excluded 6
    results/                three runs, families and distance databases
  discern/                  discern_patches.diff, reference_manifest.tsv
    known/                    46 references (.gbk + .txt), one per genome
    known_excluded/           6 excluded references, same form
    predicted_condensed/      31 query clusters, one per genome
    predicted/                full antiSMASH trees, un-condensed; read by no
                              script. Same content as antiSMASH/predicted but
                              under antiSMASH's native filenames, which DiscERN
                              requires: it derives each region's filename from
                              its clusterblast table (contig_1_c9.txt ->
                              contig_1.region009.gbk), so the genome-prefixed
                              names used elsewhere make those lookups fail
                              silently. Recreate with, from antiSMASH/predicted:
                              for each <genome>_<contig>.regionNNN.gbk, drop the
                              <genome>_ prefix.
    results/                  the run
```

## Reproducibility note

`step4_build_discern_input.py` was verified against the shipped reference set.
It reproduces it in every respect the analysis depends on: identical sequence
and identical algorithm-relevant features (CDS, aSDomain, PFAM_domain,
protocluster, region) on all 46 references, and byte-identical
knownclusterblast tables on all 46.

The files are not byte-identical, and a rerun will not produce byte-identical
files either. Three things differ: the DEFINITION line, the antiSMASH run
timestamp, and, in 7 of 46 records, the coordinate of one `abmotifs` CDS_motif
annotation sitting at the detection threshold (score 14.6, E-value 8.2e-05).
None of these is read by either active DiscERN algorithm -- the BiG-SLiCE arm
builds its vector from domain content and the clusterblast arm from the table.

## Limitations

`raw/known/` is empty: the 35 NCBI reference genomes were not retained as whole
sequences, only their antiSMASH output. Consequently `antiSMASH/known/` holds
region GenBanks without clusterblast tables or JSON. No result presented here
depends on them — BiG-SCAPE reads regions only, and the known arm serves
DiscERN solely as references, whose tables are present. It does mean the known
genomes cannot be used as a DiscERN query set, which would be needed for a
leave-one-out validation of the reference family.

The two arms were detected on different dates with the same antiSMASH version
(known 2026-09-05, predicted 2026-09-20). Region admission differs by arm by
design: a marker-free region is admitted on NRPS homology only if it runs to a
contig edge in the known arm, without that restriction in the predicted arm,
whose assemblies are near-complete and place `pvdL` mid-contig.
