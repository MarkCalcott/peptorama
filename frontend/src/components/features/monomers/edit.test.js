import { describe, it, expect } from "vitest";
import { mergeEditsIntoData, mergeEditsIntoList } from "./edit";

const data = {
  Leu: { code: "Leu", name: "Leucine", count: 7, known: "Inbuilt" },
  Val: { code: "Val", name: "Valine", count: 5, known: "Inbuilt" },
};

describe("mergeEditsIntoData", () => {
  it("applies an edit to the matching row only", () => {
    const out = mergeEditsIntoData(data, { Leu: { name: "L-Leucine" } });
    expect(out.Leu.name).toBe("L-Leucine");
    expect(out.Val.name).toBe("Valine");
  });

  it("preserves unedited fields on an edited row", () => {
    const out = mergeEditsIntoData(data, { Leu: { name: "X" } });
    expect(out.Leu.count).toBe(7);
    expect(out.Leu.known).toBe("Inbuilt");
  });

  it("keeps the original key when the code itself is edited", () => {
    const out = mergeEditsIntoData(data, { Leu: { code: "Leu-OMe" } });
    expect(Object.keys(out)).toEqual(["Leu", "Val"]);
    expect(out.Leu.code).toBe("Leu-OMe");
  });

  it("is a no-op with no edits", () => {
    expect(mergeEditsIntoData(data, {})).toEqual(data);
  });

  it("does not mutate the input", () => {
    mergeEditsIntoData(data, { Leu: { name: "X" } });
    expect(data.Leu.name).toBe("Leucine");
  });

  it("handles null data", () => {
    expect(mergeEditsIntoData(null, {})).toEqual({});
  });
});

describe("mergeEditsIntoList", () => {
  it("overlays edits and leaves other rows untouched", () => {
    const list = Object.values(data);
    const out = mergeEditsIntoList(list, { Val: { name: "D-Valine" } });
    expect(out.find((m) => m.code === "Val").name).toBe("D-Valine");
    expect(out.find((m) => m.code === "Leu").name).toBe("Leucine");
  });

  it("keeps list order", () => {
    const list = Object.values(data);
    const out = mergeEditsIntoList(list, { Leu: { name: "X" } });
    expect(out.map((m) => m.code)).toEqual(["Leu", "Val"]);
  });
});
