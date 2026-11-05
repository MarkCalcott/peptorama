import re
from dataclasses import dataclass, field, asdict
from .info_codes import InfoCode, InfoCollector
from .generate_SMILES import generate_smiles, getMonomerEntry
from peptorama.schemas import DISALLOWED_TEXT
from importlib.resources import files

# -- Policy limits --
import json

MONOMER_DICT = json.loads(
    files("peptorama").joinpath("static/data/monomers.json").read_text()
)


def _process_source(input_text, origin, output, start_idx):
    """
    Parse one input source (known or predicted) into output, in place.

    idx is threaded in via start_idx and returned so the caller can continue
    the count into the next source — peptides get globally-unique ids across
    both known and predicted rather than each source restarting at 1.

    Returns the next free index.
    """
    if not input_text.strip():
        return start_idx, []

    lines = [x.strip() for x in input_text.splitlines() if x.strip()]

    # Header detection
    first_cells = [x.strip() for x in lines[0].split(",")]
    has_header = any(
        re.match(r"^(peptides?|smiles)$", cell, re.IGNORECASE)
        for cell in first_cells
    )

    if has_header:
        col_names = [x.strip() for x in first_cells]
        lines = lines[1:]
    else:
        col_names = ["peptide"]
        col_names.extend(["C" + str(x) for x in range(1, len(first_cells))])
        output["warnings"].add(InfoCode.NO_HEADER)

    # Check for other lines
    if len(lines) == 0:
        output["warnings"].add(InfoCode.NO_PEPTIDES)
        return start_idx, []

    # Check the number of columns
    col_number = len(col_names)
    if col_number == 1:
        output["warnings"].add(InfoCode.SINGLE_COLUMN)

    # Locate peptide / name / smiles columns
    peptide_col = name_col = smile_col = None
    for i, item in enumerate(col_names):
        if re.fullmatch(r"^peptides?$", item, re.IGNORECASE):
            peptide_col = i
        elif re.fullmatch(r"^smiles$", item, re.IGNORECASE):
            smile_col = i
        elif re.fullmatch(r"names?", item, re.IGNORECASE):
            name_col = i

    # Check column names are unique
    seen = set()
    col_order = []
    for cell_id, cell in enumerate(col_names):
        if cell in seen:
            output["warnings"].add(InfoCode.DUPLICATED_METADATA, col_name=cell)
        else:
            seen.add(cell)
            if not cell_id in (peptide_col, name_col, smile_col):
                col_order.append((cell_id, cell))

    # Process each peptide
    idx = start_idx
    for line in lines:

        cells = [x.strip() for x in line.split(",")]

        peptide_str = cells[peptide_col] if peptide_col is not None else None

        if len(cells) != len(col_names):
            output["warnings"].add(InfoCode.MISMATCH_NO_COLUMNS, row=idx)
            output["peptides"].append(
                Peptide(_id=idx, peptide=peptide_str, origin=origin, valid=False)
            )
            idx += 1
            continue

        name = cells[name_col] if name_col is not None else None
        smiles = (
            cells[smile_col] if smile_col is not None and cells[smile_col] else None
        )

        metadata = {}
        for cell_id, col in col_order:
            value = cells[cell_id]
            if value == "NA":
                output["warnings"].add(InfoCode.NA_COLUMNS)
            if value == "":
                value = "NA"
            metadata[col] = value

        # Validate that at least one of peptide or smiles is present
        if not peptide_str and not smiles:
            output["warnings"].add(InfoCode.NO_PEPTIDE_OR_SMILES, row=idx)
            output["peptides"].append(
                Peptide(
                    _id=idx,
                    peptide="",
                    name=name,
                    origin=origin,
                    _warnings=output["warnings"],
                    _metadata=metadata,
                    valid=False,
                )
            )
            idx += 1
            continue

        peptide = Peptide(
            _id=idx + 1,
            peptide=peptide_str,
            name=name,
            smiles=smiles,
            origin=origin,
            _warnings=output["warnings"],
            _metadata=metadata,
        )
        output["peptides"].append(peptide)

        if peptide.valid:
            for monomer in peptide._monomers:
                if monomer not in output["monomers"]:
                    output["monomers"][monomer] = {"count": 0}
                output["monomers"][monomer]["count"] += 1

        idx += 1

    return idx, col_order


def process_input(
    known: str, predicted: str = "", user_monomers: dict | None = None
) -> dict:
    """
    This function takes the raw text input with one peptide per line. It processes
    it to return a dictionary
    """

    # The structure of the returned dictionary
    output = {
        "peptides": [],
        "monomers": {},
        "warnings": InfoCollector(),
        "metadata": {
            "known": 0,
            "predicted": 0,
            "known_order": [],
            "predicted_order": [],
        },
    }

    # Only process actual data
    if not known.strip() and not predicted.strip():
        output["warnings"].add(InfoCode.NO_INPUT)
        return output

    # Extract data from each input type
    known_count, known_order = _process_source(known, "known", output, 0)
    total_count, predicted_order = _process_source(
        predicted, "predicted", output, known_count
    )
    predicted_count = total_count - known_count

    # Merge monomers
    if user_monomers:
        monomer_dict = {**MONOMER_DICT, **user_monomers}
    else:
        monomer_dict = {**MONOMER_DICT}

    # Resolve monomers against dictionary
    DIVERGENCE_FIELDS = ("base", "exact", "name", "category", "smiles")
    for code, info in output["monomers"].items():

        resolved = {"code": code, **info, **getMonomerEntry(code, monomer_dict)}

        if resolved.get("smiles") == "[*:1]NC([*:4])C(=O)[*:2]":
            resolved["known"] = "Unknown"
            output["warnings"].add(InfoCode.UNKNOWN_MONOMERS, monomer_code=code)

        # Checks the amino acids match if the base is known, i.e. L-Ser has the base of Ser
        elif (
            resolved.get("base") in MONOMER_DICT or resolved.get("code") in MONOMER_DICT
        ):
            expected = getMonomerEntry(code, MONOMER_DICT)
            if any(resolved.get(f) != expected.get(f) for f in DIVERGENCE_FIELDS):
                resolved["known"] = "User-defined"
                output["warnings"].add(
                    InfoCode.USER_INBUILT_MONOMER_DIFFERENT, monomer_code=code
                )
            else:
                resolved["known"] = "Inbuilt"
        else:
            resolved["known"] = "User-defined"

        output["monomers"][code] = resolved

    # Construct SMILES
    for peptide in output["peptides"]:
        if peptide.smiles == None and peptide.peptide and peptide.valid:
            peptide.smiles = generate_smiles(peptide, output["monomers"])
            if peptide.smiles == None:
                output["warnings"].add(InfoCode.SMILES_NOT_GENERATED, name=peptide.name)

    # Finalise metadata
    output["peptides"] = [p.to_dict() for p in output["peptides"]]
    output["metadata"]["known"] = known_count
    output["metadata"]["predicted"] = predicted_count
    output["metadata"]["known_order"] = [col for _, col in known_order]
    output["metadata"]["predicted_order"] = [col for _, col in predicted_order]

    if (output["metadata"]["known"] <= 1) and (output["metadata"]["predicted"] <= 1):
        output["warnings"].add(InfoCode.NOT_ENOUGH_PEPTIDES)

    return output


@dataclass
class Peptide:
    _id: int
    peptide: str = None
    origin: str = None
    name: str = None
    smiles: str = None
    valid: bool = True
    _warnings: list = InfoCollector()
    _monomers: list = field(default_factory=list)
    _metadata: dict = field(default_factory=dict)

    DISALLOWED_CHARACTERS = re.compile(DISALLOWED_TEXT)
    MONOMER_REGEX = re.compile(
        r"((?:(?:(?<=[-(\/])|^)[a-z]*.{0,2}-)*[a-zA-Z0-9]*[A-Z][a-zA-Z0-9]{2,})"
    )

    def __post_init__(self):
        if self.name is None:
            self.name = "Row " + str(self._id)

        if self.peptide and self.peptide != "":
            self._clean_peptide()
            # Replace structural delimiters with '-' for regex parsing
            basic_peptide = re.sub(r"[()/]+", "-", self.peptide).strip("-")
            basic_peptide = re.sub(r"-{2,}", "-", basic_peptide)
            self._monomers = [
                x.strip()
                for x in re.findall(self.MONOMER_REGEX, basic_peptide.strip("[]"))
            ]
            self.validate()
        else:
            self.valid = False

    def _clean_peptide(self):

        original = self.peptide

        if re.search(r"--", self.peptide):
            self.peptide = re.sub(r"-{2,}", "-", self.peptide)

        if re.search(r"\s", self.peptide):
            self.peptide = re.sub(r"\s", "", self.peptide)

        if self.peptide != original:
            self._warnings.add(
                InfoCode.CLEANED_PEPTIDE,
                name=self.name,
                original=original,
                cleaned=self.peptide,
            )

    def validate(self):
        if re.search(self.DISALLOWED_CHARACTERS, self.peptide):
            self.valid = False
            self._warnings.add(InfoCode.INVALID_CHARACTERS, row=self.name)

        if len(self._monomers) <= 1 and self.peptide:
            self.valid = False
            self._warnings.add(InfoCode.ONLY_ONE_MONOMER, row=self.name)

        segments = re.split(r"[-/()]", self.peptide)
        if any(seg and len(seg) > 2 and seg == seg.lower() for seg in segments):
            self.valid = False
            self._warnings.add(InfoCode.INVALID_CAPITALISATION, row=self.name)

        return

    def to_dict(self) -> dict:
        """Flat dict for JSON output"""
        out = {
            "id": f"p_{self._id}",
            "number": self._id,
            "name": self.name,
            "origin": self.origin,
            "peptide": self.peptide,
            "smiles": self.smiles,
            "valid": self.valid,
            "monomers": self._monomers,
            "metadata": dict(self._metadata),
        }
        return out
