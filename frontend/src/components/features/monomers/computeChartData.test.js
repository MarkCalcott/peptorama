import { computeChartData } from "./computeChartData";
import { describe, it, expect } from "vitest";

const mono = (over = {}) => ({
  code: "X",
  base: "Xaa",
  exact: "Xaa",
  category: "",
  count: 1,
  stereochemistry: "L",
  known: "Inbuilt",
  ...over,
});

const opts = (over = {}) => ({
  groupBy: "base",
  splitBy: "none",
  inbuiltVisible: true,
  userdefinedVisible: true,
  unknownVisible: true,
  stereoVisible: { L: true, D: true, flat: true },
  ...over,
});

describe("computeChartData — pooled (splitBy none)", () => {
  it("sums counts per group", () => {
    const data = [
      mono({ base: "Leu", count: 3 }),
      mono({ base: "Leu", count: 4 }),
      mono({ base: "Val", count: 5 }),
    ];
    const out = computeChartData(data, opts());
    const byLabel = Object.fromEntries(
      out.labels.map((l, i) => [l, out.datasets[0].data[i]]),
    );
    expect(byLabel).toEqual({ Leu: 7, Val: 5 });
  });

  it("sorts groups by count descending", () => {
    const data = [
      mono({ base: "Small", count: 1 }),
      mono({ base: "Big", count: 9 }),
      mono({ base: "Mid", count: 4 }),
    ];
    const out = computeChartData(data, opts());
    expect(out.labels).toEqual(["Big", "Mid", "Small"]);
  });

  it("hides a status class when its visibility is off", () => {
    const data = [
      mono({ base: "Leu", known: "Inbuilt" }),
      mono({ base: "Unk", known: "Weird" }), // unknown: not Inbuilt/User-defined
    ];
    const out = computeChartData(data, opts({ unknownVisible: false }));
    expect(out.labels).toEqual(["Leu"]);
  });

  it("colours a group red if any member is unknown", () => {
    const data = [
      mono({ base: "Mix", known: "Inbuilt" }),
      mono({ base: "Mix", known: "Weird" }),
    ];
    const out = computeChartData(data, opts());
    expect(out.datasets[0].backgroundColor[0]).toBe("rgba(248,113,113,1)");
  });

  it("groups by category, falling back to Uncategorized", () => {
    const data = [
      mono({ base: "A", category: "Proteinogenic", count: 2 }),
      mono({ base: "B", category: "", count: 1 }),
    ];
    const out = computeChartData(data, opts({ groupBy: "category" }));
    expect(out.labels).toContain("Proteinogenic");
    expect(out.labels).toContain("Uncategorized");
  });
});

describe("computeChartData — stereo split", () => {
  it("produces one dataset per visible stereo class", () => {
    const data = [
      mono({ stereochemistry: "L" }),
      mono({ stereochemistry: "D" }),
    ];
    const out = computeChartData(data, opts({ splitBy: "stereochemistry" }));
    expect(out.datasets.map((d) => d.label)).toEqual(["L", "D", "Flat"]);
  });

  it("omits a dataset when that stereo class is toggled off", () => {
    const data = [mono({ stereochemistry: "L" })];
    const out = computeChartData(
      data,
      opts({
        splitBy: "stereochemistry",
        stereoVisible: { L: true, D: false, flat: false },
      }),
    );
    expect(out.datasets.map((d) => d.label)).toEqual(["L"]);
  });

  it("routes counts into the right stereo bucket", () => {
    const data = [
      mono({ base: "Leu", stereochemistry: "L", count: 3 }),
      mono({ base: "Leu", stereochemistry: "D", count: 2 }),
    ];
    const out = computeChartData(data, opts({ splitBy: "stereochemistry" }));
    const ds = Object.fromEntries(
      out.datasets.map((d) => [d.label, d.data[0]]),
    );
    expect(ds.L).toBe(3);
    expect(ds.D).toBe(2);
  });

  it("treats missing stereochemistry as flat", () => {
    const data = [mono({ base: "Leu", stereochemistry: undefined, count: 4 })];
    const out = computeChartData(data, opts({ splitBy: "stereochemistry" }));
    const flat = out.datasets.find((d) => d.label === "Flat");
    expect(flat.data[0]).toBe(4);
  });
});

describe("computeChartData — edge cases", () => {
  it("returns empty structure for no monomers", () => {
    expect(computeChartData([], opts())).toEqual({
      labels: [],
      datasets: expect.any(Array),
    });
  });
});
