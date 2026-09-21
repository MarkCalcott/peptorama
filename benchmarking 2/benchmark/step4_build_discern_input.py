#!/usr/bin/env python3
"""
step4_build_discern_input.py - turn the benchmark records into DiscERN inputs.

    python step4_build_discern_input.py --bigscape bigscape --out discern

Why this step exists
--------------------
DiscERN compares a query BGC against a family of reference BGCs, and it reads
each one as a PAIR of files: an antiSMASH region GenBank, and the
knownclusterblast table for that same region. Two of its four algorithms are
active in this analysis, and they read different halves of that pair - the
BiG-SLiCE algorithm builds a Pfam-domain vector from the .gbk, the clusterblast
algorithm builds a vector of MIBiG cluster scores from the .txt. At -k 2 a hit
must be found by both.

That is why the tables cannot simply be copied from the whole-genome antiSMASH
run. Those tables were computed over the untrimmed region, which contains genes
the condensed pyoverdine record no longer has - in this set the untrimmed
regions carry a median of 87 coding sequences against 16 after trimming, and 14
of them also contain an unrelated cluster (ranthipeptide, hydrogen-cyanide or
terpene). Pairing a condensed .gbk with its region's original .txt would
intersect two algorithms' evidence measured over different footprints.

So each condensed record is put back through antiSMASH. Detection is re-run on
the record itself, which produces a region GenBank and a knownclusterblast
table describing the same genes. Both sides of the comparison - references and
queries - are built this way, so a query and a reference are the same kind of
object: one condensed BGC per genome.

What it produces
----------------
    <out>/known/                 <accession>.gbk + <accession>.txt   (flat)
    <out>/known_excluded/        same form, for the excluded accessions
    <out>/predicted_condensed/   <genome>/<region>.gbk
                                 <genome>/knownclusterblast/*.txt
    <out>/reference_manifest.tsv

References are flat because DiscERN globs `*.gbk` and `*.txt` from the
reference directory itself and requires equal counts of each; queries are
per-genome directories because it globs `<genome>/*.region*.gbk` and
`<genome>/knownclusterblast/*.txt` there.

Genome identity is the filename. DiscERN takes its reference labels from the
basename, so the accession or genome ID is what appears on the dendrogram
leaves, in newick_tree.txt and in the hit tables.

Requirements
------------
antiSMASH 8 with its databases, and hmmpfam2 on PATH (HMMER2, a separate
package from HMMER3). Override the defaults with:

    ANTISMASH="python -m antismash"   ASDB=/path/to/databases   CPUS=4
"""

import argparse
import collections
import csv
import glob
import os
import re
import shutil
import subprocess
import sys

try:
    from Bio import SeqIO
except ImportError:
    raise SystemExit("FATAL: biopython is required (pip install biopython)")

# A record is rejected if antiSMASH no longer calls a single region over it, or
# if re-detection drops genes: either means the condensed record is not what is
# being compared, and silently shipping it would misstate the analysis.
CHROMOPHORE_PRODUCTS = {"NRP-metallophore", "NRPS", "NRPS-like"}


def short_id(label):
    """GenBank LOCUS names are capped at 16 characters."""
    return label[:16]


def stage(src_gbk, label, dest_dir):
    """Copy one condensed record out under its genome label."""
    rec = SeqIO.read(src_gbk, "genbank")
    rec.id = rec.name = short_id(label)
    rec.description = f"{label} condensed BGC"
    out = os.path.join(dest_dir, label + ".gbk")
    SeqIO.write(rec, out, "genbank")
    return out, rec


def run_antismash(gbk, out_dir, cpus):
    """Re-detect one condensed record, with clusterblast enabled.

    --genefinding-tool none is required: the record already carries its gene
    calls from the original annotation, and re-calling them here would make the
    references inconsistent with the BiG-SCAPE inputs built from the same
    records.
    """
    # antiSMASH creates --output-dir with a non-recursive os.mkdir, so its
    # parent has to exist or the run dies before doing any work.
    os.makedirs(os.path.dirname(os.path.abspath(out_dir)), exist_ok=True)
    antismash = os.environ.get("ANTISMASH", "antismash")
    asdb = os.environ.get("ASDB")
    cmd = antismash.split() + [
        "--genefinding-tool", "none",
        "--cb-knownclusters", "--cb-subclusters",
        "--output-dir", out_dir,
        "--output-basename", os.path.basename(gbk)[:-4],
        "--cpus", str(cpus), gbk,
    ]
    if asdb:
        cmd[len(antismash.split()):len(antismash.split())] = ["--databases", asdb]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "").strip().splitlines()
        return r.returncode, " | ".join(tail[-3:])[:300]
    return 0, ""


def collect(out_dir, input_gbk):
    """The region GenBank and clusterblast table antiSMASH just wrote.

    The input file is copied into the output directory by antiSMASH, so it is
    excluded by name rather than by glob.
    """
    regs = [f for f in glob.glob(os.path.join(out_dir, "*.region*.gbk"))
            if os.path.basename(f) != os.path.basename(input_gbk)]
    txts = sorted(glob.glob(os.path.join(out_dir, "knownclusterblast", "*.txt")))
    return regs, txts


def significant_hits(txt):
    """Number of MIBiG clusters in the table's Significant hits section.

    A table with none gives an all-zero clusterblast vector, and DiscERN's
    dendrogram uses cosine distance, which is undefined for such a vector.
    """
    t = open(txt, errors="ignore").read()
    m = re.search(r"Significant hits:\s*\n(.*?)(\n\s*\n|\nDetails)", t, re.S)
    return len([l for l in (m.group(1).splitlines() if m else []) if l.strip()])


def products(rec):
    return {p for ft in rec.features if ft.type == "region"
            for p in ".".join(ft.qualifiers.get("product", [])).split(".")}


def n_cds(rec):
    return sum(1 for ft in rec.features if ft.type == "CDS")


def build(src_glob, label_of, out_flat, out_trees, work, cpus, rows, dropped):
    """Re-detect every record matched by src_glob and file the results."""
    staging = os.path.join(work, "staged")
    os.makedirs(staging, exist_ok=True)
    for src in sorted(glob.glob(src_glob)):
        label = label_of(src)
        gbk, src_rec = stage(src, label, staging)
        as_out = os.path.join(work, "antismash", label)
        rc, err = run_antismash(gbk, as_out, cpus)
        regs, txts = collect(as_out, gbk)

        if rc != 0 or len(regs) != 1 or not txts:
            dropped.append(dict(label=label, reason=(
                f"antiSMASH exit {rc}: {err}" if rc else
                f"{len(regs)} regions detected, expected 1" if len(regs) != 1
                else "no knownclusterblast table")))
            continue

        rec = SeqIO.read(regs[0], "genbank")
        if n_cds(rec) < n_cds(src_rec):
            dropped.append(dict(label=label, reason=(
                f"re-detection kept {n_cds(rec)} of {n_cds(src_rec)} genes")))
            continue

        txt = max(txts, key=os.path.getsize)
        nhits = significant_hits(txt)
        if out_flat and nhits == 0:
            dropped.append(dict(label=label, reason=(
                "no significant clusterblast hit; an all-zero vector makes "
                "the cosine distance undefined")))
            continue

        if out_flat:
            shutil.copy(regs[0], os.path.join(out_flat, label + ".gbk"))
            shutil.copy(txt, os.path.join(out_flat, label + ".txt"))
        else:
            d = os.path.join(out_trees, label)
            os.makedirs(os.path.join(d, "knownclusterblast"), exist_ok=True)
            shutil.copy(regs[0], os.path.join(d, os.path.basename(regs[0])))
            for x in txts:
                shutil.copy(x, os.path.join(d, "knownclusterblast",
                                            os.path.basename(x)))

        rows.append(dict(label=label,
                         set=("reference" if out_flat else "query"),
                         product=".".join(sorted(products(rec))),
                         bp=len(rec.seq), n_cds=n_cds(rec),
                         mibig_hits=nhits))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bigscape", required=True,
                    help="directory holding known/, predicted/ and excluded/")
    ap.add_argument("--out", required=True, help="DiscERN input directory to write")
    ap.add_argument("--work", default=None,
                    help="scratch directory (default: <out>/_work, removed on success)")
    ap.add_argument("--cpus", type=int, default=4)
    a = ap.parse_args()

    if shutil.which(os.environ.get("ANTISMASH", "antismash").split()[0]) is None \
            and "ANTISMASH" not in os.environ:
        sys.exit("FATAL: antismash not on PATH. Activate its environment, or set "
                 "ANTISMASH='python -m antismash'")
    if shutil.which("hmmpfam2") is None:
        sys.exit("FATAL: hmmpfam2 not on PATH. It is HMMER2, a separate package "
                 "from HMMER3, and the clusterblast stage needs it.")

    work = a.work or os.path.join(a.out, "_work")
    known = os.path.join(a.out, "known")
    excl = os.path.join(a.out, "known_excluded")
    query = os.path.join(a.out, "predicted_condensed")
    for d in (known, excl, query, work):
        os.makedirs(d, exist_ok=True)
    for d in (known, excl):
        for old in glob.glob(os.path.join(d, "*")):
            os.remove(old)          # a stale pair would unbalance the set
    if os.path.isdir(query):
        shutil.rmtree(query)
        os.makedirs(query)

    # The label is the genome: <accession>.region001.gbk -> <accession>
    label_of = lambda f: os.path.basename(f).split(".region")[0]
    rows, dropped = [], []
    build(os.path.join(a.bigscape, "known", "*.gbk"), label_of,
          known, None, os.path.join(work, "known"), a.cpus, rows, dropped)
    build(os.path.join(a.bigscape, "excluded", "*.gbk"), label_of,
          excl, None, os.path.join(work, "excluded"), a.cpus, rows, dropped)
    build(os.path.join(a.bigscape, "predicted", "*.gbk"), label_of,
          None, query, os.path.join(work, "predicted"), a.cpus, rows, dropped)

    if dropped:
        print(f"dropped {len(dropped)} record(s):")
        for d in dropped:
            print(f"  {d['label']}: {d['reason']}")
    if not rows:
        sys.exit("FATAL: no record survived re-detection - see the reasons above")

    man = os.path.join(a.out, "reference_manifest.tsv")
    with open(man, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    g = len(glob.glob(os.path.join(known, "*.gbk")))
    t = len(glob.glob(os.path.join(known, "*.txt")))
    ge = len(glob.glob(os.path.join(excl, "*.gbk")))
    q = len(glob.glob(os.path.join(query, "*", "*.region*.gbk")))
    print(f"references {g} gbk / {t} txt   excluded {ge}   queries {q}")
    print("product classes: " + ", ".join(
        f"{k} x{v}" for k, v in collections.Counter(r["product"] for r in rows).most_common()))
    if g != t:
        sys.exit(f"FATAL: reference set unbalanced ({g} gbk, {t} txt). DiscERN "
                 "returns without running when the counts differ.")
    shutil.rmtree(work, ignore_errors=True)
    print(f"wrote {man}")


if __name__ == "__main__":
    main()
