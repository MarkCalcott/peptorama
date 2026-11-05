import { useEffect, useState } from "react";

let cytoscapePromise = null;

function loadCytoscape() {
  if (!cytoscapePromise) {
    cytoscapePromise = import("cytoscape").then((m) => m.default ?? m);
  }
  return cytoscapePromise;
}

export function useCytoscape() {
  const [cytoscape, setCytoscape] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    loadCytoscape()
      .then((C) => active && setCytoscape(() => C))
      .catch((e) => active && setError(e));
    return () => {
      active = false;
    };
  }, []);

  return { cytoscape, error };
}
