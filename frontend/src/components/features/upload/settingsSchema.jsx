export const EDGE_SCHEMA = [
  {
    legend: "Comparison method(s)",
    fields: [
      {
        kind: "select",
        help: "How peptides are compared to create edges",
        path: "edge.methods",
        options: [
          {
            value: "monomer",
            label: "Monomer",
            tip: "Compares peptides residue-by-residue. Use when monomer identity matters",
          },
          {
            value: "tanimoto",
            label: "Tanimoto",
            tip: "Chemical similarity with Tanimoto distance using Morgan fingerprints",
          },
        ],
      },
    ],
  },
  {
    legend: "Monomer alignment",
    show: (s) => s.edge.methods.includes("monomer"),
    fields: [
      {
        kind: "select",
        help: "Compare just the base monomer or consider modifications",
        path: "edge.monomer.match",
        options: [
          {
            value: "base",
            label: "Base",
            tip: "Ignore modifications: Orn = OHOrn = N-Me-Orn. Differences in side-chain modifications collapse to the same residue.",
          },
          {
            value: "exact",
            label: "Exact",
            tip: "Distinguish modifications: Ala ≠ N-Me-Ala. Each modification is its own monomer.",
          },
        ],
      },
      {
        kind: "select",
        help: "The level of stereochemistry taken into consideration",
        path: "edge.monomer.stereochemistry",
        options: [
          {
            value: "relaxed",
            label: "Relaxed",
            tip: "Ignore: L-Ala = D-Ala",
          },
          {
            value: "moderate",
            label: "Moderate",
            tip: "Include when available: L = L or flat and D = D or flat, but L ≠ D",
          },
          {
            value: "strict",
            label: "Strict",
            tip: "Use all: L ≠ D ≠ flat",
          },
        ],
      },
      {
        kind: "slider",
        path: "edge.monomer.cutoff",
        label: "Minimum monomer sequence identity for edge",
        unit: "%",
        min: 30,
        max: 100,
        step: 1,
      },
    ],
  },
  {
    legend: "Tanimoto similarity",
    show: (s) => s.edge.methods.includes("tanimoto"),
    fields: [
      {
        kind: "select",
        help: "Select radius (in bonds) for generating fingerprints",
        path: "edge.tanimoto.radius",
        options: [
          {
            value: 2,
            label: "2 atoms",
            tip: "Considers atoms within 2 bonds of each center. Best for detecting shared functional groups and immediate chemical environments.",
          },
          {
            value: 3,
            label: "3 atoms",
            tip: "Considers atoms within 3 bonds of each center.",
          },
          {
            value: 4,
            label: "4 atoms",
            tip: "Considers atoms within 4 bonds of each center. Comparing overall peptide backbone or larger motifs, but less sensitive to small local differences.",
          },
        ],
      },
      {
        kind: "slider",
        path: "edge.tanimoto.cutoff",
        label: "Minimum Tanimoto coefficient for edge.",
        unit: "",
        min: 0.3,
        max: 1,
        step: 0.01,
      },
    ],
  },
];

export const PREDICTED_FILTERING_SCHEMA = [
  {
    legend: "Enable filtering",
    fields: [
      {
        kind: "toggle",
        path: "filtering.filter",
        options: [
          {
            value: true,
            label: "Use filtering",
            tip: "Only keep peptides with a minimum similarity",
          },
          {
            value: false,
            label: "No filtering",
            tip: "Keep all predicted peptides",
          },
        ],
      },
    ],
  },
  {
    legend: "Monomer alignment",
    show: (s) => {
      return s.edge.methods.includes("monomer") && s.filtering.filter;
    },
    fields: [
      {
        kind: "slider",
        path: "filtering.monomer.cutoff",
        label: "Minimum monomer sequence identity to keep",
        unit: "%",
        min: 30,
        max: 100,
        step: 1,
      },
    ],
  },
  {
    legend: "Tanimoto similarity",
    show: (s) => {
      return s.edge.methods.includes("tanimoto") && s.filtering.filter;
    },
    fields: [
      {
        kind: "slider",
        path: "filtering.tanimoto.cutoff",
        label: "Minimum Tanimoto similarity to to keep",
        unit: "",
        min: 0.3,
        max: 1,
        step: 0.01,
      },
    ],
  },
];

export const PREDICTED_PROCESSING_SCHEMA = [
  {
    legend: "Peptide length",
    fields: [
      {
        kind: "range",
        id: "processing.length",
        help: "Minimum and maximum number of monomers for extracted peptides. Peptides outside this range are dropped.",
        minPath: "processing.length.min",
        minLimit: 3,
        maxPath: "processing.length.max",
        maxLimit: 50,
        step: 1,
      },
    ],
  },
  {
    legend: "Split on thioesterase domain",
    fields: [
      {
        kind: "toggle",
        help: "Split peptides based on internal Te-domains within a BGC (Split candidates for peptide 1 are labeled 1a, 1b … ).",
        path: "processing.split",
        options: [
          {
            value: "split",
            label: "Split at Te-domain",
            tip: "Separates predicted peptides into two when a biosynthetic pathway has an internal thioesterase domain. The original prediction is discarded when split.",
          },
          {
            value: "splitAndKeep",
            label: "Split and keep",
            tip: "Same as split but also keep the original prediction",
          },
          {
            value: "keep",
            label: "No split",
            tip: "Keep the original prediction",
          },
        ],
      },
    ],
  },
];
