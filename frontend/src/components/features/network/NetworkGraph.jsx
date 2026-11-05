import { useEffect, useRef } from "react";
import { useCytoscape } from "./useCytoscape";
import styles from "./Network.module.css";
import useStore from "@/store";

const DEFAULT_EDGE_SETTINGS = {
  layout: "cose",
};

function currentField(s) {
  return s.method === "tanimoto"
    ? `tanimoto_r${s.tanimoto.mode}_${s.tanimoto.stereochemistry}`
    : `alignment_${s.monomer.mode}_${s.monomer.stereochemistry}_id`;
}

function buildElements(result, view) {
  const nodes = result.peptides.map((p) => ({
    data: { id: p.id, label: String(p.number), origin: p.origin },
  }));

  const edgeField = currentField(view);
  const minEdge =
    view.method === "tanimoto"
      ? view.tanimoto.cutoff
      : view.monomer.cutoff / 100;

  const edges = (result.edges || [])
    .map((e) => (e.data ? e.data : e))
    .filter((d) => typeof d[edgeField] === "number" && d[edgeField] >= minEdge)
    .map((d) => ({ data: { ...d, weight: d[edgeField] } }));

  return [...nodes, ...edges];
}

function defineLayout(s) {
  const opts = { name: s.layout, animate: true, animationDuration: 500 };
  if (s.layout === "cose")
    Object.assign(opts, { idealEdgeLength: 80, nodeRepulsion: 8000 });
  return opts;
}

const NETWORK_STYLE = [
  {
    selector: "node[label]",
    style: {
      label: "data(label)",
      shape: "ellipse",
      "background-color": "#38bdf8",
      "border-width": 1.5,
      "border-color": "rgba(8,12,20,0.8)",
      color: "#e2e8f0",
      "font-family": "IBM Plex Sans, system-ui",
      "font-size": 9,
      "font-weight": 500,
      "text-valign": "bottom",
      "text-margin-y": 4,
      "text-outline-color": "#080c14",
      "text-outline-width": 2,
      width: 22,
      height: 22,
      "transition-property":
        "background-color, border-color, opacity, width, height",
      "transition-duration": 200,
    },
  },
  {
    selector: 'node[origin = "predicted"]',
    style: { shape: "round-rectangle", "background-color": "#4ade80" },
  },
  {
    selector: "node[highlightColor]",
    style: { "background-color": "data(highlightColor)" },
  },
  {
    selector: "node:selected",
    style: {
      "background-color": "#FCDE04",
      "border-color": "#f59e0b",
      "border-width": 5,
      width: 28,
      height: 28,
    },
  },
  { selector: "node.hidden", style: { display: "none" } },
  {
    selector: "node.search-match-known",
    style: { "border-color": "#f59e0b", "border-width": 3.5 },
  },
  {
    selector: "node.search-match-predicted",
    style: { "border-color": "#f59e0b", "border-width": 3.5 },
  },
  {
    selector: "node.neighbour",
    style: { "border-color": "#FCDE04", "border-width": 1.5 },
  },
  {
    selector: "edge",
    style: {
      width: "mapData(weight, 0.3, 1, 0.5, 5)",
      "line-color": "rgba(56,189,248,0.35)",
      "curve-style": "haystack",
      "haystack-radius": 0.4,
      opacity: 0.7,
      "transition-property": "opacity, line-color",
      "transition-duration": 200,
    },
  },
  {
    selector: "edge:selected",
    style: { "line-color": "#FCDE04", "border-width": 3, width: 7, height: 4 },
  },
  { selector: "edge.neighbour", style: { "line-color": "#FCDE04" } },
  { selector: "edge.hidden", style: { display: "none" } },
];

export default function NetworkGraph({
  result,
  edgeSettings = DEFAULT_EDGE_SETTINGS,
}) {
  const view = useStore((s) => s.view);
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const { cytoscape, error } = useCytoscape();
  const setSelection = useStore((s) => s.setSelection);

  const setCy = useStore((s) => s.setCy);

  useEffect(() => {
    if (!cytoscape || !result || !containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements: buildElements(result, view),
      style: NETWORK_STYLE,
      layout: defineLayout(edgeSettings),
    });

    cyRef.current = cy;
    setCy(cy);

    // Selection
    const handleNodeTap = (evt) => {
      const node = evt.target;
      const neighbors = node.neighborhood("node");
      const edges = node.connectedEdges();

      cy.elements().removeClass("neighbour");
      neighbors.addClass("neighbour");
      edges.addClass("neighbour");

      const sortedEdges = edges
        .map((ele) => {
          const otherID =
            ele.source().id() === node.id()
              ? ele.target().id()
              : ele.source().id();
          return {
            edge_id: ele.id(),
            node_id: otherID,
            weight: ele.data("weight"),
          };
        })
        .sort((a, b) => b.weight - a.weight);

      setSelection({ element: "node" });
      setSelection({ selected: node.id() });
      setSelection({ nodeNeighbours: sortedEdges.map((n) => n.node_id) });
      setSelection({ edgeNeighbours: sortedEdges.map((n) => n.edge_id) });
      useStore.getState().openSelectionCards();
    };

    const handleEdgeTap = (evt) => {
      const edge = evt.target;
      const sourceNode = edge.source();
      const targetNode = edge.target();

      cy.elements().removeClass("neighbour");
      sourceNode.addClass("neighbour");
      targetNode.addClass("neighbour");

      setSelection({ element: "edge" });
      setSelection({ selected: edge.id() });
      setSelection({ nodeNeighbours: sourceNode.id() });
      setSelection({ edgeNeighbours: targetNode.id() });
      useStore.getState().openSelectionCards();
    };

    cy.on("tap", "node", handleNodeTap);
    cy.on("tap", "edge", handleEdgeTap);
    cy.on("tap", (e) => {
      if (e.target === cy) {
        cy.elements().removeClass("neighbour");
        setSelection({ element: null });
      }
    });

    // Drawing and resizing
    let disposed = false;
    let initialRaf = 0;
    let resizeRaf = 0;

    const safeFit = () => {
      if (disposed || cy.destroyed()) return;
      cy.resize();
      cy.fit(undefined, 40);
    };

    initialRaf = requestAnimationFrame(safeFit);

    const ro = new ResizeObserver(() => {
      cancelAnimationFrame(resizeRaf);
      resizeRaf = requestAnimationFrame(safeFit);
    });
    ro.observe(containerRef.current);

    return () => {
      disposed = true;
      cancelAnimationFrame(initialRaf);
      cancelAnimationFrame(resizeRaf);
      ro.disconnect();
      setCy(null);
      cy.destroy();
      cyRef.current = null;
    };
  }, [cytoscape, result, edgeSettings]);

  if (error) return <div>Failed to load network library: {String(error)}</div>;

  return <div className={styles.network} ref={containerRef} />;
}
