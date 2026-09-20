# benchmarking 1

Pyoverdine BGC benchmarking: a set of genomes with experimentally characterised
pyoverdines (**known**) against a set whose pyoverdines are predicted only
(**predicted**), carried through three steps.

```
benchmarking 1/
  README.md                           this file
  VERSIONS.txt                        every tool and database version
  raw/            annotated genomes
    step1_assemble_annotate.sh
    known/          EMPTY - see Gaps
    predicted/      30 genomes from Mark, Bakta-annotated
  antiSMASH/      antiSMASH output
    step2_run_antismash.sh
    known/          52 genomes, 762 region GenBanks (regions only)
    predicted/      30 genomes, 424 regions + clusterblast + JSON
  benchmark/      input files, and the analyses
    step3_build_benchmark_input.py      builds the inputs below
    run_bigscape.sh                     clusters them
    run_discern.sh                      scores predicted against known
    benchmark_input_manifest.tsv        every genome, staged or not, and why
    bigscape/
      known/          46 records, one per genome
      predicted/      31 records  (29 + 2 negative controls)
      excluded/        6 records  NOT analysed - see Excluded inputs
      results/        three runs: known, predicted, combined
    discern/
      known/           82 reference regions + 82 clusterblast tables
      known_excluded/  12 + 12  NOT analysed - see Excluded inputs
      predicted/       30 genomes, the query set
      DISCERN_KNOWN_REFS_RESULTS/   the run
```

Each step folder holds one script and the two arms. Run the scripts in order;
each consumes the previous folder. The two benchmark tools take different
inputs, so they get a folder each: BiG-SCAPE clusters one record per genome,
DiscERN compares a query set against a reference family.

Everything here is a copy. The original `Benchmarking/` folder is untouched.

## The two arms

**known** — 52 genomes whose pyoverdine structure is published: 17 assembled
here from ENA reads (study `PRJEB76792`) and 35 downloaded from NCBI. These are
the ground truth the benchmark measures against.

**predicted** — the 30 isolate genomes from Mark. Unpublished, no accessions,
Bakta-annotated when received. Their pyoverdines are predicted from sequence,
which is what the benchmark is testing.

## Step 1 — raw

Annotated whole genomes, one file per genome.

`predicted/` holds the 30 as received. No annotation was run on them in this
project, so `step1_assemble_annotate.sh` covers only the assembly of the 17;
it reads run accessions from `Assembly files/ASSEMBLED_GENOMES_17/READS_MANIFEST.tsv`
and calls the study's own pipeline.

**`known/` is empty on purpose.** The 17 assembled genomes exist as Prokka
GenBanks under `Assembly files/`, but the 35 downloaded reference genomes are
not held anywhere in this project — only their antiSMASH output survives. Filling
this folder means re-downloading those 35 from NCBI. Nothing downstream is
blocked by it: `antiSMASH/known/` already contains their results.

## Step 2 — antiSMASH

BGC detection, one subfolder per genome.

`predicted/` is **complete**: 30 genomes, 424 regions, 424 `knownclusterblast`
tables and 30 `.json`, regenerated with `step2_run_antismash.sh`.

`known/` holds **region GenBanks only** — 762 regions, no clusterblast tables
and no JSON. The original run produced them and a later step discarded them.
Regenerating them needs the whole genomes, which are the missing half of
`raw/known/`, so this waits on that.

The script uses identical flags for both arms, so any difference in results
comes from the genomes rather than the analysis. `--genefinding-tool none`
keeps the gene calls from step 1 — re-calling would shift coordinates and break
the link back to `raw/`. `--cb-knownclusters --cb-subclusters` write the
clusterblast tables; these are not optional, because DiscERN reads them and a
run without them exits **successfully** having built its trees from reference
sequences alone.

`known/` is the study's original antiSMASH 8.0.4 output, one directory per
accession. `predicted/` is the equivalent for the 30, renamed as described
below.

## Step 3 — benchmark

### bigscape/ — one record per genome

    cd benchmark
    python step3_build_benchmark_input.py \
        --antismash-known ../antiSMASH/known \
        --antismash-predicted ../antiSMASH/predicted \
        --out .

One command, antiSMASH output straight to benchmark inputs. There is no
intermediate trim directory: an earlier version wrote trimmed regions to disk
and a second script staged them, but those files were never a deliverable,
only a way to pass data between two scripts, so they are now held in memory.

What it does per genome: score every region for pyoverdine markers, BLAST
every NRPS against the PAO1 PvdI/PvdJ/PvdD/PvdL reference, trim each
qualifying region to its pyoverdine CDSs, and concatenate a genome's loci into
one record.

The concatenation matters. A genome's locus is usually split across two
antiSMASH regions — `pvdL` sits apart from `pvdI`/`pvdJ`/`pvdD` — so an
unmerged genome enters the comparison as two nodes with its similarity divided
between them. Parts are ordered identically in every genome so the artificial
join is constant rather than arbitrary; domain content is unchanged by
joining, gene order gains one adjacency per join.

**The script reproduces this folder exactly**: rerunning it writes all 73
records byte-for-byte identical to the ones shipped here.

Two details worth knowing before you change anything:

- **The two arms use different region-admission rules, deliberately.** A
  region carrying a chromophore marker always qualifies. A marker-free region
  is rescued on NRPS homology — but in the known arm only if it runs to a
  contig edge. Without that restriction an NRPS-rich genome contributes
  unrelated synthetases. The predicted arm has no edge requirement, because
  those assemblies are near-complete and `pvdL` sits mid-contig, where an edge
  test would discard it and lose the chromophore synthetase. `--rescue-known`
  exposes the choice.
- **The BLAST database is built in a temp directory, not under `--out`.**
  `makeblastdb` returns exit 3 on a cloud-synced filesystem, so writing it
  beside the results fails on this folder.

### discern/ — a reference family and a query set

`known/` is the reference family: 82 pyoverdine regions with their 82 matching
clusterblast tables, flat in one directory with equal counts. Both properties
are load-bearing — DiscERN globs `*.gbk` and `*.txt` from the same directory,
and an unbalanced pair makes it exit 0 having done nothing.

`predicted/` is the query set and is empty; see Gaps.

## Excluded inputs, and why they are here

Six known-arm genomes are excluded from the analyses — the six specified,
no others. They are **staged anyway**, into `bigscape/excluded/` and `discern/known_excluded/`, which no
run script reads. An exclusion that rests on a file simply being absent cannot
be checked; these can be opened and judged on the same evidence as everything
that was kept.

`12 + 84 = 96`, the complete reference set, so nothing was quietly lost.

Full per-accession justification: `bigscape/excluded/WHY_EXCLUDED.md`.

| accession | why excluded |
|---|---|
| `LT629746`, `CP176771`, `GCA_000730605`, `AP039450`, `CP028517`, `CP023269` | curated structure disagrees with what the genome's own BGC encodes |

`CP034337` (declared surrogate) and `CP011835` (*Azomonas*, azotobactin) were
held out in an earlier version of this folder. Both are now **analysed**:
neither was on the exclusion list, and both are informative in the comparison.
`CP011835` has no pyoverdine locus, so it is staged from its NRP-metallophore
region — the azotobactin cluster — and enters as a near-miss outgroup.

## TP_1_w_a and TP_2_d_a: one substitute, one negative control

Neither genome carries an NRPS: not one condensation domain anywhere, and
`TP_2_d_a` has no siderophore synthetase among its 3,288 coding sequences.
There is no pyoverdine to compare in either, and none was invented. They are
carried through anyway, because a benchmark should show what the tools do with
a genome that has none of the target.

They are not treated the same, because they are not the same case:

| genome | staged from | why |
|---|---|---|
| `TP_1_w_a` | `region008`, **NI-siderophore** | it does make a siderophore - NRPS-independent, with an IucA/IucC synthetase and TonB-dependent receptors. That is the nearest functional analogue to a pyoverdine, so it is what gets compared. |
| `TP_2_d_a` | `region001`, arylpolyene | no siderophore of any kind exists in this genome, so this is a true negative control: a locus the cohort shares, definitively not a pyoverdine. |

The selection rule follows that logic generally - any siderophore locus beats
a shared non-target class - so it behaves sensibly on genomes beyond these two.

**Measured outcome, both singletons, but differently so:**

- `TP_1_w_a` is the only NI-siderophore among the 77 records, and BiG-SCAPE
  computed **no pairwise comparison for it at all**. It is not distant from
  the pyoverdines; it is incomparable to them.
- `TP_2_d_a` drew 2 comparisons, nearest neighbour `TP_1_d_a` at **0.974**
  against a 0.30 cutoff.
- DiscERN already covered both, since its query set is whole antiSMASH trees
  for all 30 genomes: `TP_1_w_a` no hit, `TP_2_d_a` one low-confidence
  clusterblast-only hit. Both agree with the protein-level evidence.

Expect singletons either way: every other genome contributes its *pyoverdine*
record, so a genome without one has nothing to match. Eight other predicted
genomes do carry an NI-siderophore, but they are represented in the comparison
by their pyoverdine, not their NIS.

## Genome naming

The predicted arm previously carried two naming schemes for the same genomes —
`KP_1_d_a` in the source files, `1kda` in the analysis output. Everything here
uses the `KP_1_d_a` form.

The mapping was derived from sequence, not from the naming pattern: for each
genome, whole antiSMASH regions were tested for exact containment in each
candidate assembly. 28 of 30 resolved that way. The exceptions are `OW_3_d_a`
and `OW_3_d_b`, which differ by **one base pair** across 6.55 Mb and share all
20 regions exactly — no sequence test can separate them, so those two follow
the naming convention that the other 28 confirm.

Where the mapping still applies is `benchmark/bigscape/`, whose records are
named for their genome (`KP_1_d_a.region001.gbk`). The two records from
`SN_3_w_a` keep their contig suffix, because that genome's file contains two
distinct chromosome-sized records and they cluster separately.

`antiSMASH/predicted/` was regenerated from the Bakta genomes, so the genome
name is both the directory and the filename prefix
(`KP_1_d_a/KP_1_d_a_contig_1.region001.gbk`). Record identifiers inside the
staged benchmark files now also carry the long names, so a tool that labels
its output from the record rather than the filename reports `KP_1_w_a` and not
`1kwa`. That was not true of an earlier version of this folder.

## Running the analyses

    cd benchmark
    PFAM=<path to Pfam-A.hmm> ./run_bigscape.sh
    DISCERN_SRC=<patched DiscERN tree> ./run_discern.sh

Both scripts read only the analysed folders; `excluded/` and
`known_excluded/` are never passed to a tool. Each script preflights the
conditions that otherwise fail silently — a truncated Pfam, an unbalanced
reference directory, an unpatched DiscERN, missing BiG-SLiCE models — and
`run_discern.sh` checks afterwards that the output tree has more leaves than
the reference count, which is the test that separates a real result from the
reference-only failure mode.

Results are already present: `bigscape/results/` (three runs, 77 records, 36
families, 8 of them linking the two arms) and
`discern/DISCERN_KNOWN_REFS_RESULTS/`.

## Was everything processed the same way?

Mostly, and the exceptions are listed here rather than left to be discovered.

**Identical across all 82 genomes:** antiSMASH 8.0.4 produced every one of the
1,186 regions; one run of `step3_build_benchmark_input.py` produced all 83
staged records; BiG-SCAPE 2.0.3 ran with identical parameters for all three
comparisons.

**Three things that differ, plus one that turned out not to:**

1. **Gene calling is actually uniform — the annotation layer is not.** All
   three groups are called by Prodigal 2.6: Prokka 1.15.6 records
   `Prodigal:v2.6`, Bakta 1.12.0 records `Prodigal:2.6`, and the 35 reference
   genomes were supplied without annotation, so antiSMASH called their genes
   itself with the same tool (they carry antiSMASH `ctg1_n` locus tags and no
   `/inference` or `/gene` qualifiers at all). CDS coordinates are therefore
   comparable throughout. What differs is the functional layer: the 35 have no
   product or gene names. That does not affect detection, because antiSMASH
   identifies clusters from HMM profiles over translated CDS rather than from
   product text.
2. **The two arms were run on different days**, both with 8.0.4: the known arm
   on 2026-09-05, the predicted arm regenerated on 2026-09-20 to recover the
   clusterblast output. Same version, so detection is unchanged.
3. **Auxiliary output exists for one arm only, and it changes nothing here.**
   `antiSMASH/predicted` carries 424 clusterblast tables and 30 JSON files;
   `antiSMASH/known` has neither - discarded by an earlier trim step. No
   result depends on them: BiG-SCAPE reads region GenBanks only, and the known
   arm is used by DiscERN solely as *references*, whose 84 tables are present
   and balanced in `discern/known/`. The only thing it forecloses is using the
   known genomes as a DiscERN *query* set - a leave-one-out validation of the
   reference set, for instance - which would need those 762 genomes re-run
   with `--cb-knownclusters`.
4. **Region admission differs by arm, deliberately** - strict (contig-edge) for
   known, permissive for predicted. Reasons under "Running the analyses".

**Seven records are not a pyoverdine locus,** all flagged in
`benchmark_input_manifest.tsv`: `TP_1_w_a` (NI-siderophore substitute) and
`TP_2_d_a` (arylpolyene negative control), `CP011835` (azotobactin), and four predicted genomes
staged from their most relevant NRPS. `SN_3_w_a` contributes two records, one
per replicon.

## Installing the tools

All three tools come from bioconda; the versions are pinned in `VERSIONS.txt`.
Genome assembly and annotation are not covered here — see the paper's methods.

    conda create -n bigscape  -c conda-forge -c bioconda bigscape=2.0.3
    conda create -n antismash -c conda-forge -c bioconda antismash=8.0.4 hmmer2

`hmmer2` is deliberate: DiscERN's clusterblast stage calls `hmmpfam2`, which is
HMMER2 and a different package from HMMER3.

Each tool needs one database that is not shipped with it:

    # antiSMASH (~7 GB)
    download-antismash-databases

    # Pfam, for BiG-SCAPE (~1.5 GB) - must be pressed
    wget https://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/Pfam-A.hmm.gz
    gunzip Pfam-A.hmm.gz && hmmpress Pfam-A.hmm

DiscERN is not packaged, and needs a patch plus its own models:

    git clone https://github.com/MaxMeta/DiscERN
    cd DiscERN && git checkout 716e932418c30ffda587964b0d1b0edf04ade3d2
    git apply .../discern_ref_dir_patch.diff        # shipped in benchmark/discern/
    wget https://github.com/medema-group/bigslice/releases/download/v2.0.0rc/bigslice-models.2022-11-30.tar.gz
    mkdir -p discern/bigslice_models
    tar xzf bigslice-models.2022-11-30.tar.gz -C discern/bigslice_models --strip-components=1

The patch is required, not optional: without it `-r <directory>` raises
`TypeError`, because three call sites pass an already-globbed file list to
functions that expect a directory. The models must sit at
`discern/bigslice_models`; no flag relocates them.


## Gaps

One thing is missing, and it has one consequence.

**`raw/known/` is empty.** The 17 assembled genomes exist as Prokka GenBanks
under `Assembly files/`, but the 35 downloaded reference genomes are not held
anywhere in this project — only their antiSMASH output survives. Filling this
means re-downloading those 35 from NCBI (~250 MB).

**Consequence: `antiSMASH/known/` stays region-only.** Regenerating its
clusterblast tables means re-running antiSMASH on those whole genomes, which do
not exist here yet. The predicted arm is unaffected and complete.

Nothing else is outstanding. DiscERN can run against this folder as it stands:
its reference directory is flat and balanced at 82/82, and all three of its
input globs resolve over the query set (424 regions, 424 clusterblast tables,
30 JSON across 30 genome directories).

## Disk

The DiscERN query set is the same data as `antiSMASH/predicted/`, so the two
are **hardlinked**: 453 MB each apparent, 455 MB actual on disk. Copying rather
than linking would have cost an extra 450 MB. Note that a cloud sync client
will not preserve the links and will upload both copies.

## Provenance

Files are copies of existing project data, not new analysis. `raw/predicted/`
and `antiSMASH/known/` come from the `Benchmarking/` folder;
`antiSMASH/predicted/`, `benchmark/bigscape/` and `benchmark/discern/known/`
come from this project's saved outputs. The original `Benchmarking/` folder is
unchanged.
