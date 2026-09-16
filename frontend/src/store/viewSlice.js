const merge = (target, patch) => {
  for (const [k, v] of Object.entries(patch)) {
    if (v?.constructor === Object && target[k]?.constructor === Object) {
      merge(target[k], v);
    } else {
      target[k] = v;
    }
  }
};

export const createViewSlice = (set) => ({
  view: {
    current: null,
    monomer: {
      mode: null,
      stereochemistry: null,
      cutoff: null,
    },
    tanimoto: {
      mode: null,
      cutoff: null,
    },
  },
  selection: {
    element: null,
    selected: null,
    nodeNeighbours: null,
    edgeNeighbours: null,
  },
  cy: null,
  setCy: (cy) => set({ cy }),
  setView: (patch) => {
    set((s) => {
      merge(s.view, patch);
    });
  },
  setSelection: (patch) =>
    set((s) => {
      Object.assign(s.selection, patch);
    }),
});
