from itertools import combinations, product
from .align import needleman_wunsch, make_score_fn

from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator, DataStructs


def normalise_peptide(
    sequence: list[str], monomers: dict, match_mode: str
) -> dict[str, list]:
    """Normalises peptides to be expressed as base or exact monomers"""
    field = "base" if match_mode == "base" else "exact"
    return [
        (monomers[code][field], monomers[code]["stereochemistry"]) for code in sequence
    ]


class FingerprintCache:
    """
    Request-scoped cache for Morgan fingerprint generation.

    Caches three layers, all keyed by canonical SMILES so that equivalent
    inputs collapse to one entry:
      - canonical SMILES strings (per stereo mode)
      - parsed molecules (per canonical string)
      - fingerprints (per canonical string + radius)

    Plus the Morgan generator itself, cached per radius.

    Instantiate one per request/job; let it be garbage-collected when done.
    """

    def __init__(self):
        self._canonical: dict[tuple[str, bool], str | None] = {}
        self._mols: dict[str, Chem.Mol | None] = {}
        self._fps: dict[tuple[str, int], object] = {}
        self._gens: dict[int, object] = {}

    def fingerprint(self, smiles: str, radius: int, use_stereo: bool):
        """
        Get a Morgan fingerprint for the given SMILES.

        Returns None if the SMILES cannot be parsed.
        """
        if smiles is None:
            return None

        canonical = self._canonicalize(smiles, use_stereo)
        if canonical is None:
            return None

        fp_key = (canonical, radius)
        if fp_key not in self._fps:
            mol = self._mol(canonical)
            self._fps[fp_key] = (
                self._generator(radius).GetFingerprint(mol) if mol is not None else None
            )
        return self._fps[fp_key]

    def _canonicalize(self, smiles: str, use_stereo: bool) -> str | None:
        key = (smiles, use_stereo)
        if key not in self._canonical:
            mol = Chem.MolFromSmiles(smiles)
            self._canonical[key] = (
                Chem.MolToSmiles(mol, isomericSmiles=use_stereo)
                if mol is not None
                else None
            )
        return self._canonical[key]

    def _mol(self, canonical: str) -> Chem.Mol | None:
        if canonical not in self._mols:
            self._mols[canonical] = Chem.MolFromSmiles(canonical)
        return self._mols[canonical]

    def _generator(self, radius: int):
        if radius not in self._gens:
            self._gens[radius] = rdFingerprintGenerator.GetMorganGenerator(
                radius=radius, fpSize=2048
            )
        return self._gens[radius]


def build_network(processed: dict, config) -> list[dict]:
    """
    Build a Cytoscape.js elements payload from the output of process_input().

    Args:
        processed: output of process_input() — must contain "peptides" and "monomers"
        cfg:       network configuration (alignment params, etc.)

    Returns:
        {"nodes": [...], "edges": [...]} ready for Cytoscape.js
    """
    methods = config.edge.methods

    monomer_match = config.edge.monomer.match
    monomer_stereochemistry = config.edge.monomer.stereochemistry
    monomer_cutoff = config.edge.monomer.cutoff

    tanimoto_radius = config.edge.tanimoto.radius
    tanimoto_cutoff = config.edge.tanimoto.cutoff

    peptides = processed["peptides"]

    if "tanimoto" in methods:
        tanimoto_cache = FingerprintCache()

    if "monomer" in methods:
        monomers = processed["monomers"]

        sequences = {
            p["id"]: {
                match_mode: normalise_peptide(
                    p["monomers"], monomers, match_mode=match_mode
                )
                for match_mode in ("base", "exact")
            }
            for p in peptides
        }
        alignment_variants = [
            (match_mode, stereo_mode)
            for match_mode, stereo_mode in product(
                monomer_match,
                monomer_stereochemistry,
            )
        ]

    edges = []
    for a, b in combinations(peptides, 2):
        edge = {
            "id": f"e{a['number']}_{b['number']}",
            "source": a["id"],
            "target": b["id"],
        }

        keep_edge = False

        # Calculate the tanimoto scores
        if "tanimoto" in methods:
            for radius in tanimoto_radius:
                fingerprint_a = tanimoto_cache.fingerprint(
                    a["smiles"], radius=radius, use_stereo=False
                )
                fingerprint_b = tanimoto_cache.fingerprint(
                    b["smiles"], radius=radius, use_stereo=False
                )
                t_score = (
                    DataStructs.TanimotoSimilarity(fingerprint_a, fingerprint_b)
                    if fingerprint_a and fingerprint_b
                    else 0.0
                )

                if t_score >= tanimoto_cutoff:
                    edge[f"tanimoto_r{radius}"] = round(t_score, 2)
                    keep_edge = True

        if "monomer" in methods:
            for match_mode, stereo_mode in alignment_variants:
                seq_a = sequences[a["id"]][match_mode]
                seq_b = sequences[b["id"]][match_mode]
                code = needleman_wunsch(
                    seq_a, seq_b, score_fn=make_score_fn(stereo_mode)
                )
                identity = code.count("=") / len(code) if code else 0.0

                if identity >= (monomer_cutoff / 100.0):
                    edge[f"alignment_{match_mode}_{stereo_mode}_id"] = round(
                        identity, 2
                    )
                    edge[f"alignment_{match_mode}_{stereo_mode}_align"] = code
                    keep_edge = True

        if keep_edge:
            edges.append(edge)

    return edges
