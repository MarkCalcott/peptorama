import pytest
from peptorama.processing.generate_SMILES import generate_smiles
from peptorama.processing.validate import MONOMER_DICT
from dataclasses import dataclass
import json
from pathlib import Path
from rdkit import Chem

MONOMER_DICT = {**{k: {**v, "known": "Inbuilt"} for k, v in MONOMER_DICT.items()}}


@dataclass
class FakePeptide:
    peptide: str
    _monomers: list


def fake_peptide_generator(peptide_str, monomers=None):
    if monomers:
        return FakePeptide(peptide_str, monomers)
    else:
        return FakePeptide(peptide_str, peptide_str.split("-"))


BASIC_TEST_CASES = [
    (fake_peptide_generator("Ala-Ala-Ala"), "NC(C)C(=O)NC(C)C(=O)NC(C)C(=O)O"),
    (fake_peptide_generator("Ala-Ala-tAld"), "NC(C)C(=O)NC(C)C(=O)"),
    (
        fake_peptide_generator("[Ala-Ala-Ala]", ["Ala", "Ala", "Ala"]),
        "N9C(C)C(=O)NC(C)C(=O)NC(C)C(=O)9",
    ),
    (
        fake_peptide_generator("[[[Ala-Ser]]]", ["Ala", "Ser"]),
        "N9C(C)C(=O)NC(CO)C(=O)NC(C)C(=O)NC(CO)C(=O)NC(C)C(=O)NC(CO)C(=O)9",
    ),
    (
        fake_peptide_generator("Ala-(Ser-Ala-Ala)", ["Ala", "Ser", "Ala", "Ala"]),
        "NC(C)C(=O)NC(CO9)C(=O)NC(C)C(=O)NC(C)C(=O)9",
    ),
    (
        fake_peptide_generator("Ala-(Lys-Ala-Ala)", ["Ala", "Lys", "Ala", "Ala"]),
        "NC(C)C(=O)NC(CCCCN9)C(=O)NC(C)C(=O)NC(C)C(=O)9",
    ),
    (
        fake_peptide_generator("Ala/azDab-Ala", ["Ala", "azDab", "Ala"]),
        "NC(C)C1NC(CCN=1)C(=O)NC(C)C(=O)O",
    ),
    (fake_peptide_generator("Ala-Ala-Banana", ["Ala", "Ala", "Banana"]), None),
]


class TestDummyProteins:
    """Testing basic proteins to check base operations"""

    @pytest.mark.parametrize("peptide,expected", BASIC_TEST_CASES)
    def test_generate_smiles_basic(self, peptide, expected):
        result = generate_smiles(peptide, MONOMER_DICT)
        if expected:
            expected = Chem.MolToSmiles(Chem.MolFromSmiles(expected))

        assert (
            result == expected
        ), f"Failed for {peptide.peptide}: got {result!r}, expected {expected!r}"

    def test_undefined(self):
        user_monomers = {
            **MONOMER_DICT,
            "Banana": {
                "code": "Banana",
                "base": "Banana",
                "stereochemistry": "flat",
                "name": None,
                "IUPAC": None,
                "smiles": "[*:1]NC([*:4])C(=O)[*:2]",
                "category": None,
                "known": "User-defined",
            },
        }
        banana_peptide = fake_peptide_generator(
            "Ala-Banana-Ala", ["Ala", "Banana", "Ala"]
        )
        result = generate_smiles(banana_peptide, user_monomers)
        assert result == Chem.MolToSmiles(
            Chem.MolFromSmiles("NC(C)C(=O)NC(*)C(=O)NC(C)C(=O)O")
        )
