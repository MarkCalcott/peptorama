import pytest
from peptorama.processing.generate_SMILES import getMonomerEntry
from peptorama.processing.validate import MONOMER_DICT
import json
from pathlib import Path

MONOMER_DICT = {**{k: {**v, "known": "Inbuilt"} for k, v in MONOMER_DICT.items()}}


class TestProteinogenic:
    """Base proteinogenic amino acids - no modifications."""

    def test_Gly(self):
        result = getMonomerEntry("Gly", MONOMER_DICT)
        assert result["exact"] == "Gly"
        assert result["base"] == "Gly"
        assert result["stereochemistry"] == "flat"
        assert result["name"] == "Glycine"
        assert result["smiles"] == "[*:1]NCC(=O)[*:2]"
        assert result["category"] == "Proteinogenic"

    def test_Ala(self):
        result = getMonomerEntry("Ala", MONOMER_DICT)
        assert result["exact"] == "Ala"
        assert result["base"] == "Ala"
        assert result["stereochemistry"] == "flat"
        assert result["name"] == "Alanine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]NC(C)C(=O)[*:2]"

    def test_Val(self):
        result = getMonomerEntry("Val", MONOMER_DICT)
        assert result["exact"] == "Val"
        assert result["base"] == "Val"
        assert result["stereochemistry"] == "flat"
        assert result["name"] == "Valine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]NC(C(C)C)C(=O)[*:2]"


class TestMonomerOveride:
    """Pro has L-Pro and D-Pro as manual entries"""

    def test_Pro(self):
        result = getMonomerEntry("Pro", MONOMER_DICT)
        assert result["exact"] == "Pro"
        assert result["base"] == "Pro"
        assert result["stereochemistry"] == "flat"
        assert result["name"] == "Proline"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N1CCCC1C(=O)[*:2]"

    def test_L_Pro(self):
        result = getMonomerEntry("L-Pro", MONOMER_DICT)
        assert result["exact"] == "Pro"
        assert result["base"] == "Pro"
        assert result["stereochemistry"] == "L"
        assert result["name"] == "Proline"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N1CCC[C@H]1C(=O)[*:2]"

    def test_D_Pro(self):
        result = getMonomerEntry("D-Pro", MONOMER_DICT)
        assert result["exact"] == "Pro"
        assert result["base"] == "Pro"
        assert result["stereochemistry"] == "D"
        assert result["name"] == "Proline"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N1CCC[C@@H]1C(=O)[*:2]"


class TestStereochemistry:
    """Base proteinogenic amino acids - no modifications."""

    def test_L_Ala(self):
        result = getMonomerEntry("L-Ala", MONOMER_DICT)
        assert result["exact"] == "Ala"
        assert result["base"] == "Ala"
        assert result["stereochemistry"] == "L"
        assert result["name"] == "Alanine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N[C@@H](C)C(=O)[*:2]"

    def test_D_Ala(self):
        result = getMonomerEntry("D-Ala", MONOMER_DICT)
        assert result["exact"] == "Ala"
        assert result["base"] == "Ala"
        assert result["stereochemistry"] == "D"
        assert result["name"] == "Alanine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N[C@H](C)C(=O)[*:2]"

    def test_L_Val(self):
        result = getMonomerEntry("L-Val", MONOMER_DICT)
        assert result["exact"] == "Val"
        assert result["base"] == "Val"
        assert result["stereochemistry"] == "L"
        assert result["name"] == "Valine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N[C@@H](C(C)C)C(=O)[*:2]"

    def test_D_Val(self):
        result = getMonomerEntry("D-Val", MONOMER_DICT)
        assert result["exact"] == "Val"
        assert result["base"] == "Val"
        assert result["stereochemistry"] == "D"
        assert result["name"] == "Valine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N[C@H](C(C)C)C(=O)[*:2]"


class TestNMethylation:
    """N-Me- prefix adds N-methylation to the SMILES"""

    def test_Nme_Val(self):
        result = getMonomerEntry("N-Me-Val", MONOMER_DICT)
        assert result["exact"] == "N-Me-Val"
        assert result["base"] == "Val"
        assert result["stereochemistry"] == "flat"
        assert result["name"] == "Valine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N(C)C(C(C)C)C(=O)[*:2]"

    def test_L_Nme_Val(self):
        result = getMonomerEntry("L-N-Me-Val", MONOMER_DICT)
        assert result["exact"] == "N-Me-Val"
        assert result["base"] == "Val"
        assert result["stereochemistry"] == "L"
        assert result["name"] == "Valine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N(C)[C@@H](C(C)C)C(=O)[*:2]"

    def test_D_Nme_Val(self):
        result = getMonomerEntry("D-N-Me-Val", MONOMER_DICT)
        assert result["exact"] == "N-Me-Val"
        assert result["base"] == "Val"
        assert result["stereochemistry"] == "D"
        assert result["name"] == "Valine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N(C)[C@H](C(C)C)C(=O)[*:2]"


class TestOMethylation:
    """O-Me- replaces [*:3] with C on serine or tyrosine."""

    def test_O_Me_Ser(self):
        result = getMonomerEntry("O-Me-Ser", MONOMER_DICT)
        assert result["exact"] == "O-Me-Ser"
        assert result["base"] == "Ser"
        assert result["stereochemistry"] == "flat"
        assert result["name"] == "Serine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]NC(COC)C(=O)[*:2]"

    def test_L_O_Me_Ser(self):
        result = getMonomerEntry("L-O-Me-Ser", MONOMER_DICT)
        assert result["exact"] == "O-Me-Ser"
        assert result["base"] == "Ser"
        assert result["stereochemistry"] == "L"
        assert result["name"] == "Serine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N[C@@H](COC)C(=O)[*:2]"

    def test_D_O_Me_Ser(self):
        result = getMonomerEntry("D-O-Me-Ser", MONOMER_DICT)
        assert result["exact"] == "O-Me-Ser"
        assert result["base"] == "Ser"
        assert result["stereochemistry"] == "D"
        assert result["name"] == "Serine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N[C@H](COC)C(=O)[*:2]"

    def test_O_Me_Tyr(self):
        result = getMonomerEntry("O-Me-Tyr", MONOMER_DICT)
        assert result["exact"] == "O-Me-Tyr"
        assert result["base"] == "Tyr"
        assert result["stereochemistry"] == "flat"
        assert result["name"] == "Tyrosine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]NC(Cc1ccc(OC)cc1)C(=O)[*:2]"


class TestSMethylation:
    """S-Me- replaces [*:3] with C on cysteine."""

    def test_S_Me_Cys(self):
        result = getMonomerEntry("S-Me-Cys", MONOMER_DICT)
        assert result["exact"] == "S-Me-Cys"
        assert result["base"] == "Cys"
        assert result["stereochemistry"] == "flat"
        assert result["name"] == "Cysteine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]NC(CSC)C(=O)[*:2]"


class TestDoubleMethylation:
    """Test both N and S methylation on Cys."""

    def test_S_Me_Cys(self):
        result = getMonomerEntry("N-Me-S-Me-Cys", MONOMER_DICT)
        assert result["exact"] == "N-Me-S-Me-Cys"
        assert result["base"] == "Cys"
        assert result["stereochemistry"] == "flat"
        assert result["name"] == "Cysteine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N(C)C(CSC)C(=O)[*:2]"

    def test_L_O_Me_Ser(self):
        result = getMonomerEntry("L-N-Me-O-Me-Ser", MONOMER_DICT)
        assert result["exact"] == "N-Me-O-Me-Ser"
        assert result["base"] == "Ser"
        assert result["stereochemistry"] == "L"
        assert result["name"] == "Serine"
        assert result["category"] == "Proteinogenic"
        assert result["smiles"] == "[*:1]N(C)[C@@H](COC)C(=O)[*:2]"


class TestUnknownMonomers:
    """Unknown bases (X-prefixed) return known=False with generic SMILES."""

    def test_l_X11(self):
        result = getMonomerEntry("L-X11", MONOMER_DICT)
        assert result["base"] == "X11"
        assert result["stereochemistry"] == "L"
        assert result["name"] is None
        assert result["category"] is None
        assert result["smiles"] == "[*:1]NC([*:4])C(=O)[*:2]"

    def test_l_NMe_X11(self):
        result = getMonomerEntry("L-N-Me-X11", MONOMER_DICT)
        assert result["base"] == "X11"
        assert result["stereochemistry"] == "L"
        assert result["name"] is None
        assert result["category"] is None
        assert result["smiles"] == "[*:1]NC([*:4])C(=O)[*:2]"

    def test_l_X1165546643(self):
        result = getMonomerEntry("L-XX-X1165546643", MONOMER_DICT)
        assert result["base"] == "X1165546643"
        assert result["stereochemistry"] == "L"
        assert result["name"] is None
        assert result["category"] is None
        assert result["smiles"] == "[*:1]NC([*:4])C(=O)[*:2]"

    def test_l_X1165546643(self):
        result = getMonomerEntry("ABCDEFGHIJKLMNO", MONOMER_DICT)
        assert result["base"] == "MNO"
        assert result["stereochemistry"] == "flat"
        assert result["name"] is None
        assert result["category"] is None
        assert result["smiles"] == "[*:1]NC([*:4])C(=O)[*:2]"


class TestEdgeCases:
    """Tricky cases that shouldn't silently succeed."""

    def test_o_me_gly_is_not_known(self):
        # Glycine has no beta carbon to methylate
        result = getMonomerEntry("O-Me-Gly", MONOMER_DICT)
        assert result["smiles"] == "[*:1]NC([*:4])C(=O)[*:2]"


@pytest.mark.parametrize(
    "code,expected_base,expected_stereo",
    [
        ("Ala", "Ala", "flat"),
        ("L-Pro", "Pro", "L"),
        ("D-Pro", "Pro", "D"),
        ("L-Ser", "Ser", "L"),
        ("N-Me-Val", "Val", "flat"),
        ("L-NMeVal", "Val", "L"),
        ("D-N-Me-Val", "Val", "D"),
        ("L-O-Me-Ser", "Ser", "L"),
        ("D-O-Me-Ser", "Ser", "D"),
        ("L-b-Me-Asp", "Asp", "L"),
        ("L-S-Me-N-Me-Cys", "Cys", "L"),
    ],
)
def test_base_and_stereochemistry(code, expected_base, expected_stereo):
    result = getMonomerEntry(code, MONOMER_DICT)
    assert result["base"] == expected_base
    assert result["stereochemistry"] == expected_stereo
