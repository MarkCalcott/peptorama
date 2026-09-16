from enum import Enum
from collections import defaultdict

_SEVERITY_ORDER = {
    "info": 0,
    "warning": 1,
    "error": 2,
    "critical": 3,
}


class SeverityLevel(Enum):
    INFO = (
        "info"  # Things that might be useful information but not impacting processing
    )
    WARNING = "warning"  # Small changes that shouldn't affect processing, e.g. trimming internal white space
    ERROR = "error"  # Changes that impact results but the program still runs, e.g. dropping bad rows or with incomplete info
    CRITICAL = "critical"  # Things that block the program from running

    @property
    def severity(self) -> int:
        return _SEVERITY_ORDER[self.value]

    def __lt__(self, other):
        if not isinstance(other, SeverityLevel):
            return NotImplemented
        return self.severity < other.severity

    def __le__(self, other):
        if not isinstance(other, SeverityLevel):
            return NotImplemented
        return self.severity <= other.severity


class InfoCode(Enum):

    # File format
    NO_INPUT = (1001, SeverityLevel.CRITICAL)
    SINGLE_COLUMN = (1002, SeverityLevel.INFO)
    NO_HEADER = (1003, SeverityLevel.WARNING)
    NO_PEPTIDES = (1004, SeverityLevel.CRITICAL)
    MISMATCH_NO_COLUMNS = (1005, SeverityLevel.ERROR)

    # Peptide processing input
    CLEANED_PEPTIDE = (2001, SeverityLevel.WARNING)
    DUPLICATED_METADATA = (2002, SeverityLevel.ERROR)
    NO_PEPTIDE = (2003, SeverityLevel.ERROR)
    INVALID_CHARACTERS = (2004, SeverityLevel.ERROR)
    ONLY_ONE_MONOMER = (2005, SeverityLevel.ERROR)
    NOT_ENOUGH_PEPTIDES = (2006, SeverityLevel.CRITICAL)
    INVALID_CAPITALISATION = (2007, SeverityLevel.ERROR)
    UNKNOWN_MONOMERS = (2008, SeverityLevel.WARNING)
    USER_MONOMERS = (2009, SeverityLevel.WARNING)
    NA_COLUMNS = (2010, SeverityLevel.WARNING)
    USER_INBUILT_MONOMER_DIFFERENT = (2011, SeverityLevel.WARNING)
    SMILES_NOT_GENERATED = (2012, SeverityLevel.WARNING)
    NO_PEPTIDE_OR_SMILES = (2013, SeverityLevel.ERROR)


    def __init__(self, code: int, level: SeverityLevel):
        self.code = code
        self._level = level

    @property
    def level(self) -> SeverityLevel:
        return self._level


class InfoCollector:
    def __init__(self):
        self._store: dict[InfoCode, list[dict]] = defaultdict(list)

    def add(self, code: InfoCode, **data):
        """
        Add structured information or warning

        Example:
            warnings.add(InfoCode.NAME_DUPLICATED, row=2, name="ABC")
        """
        self._store[code].append(data)

    def has_level(self, level: SeverityLevel) -> bool:
        """Check if any collected issue is at or above the given level"""
        return any(code.level >= level for code in self._store)

    def has_critical(self) -> bool:
        return self.has_level(SeverityLevel.CRITICAL)

    def count(self, level: SeverityLevel | None = None) -> int:
        """Count total entries for a severity level, optionally filtered by level."""
        if level is None:
            return sum(len(v) for v in self._store.values())
        return sum(len(v) for code, v in self._store.items() if code.level == level)

    def count_infocode(self, code: InfoCode) -> int:
        """Count entries for a specific InfoCode."""
        print("test")
        return len(self._store.get(code, []))

    def to_list(self) -> list[dict]:
        """
        Make information frontend ready
        """
        output = []
        for code, entries in self._store.items():
            messages = render(code, entries)

            for msg in messages:
                output.append(
                    {"code": code.code, "message": msg, "level": code.level.value}
                )

        return output

    def __bool__(self):
        return bool(self._store)


# --- Renderers ---
def static(message: str):
    """Always returns the same message regardless of entries."""

    def _render(entries: list[dict]) -> list[str]:
        return [message]

    return _render


def per_entry(template: str):
    """One message per entry, formatted with the entry's data."""

    def _render(entries: list[dict]) -> list[str]:
        return [template.format(**e) for e in entries]

    return _render


def aggregated(template: str, key: str = "row"):
    """Single message listing all values of `key` across entries."""

    def _render(entries: list[dict]) -> list[str]:
        values = [str(e[key]) for e in entries if key in e]
        if values:
            return [template.format(values=", ".join(values))]
        return []

    return _render


RENDERERS = {
    InfoCode.NO_HEADER: static("No header row was detected; one was auto-generated."),
    InfoCode.SINGLE_COLUMN: static("Only a single column was detected."),
    InfoCode.DUPLICATED_METADATA: aggregated(
        "Duplicated metadata column(s), only the first occurance of each was kept: {values}",
        key="col_name",
    ),
    InfoCode.CLEANED_PEPTIDE: per_entry(
        "Peptide {name} was cleaned: '{original}' → '{cleaned}"
    ),
    InfoCode.NO_PEPTIDE: aggregated(
        "No peptide was found resulting in samples being dropped: {values}"
    ),
    InfoCode.INVALID_CHARACTERS: aggregated(
        "Invalid characters were found in peptides and were therefore dropped: {values}"
    ),
    InfoCode.ONLY_ONE_MONOMER: aggregated(
        "Only one monomer was detected resulting in samples being dropped: {values}"
    ),
    InfoCode.NOT_ENOUGH_PEPTIDES: static("Not enough peptides were detected."),
    InfoCode.MISMATCH_NO_COLUMNS: aggregated(
        "The number of columns in the header and did not match some samples(s) resulting in skipped processing: Row(s) {values}"
    ),
    InfoCode.INVALID_CAPITALISATION: aggregated(
        "There was incorrect capitalisation resulting in skipping samples(s): {values}"
    ),
    InfoCode.UNKNOWN_MONOMERS: aggregated(
        "Unknown monomer(s) detected. Structures containing these will contain an undefined sidechain: {values}",
        key="monomer_code",
    ),
    InfoCode.USER_MONOMERS: static("User monomers have been used where provided."),
    InfoCode.NA_COLUMNS: static(
        "NA was detected as a value in metadata. Be aware that missing data will also be filled as NA."
    ),
    InfoCode.USER_INBUILT_MONOMER_DIFFERENT: aggregated(
        "The user provided a monomer listed as 'Inbuilt' that differs from the inbuilt value. These may be modifications of simpler amino acids. The users version has been used when matching: {values}",
        key="monomer_code",
    ),
    InfoCode.SMILES_NOT_GENERATED: aggregated(
        "Compound structures could not be generated for some peptides: {values}",
        key="name",
    ),
    InfoCode.NO_PEPTIDE_OR_SMILES: aggregated(
        "No peptide sequence or SMILES provided: Row(s) {values}",
        key="row",
    ),
}


def render(code: InfoCode, entries: list[dict]) -> list[str]:
    renderer = RENDERERS.get(code)
    if renderer is None:
        # Fallback so missing renderers don't crash the system
        return [f"Issue detected: {code.name} - {len(entries)} occurrence(s)"]
    return renderer(entries)
