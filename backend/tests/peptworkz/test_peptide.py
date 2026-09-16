import pytest

from peptworkz.validate import Peptide


class TestPeptideInit:
    def test_default_name_uses_id(self):
        p = Peptide(_id=42, peptide="Met-Ala-Arg-Lys")
        assert p.name == "Row 42"

    def test_custom_name_preserved(self):
        p = Peptide(_id=1, peptide="Trp-Ala-Ser", name="my_pep")
        assert p.name == "my_pep"

    def test_default_fields(self):
        p = Peptide(_id=0, peptide="His-Glu-Arg-Glu")
        assert p.smiles is None
        assert p.valid is True
        assert p._metadata == {}

    def test_simple_monomers_extracted(self):
        p = Peptide(_id=1, peptide="Ala-Gly-Pro")
        assert p._monomers == ["Ala", "Gly", "Pro"]


class TestMonomerRegex:

    @pytest.mark.parametrize(
        "sequence, expected",
        [
            ("Ala-Gly", ["Ala", "Gly"]),
            ("Ala", ["Ala"]),
            ("L-Ala-Gly-D-Pro", ["L-Ala", "Gly", "D-Pro"]),
            ("L-Ala-N-Me-Tyr-D-Pro", ["L-Ala", "N-Me-Tyr", "D-Pro"]),
        ],
    )
    def test_simple_sequences(self, sequence, expected):
        p = Peptide(_id=1, peptide=sequence)
        assert p._monomers == expected

    def test_parenthesized_branch(self):
        p = Peptide(_id=1, peptide="Ala(Gly)Pro")
        # monomers should include tokens found inside parens
        assert len(p._monomers) >= 2

    def test_dash_separated(self):
        p = Peptide(_id=1, peptide="Ala-Gly")
        assert len(p._monomers) >= 1

    def test_no_match_on_digits_only(self):
        p = Peptide(_id=1, peptide="12345")
        assert p._monomers == []
