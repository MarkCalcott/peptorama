import re
from .info_codes import InfoCode
from rdkit import Chem

def _parse_methylation(monomer):
    atoms = []
    remainder = monomer
    for match in re.finditer(r"([NOS])-Me-", monomer):
        atoms.append(match.group(1))
        remainder = remainder.replace(match.group(), "", 1)
    return atoms, remainder


def getMonomerEntry(
    raw_monomer: str, monomers: dict) -> dict:
    """Takes in a raw amino acid, finds the base, adds basic decoration and stereochemistry for the alpha carbon"""

    # Return if in dictionary
    if raw_monomer in monomers:           
        entry = monomers[raw_monomer]
        return entry
    
    # Check the stereochemistry
    if raw_monomer.upper().startswith("L-"):
        stereochemistry = "L"
        flat_monomer = raw_monomer[2:]
    elif raw_monomer.upper().startswith("D-"):
        stereochemistry = "D"
        flat_monomer = raw_monomer[2:]
    else:
        stereochemistry = None
        flat_monomer = raw_monomer

    # Check for methylation
    methylation_pos, monomer = _parse_methylation(flat_monomer)

    # Monomer without methylation
    if stereochemistry:
        stereo_monomer = stereochemistry + "-" + monomer
    else:
        stereo_monomer = monomer

    # Get the base SMILES if available
    smiles = ""
    name = None
    category = None
    if stereochemistry and methylation_pos:
        if flat_monomer in monomers and stereo_monomer not in monomers:
            smiles = monomers[flat_monomer]["smiles"]
            name = monomers[flat_monomer]["name"]
            category = monomers[flat_monomer]["category"]
        elif flat_monomer not in monomers and stereo_monomer in monomers:
            smiles = monomers[stereo_monomer]["smiles"]
            name = monomers[stereo_monomer]["name"]
            category = monomers[stereo_monomer]["category"]
        else:
            smiles = ""

    if len(methylation_pos) > 0:
        if monomer in monomers:
            if len(smiles) == 0:
                smiles = monomers[monomer]["smiles"]
                name = monomers[monomer]["name"]
                category = monomers[monomer]["category"]
            if "O" in methylation_pos or "S" in methylation_pos:
                new = smiles.replace("[*:3]", "C")
                if new == smiles:
                    smiles = ""
                else:
                    smiles = new
            if "N" in methylation_pos:
                new = smiles.replace("[*:1]N", "[*:1]N(C)")
                if new == smiles:
                    smiles = ""
                else:
                    smiles = new

    if stereochemistry:
        if monomer in monomers:
            if len(smiles) == 0:
                smiles = monomers[flat_monomer]["smiles"]
                name = monomers[flat_monomer]["name"]
                category = monomers[flat_monomer]["category"]

            if smiles.startswith("[*:1]NC") or smiles.startswith("[*:1]N(C)C"):
                if stereochemistry == "L":
                    smiles = smiles.replace("[*:1]NC", "[*:1]N[C@@H]", 1)
                    smiles = smiles.replace("[*:1]N(C)C", "[*:1]N(C)[C@@H]", 1)
                elif stereochemistry == "D":
                    smiles = smiles.replace("[*:1]NC", "[*:1]N[C@H]", 1)
                    smiles = smiles.replace("[*:1]N(C)C", "[*:1]N(C)[C@H]", 1)
                else:
                    smiles = ""

    # Find the base amino acid, easier to find the shortest base amino acid by reversing
    reversed_monomer = raw_monomer[::-1]
    reversed_base = re.match(r"^[a-zA-Z0-9]{2,}?[A-Z]", reversed_monomer)
    base = reversed_base.group()[::-1]

    if len(smiles) == 0 or not Chem.MolFromSmiles(smiles):
        smiles = "[*:1]NC([*:4])C(=O)[*:2]"  # Blank amino acid with label for unknown


    # Creating entry
    
    entry = {
        "exact": flat_monomer,
        "base": base,
        "stereochemistry": stereochemistry or "flat",
        "name": name,
        "IUPAC": None,
        "smiles": smiles,
        "category": category,
    }
      

    return entry

def internal_multiple_cyclisation(mol_1, mol_2, label=9):
    """
    For internal cyclisation of multiple peptides. 

    Takes two SMILES strings and attaches the terminus of the first to the to an 
    internal residue of the second.
    """
    mol_1 = re.sub(r"\[\*:[2]\]", "[*:9]", mol_1)
    mol_2 = re.sub(r"\[\*:[34]\]", "[*:9]", mol_2)
    combined_smiles = mol_1 + "." + mol_2
    combined_smiles = combined_smiles.replace("[*:1]", "")
    
    mol = Chem.MolFromSmiles(combined_smiles)
    if mol is None:
        raise ValueError(f"Could not parse SMILES:\n  {combined_smiles}")

    label = 9
    hits = []
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 0 and atom.GetAtomMapNum() == label:
            nbrs = atom.GetNeighbors()
            if len(nbrs) != 1:
                raise ValueError(
                    f"[*:{label}] at idx {atom.GetIdx()} has {len(nbrs)} "
                    f"neighbors; expected exactly 1."
                )
            hits.append((atom.GetIdx(), nbrs[0].GetIdx()))

    if len(hits) != 2:
        raise ValueError(
            f"Expected exactly 2 atoms with map number {label}, found {len(hits)}."
        )

    (dummy_a, anchor_a), (dummy_b, anchor_b) = hits

    rw = Chem.RWMol(mol)
    rw.AddBond(anchor_a, anchor_b, Chem.BondType.SINGLE)

    for didx in sorted([dummy_a, dummy_b], reverse=True):
        rw.RemoveAtom(didx)

    try:
        Chem.SanitizeMol(rw)
    except Exception as e:
        print(f"Warning: SanitizeMol raised {e}; returning unsanitized mol.")

    return Chem.MolToSmiles(rw)


def generate_smiles(
    peptide: object, monomers: dict
) -> str:

    peptide_str = peptide.peptide

    smiles_monomers = []
    cyclisation_release = False

    # Resolve head to tail cyclisation
    if peptide_str.startswith("[") and peptide_str.endswith("]"):
        n = 0
        while peptide_str.startswith("[") and peptide_str.endswith("]"):
            cyclisation_release = "head-to-tail"
            n += 1
            peptide_str = peptide_str[1:-1]

        monomer_list = peptide._monomers * n

    else:
        monomer_list = peptide._monomers

    for monomer in monomer_list:
        # Check for cyclisation
        pos = peptide_str.find(monomer)

        # Removes (=O)[*:2] from upstream monomer
        remove_carbonyl = pos > 0 and "/" in peptide_str[0:pos]

        # Terminus to the amine group
        intramolecular = pos > 0 and "(" in peptide_str[0:pos]
        if intramolecular: intramolecular_n = peptide_str[0:pos].count("(")

        # Remove the first monomer
        end = pos + len(monomer)
        peptide_str = peptide_str[end:].lstrip("-")

        # Get the monomers in smiles format
        if monomer in monomers:
            if remove_carbonyl:
                smiles_monomer = monomers[monomer]["smiles"]
                smiles_monomers[-1] = smiles_monomers[-1].replace("C(=O)[*:2]", "[*:2]")
            if intramolecular:
                smiles_monomer = monomers[monomer]["smiles"]
                cyclisation_release = "intramolecular"
            else:
                smiles_monomer = re.sub(r"\[\*:[3]\]", "", monomers[monomer]["smiles"])
                smiles_monomer = re.sub(r"\[\*:[4]\]", "*", smiles_monomer)

            smiles_monomers.append(smiles_monomer)
        else:
            return None

    smiles_peptide = "[*:1][*:2]"

    for i in range(len(smiles_monomers)):
        # Used replace to provide flexibility but the onus is on the user
        smiles_peptide = smiles_peptide.replace("[*:2]", "") + smiles_monomers[
            i
        ].replace("[*:1]", "")

    # Peptide still has leaving groups at this stage, [*:1]peptide[*:2]
    if cyclisation_release == "head-to-tail":
        smiles_peptide = smiles_peptide.replace("[*:1]", "")
        smiles_peptide = smiles_peptide.replace("[*:2]", "")
        smiles_peptide = smiles_peptide[0] + "9" + smiles_peptide[1:] + "9"

    elif cyclisation_release == "intramolecular":
        subunit = smiles_peptide.replace("[*:1]", "")
        while intramolecular_n >= 1:
            if intramolecular_n == 1:
                smiles_peptide = re.sub(r"\[\*:[234]\]", "9", smiles_peptide)
                smiles_peptide = smiles_peptide.replace("[*:1]", "")
                break
            smiles_peptide = internal_multiple_cyclisation(smiles_peptide, subunit) 
            intramolecular_n -= 1

        
    else:
        smiles_peptide = smiles_peptide.replace("[*:1]", "")
        # This allows aldehydes if 2 is absent or other terminal groups
        smiles_peptide = smiles_peptide.replace("[*:2]", "O")

    # Replace placeholders with numbers
    smiles_peptide = re.sub(r'\(\[\*:([5-8])\]\)', r'\1', smiles_peptide)
    smiles_peptide = re.sub(r'\[\*:([5-8])\]', r'\1', smiles_peptide)

    # Check with RDKit
    mol = Chem.MolFromSmiles(smiles_peptide)
    if not mol:
        return None

    return Chem.MolToSmiles(mol)
