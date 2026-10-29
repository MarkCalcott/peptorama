import pytest
from peptorama.processing.validate import process_input
from rdkit import Chem

user_monomers = {
    "Bmt": {
        "exact": "Bmt",
        "base": "Bmt",
        "stereochemistry": "flat",
        "name": "(4R)-4-[(E)-2-butenyl]-4-methyl-l-threonine",
        "smiles": r"[*:1]NC([C@H](O)[C@H](C)C\C=C\C)C(=O)[*:2]",
        "category": "Non-proteinogenic",
        "known": "User-defined",
    },
    "L-ureidoVal": {
        "exact": "ureidoVal",
        "base": "Val",
        "stereochemistry": "L",
        "name": "Uriedo-linked Val",
        "smiles": "[*:1]C(=O)(O)[C@H](C(C)C)NC(=O)[*:2]",
        "category": None,
        "known": "Uriedo-linked",
    },
    "dhLys": {
        "exact": "dhLys",
        "base": "Lys",
        "stereochemistry": "flat",
        "name": "3,4-dehydrolysine",
        "smiles": "[*:1]NC(/C=C/CCN[*:3])C(=O)[*:2]",
        "category": None,
        "known": "Non-proteinogenic",
    },
    "Sal": {
        "exact": "Sal",
        "base": "Sal",
        "stereochemistry": "flat",
        "name": "Salicylate",
        "smiles": "C1C=CC=C(O)C=1C(=O)[*:2]",
        "category": "Non-proteinogenic",
    },
    "L-Thz": {
        "exact": "Thz",
        "base": "Cys",
        "stereochemistry": "L",
        "name": "Thiazoline",
        "smiles": "[*:1]C1SC[C@@H](N=1)C(=O)[*:2]",
        "category": "Cyclised proteinogenic",
    },
    "L-Me-Thz": {
        "exact": "Me-Thz",
        "base": "Cys",
        "stereochemistry": "L",
        "name": "Thiazoline",
        "smiles": "[*:1]C1SC[C@@](C)(N=1)C(=O)[*:2]",
        "category": "Cyclised proteinogenic",
    },
    "L-Thd": {
        "exact": "Thd",
        "base": "Cys",
        "stereochemistry": "L",
        "name": "Thiazolidine",
        "smiles": "[*:1]C1SC[C@H](N1)C(=O)[*:2]",
        "category": "Cyclised proteinogenic",
    },
    "di-Me-KR-Mal": {
        "exact": "di-Me-KR-Mal",
        "base": "Mal",
        "stereochemistry": "flat",
        "name": "Dimethylated, reduced malonate",
        "smiles": "[*:1][C@@H](O)C(C)(C)C(=O)[*:2]",
        "category": "Polyketide",
    },
    "n-Dec": {
        "exact": "n-Dec",
        "base": "Dec",
        "stereochemistry": "flat",
        "name": "N-decanoyl",
        "smiles": "CCCCCCCCCC(=O)[*:2]",
        "category": "Fatty acid",
    },
    "3-Me-Glu": {
        "exact": "3-Me-Glu",
        "base": "Glu",
        "stereochemistry": "flat",
        "name": "",
        "smiles": "[*:1]NC([C@H](C)CC(=O)O[*:3])C(=O)[*:2]",
        "category": "Non-proteinogenic",
    },
    "Kyn": {
        "exact": "Kyn",
        "base": "Kyn",
        "stereochemistry": "flat",
        "name": "Kynurenine",
        "smiles": "[*:1]NC(CC(=O)C1=C(N)C=CC=C1)C(=O)[*:2]",
        "category": "Non-proteinogenic",
    },
    "Bht": {
        "exact": "Bht",
        "base": "Bht",
        "stereochemistry": "flat",
        "name": "β-hydroxytyrosine",
        "smiles": "[*:1]NC([C@H](O)C1=CC(Cl)=C(O([*:5]))C=C1)C(=O)[*:2]",
        "category": "Non-proteinogenic",
    },
    "D-Hpg": {
            "exact": "D-Hpg",
            "base": "Hpg",
            "stereochemistry": "flat",
            "name": "4-hydroxyphenylglycine",
            "smiles": "[*:1]N[C@H](C1=CC([*:6])=C(O)C=C1)C(=O)[*:2]",
            "category": "Non-proteinogenic",
        },
    "gvHpg": {
        "exact": "gvHpg",
        "base": "Hpg",
        "stereochemistry": "flat",
        "name": "Glucose + vancosamine 4-hydroxyphenylglycine",
        "smiles": "[*:1]NC(C1=CC([*:5])=C(O[C@@H]2O[C@H](CO)[C@@H](O)[C@H](O)[C@H]2O[C@@H]3O[C@@H](C)[C@@H](O)[C@@](C)(N)C3)C([*:5])=C1)C(=O)[*:2]",
        "category": "Non-proteinogenic",
    },

    "Dpg": {
        "exact": "Dpg",
        "base": "Dpg",
        "stereochemistry": "flat",
        "name": "3,5-dihydroxyphenylglycine",
        "smiles": "[*:1]NC(C1=C([*:6])C(O)=CC(O)=C1)C(=O)[*:2]",
        "category": "Non-proteinogenic",
    },
    "Pyr": {
        "exact": "Pyr",
        "base": "Pyr",
        "stereochemistry": "flat",
        "name": "Pyruvic acid",
        "smiles": "[*:1]CC(=O)C(=O)[*:2]",
        "category": "Non-proteinogenic",
    },
    "isoSta": {
        "exact": "isoSta",
        "base": "isoSta",
        "stereochemistry": "flat",
        "name": "Isostatine",
        "smiles": "[*:1]N[C@H]([C@@H](C)CC)[C@@H](O)CC(=O)[*:2]",
        "category": "Non-proteinogenic",
    },
    "Hip": {
        "exact": "Hip",
        "base": "Hip",
        "stereochemistry": "flat",
        "name": "Hydroxyisovalerylpropionyl",
        "smiles": "[*:1]O[C@@H](C(C)C)C(=O)[C@H](C)C(=O)[*:2]",
        "category": "Non-proteinogenic",
    },
    "cl-Cys": {
        "exact": "cl-Cys",
        "base": "Cys",
        "stereochemistry": "flat",
        "name": "Cross-linked cysteine",
        "smiles": "[*:1]NC(CS([*:5]))C(=O)[*:2]",
        "category": "Proteinogenic",
    },
    "3HQA": {
        "exact": "3HQA",
        "base": "3HQA",
        "stereochemistry": "flat",
        "name": "3-hydroxyquinaldic acid",
        "smiles": "C1(O)=CC2=C(C=CC=C2)N=C1C(=O)[*:2]",
        "category": "Non-proteinogenic",
    },
    "DHB": {
        "exact": "DHB",
        "base": "DHB",
        "stereochemistry": "flat",
        "name": "2,3-dihydroxybenzoic acid",
        "smiles": "C1(C(O)=C(O)C=CC=1)C(=O)[*:2]",
        "category": "Non-proteinogenic",
    },
}

pubchem = {
    5284373: "CC[C@H]1C(=O)N(CC(=O)N([C@H](C(=O)N[C@H](C(=O)N([C@H](C(=O)N[C@H](C(=O)N[C@@H](C(=O)N([C@H](C(=O)N([C@H](C(=O)N([C@H](C(=O)N([C@H](C(=O)N1)[C@@H]([C@H](C)C/C=C/C)O)C)C(C)C)C)CC(C)C)C)CC(C)C)C)C)C)CC(C)C)C)C(C)C)CC(C)C)C)C",
    42601513: "CC(C)[C@H]1/C=C/C(=O)NCC/C=C/[C@@H](C(=O)N1)NC(=O)[C@H](C(C)C)NC(=O)N[C@@H](C(C)C)C(=O)O",
    443589: "C[C@@]1(CSC(=N1)C(C)(C)[C@@H]([C@@H]2CSC(N2)[C@H]3CSC(=N3)C4=CC=CC=C4O)O)C(=O)O",
    16129635: "CC(C)C[C@H]1C(=O)N[C@@H](C(=O)N2CCC[C@H]2C(=O)N[C@H](C(=O)N[C@@H](C(=O)N[C@H](C(=O)N[C@H](C(=O)N[C@H](C(=O)N[C@H](C(=O)N[C@H](C(=O)N1)CCCN)C(C)C)CC3=CC=C(C=C3)O)CCC(=O)N)CC(=O)N)CC4=CC=CC=C4)CC5=CC=CC=C5)CC6=CC=CC=C6",
    73357: "CC(C)C[C@H]1C(=O)N[C@@H](C(=O)N2CCC[C@H]2C(=O)N[C@H](C(=O)N[C@H](C(=O)N[C@H](C(=O)N[C@@H](C(=O)N3CCC[C@H]3C(=O)N[C@H](C(=O)N[C@H](C(=O)N1)CCCN)C(C)C)CC4=CC=CC=C4)CC(C)C)CCCN)C(C)C)CC5=CC=CC=C5",
    21585658: "CCCCCCCCCC(=O)N[C@@H](CC1=CNC2=CC=CC=C21)C(=O)N[C@H](CC(=O)N)C(=O)N[C@@H](CC(=O)O)C(=O)N[C@H]3[C@H](OC(=O)[C@@H](NC(=O)[C@@H](NC(=O)[C@H](NC(=O)CNC(=O)[C@@H](NC(=O)[C@H](NC(=O)[C@@H](NC(=O)[C@@H](NC(=O)CNC3=O)CCCN)CC(=O)O)C)CC(=O)O)CO)[C@H](C)CC(=O)O)CC(=O)C4=CC=CC=C4N)C",
    14969: "C[C@H]1[C@H]([C@@](C[C@@H](O1)O[C@@H]2[C@H]([C@@H]([C@H](O[C@H]2OC3=C4C=C5C=C3OC6=C(C=C(C=C6)[C@H]([C@H](C(=O)N[C@H](C(=O)N[C@H]5C(=O)N[C@@H]7C8=CC(=C(C=C8)O)C9=C(C=C(C=C9O)O)[C@H](NC(=O)[C@H]([C@@H](C1=CC(=C(O4)C=C1)Cl)O)NC7=O)C(=O)O)CC(=O)N)NC(=O)[C@@H](CC(C)C)NC)O)Cl)CO)O)O)(C)N)O",
    9812534: "CC[C@H](C)[C@@H]1[C@H](CC(=O)O[C@H](C(=O)[C@@H](C(=O)N[C@H](C(=O)N2CCC[C@H]2C(=O)N([C@H](C(=O)O[C@@H]([C@@H](C(=O)N1)NC(=O)[C@@H](CC(C)C)N(C)C(=O)[C@@H]3CCCN3C(=O)C(=O)C)C)CC4=CC=C(C=C4)OC)C)CC(C)C)C)C(C)C)O",
    9855014: "CN1[C@H]2CSSC[C@@H](C(=O)N([C@H](C(=O)SC[C@H](C(=O)NCC1=O)NC(=O)C3=NC4=CC=CC=C4C=C3O)CSC)C)N(C(=O)CNC(=O)[C@@H](CSC(=O)[C@@H](N(C2=O)C)CSC)NC(=O)C5=NC6=CC=CC=C6C=C5O)C",
    34231: "C1[C@@H](C(=O)OC[C@@H](C(=O)OC[C@@H](C(=O)O1)NC(=O)C2=C(C(=CC=C2)O)O)NC(=O)C3=C(C(=CC=C3)O)O)NC(=O)C4=C(C(=CC=C4)O)O",
}


def test_multiple_peptide_input():
    result = process_input(
        """peptide, name, PubChemCID, features
    [D-Phe-L-Pro-L-Phe-D-Phe-L-Asn-L-Gln-L-Tyr-L-Val-L-Orn-L-Leu], Tyrocidine, 16129635, Standard
    [[D-Phe-L-Pro-L-Val-L-Orn-L-Leu]], Gramicidin S, 73357, Standard
    n-Dec-L-Trp-D-Asn-L-Asp-(L-Thr-Gly-L-Orn-L-Asp-D-Ala-L-Asp-Gly-D-Ser-L-3-Me-Glu-L-Kyn), Daptomycin, 21585658, Standard|Defined residues
    L-ureidoVal-L-Val-(L-dhLys-L-Val/DH-Mal), Syringolin A, 42601513, ureido|intramolecular|dhLys|DH-Mal
    Sal/L-Thz/L-Thd/di-Me-KR-Mal/L-Me-Thz, Yersiniabactin, 443589, Thz|Tzd
    D-N-Me-Leu-D-Bht-L-Asn-D-gvHpg-D-Hpg-L-Bht-L-Dpg, Vancomycin, 14969, Cross-linked
    3HQA-((D-Cys-Gly-L-N-Me-cl-Cys-L-S-Me-N-Me-Cys)), Thiocoraline A, 9855014, S-Me|N-Me|dimeric intramolecular|cross-linking
    [D-Ala-L-N-Me-Leu-L-N-Me-Leu-L-N-Me-Val-L-N-Me-Bmt-L-Abu-N-Me-Gly-L-N-Me-Leu-L-Val-L-N-Me-Leu-L-Ala], Cyclosporine, 5284373, D|N-methyl|dimeric head-to-tail|Bmt
    Pyr-L-Pro-D-N-Me-Leu-(L-Thr-isoSta-Hip-L-Leu-L-Pro-L-N-Me-O-Me-Tyr), Plitidepsin, 9812534, isostatine|hydroxy acid|O-Me
    DHB-(((L-Ser))), enterobactin, 34231, trimeric intramolecular
    """,
        """""",
        user_monomers,
    )
    for peptide in result["peptides"]:
        print (peptide)
        mol1 = Chem.MolFromSmiles(peptide["smiles"])
        mol2 = Chem.MolFromSmiles(pubchem[int(peptide["metadata"]["PubChemCID"])])
        assert Chem.MolToSmiles(mol1) == Chem.MolToSmiles(mol2)
