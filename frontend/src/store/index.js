import { create } from "zustand";
import { createLayoutSlice } from "./layoutSlice";
import { createJobSlice } from "./jobSlice";
import { createViewSlice } from "./viewSlice";
import { immer } from "zustand/middleware/immer";

function combineSlices(...slices) {
  return (set, get, api) => {
    const merged = {};
    const seen = new Set();
    for (const slice of slices) {
      const part = slice(set, get, api);
      for (const key of Object.keys(part)) {
        if (seen.has(key))
          throw new Error(`Store slice key collision: "${key}"`);
        seen.add(key);
      }
      Object.assign(merged, part);
    }
    return merged;
  };
}

const useStore = create(
  immer(combineSlices(createLayoutSlice, createJobSlice, createViewSlice)),
);

export default useStore;
