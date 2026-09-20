#!/usr/bin/env bash
# =============================================================================
# run_bigscape.sh - cluster the benchmark inputs, three ways
# =============================================================================
#
#   ./run_bigscape.sh [out_dir]
#
# Reads bigscape/known and bigscape/predicted, one record per genome, and runs
# BiG-SCAPE three times: each arm alone and the two together. Parameters are
# identical across the three runs, so any family that appears or merges is
# attributable to which records were compared and not to how.
#
# bigscape/excluded is deliberately NOT read. Those genomes are staged so their
# exclusion can be inspected, not analysed.
#
# Flags, and why each is pinned rather than left to default:
#   --alignment-mode glocal   `auto` switches per pair and is not comparable
#                             across runs
#   --include-singletons      without it a singleton-heavy set looks denser
#                             than it is
#   --record-type region      cluster whole regions, not protoclusters
#   --mibig-version           NOT used: it downloads into BiG-SCAPE's own
#                             install directory, which fails on a read-only
#                             install, and no MIBiG comparison is wanted
#
# Requires: bigscape on PATH (or BIGSCAPE=), and Pfam-A.hmm, pressed with
# hmmpress. Fetch it with:
#   wget https://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/Pfam-A.hmm.gz
#   gunzip Pfam-A.hmm.gz && hmmpress Pfam-A.hmm
# then pass PFAM=/path/to/Pfam-A.hmm
# Cutoff is BiG-SCAPE's default 0.30. It is not tuned for pyoverdines; the .db
# files hold every pairwise distance, so re-cutting needs no rerun.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$HERE/bigscape/results}"
PFAM="${PFAM:-$HERE/Pfam-A.hmm}"
CORES="${CORES:-10}"
BIGSCAPE="${BIGSCAPE:-$(command -v bigscape || true)}"

[ -n "$BIGSCAPE" ] && [ -x "$BIGSCAPE" ] || {
    echo "FATAL: bigscape not on PATH. Activate its environment, or set" >&2
    echo "       BIGSCAPE=/path/to/bigscape" >&2; exit 3; }
[ -f "$PFAM" ]     || { echo "FATAL: no Pfam at $PFAM (set PFAM=)" >&2; exit 3; }

# A truncated Pfam still runs and still produces families, just wrong ones.
NPROF=$(grep -c '^HMMER3' "$PFAM")
[ "$NPROF" -gt 20000 ] || { echo "FATAL: Pfam has $NPROF profiles - truncated" >&2; exit 3; }
echo "  Pfam profiles: $NPROF"

mkdir -p "$OUT"
rm -rf "$OUT/in_known" "$OUT/in_predicted" "$OUT/in_combined"
mkdir -p "$OUT/in_known" "$OUT/in_predicted" "$OUT/in_combined"

cp "$HERE/bigscape/known"/*.gbk     "$OUT/in_known"/
cp "$HERE/bigscape/predicted"/*.gbk "$OUT/in_predicted"/
cp "$HERE/bigscape/known"/*.gbk "$HERE/bigscape/predicted"/*.gbk "$OUT/in_combined"/

for s in known predicted combined; do
    echo "  in_$s: $(ls "$OUT/in_$s" | wc -l) records"
done

run () {
    local name="$1"
    rm -rf "$OUT/$name"
    echo "=== $name"
    "$BIGSCAPE" cluster -i "$OUT/in_$name" -o "$OUT/$name" -p "$PFAM" \
        --alignment-mode glocal --include-singletons --record-type region \
        --cores "$CORES" 2>&1 | grep -Ei "error|traceback|famil" | tail -4
    echo "  exit=$? db=$([ -f "$OUT/$name/$name.db" ] && echo yes || echo NO)"
}

run combined
run known
run predicted

echo "=== done"
find "$OUT" -name "*.db" -printf "  %p\n" | sed "s|$OUT/|  |"
