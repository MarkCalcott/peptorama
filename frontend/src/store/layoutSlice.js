export const createLayoutSlice = (set) => ({
  panels: {
    left: {
      info: true,
      nodes: false,
      edges: false,
    },
    centre: {
      upload: true,
      network: false,
    },
    right: {
      alignment: false,
      selection: false,
      monomers: false,
      metadata: false,
    },
  },

  toggleCard: (cardId, toggle = true, nonToggleValue = false) =>
    set((s) => {
      for (const panel in s.panels) {
        if (cardId in s.panels[panel])
          if (toggle) {
            s.panels[panel][cardId] = !s.panels[panel][cardId];
          } else {
            s.panels[panel][cardId] = nonToggleValue;
          }
      }
    }),

  openSelectionCards: () =>
    set((s) => {
      const { right } = s.panels;
      if (!right.alignment && !right.selection) {
        right.alignment = true;
        right.selection = true;
      }
    }),
});
