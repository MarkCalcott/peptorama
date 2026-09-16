import pytest

from peptworkz.info_codes import (
    SeverityLevel,
    InfoCode,
    InfoCollector,
    render,
    static,
    per_entry,
    aggregated,
)

# --- SeverityLevel ordering ---


class TestSeverityLevel:
    def test_ordering(self):
        assert SeverityLevel.INFO < SeverityLevel.WARNING
        assert SeverityLevel.WARNING < SeverityLevel.ERROR
        assert SeverityLevel.ERROR < SeverityLevel.CRITICAL

    def test_equal_not_less(self):
        assert not SeverityLevel.ERROR < SeverityLevel.ERROR
        assert SeverityLevel.ERROR <= SeverityLevel.ERROR

    def test_not_comparable_to_other_types(self):
        assert SeverityLevel.INFO.__lt__("info") is NotImplemented


# --- InfoCode ---


class TestInfoCode:

    def test_code_value(self):
        assert InfoCode.NO_INPUT.code == 1001
        assert InfoCode.SINGLE_COLUMN.code == 1002
        assert InfoCode.NO_HEADER.code == 1003
        assert InfoCode.NO_PEPTIDES.code == 1004
        assert InfoCode.MISMATCH_NO_COLUMNS.code == 1005
        assert InfoCode.CLEANED_PEPTIDE.code == 2001
        assert InfoCode.DUPLICATED_METADATA.code == 2002
        assert InfoCode.NO_PEPTIDE.code == 2003
        assert InfoCode.INVALID_CHARACTERS.code == 2004
        assert InfoCode.ONLY_ONE_MONOMER.code == 2005
        assert InfoCode.NOT_ENOUGH_PEPTIDES.code == 2006
        assert InfoCode.INVALID_CAPITALISATION.code == 2007
        assert InfoCode.UNKNOWN_MONOMERS.code == 2008
        assert InfoCode.USER_MONOMERS.code == 2009
        assert InfoCode.NA_COLUMNS.code == 2010
        assert InfoCode.USER_INBUILT_MONOMER_DIFFERENT.code == 2011
        assert InfoCode.SMILES_NOT_GENERATED.code == 2012
        assert InfoCode.NO_PEPTIDE_OR_SMILES.code == 2013
        

    def test_level(self):
        assert InfoCode.NO_INPUT.level.value == "critical"
        assert InfoCode.SINGLE_COLUMN.level.value == "info"
        assert InfoCode.NO_HEADER.level.value == "warning"
        assert InfoCode.NO_PEPTIDES.level.value == "critical"
        assert InfoCode.MISMATCH_NO_COLUMNS.level.value == "error"
        assert InfoCode.CLEANED_PEPTIDE.level.value == "warning"
        assert InfoCode.DUPLICATED_METADATA.level.value == "error"
        assert InfoCode.NO_PEPTIDE.level.value == "error"
        assert InfoCode.INVALID_CHARACTERS.level.value == "error"
        assert InfoCode.ONLY_ONE_MONOMER.level.value == "error"
        assert InfoCode.NOT_ENOUGH_PEPTIDES.level.value == "critical"
        assert InfoCode.INVALID_CAPITALISATION.level.value == "error"
        assert InfoCode.UNKNOWN_MONOMERS.level.value == "warning"
        assert InfoCode.USER_MONOMERS.level.value == "warning"
        assert InfoCode.NA_COLUMNS.level.value == "warning"
        assert InfoCode.USER_INBUILT_MONOMER_DIFFERENT.level.value == "warning"
        assert InfoCode.SMILES_NOT_GENERATED.level.value == "warning"
        assert InfoCode.NO_PEPTIDE_OR_SMILES.level.value == "error"
        


# --- Renderer factories ---


class TestStatic:
    def test_ignores_entries(self):
        r = static("Eek, something bad happened!")
        assert r([]) == ["Eek, something bad happened!"]
        assert r([{}, {}, {}]) == ["Eek, something bad happened!"]


class TestPerEntry:
    def test_formats_each_entry(self):
        r = per_entry("Row {row}: {name}")
        entries = [{"row": 1, "name": "A"}, {"row": 2, "name": "B"}]
        assert r(entries) == ["Row 1: A", "Row 2: B"]

    def test_empty_entries(self):
        r = per_entry("Row {row}")
        assert r([]) == []

    def test_missing_key_raises(self):
        r = per_entry("Row {row}: {name}")
        with pytest.raises(KeyError):
            r([{"row": 1}])


class TestAggregated:
    def test_collects_key_values(self):
        r = aggregated("Affected rows: {values}")
        entries = [{"row": 1}, {"row": 5}, {"row": 12}]
        assert r(entries) == ["Affected rows: 1, 5, 12"]

    def test_skips_entries_missing_key(self):
        r = aggregated("Rows: {values}")
        entries = [{"row": 1}, {"not_a_row": "x"}, {"row": 3}]
        assert r(entries) == ["Rows: 1, 3"]

    def test_all_missing_returns_empty(self):
        r = aggregated("Rows: {values}")
        assert r([{"other": "x"}]) == []

    def test_custom_key(self):
        r = aggregated("Names: {values}", key="name")
        entries = [{"name": "Alice"}, {"name": "Bob"}]
        assert r(entries) == ["Names: Alice, Bob"]


# --- render() fallback ---


class TestRender:
    def test_known_code(self):
        result = render(InfoCode.SINGLE_COLUMN, [{}, {}])
        assert result == ["Only a single column was detected."]

    def test_unknown_code_uses_fallback(self, monkeypatch):
        # Temporarily add a code that has no renderer
        from unittest.mock import MagicMock

        fake_code = MagicMock()
        fake_code.name = "HOUSTON_WE_HAVE_A_PROBLEM"
        result = render(fake_code, [{}, {}, {}])
        assert result == ["Issue detected: HOUSTON_WE_HAVE_A_PROBLEM - 3 occurrence(s)"]


# --- InfoCollector ---


# Test codes that won't change when real codes are reorganized
class FakeCode:
    def __init__(self, name: str, code: int, level: SeverityLevel):
        self.code = code
        self._level = level
        self.name = name

    @property
    def level(self) -> SeverityLevel:
        return self._level


FAKE_INFO = FakeCode("FAKE_INFO", 9001, SeverityLevel.INFO)
FAKE_WARNING = FakeCode("FAKE_WARNING", 9002, SeverityLevel.WARNING)
FAKE_ERROR = FakeCode("FAKE_ERROR", 9003, SeverityLevel.ERROR)
FAKE_CRITICAL = FakeCode("FAKE_CRITICAL", 9004, SeverityLevel.CRITICAL)


@pytest.fixture
def collector():
    return InfoCollector()


class TestInfoCollector:
    def test_empty_is_falsy(self, collector):
        assert not collector

    def test_non_empty_is_truthy(self, collector):
        collector.add(FAKE_INFO)
        assert collector

    def test_add_and_count(self, collector):
        collector.add(InfoCode.SINGLE_COLUMN)
        collector.add(InfoCode.SINGLE_COLUMN)
        assert collector.count() == 2

    def test_has_level_detects_errors(self, collector):
        collector.add(FAKE_ERROR)
        assert collector.has_level(SeverityLevel.ERROR)
        assert not collector.has_level(SeverityLevel.CRITICAL)

    def test_has_critical(self, collector):
        collector.add(FAKE_CRITICAL)
        assert collector.has_critical()

    def test_has_critical(self, collector):
        collector.add(FAKE_INFO)
        collector.add(FAKE_WARNING)
        collector.add(FAKE_ERROR)
        assert not collector.has_critical()
        assert collector.count() == 3

    def test_count_by_level(self, collector):
        collector.add(FAKE_INFO)
        collector.add(FAKE_INFO)
        collector.add(FAKE_ERROR)
        assert collector.count(SeverityLevel.INFO) == 2
        assert collector.count(SeverityLevel.WARNING) == 0
        assert collector.count(SeverityLevel.ERROR) == 1
        assert collector.count(SeverityLevel.CRITICAL) == 0


class TestToList:
    def test_structure(self, collector):
        collector.add(FAKE_INFO)
        result = collector.to_list()
        assert len(result) == 1
        item = result[0]
        assert item["code"] == 9001
        assert item["message"] == "Issue detected: FAKE_INFO - 1 occurrence(s)"
        assert item["level"] == "info"
