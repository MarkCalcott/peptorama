#!/usr/bin/env bash
# =============================================================================
# STEP 2 - antiSMASH/ : detect BGCs in every genome
# =============================================================================
#
# One script, both arms. The flags are identical for known and predicted, so
# any difference between the two sets of results comes from the genomes and not
# from how they were analysed.
#
#   --genefinding-tool none    inputs already carry gene calls (Prokka for the
#                              17, Bakta for the 30, NCBI for the references).
#                              Re-calling genes here would change coordinates
#                              and break the link back to raw/.
#   --cb-knownclusters
#   --cb-subclusters           write the knownclusterblast/ tables. These are
#                              NOT optional: DiscERN reads them, and a run
#                              without them exits 0 having built its trees from
#                              reference sequences alone.
#   --taxon bacteria
#
# Two prerequisites that fail in confusing ways if missed:
#   * PYTHONPATH must point at a WRITABLE copy of the antismash package - it
#     caches pressed HMMs and SVM pickles inside its own install tree.
#   * hmmpfam2 must be on PATH. Five RiPP modules need it and --check-prereqs
#     exits non-zero without it.
#
# Usage:
#   ./step2_run_antismash.sh <input_dir_of_genome_gbk> <out_dir> [cpus] [parallel]
#
# Output per genome: <out_dir>/<genome>/ with *.region*.gbk, knownclusterblast/
# and <genome>.json - which is the layout antiSMASH/known/ and
# antiSMASH/predicted/ hold.

set -uo pipefail

SRC="${1:?usage: $0 <input_dir> <out_dir> [cpus] [parallel]}"
OUT="${2:?usage: $0 <input_dir> <out_dir> [cpus] [parallel]}"
CPUS="${3:-4}"
PAR="${4:-3}"
DB="${DB:-$PWD/asdb_full}"          # download-antismash-databases --database-dir
PKG="${PKG:-$PWD/aspkg}"            # writable copy of the antismash package

export PYTHONPATH="$PKG"
command -v hmmpfam2 >/dev/null || { echo "FATAL: hmmpfam2 not on PATH" >&2; exit 3; }
[ -d "$PKG/antismash" ] || { echo "FATAL: no writable antismash copy at $PKG" >&2; exit 3; }
[ -d "$DB" ]            || { echo "FATAL: no databases at $DB" >&2; exit 3; }

mkdir -p "$OUT"

one () {
    local f="$1" g d
    g=$(basename "$f"); g="${g%.*}"; d="$OUT/$g"
    [ -s "$d/$g.json" ] && { echo "  skip $g (done)"; return 0; }
    rm -rf "$d"; mkdir -p "$d"
    antismash --databases "$DB" --taxon bacteria \
              --genefinding-tool none \
              --cb-knownclusters --cb-subclusters \
              --output-dir "$d" --output-basename "$g" \
              --cpus "$CPUS" "$f" > "$d/antismash.log" 2>&1
    echo "  $g rc=$? regions=$(find "$d" -name '*.region*.gbk' | wc -l)"
}

n=0
for f in "$SRC"/*.gb*; do
    one "$f" &
    n=$((n+1)); [ $((n % PAR)) -eq 0 ] && wait
done
wait

echo "=== done: $(find "$OUT" -name '*.region*.gbk' | wc -l) regions, \
$(find "$OUT" -path '*knownclusterblast*' -name '*.txt' | wc -l) clusterblast tables"
