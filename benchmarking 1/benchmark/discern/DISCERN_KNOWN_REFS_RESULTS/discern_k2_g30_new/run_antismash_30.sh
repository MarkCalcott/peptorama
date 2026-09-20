#!/usr/bin/env bash
# run_antismash_30.sh - regenerate full antiSMASH output for the 30 unknown-arm
# genomes, using the study's original flags.
#
# WHY: the raw output in the shared folder contains only regions/*.gbk. The
# knownclusterblast/*.txt and regions.json were produced by the original run
# (run_antismash_all.sh line 29: --cb-knownclusters --cb-subclusters) but were
# discarded by the trim-to-BiG-SCAPE-input step. DiscERN's clusterblast
# algorithm reads the .txt; its polymer/peptide data reads the .json. This
# restores both from the whole-genome Bakta GenBanks, which carry gene calls,
# so --genefinding-tool none re-detects without re-annotating.
#
# Two prerequisites that fail loudly if wrong (both hit during setup):
#  * PYTHONPATH must point at a WRITABLE copy of the antismash package -- it
#    caches pressed HMMs and SVM pickles inside its own tree.
#  * hmmpfam2 must be on PATH. It is in the discern env, NOT the antismash env;
#    five RiPP modules need it and --check-prereqs exits non-zero without it.
set -uo pipefail
SRC="${SRC:-../../../../raw/predicted}"
OUT="${OUT:-as30}"
DB="${DB:-$PWD/asdb_full}"
PKG="${PKG:-$PWD/aspkg}"
ENVD="${ENVD:-}"   # optional: prefix holding antismash + hmmpfam2
JOBS="${JOBS:-4}"       # cpus per genome
PAR="${PAR:-3}"         # genomes at once  (JOBS*PAR <= cores)

[ -n "$ENVD" ] && export PATH="$ENVD/bin:$PATH"
export PYTHONPATH="$PKG"
[ -d "$PKG/antismash" ] || { echo "FATAL: no writable antismash copy at $PKG" >&2; exit 3; }
[ -d "$DB" ]            || { echo "FATAL: no databases at $DB" >&2; exit 3; }
command -v hmmpfam2 >/dev/null || { echo "FATAL: hmmpfam2 not on PATH" >&2; exit 3; }

mkdir -p "$OUT" logs
T="$OUT/per_genome.tsv"
printf "genome\texit\twall_s\tregions\tkcb_txt\tjson\n" > "$T"

one () {
  local f="$1" g d t0 t1 rc
  g=$(basename "$f" .gbk); d="$OUT/$g"
  # resume: --output-basename writes <genome>.json, not regions.json
  [ -s "$d/$g.json" ] && [ -d "$d/knownclusterblast" ] && { echo "  skip $g (done)"; return 0; }
  rm -rf "$d"; mkdir -p "$d"
  t0=$(date +%s)
  "${ENVD:+$ENVD/bin/}python3" -m antismash \
      --databases "$DB" --taxon bacteria \
      --genefinding-tool none \
      --cb-knownclusters --cb-subclusters \
      --output-dir "$d" --output-basename "$g" \
      --cpus "$JOBS" "$f" > "logs/as_$g.log" 2>&1
  rc=$?; t1=$(date +%s)
  printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$g" "$rc" "$((t1-t0))" \
    "$(find "$d" -name '*.region*.gbk' | wc -l)" \
    "$(find "$d" -path '*knownclusterblast*' -name '*.txt' | wc -l)" \
    "$([ -s "$d/$g.json" ] && echo 1 || echo 0)" >> "$T"
  echo "  $g rc=$rc $((t1-t0))s"
}

n=0
for f in "$SRC"/*.gbk; do
  one "$f" &
  n=$((n+1))
  [ $((n % PAR)) -eq 0 ] && wait
done
wait
echo "=== done"
awk -F'\t' 'NR>1{tot++; if($2==0)ok++; r+=$4; k+=$5; j+=$6} END{
  printf "genomes=%d ok=%d regions=%d kcb_txt=%d json=%d\n",tot,ok,r,k,j}' "$T"
