#!/usr/bin/env bash
# =============================================================================
# STEP 1 - raw/ : produce annotated genomes
# =============================================================================
#
# known/      Assembled from ENA reads (study PRJEB76792, 17 runs) and, for the
#             35 literature reference strains, downloaded from NCBI. Only the
#             assembly half is scripted here; see README.md for the status of
#             this folder.
#
# predicted/  The 30 isolate genomes arrived from Mark already annotated with
#             Bakta. No annotation step was run on them in this project, so
#             there is no code here for that half - the files in
#             raw/predicted/ are the originals as received.
#
# Assembly (the 17): fastp trimming -> coverage-based subsampling to 80x
# -> SPAdes -> polishing -> QC. -x 80 is applied to every genome because the
# subsample stage is self-limiting: fraction = min(1, 80/coverage), so libraries
# already below 80x pass through untouched. That keeps one command for all 17
# rather than a list of exceptions.
#
# Usage:
#   ./step1_assemble_annotate.sh <reads_dir> <out_dir>
#
# Reads are not redistributed here: fetch them from ENA with the run accessions
# in READS_MANIFEST.tsv, which ships with the original assembly work rather
# than with this folder. Reads are public: ENA study PRJEB76792, 17 runs.
#
#   PIPELINE=/path/to/assemble_pseudomonas_genomes.sh \
#   MANIFEST=/path/to/READS_MANIFEST.tsv \
#       ./step1_assemble_annotate.sh <reads_dir> <out_dir>

set -uo pipefail

READS="${1:?usage: $0 <reads_dir> <out_dir>}"
OUT="${2:?usage: $0 <reads_dir> <out_dir>}"

# The full pipeline lives in the study's own script, kept verbatim at
#   Assembly files/ASSEMBLED_GENOMES_17/code/assemble_pseudomonas_genomes.sh
# and driven for all 17 by run_all_17_final.sh in the same directory.
# Both of these live OUTSIDE this folder, with the original assembly work.
# They are not bundled here, so point at them explicitly rather than have the
# script resolve a path that only exists on one machine.
PIPELINE="${PIPELINE:?set PIPELINE=/path/to/assemble_pseudomonas_genomes.sh}"
MANIFEST="${MANIFEST:?set MANIFEST=/path/to/READS_MANIFEST.tsv}"

[ -x "$PIPELINE" ] || { echo "FATAL: pipeline not found at $PIPELINE" >&2; exit 2; }

while IFS=$'\t' read -r run _rest; do
    [ "$run" = "run_accession" ] && continue          # header
    [ -z "$run" ] && continue
    echo "=== $run"
    "$PIPELINE" -1 "$READS/${run}_1.fastq.gz" \
                -2 "$READS/${run}_2.fastq.gz" \
                -o "$OUT/$run" -x 80
done < "$MANIFEST"

echo "done. Annotate the assemblies with Prokka to match raw/known/."
