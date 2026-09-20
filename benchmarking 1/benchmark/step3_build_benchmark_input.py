#!/usr/bin/env python3
"""
step3_build_benchmark_input.py - antiSMASH output in, benchmark inputs out.

    python step3_build_benchmark_input.py \
        --antismash-known     ../antiSMASH/known \
        --antismash-predicted ../antiSMASH/predicted \
        --out                 .

One step, no intermediate trim directory. Earlier this was two scripts with a
`pvd_all` / `pvd_unknown` staging area between them; the trimmed regions were
never a deliverable in their own right, only a way to pass data along, so they
are now held in memory and never written.

What it does, per genome directory of antiSMASH regions:

  1. Score every region for pyoverdine markers (PvdP, PvdO, PvdA).
  2. BLAST every NRPS protein against the PAO1 PvdI/PvdJ/PvdD/PvdL reference.
     A region qualifies if it carries a marker OR its NRPS are pyoverdine
     orthologues - the second test is what recovers loci that antiSMASH split,
     since pvdL usually sits in a separate region from pvdI/pvdJ/pvdD.
  3. Trim each qualifying region to the span of its pyoverdine CDSs.
  4. Concatenate a genome's trimmed loci into ONE record, so each genome is a
     single comparable unit rather than several nodes sharing its similarity.

Concatenation costs one artificial gene adjacency per join. Parts are ordered
identically in every genome (peptide synthetases first, pvdL last) so the
artefact is constant rather than arbitrary; domain content is unaffected.

Two behaviours that were previously special-cased are now derived from the
data:

  * A genome whose qualifying regions sit on two different contigs, each
    carrying its own chromophore marker, is written as two records. That is
    the two-organisms-in-one-assembly case; it is detected rather than
    hardcoded, and every split is listed in the manifest.
  * Genome labels come from the directory names, so the script works with the
    long naming (`SN_3_w_a`) as well as any other scheme. The previous version
    assumed short labels and failed against renamed directories.

Requires: biopython, blastp and makeblastdb on PATH.
Outputs: <out>/bigscape/{known,predicted}/<label>.region001.gbk
         <out>/benchmark_input_manifest.tsv
"""
import os, re, csv, glob, shutil, tempfile, argparse, subprocess, collections

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.SeqFeature import SeqFeature, FeatureLocation


# --------------------------------------------------------------------------
# lifted verbatim from pvd_trim.py
# --------------------------------------------------------------------------


PVD_SPECIFIC = {"PvdP", "PvdO"}          # pyoverdine chromophore maturation

PVD_SUPPORT  = {"Orn_monoox"}            # PvdA; hydroxamate siderophores broadly

NRPS_CORE    = {"AMP-binding", "Condensation", "PP-binding", "A-OX"}

PVDL_STARTER = "FAAL_cd05931"            # PvdL fatty-acyl-AMP ligase starter

CHROMOPHORE_MONOMERS = {"Tyr"}

TAILORING    = {"Aminotran_5", "Aminotran_3", "TauD", "TBH_Asp", "IBH_Asp",
                "IBH_His", "Thioesterase", "Orn_monoox", "PvdP", "PvdO"}

_NORM = [
    (r"^(fo|f|ac|a|c|n5|oh)*-?oh-?orn$", "Orn"), (r"^orn$", "Orn"),
    (r"^cit$", "Cit"),
    (r"^(oh)?asp$", "Asp"),  (r"^(oh)?asn$", "Asn"),
    (r"^(e|oh)?lys$", "Lys"), (r"^(a|oh)?thr$", "Thr"),
    (r"^(oh)?his$", "His"),  (r"^(f|oh)?ser$", "Ser"),
    (r"^(oh)?dab$", "Dab"),  (r"^hse$", "Hse"),
]

_THREE = {"ala","arg","asn","asp","cys","gln","glu","gly","his","ile","leu",
          "lys","met","phe","pro","ser","thr","trp","tyr","val"}

_PKS = {"mal","mmal","mxmal","emal","ccmal","me-ccmal","redmal","ohmal",
        "pk","ohmmal","nh2"}

def norm_residue(tok):
    """Normalise one monomer name to a base residue, or None if not a residue."""
    t = re.sub(r"[()\[\]\s]", "", str(tok)).lower()
    t = re.sub(r"^[dl]-", "", t)
    if t == "x":
        return "?"                      # A-domain called, specificity unresolved
    if t in ("nh2", "", "nan", "?", "-") or t in _PKS:
        return None
    if re.match(r"^(me-)?(cc|oh|red|m|mx|e)?mal$", t):
        return None
    for pat, rep in _NORM:
        if re.match(pat, t):
            return rep
    if t in _THREE:
        return t.capitalize()
    for k in ("orn", "asp", "asn", "lys", "thr", "his", "ser", "dab", "hse", "cit"):
        if k in t:
            return k.capitalize()
    return t.capitalize() if t else None

def cds_records(rec):
    """Per-CDS summary of one region: position, strand, domains, modules."""
    out = []
    for ft in rec.features:
        if ft.type != "CDS":
            continue
        q = ft.qualifiers
        out.append(dict(
            lt=q.get("locus_tag", ["?"])[0],
            start=int(ft.location.start), end=int(ft.location.end),
            strand=ft.location.strand,
            sm={x.split(" (")[0] for x in q.get("sec_met_domain", [])},
            kind=q.get("gene_kind", [""])[0],
            aa=len(q.get("translation", [""])[0]),
            gene=q.get("gene", [""])[0] or "",
            product=q.get("product", [""])[0] or "",
            mods=[]))
    idx = {c["lt"]: c for c in out}
    for ft in rec.features:
        if ft.type != "aSModule":
            continue
        pair = ft.qualifiers.get("monomer_pairings", [""])[0]
        mono = pair.split("->")[-1].strip() if pair else ""
        for lt in ft.qualifiers.get("locus_tags", []):
            if lt in idx:
                idx[lt]["mods"].append(dict(pos=int(ft.location.start), mono=mono))
    for c in out:
        c["mods"].sort(key=lambda m: m["pos"] if c["strand"] != -1 else -m["pos"])
    return out

def region_meta(rec):
    prod, edge = [], "?"
    for ft in rec.features:
        if ft.type == "region":
            prod = ft.qualifiers.get("product", [])
            edge = ft.qualifiers.get("contig_edge", ["?"])[0]
    return ".".join(prod), edge

def score_region(cdss):
    """Pyoverdine evidence score for one region."""
    marks = set().union(*[c["sm"] for c in cdss]) if cdss else set()
    spec, supp = marks & PVD_SPECIFIC, marks & PVD_SUPPORT
    nrps = [c for c in cdss if (c["sm"] & NRPS_CORE) and c["mods"]]
    score = 10*len(spec) + 3*len(supp) + (2 if nrps else 0)
    return score, sorted(spec), sorted(supp), sum(len(c["mods"]) for c in cdss), nrps

def pvd_cdss(cdss, nrps_keep=None):
    """CDSs kept in the trim: pyoverdine synthetases + pvd tailoring genes.

    nrps_keep restricts the synthetases to those passing the homology filter,
    so a merged region does not drag a neighbouring cluster into the trim.
    Passing None keeps every module-bearing NRPS (marker-only mode).
    """
    out = []
    for c in cdss:
        is_nrps = bool(c["mods"] and (c["sm"] & NRPS_CORE))
        if is_nrps:
            if nrps_keep is None or c["lt"] in nrps_keep:
                out.append(c)
        elif c["sm"] & (PVD_SPECIFIC | PVD_SUPPORT | TAILORING):
            out.append(c)
    return out

def order_synthetases(nrps_cdss):
    """Order NRPS CDSs along the assembly line.

    Within one strand, transcription order (ascending start on +, descending
    on -) reproduces module order for the canonical pvd architecture.  When the
    locus uses both strands, gene count alone picks the wrong group first, so
    the arrangement is chosen by two structural anchors: the terminal
    thioesterase must come last, and a starter module (first module with no
    upstream condensation domain) should come first.
    """
    plus = sorted([c for c in nrps_cdss if c["strand"] != -1], key=lambda c: c["start"])
    minus = sorted([c for c in nrps_cdss if c["strand"] == -1], key=lambda c: -c["start"])
    groups = [g for g in (minus, plus) if g]
    if len(groups) < 2:
        return groups[0] if groups else []
    cand = [groups[0] + groups[1], groups[1] + groups[0]]

    def penalty(seq):
        p = 0
        te = [i for i, c in enumerate(seq) if "Thioesterase" in c["sm"]]
        if te and max(te) != len(seq) - 1:
            p += 10                      # TE-bearing synthetase is not last
        if len(seq) > 1 and "Thioesterase" in seq[0]["sm"]:
            p += 5                       # ... and must not be first
        return p

    cand.sort(key=penalty)
    return cand[0]

def trim_record(rec, keep, flank=0):
    """Slice a region down to the span of the pyoverdine-associated CDSs."""
    lo = max(0, min(c["start"] for c in keep) - flank)
    hi = min(len(rec.seq), max(c["end"] for c in keep) + flank)
    sub = rec[lo:hi]
    sub.id, sub.name = rec.id, rec.name[:16]
    ann = dict(rec.annotations)
    ann["molecule_type"] = "DNA"
    ann["comment"] = (f"Trimmed to the pyoverdine BGC by pvd_trim.py: bases "
                      f"[{lo}:{hi}] of a {len(rec.seq)} bp antiSMASH region.\n"
                      + str(rec.annotations.get("comment", "")))
    sub.annotations = ann
    return sub, lo, hi

PVD_NRPS_MIN_ID = 45.0

PVD_NRPS_MIN_BITS_PER_AA = 0.50

PAO1_PVD_LOCI = {"ctg1_2454": "PvdI", "ctg1_2453": "PvdJ",
                 "ctg1_2452": "PvdD", "ctg1_2476": "PvdL"}

def build_pvd_reference(pao1_region_gbk, out_faa):
    """Write PAO1 PvdI/PvdJ/PvdD/PvdL protein sequences from an antiSMASH region."""
    rec = SeqIO.read(pao1_region_gbk, "genbank")
    got = {}
    for ft in rec.features:
        if ft.type != "CDS":
            continue
        lt = ft.qualifiers.get("locus_tag", ["?"])[0]
        if lt in PAO1_PVD_LOCI:
            got[PAO1_PVD_LOCI[lt]] = ft.qualifiers["translation"][0]
    missing = set(PAO1_PVD_LOCI.values()) - set(got)
    if missing:
        raise RuntimeError(f"PAO1 reference incomplete, missing {sorted(missing)}")
    os.makedirs(os.path.dirname(out_faa) or ".", exist_ok=True)
    with open(out_faa, "w") as fh:
        for k, v in got.items():
            fh.write(f">{k}_PAO1\n{v}\n")
    return {k: len(v) for k, v in got.items()}

def nrps_proteins(rec, cdss):
    """(locus_tag, protein) for every module-bearing NRPS CDS in a region."""
    want = {c["lt"] for c in cdss if c["mods"] and (c["sm"] & NRPS_CORE)}
    out = []
    for ft in rec.features:
        if ft.type != "CDS":
            continue
        lt = ft.qualifiers.get("locus_tag", ["?"])[0]
        if lt in want and ft.qualifiers.get("translation"):
            out.append((lt, ft.qualifiers["translation"][0]))
    return out

def blastp_best(query_faa, db, threads=8, evalue=1e-20):
    """locus_tag -> (subject, pident, bitscore, aln_len) for the best hit."""
    import subprocess
    if not os.path.getsize(query_faa):
        return {}
    r = subprocess.run(
        ["blastp", "-query", query_faa, "-db", db, "-outfmt",
         "6 qseqid sseqid pident length bitscore", "-max_target_seqs", "5",
         "-evalue", str(evalue), "-num_threads", str(threads)],
        capture_output=True, text=True)
    best = {}
    for ln in r.stdout.strip().split("\n"):
        if not ln:
            continue
        q, s, pid, L, bits = ln.split("\t")
        pid, bits, L = float(pid), float(bits), int(L)
        if q not in best or bits > best[q][2]:
            best[q] = (s, pid, bits, L)
    return best


# --------------------------------------------------------------------------
# lifted verbatim from the previous step-3 script
# --------------------------------------------------------------------------


ACC_RE = re.compile(r"(?:NZ|NC)_[A-Z]*_?[0-9]{5,}(?:\.[0-9]+)?"
                    r"|(?:GCA|GCF)_[0-9]{9}(?:\.[0-9]+)?"
                    r"|\b[A-Z]{2,4}[0-9]{5,}(?:\.[0-9]+)?")

def accession_of(cell):
    """First real accession in a workbook cell.

    Five cells read 'Fragmented <ACC>' and others carry footnote marks or
    '<A> / <B>' alternatives, so the leading whitespace-delimited token is not
    the accession: it collapsed five genomes onto one filename and made
    --exclude GCA_000730605 silently match nothing.
    """
    m = ACC_RE.search(str(cell))
    return m.group(0) if m else re.sub(r"[^A-Za-z0-9._-]+", "_", str(cell))[:24]

SPACER = 100          # bp of N between concatenated loci; marks the seam

WRAPPERS = ("region", "cand_cluster", "protocluster", "proto_core")

def one_region(rec, label):
    """Replace all wrapper features with ONE coherent region spanning the record.

    A concatenated genome carries one region feature per part, and BiG-SCAPE
    run with --record-type region turns each into its own record -- which is
    exactly the per-genome splitting this staging exists to prevent.  The
    replacement declares the whole staged record as a single region with a
    single candidate cluster and protocluster, and carries over the real
    product, category and detection rules from the parts (unioned) so nothing
    about the chemistry is invented.
    """
    from Bio.SeqFeature import SeqFeature, FeatureLocation
    prods, cats, rules, tools = [], [], [], []
    for ft in rec.features:
        if ft.type not in WRAPPERS:
            continue
        for x in ft.qualifiers.get("product", []):
            if x not in prods:
                prods.append(x)
        for x in ft.qualifiers.get("category", []):
            if x not in cats:
                cats.append(x)
        for k in ("rules", "detection_rules", "detection_rule"):
            for x in ft.qualifiers.get(k, []):
                if x not in rules:
                    rules.append(x)
        tools += ft.qualifiers.get("tool", [])
    if not prods:
        prods = ["NRPS"]
    if not cats:
        cats = ["NRPS"]
    L = len(rec.seq)
    kept = [ft for ft in rec.features if ft.type not in WRAPPERS]
    loc = FeatureLocation(0, L)
    common = dict(product=prods, contig_edge=["False"], tool=["antismash"])
    new = [
        SeqFeature(type="region", location=loc, qualifiers=dict(
            common, region_number=["1"], candidate_cluster_numbers=["1"],
            rules=rules or ["staged"])),
        SeqFeature(type="cand_cluster", location=loc, qualifiers=dict(
            common, candidate_cluster_number=["1"], kind=["neighbouring"],
            protoclusters=["1"], detection_rules=rules or ["staged"])),
        SeqFeature(type="protocluster", location=loc, qualifiers=dict(
            common, protocluster_number=["1"], category=cats,
            core_location=[f"[0:{L}]"], aStool=["rule-based-clusters"],
            cutoff=["30000"], neighbourhood=["20000"],
            detection_rule=rules[:1] or ["staged"])),
        SeqFeature(type="proto_core", location=loc, qualifiers=dict(
            product=prods, protocluster_number=["1"], tool=["antismash"],
            aStool=["rule-based-clusters"], cutoff=["30000"],
            neighbourhood=["20000"], detection_rule=rules[:1] or ["staged"])),
    ]
    rec.features = new + kept
    return rec

def merge_records(recs, new_id, spacer=SPACER):
    """Concatenate records into one, offsetting every feature; N-spacer seams."""
    seq = ""
    feats, seams = [], []
    for i, r in enumerate(recs):
        off = len(seq)
        for ft in r.features:
            if ft.type == "source":
                continue
            feats.append(ft._shift(off))
        seq += str(r.seq)
        if i < len(recs) - 1:
            seams.append((len(seq), len(seq) + spacer))
            seq += "N" * spacer
    out = SeqRecord(Seq(seq), id=new_id[:16], name=new_id[:16],
                    description=f"pyoverdine BGC of {new_id}, "
                                f"{len(recs)} locus/loci concatenated")
    out.features = feats
    for lo, hi in seams:
        out.features.append(SeqFeature(
            type="misc_feature",
            location=__import__("Bio.SeqFeature", fromlist=["FeatureLocation"])
                     .FeatureLocation(lo, hi),
            qualifiers={"note": ["concatenation seam inserted by "
                                 "build_one_per_genome.py; not genomic sequence"]}))
    # The antiSMASH structured comment must survive the merge.  Without it
    # GBK.get_as_version() cannot read a version, falls back to antiSMASH 4
    # semantics, looks for `cluster` features instead of `region`, finds none
    # and rejects the file with "does not contain an antiSMASH cluster or
    # region feature" -- even though a valid region feature is present.
    out.annotations = dict(recs[0].annotations)
    out.annotations.update({"molecule_type": "DNA", "topology": "linear",
                       "organism": new_id, "source": new_id,
                       "comment": ("One-record-per-genome staging for BiG-SCAPE. "
                                   f"{len(recs)} trimmed pyoverdine locus/loci "
                                   f"joined by {spacer} bp N spacers.\n" +
                                   "\n".join(f"part {i+1}: {r.id} {len(r.seq)} bp"
                                             for i, r in enumerate(recs)))})
    return out

def n_pvd_nrps(rec):
    """Ordering key: how many pyoverdine-orthologous synthetases the record holds."""
    n = 0
    for ft in rec.features:
        if ft.type != "CDS":
            continue
        sm = " ".join(ft.qualifiers.get("sec_met_domain", []))
        if "AMP-binding" in sm or "Condensation" in sm:
            n += 1
    return n

def stage(recs, label, out_dir, prefix=""):
    recs = sorted(recs, key=lambda r: (-n_pvd_nrps(r), r.id))
    m = merge_records(recs, label) if len(recs) > 1 else recs[0]
    if len(recs) == 1:
        m.id, m.name = label[:16], label[:16]
        m.annotations.setdefault("molecule_type", "DNA")
    m = one_region(m, label)
    # ".region001" is load-bearing: BiG-SCAPE's default --include-gbk is
    # ["cluster", "region"] and filter_files() matches on the FILENAME, so a
    # file without one of those substrings is silently discarded before any
    # parsing happens -- the run then fails with "No valid input GBKs were
    # found" and no per-file diagnostic.
    # the known/predicted folder already says which arm this is, so the arm
    # prefix the earlier version baked into every filename is dropped
    stem = f"{prefix}__{label}" if prefix else label
    fo = os.path.join(out_dir,
                      f"{re.sub(r'[^A-Za-z0-9._-]+','_',stem)}.region001.gbk")
    SeqIO.write(m, fo, "genbank")
    cds = sum(1 for ft in m.features if ft.type == "CDS")
    return fo, len(m.seq), cds, len(recs)

def region_inventory(genome_dir):
    """Every region product in a genome, for reporting when no NRPS exists."""
    out = []
    for f in sorted(glob.glob(os.path.join(genome_dir, "*.gbk"))):
        rec = SeqIO.read(f, "genbank")
        for ft in rec.features:
            if ft.type == "region":
                out.append(".".join(ft.qualifiers.get("product", [])))
    return sorted(set(out))

def pick_relevant_nrps(genome_dir):
    """For a genome with no pyoverdine BGC: its most relevant NRPS region.

    Requires a genuine NRPS product AND at least one aSModule.  An arylpolyene
    or betalactone region carrying a single AMP-binding domain is a fatty-acyl
    AMP ligase, not a synthetase, and staging one as "the relevant NRPS" would
    put a node in the comparison that cannot share domain content with any
    pyoverdine and is a guaranteed singleton.  Better to report the absence.
    """
    best, best_key = None, None
    for f in sorted(glob.glob(os.path.join(genome_dir, "*.gbk"))):
        rec = SeqIO.read(f, "genbank")
        prod = ""
        for ft in rec.features:
            if ft.type == "region":
                prod = ".".join(ft.qualifiers.get("product", []))
        nmod = sum(1 for ft in rec.features if ft.type == "aSModule")
        if ("NRPS" not in prod and "NRP-" not in prod) or nmod == 0:
            continue
        sidero = 1 if ("metallophore" in prod.lower() or "sidero" in prod.lower()) else 0
        key = (sidero, nmod, len(rec.seq))
        if best_key is None or key > best_key:
            best, best_key, bf, bp = rec, key, os.path.basename(f), prod
    return (best, bf, bp, best_key) if best is not None else (None, "", "", None)

# ---------------------------------------------------------------------------
# one-step driver: antiSMASH regions -> benchmark-ready records
# ---------------------------------------------------------------------------

# Known-arm accessions excluded as unsuitable references. The first six are
# genomes whose curated structure disagrees with what their own BGC encodes;
# CP034337 is a declared surrogate; CP011835 is Azomonas macrocytogenes, an
# azotobactin producer with no PvdP/PvdO, so it is not a pyoverdine at all.
# Exactly the six accessions specified for exclusion. CP034337 (declared
# surrogate) and CP011835 (Azomonas, azotobactin) are NOT excluded: both are
# analysed. They are informative in the comparison rather than absent from it,
# and neither was on the list.
DEFAULT_EXCLUDE = ["LT629746", "CP176771", "GCA_000730605", "AP039450",
                   "CP028517", "CP023269"]

# One genome is filed under a different accession by the antiSMASH run than by
# the workbook and every downstream table. Label it the way the rest of the
# project does, so results join up.
LABEL_ALIAS = {"GCA_000278565.1": "AKVH01000000"}   # Pseudomonas sp. Ag1


def genome_label(dirname, arm):
    """Label for a genome directory.

    Known-arm directories are '<accession>_<species blurb>'; predicted-arm
    directories are already the genome name. Deriving the label from the
    directory rather than from a lookup table is what lets this run against
    either naming scheme - the previous version hardcoded short labels and
    could not find renamed directories.
    """
    if arm == "known":
        acc = accession_of(dirname) or dirname.split("_")[0]
        return LABEL_ALIAS.get(acc, acc)
    return dirname


def trim_genome(gdir, db, threads, rescue="any"):
    """Qualifying pyoverdine regions of one genome, trimmed.

    Returns (trimmed_records, info) where info carries the per-region audit.
    A region always qualifies if it bears a chromophore marker. A marker-free
    region is rescued on NRPS homology, and `rescue` sets how strictly:

      "edge"  only if the region runs to a contig edge - the split-locus case
              in a draft assembly. Without this restriction an NRPS-rich
              genome (P. protegens Pf-5 is the example that forced it)
              contributes unrelated synthetases.
      "any"   any marker-free region whose NRPS are pyoverdine orthologues.

    The two arms differ, and deliberately. The known arm is largely draft
    assemblies, where a split locus does end at a contig edge, so "edge" is
    both safe and sufficient. The predicted arm is near-complete assemblies
    where pvdL sits in its own region in the middle of a contig; "edge" would
    discard it and lose the chromophore synthetase. Using one rule for both
    would change results on one arm or the other, so the asymmetry is kept and
    named rather than quietly unified.
    """
    files = sorted(glob.glob(os.path.join(gdir, "*.region*.gbk")))
    if not files:
        return [], []

    allreg, qf = [], os.path.join(os.path.dirname(db), "_q.faa")
    with open(qf, "w") as fh:
        for f in files:
            rec = SeqIO.read(f, "genbank")
            cdss = cds_records(rec)
            score, spec, supp, nmod, nrps = score_region(cdss)
            prod, edge = region_meta(rec)
            allreg.append(dict(f=f, rec=rec, cdss=cdss, score=score, spec=spec,
                               supp=supp, nmod=nmod, nrps=nrps, prod=prod, edge=edge))
            for lt, prot in nrps_proteins(rec, cdss):
                fh.write(f">{os.path.basename(f)}|{lt}\n{prot}\n")

    best = blastp_best(qf, db, threads=threads) if os.path.getsize(qf) else {}

    cands = []
    for k in allreg:
        hits = {}
        for key, (subj, pid, bits, L) in best.items():
            rf, lt = key.split("|", 1)
            if rf != os.path.basename(k["f"]):
                continue
            aa = next((c["aa"] for c in k["cdss"] if c["lt"] == lt), 0) or 1
            if pid >= PVD_NRPS_MIN_ID or bits / aa >= PVD_NRPS_MIN_BITS_PER_AA:
                hits[lt] = (subj, pid, bits, L)
        k["pvd_nrps"] = hits
        rescued = bool(hits) and (k["edge"] == "True" if rescue == "edge" else True)
        if k["spec"] or rescued:
            k["nrps"] = [c for c in k["nrps"] if c["lt"] in hits]
            cands.append(k)
    cands.sort(key=lambda x: (-x["score"], -len(x["pvd_nrps"]), -x["nmod"]))

    recs, info = [], []
    for k in cands:
        keep = pvd_cdss(k["cdss"], {c["lt"] for c in k["nrps"]})
        if not keep:
            continue
        sub, lo, hi = trim_record(k["rec"], keep, 0)
        # remember which contig this locus came from, for the split test below
        contig = re.search(r"contig_\d+", os.path.basename(k["f"])) or \
                 re.search(r"contig_\d+", str(k["rec"].id))
        sub.annotations["source_contig"] = contig.group(0) if contig else "contig_1"
        sub.annotations["has_chromophore_marker"] = bool(k["spec"])
        recs.append(sub)
        info.append(dict(region=os.path.basename(k["f"]), product=k["prod"],
                         contig_edge=k["edge"], region_bp=len(k["rec"].seq),
                         trimmed_bp=len(sub.seq), trim_start=lo, trim_end=hi,
                         n_cds_kept=len(keep), markers=",".join(k["spec"] + k["supp"]),
                         pvd_nrps=";".join(sorted(k["pvd_nrps"]))))
    return recs, info


# Product classes used as a negative control, most widely shared first. A
# negative control must be a locus the cohort genuinely shares, otherwise its
# isolation in the output says nothing about the genome and only reflects that
# nothing else carries that product.
# A siderophore locus of any kind is preferred: it is the nearest functional
# analogue to a pyoverdine, so if the genome has one that is the honest thing
# to compare. Only a genome with no siderophore at all falls through to a
# widely shared non-target class, which is a true negative control.
SIDEROPHORE_HINTS = ("siderophore", "metallophore")
NEG_CONTROL_PREFER = ("arylpolyene", "terpene-precursor", "RiPP-like")


def pick_negative_control(gdir):
    """Best stand-in locus for a genome with no NRPS at all.

    Two of the predicted genomes carry no condensation domain anywhere in the
    genome and no siderophore synthetase of any kind, so there is no
    pyoverdine-adjacent locus to compare and no honest way to manufacture one.
    They are still worth carrying through: a benchmark should show what the
    tools do with a genome that has none of the target, and dropping them
    would make the predicted arm look cleaner than the data is.

    The locus chosen is the largest region of the most widely shared product
    class (arylpolyene, in 29 of the 30 predicted genomes), so the choice does
    not depend on something idiosyncratic to these two genomes.

    Do not expect it to cluster with anything. Every other genome contributes
    its PYOVERDINE record, not its arylpolyene, so a negative control has no
    counterpart in the comparison and comes out a singleton. Measured: both
    controls sit at distance 0.802 from their nearest neighbour - each other -
    against a 0.30 cutoff. That is the intended outcome and the informative
    one; it shows what the clustering does with a genome that has none of the
    target, which is not visible if the genome is simply dropped.
    """
    best = None
    for f in sorted(glob.glob(os.path.join(gdir, "*.region*.gbk"))):
        rec = SeqIO.read(f, "genbank")
        prod, _ = region_meta(rec)
        try:
            rank = next(i for i, p in enumerate(NEG_CONTROL_PREFER) if p in prod)
        except StopIteration:
            rank = len(NEG_CONTROL_PREFER)
        if any(h in prod.lower() for h in SIDEROPHORE_HINTS):
            rank = -1                      # a siderophore always wins
        key = (rank, -len(rec.seq))
        if best is None or key < best[0]:
            best = (key, rec, prod, os.path.basename(f))
    if best is None:
        return None, "", ""
    return best[1], best[2], best[3]


def split_by_organism(recs):
    """Group a genome's loci into separate records when the assembly holds two
    organisms.

    An assembly file occasionally contains two chromosome-sized records, each
    with its own complete pyoverdine cluster. Those must not be merged: they
    are different organisms and merging them would invent a chimera. The test
    is structural - two or more contigs, each carrying a region with its own
    chromophore marker - so it is derived from the data rather than from a
    hardcoded genome name, which is what the previous version used.

    A locus merely split across regions of the SAME contig groups normally,
    and so does a fragmented assembly where only one contig bears a marker.
    """
    bycontig = collections.defaultdict(list)
    for r in recs:
        bycontig[r.annotations.get("source_contig", "contig_1")].append(r)
    marked = [c for c, rr in bycontig.items()
              if any(x.annotations.get("has_chromophore_marker") for x in rr)]
    if len(bycontig) > 1 and len(marked) > 1:
        return [(c, bycontig[c]) for c in sorted(bycontig)]
    return [(None, recs)]


def main():
    ap = argparse.ArgumentParser(
        description="antiSMASH output -> one benchmark-ready record per genome")
    ap.add_argument("--antismash-known", required=True)
    ap.add_argument("--antismash-predicted", required=True)
    ap.add_argument("--out", default=".")
    ap.add_argument("--pao1", default=None,
                    help="PAO1 region GenBank for the PvdI/J/D/L reference; "
                         "found automatically inside --antismash-known if omitted")
    ap.add_argument("--exclude", nargs="*", default=DEFAULT_EXCLUDE)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--rescue-known", default="edge", choices=["edge", "any"],
                    help="how marker-free regions are rescued in the known arm")
    a = ap.parse_args()

    # ---- reference --------------------------------------------------------
    pao1 = a.pao1
    if not pao1:
        hits = glob.glob(os.path.join(a.antismash_known, "AE004091*",
                                      "*region008.gbk"))
        if not hits:
            ap.error("no PAO1 AE004091 region008 found under --antismash-known; "
                     "pass --pao1 explicitly")
        pao1 = hits[0]
    # The BLAST database goes to a real temp directory, never under --out:
    # makeblastdb fails with exit 3 on a cloud-synced filesystem, and a
    # scratch database has no business living in the deliverable folder.
    refdir = tempfile.mkdtemp(prefix="pvdref_")
    faa = os.path.join(refdir, "pao1_pvd_nrps.faa")
    print("reference:", build_pvd_reference(pao1, faa))
    db = os.path.join(refdir, "pvddb")
    subprocess.run(["makeblastdb", "-in", faa, "-dbtype", "prot", "-out", db],
                   check=True, capture_output=True)

    rows = []
    for arm, src in (("known", a.antismash_known),
                     ("predicted", a.antismash_predicted)):
        out_dir = os.path.join(a.out, "bigscape", arm)
        excl_dir = os.path.join(a.out, "bigscape", "excluded")
        if os.path.isdir(excl_dir) and arm == "known":
            for old in glob.glob(os.path.join(excl_dir, "*.gbk")):
                os.remove(old)
        os.makedirs(excl_dir, exist_ok=True)
        if os.path.isdir(out_dir):
            for old in glob.glob(os.path.join(out_dir, "*.gbk")):
                os.remove(old)          # stale output from a previous run would
        os.makedirs(out_dir, exist_ok=True)   # otherwise be counted as result

        for d in sorted(os.listdir(src)):
            gdir = os.path.join(src, d)
            if not os.path.isdir(gdir):
                continue
            label = genome_label(d, arm)

            excluded = arm == "known" and any(label.startswith(x) for x in a.exclude)
            if excluded:
                # Staged, but into a folder the analyses do not read. The
                # exclusion has to be justifiable from the same evidence
                # everything else is judged on, which means the record has to
                # exist rather than simply be absent.
                recs, info = trim_genome(gdir, db, a.threads, rescue="edge")
                why = "excluded reference"
                if not recs:
                    # Same fallback chain as the predicted arm. An excluded
                    # genome still has to be inspectable, or the exclusion
                    # rests on an absence the reader cannot check.
                    rec, srcfile, prod, _ = pick_relevant_nrps(gdir)
                    if rec is None:
                        rec, prod, srcfile = pick_negative_control(gdir)
                        why += f"; no pyoverdine locus, negative control: {prod}"
                    else:
                        why += f"; no pyoverdine locus, most relevant NRPS: {prod}"
                    if rec is None:
                        rows.append(dict(arm=arm, directory=d, label=label,
                                         staged="no", reason=why + "; nothing to stage",
                                         n_loci=0, bp="", n_cds="", regions="", file=""))
                        continue
                    recs, info = [rec], [dict(region=srcfile)]
                fo, bp, cds, n = stage(recs, label, excl_dir)
                rows.append(dict(arm=arm, directory=d, label=label,
                                 staged="excluded", reason=why,
                                 n_loci=n, bp=bp, n_cds=cds,
                                 regions=";".join(i["region"] for i in info),
                                 file=os.path.basename(fo)))
                continue

            recs, info = trim_genome(gdir, db, a.threads,
                                     rescue=("edge" if arm == "known" else "any"))

            if not recs:
                # A genome with no pyoverdine locus is still compared, using
                # its most relevant NRPS region instead, so the benchmark
                # reports on every genome rather than silently shrinking to the
                # positives. This applies to BOTH arms: Azomonas macrocytogenes
                # in the known arm makes azotobactin, which shares the
                # pyoverdine chromophore, and is a genuine near-miss outgroup.
                # Only a genome with no NRPS region carrying any module is
                # dropped: a lone adenylation domain is a fatty-acyl AMP
                # ligase, which cannot share domain content with any pyoverdine
                # and would contribute an uninformative node.
                if True:
                    rec, srcfile, prod, _ = pick_relevant_nrps(gdir)
                    note = "no pyoverdine locus; most relevant NRPS"
                    if rec is None:
                        rec, prod, srcfile = pick_negative_control(gdir)
                        note = ("no pyoverdine and no NRPS; nearest siderophore locus"
                                if any(h in prod.lower() for h in SIDEROPHORE_HINTS)
                                else "NEGATIVE CONTROL - no NRPS and no siderophore; locus")
                    if rec is not None:
                        fo, bp, cds, n = stage([rec], label, out_dir)
                        rows.append(dict(
                            arm=arm, directory=d, label=label, staged="yes",
                            reason=f"{note}: {prod}",
                            n_loci=n, bp=bp, n_cds=cds, regions=srcfile,
                            file=os.path.basename(fo)))
                        continue
                inv = region_inventory(gdir)
                rows.append(dict(
                    arm=arm, directory=d, label=label, staged="no",
                    reason="no NRPS region with any module; regions present: "
                           + ", ".join(inv),
                    n_loci=0, bp="", n_cds="", regions="", file=""))
                continue

            for contig, group in split_by_organism(recs):
                lab = f"{label}_{contig}" if contig else label
                fo, bp, cds, n = stage(group, lab, out_dir)
                rows.append(dict(
                    arm=arm, directory=d, label=lab, staged="yes",
                    reason="split: two organisms in one assembly" if contig else "",
                    n_loci=n, bp=bp, n_cds=cds,
                    regions=";".join(i["region"] for i in info),
                    file=os.path.basename(fo)))

    shutil.rmtree(refdir, ignore_errors=True)

    man = os.path.join(a.out, "benchmark_input_manifest.tsv")
    with open(man, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader(); w.writerows(rows)

    st = [r for r in rows if r["staged"] == "yes"]
    for arm in ("known", "predicted"):
        print(f"  {arm}: {sum(1 for r in st if r['arm'] == arm)} records staged, "
              f"{sum(1 for r in rows if r['arm'] == arm and r['staged'] == 'excluded')} "
              f"held out as excluded, "
              f"{sum(1 for r in rows if r['arm'] == arm and r['staged'] == 'no')} not staged")
    for r in rows:
        if "NEGATIVE CONTROL" in r["reason"] or "nearest siderophore" in r["reason"]:
            print(f"  negative control: {r['label']} ({r['reason'].split(': ',1)[1]})")
    for r in rows:
        if r["reason"].startswith("split"):
            print(f"  split: {r['label']}")
    print(f"  manifest: {man}")


if __name__ == "__main__":
    main()
