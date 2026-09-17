import defaults from "./data/config.json";

export const SCHEMA = 1;

export const toNetworkFile = (data) => ({
  kind: "network",
  savedAt: new Date().toISOString(),
  data: data,
});

export const toInputFile = (input, settings) => ({
  schema: SCHEMA,
  kind: "input",
  savedAt: new Date().toISOString(),
  input: input,
  settings: settings,
});

const firstPresent = (available, order) => {
  console.log(order);
  return order.find((v) => available?.includes(v)) ?? null;
};

function createBroadestMonomerView(config) {
  if (config.methods?.includes("monomer")) {
    return {
      monomer: {
        mode: firstPresent(config.monomer.match, ["base", "exact"]),
        stereochemistry: firstPresent(config.monomer.stereochemistry, [
          "relaxed",
          "moderate",
          "strict",
        ]),
        cutoff: config.monomer.cutoff,
      },
    };
  }
  return null;
}

function createBroadestTanimotoView(config) {
  if (config.methods?.includes("tanimoto")) {
    return {
      tanimoto: {
        mode: firstPresent(config.tanimoto.radius, [2, 3, 4]),
        cutoff: config.tanimoto.cutoff,
      },
    };
  }
  return null;
}

const makeInput = () => ({
  known: "",
  predicted: "",
  monomers: null,
});

const makeOutput = () => ({
  peptides: [],
  edges: [],
  monomers: [],
  metadata: [],
  warnings: [],
  settings: [],
  schema: null,
});

const makeSettings = () => ({
  edge: {
    methods: ["monomer"], // can be monomer and/or tanimoto
    monomer: { match: ["base"], stereochemistry: ["relaxed"], cutoff: 40 }, // cutoff can be 30 to 100
    tanimoto: { radius: [2], cutoff: 0.45 }, // radius can be 2, 3 or 4; cutoff can be 0.3 to 1
  },
  processing: {
    length: { min: 3, max: 40 },
    split: "split",
  }
});

const makeData = () => ({
  input: makeInput(),
  output: makeOutput(),
  settings: makeSettings(),
});

const resolve = (settings, path) => {
  const keys = path.split(".");
  let node = settings;
  for (let i = 0; i < keys.length - 1; i++) node = node[keys[i]];
  return [node, keys.at(-1)];
};

export const createJobSlice = (set, get) => ({
  config: defaults,
  status: "idle", // idle | uploading | processing | ready | error
  data: makeData(defaults),

  // Setting input
  updateInput: (patch) =>
    set((s) => {
      Object.assign(s.data.input, patch);
    }),
  setInput: (key, value) => get().updateInput({ [key]: value }),
  setMonomers: (monomers) => get().updateInput({ monomers }),

  setSetting: (path, value) =>
    set((s) => {
      const [node, key] = resolve(s.data.settings, path);
      node[key] = value;
    }),

  selectSetting: (path, value) =>
    set((s) => {
      const [node, key] = resolve(s.data.settings, path);
      const arr = node[key];
      const i = arr.indexOf(value);
      if (i === -1) {
        arr.push(value);
        arr.sort((a, b) => (a > b ? 1 : -1));
      } else {
        if (arr.length > 1) arr.splice(i, 1);
        else alert("Cannot unselect. At least one needs to be selected.");
      }
    }),

  // Update output
  peptidesById: null,
  edgesById: null,
  updateOutput: (patch) =>
    set((s) => {
      Object.assign(s.data.output, patch);
    }),

  setOutput: (result) => {
    set((s) => ({
      data: {
        ...s.data,
        output: { ...s.data.output, ...result },
      },
      peptidesById: Object.fromEntries(
        (result.peptides ?? []).map((p) => [p.id, p]),
      ),
      edgesById: Object.fromEntries((result.edges ?? []).map((p) => [p.id, p])),
    }));
  },

  // Run ID to cancel processes when others start
  runID: 0,
  isCurrentRun: (id) => get().runID === id,
  startRun: () => {
    const newID = get().runID + 1;
    set({ runID: newID });
    return newID;
  },

  // Resets input and network
  resetJob: () =>
    set((s) => ({ data: makeData(get().config), runID: s.runID + 1 })),

  // Info panel updates
  info: { id: "welcome", params: {} },
  setInfo: (id, params = {}) => set({ info: { id, params } }),

  // Save a job
  saveNetwork: () => {
    const blob = new Blob(
      [JSON.stringify(toNetworkFile(get().data.output), null, 2)],
      {
        type: "application/json",
      },
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `network-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
  saveInput: () => {
    const blob = new Blob(
      [
        JSON.stringify(
          toInputFile(get().data.input, get().data.settings),
          null,
          2,
        ),
      ],
      {
        type: "application/json",
      },
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `input-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },

  // Load saved job
  loadFromFile: async (file) => {
    try {
      const input = JSON.parse(await file.text());
      if (!["network", "input"].includes(input.kind))
        throw new Error(`Unknown kind: ${input.kind}`);

      if (input.kind === "network") {
        if (!input.data) throw new Error("Missing input data");
        if (input.data.schema !== SCHEMA)
          throw new Error(`Unknown version: ${input.data.schema}`);
        const result = get().loadNetwork(input.data);
        if (!result.ok) throw new Error(result.error);
        return { ok: true };
      }

      if (input.kind === "input") {
        if (!input.input) throw new Error("Missing input data");
        if (!input.settings) throw new Error("Missing settings data");
        if (input.schema !== SCHEMA)
          throw new Error(`Unknown version: ${input.data.schema}`);

        set((s) => ({
          data: { ...s.data, input: input.input, settings: input.settings },
        }));
        console.log(input.input);
        return { ok: true };
      }

      return { ok: false, error: `Could not determine data type` };
    } catch (err) {
      set({ output: makeOutput(), settings: makeSettings() });
      return { ok: false, error: `Could not load file: ${err.message}` };
    }
  },

  // loadNetwork
  loadNetwork: (payload) => {
    if (!payload) {
      return { ok: false, error: "No network data" };
    }

    try {
      get().setMonomers(payload.monomers);
      get().setOutput(payload);

      const tanimoto = createBroadestTanimotoView(payload.settings.edge);
      const monomer = createBroadestMonomerView(payload.settings.edge);

      // order matters: monomer last so it wins as the current view when present
      if (tanimoto) {
        get().setView(tanimoto);
        get().setView({ current: "tanimoto" });
      }
      if (monomer) {
        get().setView(monomer);
        get().setView({ current: "monomer" });
      }

      get().toggleCard("upload", false, false);
      get().toggleCard("network", false, true);

      set({ loadError: null });
      return { ok: true };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },
});
