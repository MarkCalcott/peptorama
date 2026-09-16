import { describe, it, expect } from "vitest";
import { validateMonomer } from "./monomerValidation";

describe("validateMonomer", () => {
  it("accepts a clean monomer", () => {
    const errors = validateMonomer({
      code: "Leu",
      name: "Leucine",
      base: "Leu",
    });
    expect(errors).toEqual({});
  });

  it("requires a code", () => {
    expect(validateMonomer({ code: "" }).code).toBe("Code is required");
    expect(validateMonomer({ code: "   " }).code).toBe("Code is required");
  });

  it("rejects disallowed characters in text fields", () => {
    expect(validateMonomer({ code: "Leu", name: "Leu<cine" })).toHaveProperty(
      "name",
    );
  });

  it("rejects a hyphen in base", () => {
    expect(validateMonomer({ code: "Leu", base: "N-Me-Gly" })).toHaveProperty(
      "base",
    );
  });

  it("allows valid SMILES punctuation", () => {
    const smiles = "[*:1]N[C@H](C)C(=O)[*:2]";
    expect(validateMonomer({ code: "Ala", smiles })).toEqual({});
  });

  it("allows # and % in SMILES", () => {
    expect(validateMonomer({ code: "X", smiles: "C#N" })).toEqual({});
    expect(validateMonomer({ code: "X", smiles: "C%10CCCCC%10" })).toEqual({});
  });

  it("treats blank optional fields as valid", () => {
    expect(validateMonomer({ code: "Leu", name: "", smiles: "" })).toEqual({});
  });

  it("does not throw on null", () => {
    expect(() => validateMonomer(null)).not.toThrow();
  });
});
