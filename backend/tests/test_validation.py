import pytest
from peptorama.processing.validate import process_input, Peptide
from peptorama.processing.info_codes import InfoCode

# ---------------------------------------------------------------------------
# Examples of acceptable input
# ---------------------------------------------------------------------------

SIMPLE_INPUT = """\
peptide
Ala-Thr-Ser
D-Ala-Thr-L-Ser
"""

SIMPLE_INPUT_NO_HEADER = """\
Ala-Thr-Ser
D-Ala-Thr-L-Ser
"""

MULTI_COLUMN_INPUT = """\
peptide, name, cyclisation, strain, bioactivity
Gly-L-Ala-β-OH-Tyr-D-Leu-Orn-Pro, NRP-001, head-to-tail, S. ambofaciens, antibacterial
D-Phe-N-Me-Gly-Orn-Val-Pip-Thr, NRP-002, branched, B. subtilis, antifungal
L-Ser-Gly-D-Ala-Leu-N-Me-Gly-Val-Pro, NRP-003, linear, S. venezuelae, cytotoxic
"""

INPUT_WITH_SMILES = """\
peptide, name, smiles
Ala-Thr-Ser, pep1, CC(N)C(=O)NC(C(=O)NC(CO)C(=O)O)C(C)O
D-Ala-Val, pep2, CC(N)C(=O)NC(C(C)C)C(=O)O
"""

CYCLIC_PEPTIDES_INPUT = """\
peptide, name
[Ala-Thr-Ser], cyclic-head-to-tail
Ala-(Ser-Gly-Phe), cyclic-sidechain
Ala-Gln/Dab-Phe, cyclic-internal
"""


class TestSimpleParsing:
    """Peptide-only input with and without headers."""

    def test_simple_input_parses_all_peptides(self):
        result = process_input(SIMPLE_INPUT)
        assert result["metadata"]["known"] == 2

    def test_simple_input_peptide_strings_preserved(self):
        result = process_input(SIMPLE_INPUT)
        peptides = [p["peptide"] for p in result["peptides"]]
        assert "Ala-Thr-Ser" in peptides
        assert "D-Ala-Thr-L-Ser" in peptides

    def test_simple_input_collects_monomers(self):
        result = process_input(SIMPLE_INPUT)
        # Should find monomers from both peptides
        assert len(result["monomers"]) == 5

    def test_no_header_still_parses(self):
        result = process_input(SIMPLE_INPUT_NO_HEADER)
        assert result["metadata"]["known"] == 2

    def test_no_header_triggers_warning(self):
        result = process_input(SIMPLE_INPUT_NO_HEADER)
        assert result["warnings"].count_infocode(InfoCode.NO_HEADER) == 1

    def test_header_detected_case_insensitive(self):
        input_text = "Peptide\nAla-Thr-Ser\nVal-Leu-Pro\nGly-Ala-Phe\n"
        result = process_input(input_text)
        assert result["warnings"].count_infocode(InfoCode.NO_HEADER) == 0

    def test_header_detected_plural(self):
        input_text = "Peptides\nAla-Thr-Ser\nVal-Leu-Pro\nGly-Ala-Phe\n"
        result = process_input(input_text)
        assert result["warnings"].count_infocode(InfoCode.NO_HEADER) == 0

    def test_single_column_warning(self):
        result = process_input(SIMPLE_INPUT)
        assert result["warnings"].count_infocode(InfoCode.SINGLE_COLUMN) == 1


class TestMultiColumnParsing:
    """Input with peptide + name + additional metadata columns."""

    def test_multi_column_parses_all_rows(self):
        result = process_input(MULTI_COLUMN_INPUT)
        assert result["metadata"]["known"] == 3

    def test_multi_column_metadata_columns_detected(self):
        result = process_input(MULTI_COLUMN_INPUT)
        col_order = result["metadata"]["known_order"]
        # name is a reserved column, so metadata should be cyclisation, strain, bioactivity
        assert "cyclisation" in col_order
        assert "strain" in col_order
        assert "bioactivity" in col_order
        assert "name" not in result["metadata"]["known_order"]

    def test_multi_column_peptide_names_assigned(self):
        result = process_input(MULTI_COLUMN_INPUT)
        names = [p["name"] for p in result["peptides"]]
        assert "NRP-001" in names
        assert "NRP-002" in names
        assert "NRP-003" in names

    def test_multi_column_metadata_values_on_peptide(self):
        result = process_input(MULTI_COLUMN_INPUT)
        first = result["peptides"][0]["metadata"]
        assert first.get("cyclisation") == "head-to-tail"
        assert first.get("strain") == "S. ambofaciens"

    def test_no_single_column_warning_for_multi(self):
        result = process_input(MULTI_COLUMN_INPUT)
        assert result["warnings"].count_infocode(InfoCode.SINGLE_COLUMN) == 0


class TestReservedColumns:
    """The 'name' and 'smiles' columns receive special treatment."""

    def test_smiles_column_parsed(self):
        result = process_input(INPUT_WITH_SMILES)
        # smiles should not appear in metadata known_order
        assert "smiles" not in result["metadata"]["known_order"]

    def test_name_column_parsed(self):
        result = process_input(INPUT_WITH_SMILES)
        names = [p["name"] for p in result["peptides"]]
        assert "pep1" in names
        assert "pep2" in names

    def test_default_name_is_row_index(self):
        """When no name column, peptide name defaults to its row index."""
        result = process_input(SIMPLE_INPUT)
        names = [p["name"] for p in result["peptides"]]
        assert "Row 1" in names
        assert "Row 2" in names


class TestPeptideFormats:
    """Linear, cyclic, and modified monomer peptide formats."""

    def test_cyclic_bracket_notation(self):
        result = process_input(CYCLIC_PEPTIDES_INPUT)
        assert result["metadata"]["known"] == 3
        assert len(result["monomers"]) == 7

    def test_cyclic_peptide(self):
        result = Peptide(1, "L-Asn-D-FOHOrn-L-Lys-(L-Thr-Ala-Ala-D-FOHOrn-D-Lys)")
        assert len(result._monomers) == 8
        assert "L-Thr" in result._monomers
        assert "L-Lys" in result._monomers
        assert "D-Lys" in result._monomers

    def test_modified_monomers_parsed(self):
        """Monomers with prefixes like D-, L-, N-Me-, β-OH- should be captured."""
        result = process_input(MULTI_COLUMN_INPUT)
        monomers = result["monomers"]
        # The regex should capture modified monomers
        assert len(monomers) == 14

    def test_branch_slash_notation_handled(self):
        """Peptides with / for branching (e.g. Gln/Dab) should parse."""
        result = process_input(CYCLIC_PEPTIDES_INPUT)
        # Should not crash; the slash peptide should be in results
        assert len(result["peptides"]) == 3
        assert "Gln" in result["monomers"]
        assert "Dab" in result["monomers"]


class TestPeptideCleaning:
    """Peptide sequences are cleaned before validation."""

    def test_double_dash_cleaned(self):
        input_text = "peptide\nAla--Thr--Ser\nVal-Leu-Pro\nGly-Ala-Phe\n"
        result = process_input(input_text)
        cleaned = result["peptides"][0]["peptide"]
        assert "--" not in cleaned

    def test_whitespace_in_peptide_removed(self):
        input_text = "peptide\nAla- Thr -Ser\nVal-Leu-Pro\nGly-Ala-Phe\n"
        result = process_input(input_text)
        cleaned = result["peptides"][0]["peptide"]
        assert " " not in cleaned

    def test_cleaning_triggers_warning(self):
        input_text = "peptide\nAla--Thr-Ser\nVal- Leu-Pro\nGly-Ala-Phe\n"
        result = process_input(input_text)
        assert result["warnings"].count_infocode(InfoCode.CLEANED_PEPTIDE) == 2


class TestValidation:
    """Invalid input, empty input, and edge cases."""

    def test_empty_input(self):
        result = process_input("")
        assert result["warnings"].count_infocode(InfoCode.NO_INPUT) == 1

    def test_whitespace_only_input(self):
        result = process_input("   \n  \n  ")
        assert result["warnings"].count_infocode(InfoCode.NO_INPUT) == 1

    def test_header_only_no_data(self):
        result = process_input("peptide\n")
        assert result["warnings"].count_infocode(InfoCode.NO_PEPTIDES) == 1

    def test_not_enough_peptides_warning(self):
        """Fewer than 2 valid peptides should warn and not succeed."""
        input_text = "peptide\nAla-Thr-Ser\n"
        result = process_input(input_text)
        assert result["warnings"].count_infocode(InfoCode.NOT_ENOUGH_PEPTIDES) == 1

    def test_mismatched_column_count_raises(self):
        """Row with wrong number of columns should raise ValueError."""
        input_text = "peptide, name\nAla-Thr-Ser\n"
        result = process_input(input_text)
        assert result["warnings"].count_infocode(InfoCode.MISMATCH_NO_COLUMNS) == 1

    def test_disallowed_characters_invalidate_peptide(self):
        input_text = "peptide\n#Invalid-Pep\nInvalid-#-Pep\nGly-Ala-Phe\n"
        result = process_input(input_text)
        invalid = [p for p in result["peptides"] if not p["valid"]]
        assert len(invalid) == 2

    def test_single_monomer_invalidates_peptide(self):
        input_text = "peptide\nAla\nVal-Leu-Pro\nGly-Ala-Phe\n"
        result = process_input(input_text)
        first = result["peptides"][0]
        assert first["valid"] is False

    def test_incorrect_monomer_invalidates_peptide(self):
        input_text = "peptide\nAa-Lu-Pr\nVal-leu-Pro\nGly-Adda-Phe-BUT\n"
        result = process_input(input_text)
        assert result["peptides"][0]["valid"] is False
        assert result["peptides"][1]["valid"] is False
        assert result["peptides"][2]["valid"] is True

    def test_unknown_monomers_collected(self):
        raw = process_input("peptide\nGly-L-Ala-Xxx-Zzz")
        print(raw)
        unknown = [c for c, m in raw["monomers"].items() if m["known"] == "Unknown"]
        assert "Xxx" in unknown
        assert "Zzz" in unknown

    def test_known_monomers_resolved(self):
        raw = process_input("peptide\nGly-L-Ala-Pro")
        for code in ["Gly", "L-Ala", "Pro"]:
            assert raw["monomers"][code]["known"] is "Inbuilt"
            assert raw["monomers"][code]["name"] is not None


class TestPeptideDataclass:
    """Direct tests on the Peptide dataclass."""

    def test_peptide_to_dict_has_required_keys(self):
        from peptorama.processing.info_codes import InfoCollector

        p = Peptide(
            _id=1,
            peptide="Ala-Thr-Ser",
            _warnings=InfoCollector(),
        )
        d = p.to_dict()
        assert "id" in d
        assert "number" in d
        assert "name" in d
        assert "peptide" in d
        assert "valid" in d
        assert "monomers" in d

    def test_peptide_name_defaults_to_id(self):
        from peptorama.processing.info_codes import InfoCollector

        p = Peptide(_id=42, peptide="Ala-Thr-Ser", _warnings=InfoCollector())
        assert p.name == "Row 42"

    def test_peptide_monomer_extraction(self):
        from peptorama.processing.info_codes import InfoCollector

        p = Peptide(
            _id=1,
            peptide="Gly-L-Ala-D-Leu-Orn-Pro",
            _warnings=InfoCollector(),
        )
        assert len(p._monomers) == 5

    def test_peptide_metadata_in_dict(self):
        from peptorama.processing.info_codes import InfoCollector

        p = Peptide(
            _id=1,
            peptide="Ala-Thr-Ser",
            _warnings=InfoCollector(),
            _metadata={"cyclisation": "linear", "banana": False},
        )
        d = p.to_dict()
        assert d["metadata"]["cyclisation"] == "linear"
        assert d["metadata"]["banana"] == False

    def test_empty_peptide_is_invalid(self):
        from peptorama.processing.info_codes import InfoCollector

        p = Peptide(_id=1, peptide="", _warnings=InfoCollector())
        assert p.valid is False


class TestOutputStructure:
    """Verify the shape of the returned dictionary."""

    def test_output_has_expected_keys(self):
        result = process_input(SIMPLE_INPUT)
        assert "peptides" in result
        assert "monomers" in result
        assert "warnings" in result
        assert "metadata" in result

    def test_metadata_has_expected_keys(self):
        result = process_input(SIMPLE_INPUT)
        meta = result["metadata"]
        assert "known" in meta
        assert "predicted" in meta
        assert "known_order" in meta
        assert "predicted_order" in meta

    def test_monomers_is_a_dict(self):
        result = process_input(SIMPLE_INPUT)
        assert isinstance(result["monomers"], dict)

    def test_peptides_is_list_of_dicts(self):
        result = process_input(SIMPLE_INPUT)
        assert isinstance(result["peptides"], list)
        for p in result["peptides"]:
            assert isinstance(p, dict)

    def test_peptide_ids_are_sequential(self):
        result = process_input(MULTI_COLUMN_INPUT)
        ids = [p["id"] for p in result["peptides"]]
        assert ids == ["p_1", "p_2", "p_3"]


class TestEdgeCases:
    """Blank lines, extra whitespace, trailing commas."""

    def test_blank_lines_ignored(self):
        input_text = "peptide\n\nAla-Thr-Ser\n\nVal-Leu-Pro\n\nGly-Ala-Phe\n"
        result = process_input(input_text)
        assert result["metadata"]["known"] == 3

    def test_leading_trailing_whitespace_stripped(self):
        input_text = "  peptide  \n  Ala-Thr-Ser  \n  Val-Leu-Pro  \n  Gly-Ala-Phe  \n"
        result = process_input(input_text)
        assert result["metadata"]["known"] == 3

    def test_cell_whitespace_stripped(self):
        input_text = "peptide , name\nAla-Thr-Ser , pep1\nVal-Leu-Pro , pep2\nGly-Ala-Phe , pep3\n"
        result = process_input(input_text)
        names = [p["name"] for p in result["peptides"]]
        assert "pep1" in names  # not " pep1"


@pytest.fixture
def user_monomer_asn_mismatched():
    """User claims Inbuilt but smiles differs from reference Asn."""
    return {
        "Ala": {
            "exact": "Asn",
            "name": "Test",
            "stereochemistry": "flat",
            "base": "Asn",
            "category": "",
            "smiles": "[*:1]NC(CC(=O)N)C(=O)[*:2]",
            "count": 1,
            "known": "Inbuilt",
        },
        "Banana": {
            "exact": "Banana",
            "name": "Banana",
            "stereochemistry": "flat",
            "base": "Banana",
            "category": "",
            "smiles": "[*:1][*:2]",
            "count": 1,
            "known": "Inbuilt",
        },
    }


class TestInbuiltMonomerWarnings:
    def test_mismatched_actual_inbuilt_user_inbuilt(self, user_monomer_asn_mismatched):
        result = process_input(
            SIMPLE_INPUT,
            "",
            user_monomer_asn_mismatched,
        )
        # Result is 2 because of Ala and D-Ala
        assert (
            result["warnings"].count_infocode(InfoCode.USER_INBUILT_MONOMER_DIFFERENT)
            == 2
        )


# ---------------------------------------------------------------------------
# SMILES-only input examples
# ---------------------------------------------------------------------------

SMILES_ONLY_INPUT = """\
smiles
CC(N)C(=O)NC(C(=O)NC(CO)C(=O)O)C(C)O
CC(N)C(=O)NC(C(C)C)C(=O)O
"""

SMILES_ONLY_WITH_NAME = """\
smiles, name
CC(N)C(=O)NC(C(=O)NC(CO)C(=O)O)C(C)O, pep1
CC(N)C(=O)NC(C(C)C)C(=O)O, pep2
"""

SMILES_ONLY_MULTI_COLUMN = """\
smiles, name, bioactivity
CC(N)C(=O)NC(C(=O)NC(CO)C(=O)O)C(C)O, pep1, antibacterial
CC(N)C(=O)NC(C(C)C)C(=O)O, pep2, antifungal
"""

SMILES_AND_PEPTIDE_INPUT = """\
smiles, peptide, name
CC(N)C(=O)NC(C(=O)NC(CO)C(=O)O)C(C)O, Ala-Thr-Ser, pep1
CC(N)C(=O)NC(C(C)C)C(=O)O, D-Ala-Val, pep2
"""


class TestSmilesOnlyParsing:
    """SMILES as the primary (first) column, no peptide column."""

    def test_smiles_only_parses_all_rows(self):
        result = process_input(SMILES_ONLY_INPUT)
        assert result["metadata"]["known"] == 2

    def test_smiles_only_smiles_preserved(self):
        result = process_input(SMILES_ONLY_INPUT)
        smiles = [p["smiles"] for p in result["peptides"]]
        assert "CC(N)C(=O)NC(C(=O)NC(CO)C(=O)O)C(C)O" in smiles
        assert "CC(N)C(=O)NC(C(C)C)C(=O)O" in smiles

    def test_smiles_only_peptide_field_is_none(self):
        result = process_input(SMILES_ONLY_INPUT)
        for p in result["peptides"]:
            assert p["peptide"] is None

    def test_smiles_only_no_monomers_extracted(self):
        result = process_input(SMILES_ONLY_INPUT)
        assert len(result["monomers"]) == 0

    def test_smiles_only_invalid(self):
        result = process_input(SMILES_ONLY_INPUT)
        for p in result["peptides"]:
            assert p["valid"] is False

    def test_smiles_only_header_detected(self):
        result = process_input(SMILES_ONLY_INPUT)
        assert result["warnings"].count_infocode(InfoCode.NO_HEADER) == 0

    def test_smiles_only_default_names(self):
        result = process_input(SMILES_ONLY_INPUT)
        names = [p["name"] for p in result["peptides"]]
        assert "Row 1" in names
        assert "Row 2" in names


class TestSmilesOnlyWithMetadata:
    """SMILES-first input with name and additional columns."""

    def test_smiles_with_name_parsed(self):
        result = process_input(SMILES_ONLY_WITH_NAME)
        names = [p["name"] for p in result["peptides"]]
        assert "pep1" in names
        assert "pep2" in names

    def test_smiles_multi_column_metadata(self):
        result = process_input(SMILES_ONLY_MULTI_COLUMN)
        col_order = result["metadata"]["known_order"]
        assert "bioactivity" in col_order
        assert "name" not in col_order
        assert "smiles" not in col_order

    def test_smiles_multi_column_values_on_peptide(self):
        result = process_input(SMILES_ONLY_MULTI_COLUMN)
        first = result["peptides"][0]["metadata"]
        assert first.get("bioactivity") == "antibacterial"


class TestSmilesPlusPeptide:
    """Both SMILES and peptide columns present, SMILES as primary."""

    def test_both_columns_parsed(self):
        result = process_input(SMILES_AND_PEPTIDE_INPUT)
        assert result["metadata"]["known"] == 2

    def test_both_smiles_and_peptide_populated(self):
        result = process_input(SMILES_AND_PEPTIDE_INPUT)
        for p in result["peptides"]:
            assert p["smiles"] is not None
            assert p["peptide"] is not None

    def test_monomers_extracted_from_peptide_column(self):
        result = process_input(SMILES_AND_PEPTIDE_INPUT)
        assert len(result["monomers"]) > 0

    def test_smiles_not_in_known_order(self):
        result = process_input(SMILES_AND_PEPTIDE_INPUT)
        assert "smiles" not in result["metadata"]["known_order"]

    def test_peptide_not_in_known_order(self):
        result = process_input(SMILES_AND_PEPTIDE_INPUT)
        assert "peptide" not in result["metadata"]["known_order"]


class TestSmilesOnlyValidation:
    """Edge cases and validation for SMILES-only mode."""

    def test_empty_smiles_row_invalid(self):
        input_text = "smiles\n\nCC(N)C(=O)NC(C(C)C)C(=O)O\nCC(N)C(=O)O\n"
        result = process_input(input_text)
        # blank lines are stripped, so only 2 rows
        assert result["metadata"]["known"] == 2

    def test_single_smiles_not_enough(self):
        input_text = "smiles\nCC(N)C(=O)NC(C(C)C)C(=O)O\n"
        result = process_input(input_text)
        assert result["warnings"].count_infocode(InfoCode.NOT_ENOUGH_PEPTIDES) == 1

    def test_smiles_mismatched_columns_warns(self):
        input_text = "smiles, name\nCC(N)C(=O)O\n"
        result = process_input(input_text)
        assert result["warnings"].count_infocode(InfoCode.MISMATCH_NO_COLUMNS) == 1

    def test_smiles_only_no_smiles_generation_attempted(self):
        """When SMILES is already provided, no generation should occur."""
        result = process_input(SMILES_ONLY_INPUT)
        assert result["warnings"].count_infocode(InfoCode.SMILES_NOT_GENERATED) == 0
