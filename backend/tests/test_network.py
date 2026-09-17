from types import SimpleNamespace

import pytest
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.DataStructs import ExplicitBitVect

from peptorama.processing import network as net

RDLogger.DisableLog("rdApp.*")  # silence parse errors from invalid SMILES

# --------------------------------------------------------------------------- #
# Shared fixtures / helpers
# --------------------------------------------------------------------------- #

L_ALA = "C[C@H](N)C(=O)O"
D_ALA = "C[C@@H](N)C(=O)O"
ETHANOL = "CCO"
ETHANOL_ALT = "OCC"
BENZENE = "c1ccccc1"
INVALID = "not_a_smiles(("


@pytest.fixture
def monomers():
    return {
        "A": {"base": "A", "exact": "A", "stereochemistry": "L"},
        "a": {"base": "A", "exact": "a", "stereochemistry": "D"},
        "G": {"base": "G", "exact": "G", "stereochemistry": "flat"},
        "Aib": {"base": "A", "exact": "Aib", "stereochemistry": "flat"},
    }


def make_peptide(number, smiles, seq=("A",)):
    return {
        "id": f"p{number}",
        "number": number,
        "smiles": smiles,
        "monomers": list(seq),
    }


def make_config(
    methods=(),
    match=("base",),
    stereochemistry=("strict",),
    monomer_cutoff=0,
    radius=(2,),
    tanimoto_cutoff=0.0,
):
    return SimpleNamespace(
        edge=SimpleNamespace(
            methods=list(methods),
            monomer=SimpleNamespace(
                match=list(match),
                stereochemistry=list(stereochemistry),
                cutoff=monomer_cutoff,
            ),
            tanimoto=SimpleNamespace(radius=list(radius), cutoff=tanimoto_cutoff),
        )
    )


@pytest.fixture
def fake_align(monkeypatch):
    """
    Replace the alignment functions with recorders.

    `state.code` controls what needleman_wunsch returns; set it to a string,
    or to a callable(seq_a, seq_b) for per-pair results.
    """
    state = SimpleNamespace(code="====", nw_calls=[], score_fn_calls=[])

    def fake_make_score_fn(stereo_mode):
        state.score_fn_calls.append(stereo_mode)
        return ("score_fn", stereo_mode)

    def fake_nw(seq_a, seq_b, score_fn=None):
        state.nw_calls.append((seq_a, seq_b, score_fn))
        return state.code(seq_a, seq_b) if callable(state.code) else state.code

    monkeypatch.setattr(net, "make_score_fn", fake_make_score_fn)
    monkeypatch.setattr(net, "needleman_wunsch", fake_nw)
    return state


# --------------------------------------------------------------------------- #
# normalise_peptide
# --------------------------------------------------------------------------- #


class TestNormalisePeptide:
    def test_base_mode_uses_base_field(self, monomers):
        result = net.normalise_peptide(["A", "a", "Aib"], monomers, "base")
        assert result == [("A", "L"), ("A", "D"), ("A", "flat")]

    def test_exact_mode_uses_exact_field(self, monomers):
        result = net.normalise_peptide(["A", "a", "Aib"], monomers, "exact")
        assert result == [("A", "L"), ("a", "D"), ("Aib", "flat")]

    def test_returns_list_of_tuples(self, monomers):
        result = net.normalise_peptide(["G"], monomers, "base")
        assert isinstance(result, list)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in result)

    def test_empty_sequence(self, monomers):
        assert net.normalise_peptide([], monomers, "base") == []

    def test_preserves_order_and_duplicates(self, monomers):
        result = net.normalise_peptide(["G", "A", "G", "A"], monomers, "exact")
        assert result == [("G", "flat"), ("A", "L"), ("G", "flat"), ("A", "L")]

    def test_unknown_code_raises_key_error(self, monomers):
        with pytest.raises(KeyError):
            net.normalise_peptide(["A", "Xyz"], monomers, "base")


# --------------------------------------------------------------------------- #
# FingerprintCache
# --------------------------------------------------------------------------- #


class TestFingerprintCache:
    def test_none_smiles_returns_none(self):
        assert net.FingerprintCache().fingerprint(None, 2, False) is None

    def test_invalid_smiles_returns_none(self):
        assert net.FingerprintCache().fingerprint(INVALID, 2, False) is None

    def test_valid_smiles_returns_2048_bit_vector(self):
        fp = net.FingerprintCache().fingerprint(ETHANOL, 2, False)
        assert isinstance(fp, ExplicitBitVect)
        assert fp.GetNumBits() == 2048
        assert fp.GetNumOnBits() > 0

    def test_matches_direct_rdkit_fingerprint(self):
        expected = rdFingerprintGenerator.GetMorganGenerator(
            radius=2, fpSize=2048
        ).GetFingerprint(Chem.MolFromSmiles(BENZENE))
        assert net.FingerprintCache().fingerprint(BENZENE, 2, False) == expected

    def test_repeated_call_returns_same_object(self):
        cache = net.FingerprintCache()
        assert cache.fingerprint(ETHANOL, 2, False) is cache.fingerprint(
            ETHANOL, 2, False
        )

    def test_equivalent_smiles_share_one_entry(self):
        cache = net.FingerprintCache()
        fp1 = cache.fingerprint(ETHANOL, 2, False)
        fp2 = cache.fingerprint(ETHANOL_ALT, 2, False)
        assert fp1 is fp2
        assert len(cache._fps) == 1
        assert len(cache._mols) == 1
        # Both raw inputs are remembered in the canonical layer.
        assert len(cache._canonical) == 2

    def test_different_radii_are_cached_separately(self):
        cache = net.FingerprintCache()
        fp1 = cache.fingerprint(BENZENE, 1, False)
        fp3 = cache.fingerprint(BENZENE, 3, False)
        assert fp1 is not fp3
        assert len(cache._fps) == 2
        assert set(cache._gens) == {1, 3}
        # The molecule is parsed once and shared across radii.
        assert len(cache._mols) == 1

    def test_stereo_flag_controls_canonical_form(self):
        cache = net.FingerprintCache()
        assert cache._canonicalize(L_ALA, False) == cache._canonicalize(D_ALA, False)
        assert "@" not in cache._canonicalize(L_ALA, False)
        assert cache._canonicalize(L_ALA, True) != cache._canonicalize(D_ALA, True)
        assert "@" in cache._canonicalize(L_ALA, True)

    def test_enantiomers_collapse_without_stereo(self):
        cache = net.FingerprintCache()
        assert cache.fingerprint(L_ALA, 2, False) is cache.fingerprint(D_ALA, 2, False)

    def test_enantiomers_stay_separate_with_stereo(self):
        cache = net.FingerprintCache()
        cache.fingerprint(L_ALA, 2, True)
        cache.fingerprint(D_ALA, 2, True)
        assert len(cache._fps) == 2

    def test_generator_is_built_once_per_radius(self, monkeypatch):
        calls = []
        real = rdFingerprintGenerator.GetMorganGenerator

        def counting(**kwargs):
            calls.append(kwargs)
            return real(**kwargs)

        monkeypatch.setattr(net.rdFingerprintGenerator, "GetMorganGenerator", counting)
        cache = net.FingerprintCache()
        for smi in (ETHANOL, BENZENE, L_ALA):
            cache.fingerprint(smi, 2, False)
        cache.fingerprint(ETHANOL, 3, False)
        assert calls == [
            {"radius": 2, "fpSize": 2048},
            {"radius": 3, "fpSize": 2048},
        ]

    def test_smiles_parsed_only_on_first_request(self, monkeypatch):
        calls = []
        real = Chem.MolFromSmiles

        def counting(smi, *args, **kwargs):
            calls.append(smi)
            return real(smi, *args, **kwargs)

        monkeypatch.setattr(net.Chem, "MolFromSmiles", counting)
        cache = net.FingerprintCache()
        cache.fingerprint(ETHANOL, 2, False)
        first = len(calls)
        assert first == 2  # raw input + canonical string
        cache.fingerprint(ETHANOL, 2, False)
        cache.fingerprint(ETHANOL, 3, False)
        assert len(calls) == first

    def test_invalid_smiles_failure_is_cached(self, monkeypatch):
        calls = []
        real = Chem.MolFromSmiles

        def counting(smi, *args, **kwargs):
            calls.append(smi)
            return real(smi, *args, **kwargs)

        monkeypatch.setattr(net.Chem, "MolFromSmiles", counting)
        cache = net.FingerprintCache()
        assert cache.fingerprint(INVALID, 2, False) is None
        assert cache.fingerprint(INVALID, 2, False) is None
        assert calls == [INVALID]
        assert cache._fps == {}

    def test_caches_are_independent_between_instances(self):
        c1, c2 = net.FingerprintCache(), net.FingerprintCache()
        c1.fingerprint(ETHANOL, 2, False)
        assert c2._fps == {} and c2._canonical == {}

    def test_empty_smiles_gives_empty_fingerprint(self):
        # RDKit parses "" as an empty molecule rather than failing.
        fp = net.FingerprintCache().fingerprint("", 2, False)
        assert fp is not None
        assert fp.GetNumOnBits() == 0


# --------------------------------------------------------------------------- #
# build_network — general
# --------------------------------------------------------------------------- #


class TestBuildNetworkGeneral:
    def test_no_methods_returns_no_edges(self):
        processed = {"peptides": [make_peptide(1, ETHANOL), make_peptide(2, ETHANOL)]}
        assert net.build_network(processed, make_config(methods=[])) == []

    @pytest.mark.parametrize("n", [0, 1])
    def test_fewer_than_two_peptides(self, n):
        processed = {"peptides": [make_peptide(i, ETHANOL) for i in range(n)]}
        config = make_config(methods=["tanimoto"])
        assert net.build_network(processed, config) == []

    def test_returns_a_list(self):
        processed = {"peptides": [make_peptide(1, ETHANOL), make_peptide(2, ETHANOL)]}
        result = net.build_network(processed, make_config(methods=["tanimoto"]))
        assert isinstance(result, list)

    def test_one_edge_per_unordered_pair_in_input_order(self):
        peptides = [make_peptide(i, ETHANOL) for i in range(1, 5)]
        edges = net.build_network(
            {"peptides": peptides}, make_config(methods=["tanimoto"])
        )
        assert [e["id"] for e in edges] == [
            "e1_2",
            "e1_3",
            "e1_4",
            "e2_3",
            "e2_4",
            "e3_4",
        ]

    def test_edge_uses_number_for_id_and_id_for_endpoints(self):
        peptides = [
            {"id": "alpha", "number": 7, "smiles": ETHANOL, "monomers": []},
            {"id": "beta", "number": 42, "smiles": ETHANOL, "monomers": []},
        ]
        (edge,) = net.build_network(
            {"peptides": peptides}, make_config(methods=["tanimoto"])
        )
        assert edge["id"] == "e7_42"
        assert edge["source"] == "alpha"
        assert edge["target"] == "beta"

    def test_monomers_key_not_required_for_tanimoto_only(self):
        processed = {"peptides": [make_peptide(1, ETHANOL), make_peptide(2, ETHANOL)]}
        assert "monomers" not in processed
        assert len(net.build_network(processed, make_config(methods=["tanimoto"]))) == 1

    def test_missing_monomers_key_raises_for_monomer_method(self, fake_align):
        processed = {"peptides": [make_peptide(1, ETHANOL), make_peptide(2, ETHANOL)]}
        with pytest.raises(KeyError):
            net.build_network(processed, make_config(methods=["monomer"]))

    def test_unknown_method_is_ignored(self):
        processed = {"peptides": [make_peptide(1, ETHANOL), make_peptide(2, ETHANOL)]}
        assert net.build_network(processed, make_config(methods=["bogus"])) == []


# --------------------------------------------------------------------------- #
# build_network — tanimoto
# --------------------------------------------------------------------------- #


class TestBuildNetworkTanimoto:
    def _run(self, smiles_a, smiles_b, **cfg):
        processed = {"peptides": [make_peptide(1, smiles_a), make_peptide(2, smiles_b)]}
        return net.build_network(processed, make_config(methods=["tanimoto"], **cfg))

    def test_identical_molecules_score_one(self):
        (edge,) = self._run(BENZENE, BENZENE, tanimoto_cutoff=0.9)
        assert edge["tanimoto_r2"] == 1.0

    def test_equivalent_smiles_score_one(self):
        (edge,) = self._run(ETHANOL, ETHANOL_ALT, tanimoto_cutoff=0.9)
        assert edge["tanimoto_r2"] == 1.0

    def test_enantiomers_score_one_because_stereo_is_ignored(self):
        (edge,) = self._run(L_ALA, D_ALA, tanimoto_cutoff=0.99)
        assert edge["tanimoto_r2"] == 1.0

    def test_dissimilar_molecules_below_cutoff_are_dropped(self):
        assert self._run(ETHANOL, BENZENE, tanimoto_cutoff=0.5) == []

    def test_score_is_rounded_to_two_places(self):
        (edge,) = self._run("CCCCO", "CCCCN", tanimoto_cutoff=0.0)
        score = edge["tanimoto_r2"]
        assert 0.0 < score < 1.0
        assert score == round(score, 2)

    def test_cutoff_is_inclusive(self, monkeypatch):
        monkeypatch.setattr(net.DataStructs, "TanimotoSimilarity", lambda a, b: 0.5)
        (edge,) = self._run(ETHANOL, BENZENE, tanimoto_cutoff=0.5)
        assert edge["tanimoto_r2"] == 0.5

    def test_cutoff_applies_to_raw_not_rounded_score(self, monkeypatch):
        # 0.499 rounds to 0.5 but is still below a 0.5 cutoff.
        monkeypatch.setattr(net.DataStructs, "TanimotoSimilarity", lambda a, b: 0.499)
        assert self._run(ETHANOL, BENZENE, tanimoto_cutoff=0.5) == []

    def test_one_key_per_radius(self):
        (edge,) = self._run(BENZENE, BENZENE, radius=(1, 2, 3))
        assert {k for k in edge if k.startswith("tanimoto")} == {
            "tanimoto_r1",
            "tanimoto_r2",
            "tanimoto_r3",
        }

    def test_only_passing_radii_are_recorded(self, monkeypatch):
        # Radii are evaluated in order; make r1 pass and r3 fail.
        scores = iter([0.9, 0.1])
        monkeypatch.setattr(
            net.DataStructs, "TanimotoSimilarity", lambda a, b: next(scores)
        )
        (edge,) = self._run(ETHANOL, BENZENE, radius=(1, 3), tanimoto_cutoff=0.5)
        assert edge["tanimoto_r1"] == 0.9
        assert "tanimoto_r3" not in edge

    def test_invalid_smiles_scores_zero_and_is_dropped(self):
        assert self._run(INVALID, BENZENE, tanimoto_cutoff=0.01) == []

    def test_none_smiles_scores_zero_and_is_dropped(self):
        assert self._run(None, BENZENE, tanimoto_cutoff=0.01) == []

    def test_invalid_smiles_kept_with_zero_score_when_cutoff_is_zero(self):
        # Documents current behaviour: a failed parse is indistinguishable
        # from a genuine 0.0 score, so a zero cutoff keeps the edge.
        (edge,) = self._run(INVALID, BENZENE, tanimoto_cutoff=0.0)
        assert edge["tanimoto_r2"] == 0.0

    def test_no_alignment_keys_when_only_tanimoto(self):
        (edge,) = self._run(BENZENE, BENZENE)
        assert not any(k.startswith("alignment_") for k in edge)

    def test_fingerprints_computed_once_per_unique_structure(self, monkeypatch):
        calls = []
        real = net.FingerprintCache._generator

        def spy(self, radius):
            gen = real(self, radius)

            class Wrapped:
                def GetFingerprint(self_inner, mol):
                    calls.append(Chem.MolToSmiles(mol))
                    return gen.GetFingerprint(mol)

            return Wrapped()

        monkeypatch.setattr(net.FingerprintCache, "_generator", spy)
        peptides = [
            make_peptide(1, ETHANOL),
            make_peptide(2, ETHANOL_ALT),
            make_peptide(3, BENZENE),
            make_peptide(4, ETHANOL),
        ]
        net.build_network({"peptides": peptides}, make_config(methods=["tanimoto"]))
        canonical = {
            Chem.MolToSmiles(Chem.MolFromSmiles(s)) for s in (ETHANOL, BENZENE)
        }
        assert sorted(calls) == sorted(canonical)


# --------------------------------------------------------------------------- #
# build_network — monomer alignment
# --------------------------------------------------------------------------- #


class TestBuildNetworkMonomer:
    def _processed(self, monomers, seq_a=("A", "G"), seq_b=("a", "G")):
        return {
            "peptides": [
                make_peptide(1, ETHANOL, seq_a),
                make_peptide(2, ETHANOL, seq_b),
            ],
            "monomers": monomers,
        }

    def test_identity_and_alignment_are_recorded(self, monomers, fake_align):
        fake_align.code = "==x="
        (edge,) = net.build_network(
            self._processed(monomers), make_config(methods=["monomer"])
        )
        assert edge["alignment_base_strict_id"] == 0.75
        assert edge["alignment_base_strict_align"] == "==x="

    def test_identity_is_rounded(self, monomers, fake_align):
        fake_align.code = "==x"
        (edge,) = net.build_network(
            self._processed(monomers), make_config(methods=["monomer"])
        )
        assert edge["alignment_base_strict_id"] == 0.67

    def test_cutoff_is_a_percentage(self, monomers, fake_align):
        fake_align.code = "==xx"  # 50 %
        processed = self._processed(monomers)
        assert (
            net.build_network(
                processed, make_config(methods=["monomer"], monomer_cutoff=51)
            )
            == []
        )
        assert (
            len(
                net.build_network(
                    processed, make_config(methods=["monomer"], monomer_cutoff=50)
                )
            )
            == 1
        )

    def test_empty_alignment_scores_zero(self, monomers, fake_align):
        fake_align.code = ""
        processed = self._processed(monomers)
        assert (
            net.build_network(
                processed, make_config(methods=["monomer"], monomer_cutoff=1)
            )
            == []
        )
        (edge,) = net.build_network(
            processed, make_config(methods=["monomer"], monomer_cutoff=0)
        )
        assert edge["alignment_base_strict_id"] == 0.0
        assert edge["alignment_base_strict_align"] == ""

    def test_base_mode_passes_base_sequences(self, monomers, fake_align):
        net.build_network(
            self._processed(monomers),
            make_config(methods=["monomer"], match=["base"]),
        )
        ((seq_a, seq_b, _),) = fake_align.nw_calls
        assert seq_a == [("A", "L"), ("G", "flat")]
        assert seq_b == [("A", "D"), ("G", "flat")]

    def test_exact_mode_passes_exact_sequences(self, monomers, fake_align):
        net.build_network(
            self._processed(monomers),
            make_config(methods=["monomer"], match=["exact"]),
        )
        ((seq_a, seq_b, _),) = fake_align.nw_calls
        assert seq_a == [("A", "L"), ("G", "flat")]
        assert seq_b == [("a", "D"), ("G", "flat")]

    def test_score_fn_built_from_stereo_mode(self, monomers, fake_align):
        net.build_network(
            self._processed(monomers),
            make_config(methods=["monomer"], stereochemistry=["ignore"]),
        )
        assert fake_align.score_fn_calls == ["ignore"]
        ((_, _, score_fn),) = fake_align.nw_calls
        assert score_fn == ("score_fn", "ignore")

    def test_every_match_stereo_combination_is_run(self, monomers, fake_align):
        (edge,) = net.build_network(
            self._processed(monomers),
            make_config(
                methods=["monomer"],
                match=["base", "exact"],
                stereochemistry=["strict", "ignore"],
            ),
        )
        assert len(fake_align.nw_calls) == 4
        expected = {
            f"alignment_{m}_{s}_{suffix}"
            for m in ("base", "exact")
            for s in ("strict", "ignore")
            for suffix in ("id", "align")
        }
        assert {k for k in edge if k.startswith("alignment_")} == expected

    def test_sequences_normalised_once_per_peptide(
        self, monomers, fake_align, monkeypatch
    ):
        calls = []
        real = net.normalise_peptide

        def spy(sequence, monomers, match_mode):
            calls.append((tuple(sequence), match_mode))
            return real(sequence, monomers, match_mode)

        monkeypatch.setattr(net, "normalise_peptide", spy)
        peptides = [make_peptide(i, ETHANOL, ("A", "G")) for i in range(4)]
        net.build_network(
            {"peptides": peptides, "monomers": monomers},
            make_config(methods=["monomer"], match=["base", "exact"]),
        )
        # Always both modes, once per peptide, regardless of pair count.
        assert len(calls) == 4 * 2

    def test_unknown_monomer_code_raises(self, monomers, fake_align):
        with pytest.raises(KeyError):
            net.build_network(
                self._processed(monomers, seq_b=("Zzz",)),
                make_config(methods=["monomer"]),
            )

    def test_no_tanimoto_keys_when_only_monomer(self, monomers, fake_align):
        (edge,) = net.build_network(
            self._processed(monomers), make_config(methods=["monomer"])
        )
        assert not any(k.startswith("tanimoto_") for k in edge)

    def test_empty_match_list_produces_no_alignments(self, monomers, fake_align):
        result = net.build_network(
            self._processed(monomers), make_config(methods=["monomer"], match=[])
        )
        assert result == []
        assert fake_align.nw_calls == []


# --------------------------------------------------------------------------- #
# build_network — both methods together
# --------------------------------------------------------------------------- #


class TestBuildNetworkCombined:
    def _processed(self, monomers, smiles_a, smiles_b):
        return {
            "peptides": [
                make_peptide(1, smiles_a, ("A",)),
                make_peptide(2, smiles_b, ("A",)),
            ],
            "monomers": monomers,
        }

    def test_edge_kept_when_only_tanimoto_passes(self, monomers, fake_align):
        fake_align.code = "x"
        (edge,) = net.build_network(
            self._processed(monomers, BENZENE, BENZENE),
            make_config(
                methods=["tanimoto", "monomer"],
                tanimoto_cutoff=0.9,
                monomer_cutoff=50,
            ),
        )
        assert edge["tanimoto_r2"] == 1.0
        assert not any(k.startswith("alignment_") for k in edge)

    def test_edge_kept_when_only_monomer_passes(self, monomers, fake_align):
        fake_align.code = "="
        (edge,) = net.build_network(
            self._processed(monomers, ETHANOL, BENZENE),
            make_config(
                methods=["tanimoto", "monomer"],
                tanimoto_cutoff=0.9,
                monomer_cutoff=50,
            ),
        )
        assert edge["alignment_base_strict_id"] == 1.0
        assert not any(k.startswith("tanimoto_") for k in edge)

    def test_edge_dropped_when_neither_passes(self, monomers, fake_align):
        fake_align.code = "x"
        assert (
            net.build_network(
                self._processed(monomers, ETHANOL, BENZENE),
                make_config(
                    methods=["tanimoto", "monomer"],
                    tanimoto_cutoff=0.9,
                    monomer_cutoff=50,
                ),
            )
            == []
        )

    def test_both_sets_of_keys_when_both_pass(self, monomers, fake_align):
        fake_align.code = "="
        (edge,) = net.build_network(
            self._processed(monomers, BENZENE, BENZENE),
            make_config(methods=["monomer", "tanimoto"]),
        )
        assert set(edge) == {
            "id",
            "source",
            "target",
            "tanimoto_r2",
            "alignment_base_strict_id",
            "alignment_base_strict_align",
        }
