#!/usr/bin/env bash
# =============================================================================
# run_discern.sh - the predicted genomes against the known pyoverdine family
# =============================================================================
#
#   ./run_discern.sh [out_dir]
#
# Query : discern/predicted  - all 30 predicted genomes, whole antiSMASH trees
# Refs  : discern/known      - 82 known-pyoverdine regions, 44 accessions
#
# Note the query set is all 30 genomes, not the 31 staged records used for
# BiG-SCAPE. DiscERN reads whole antiSMASH output directories and keys its
# clusterblast tables per region filename, so a concatenated one-per-genome
# record has no matching table. Aggregating its per-region hits to one row per
# genome gives the comparable number without feeding the tool input that would
# silently invalidate half its evidence.
#
# discern/known_excluded is NOT used. Those references are kept so the
# exclusions can be inspected, not scored against.
#
# Four things fail silently if wrong, all of them checked below:
#
#  1. -k 2, never the default. --min_k defaults to 3, but only two of the four
#     algorithms are active without --poly_search: discern.py initialises the
#     polymer and overlap hit sets empty. At k=3 nothing is found and the
#     dendrograms are built from the references alone - while exiting 0.
#     k means "in exactly n algorithm sets", so with two active algorithms
#     k=2 is the intersection and k=1 the symmetric difference.
#  2. The reference directory must be FLAT with equal .gbk and .txt counts.
#     DiscERN globs both from the same directory; put the tables in a
#     knownclusterblast/ subdirectory and the count is zero, whereupon it
#     prints a message and exits 0 having done nothing.
#  3. discern.py needs discern_ref_dir_patch.diff before it will accept
#     -r <directory> at all: three call sites hand an already-globbed file
#     list to functions that expect a directory, raising TypeError.
#  4. The BiG-SLiCE models must sit at <src>/discern/bigslice_models. No flag
#     relocates them.
#
# After the run, check the newick tree has MORE leaves than the reference
# count. Equal means the reference-only failure mode above.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$HERE/discern/results}"
SRC="${DISCERN_SRC:?set DISCERN_SRC to the patched DiscERN source tree}"
PY="${PY:-python3}"

Q="$HERE/discern/predicted"
R="$HERE/discern/known"

ng=$(ls "$R"/*.gbk 2>/dev/null | wc -l)
nt=$(ls "$R"/*.txt 2>/dev/null | wc -l)
[ "$ng" -gt 0 ] && [ "$ng" -eq "$nt" ] || {
    echo "FATAL: reference dir unbalanced: $ng gbk / $nt txt" >&2; exit 3; }
grep -q "PATCH ref_dir_pathtype" "$SRC/discern/discern.py" || {
    echo "FATAL: discern_ref_dir_patch.diff not applied to $SRC" >&2; exit 3; }
[ -d "$SRC/discern/bigslice_models" ] || {
    echo "FATAL: no bigslice_models in $SRC/discern" >&2; exit 3; }
echo "  refs: $ng gbk / $nt txt (balanced); patch present; models present"
echo "  query genomes: $(find "$Q" -mindepth 1 -maxdepth 1 -type d | wc -l)"

# hmmpfam2 (HMMER2) is a hard dependency of the clusterblast stage and is a
# separate package from HMMER3: install hmmer2, or conda install -c bioconda hmmer2
command -v hmmpfam2 >/dev/null || {
    echo "FATAL: hmmpfam2 not on PATH (HMMER2, separate from HMMER3)" >&2; exit 3; }
export PYTHONPATH="$SRC"
mkdir -p "$OUT"

"$PY" -c "from discern.discern import main; main()" \
      -a "$Q" -r "$R" -o "$OUT" -k 2
echo "  exit=$?"

leaves=$(grep -oE '[(,][^(),:]+:' "$OUT/newick_tree.txt" 2>/dev/null | wc -l)
echo "  newick leaves=$leaves refs=$ng"
[ "$leaves" -gt "$ng" ] \
    && echo "  OK: tree contains query hits, not references alone" \
    || echo "  WARNING: tree has no more leaves than references - see note 1"
