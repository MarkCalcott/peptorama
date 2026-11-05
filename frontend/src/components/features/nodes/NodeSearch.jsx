import { useState, useEffect, useMemo } from "react";
import styles from "./Node.module.css";
import useStore from "@/store";

export default function NodeSearch({ type }) {
  const cy = useStore((s) => s.cy);
  const peptidesById = useStore((s) => s.peptidesById);

  const known_order = useStore((s) => s.data.output.metadata.known_order);
  const predicted_order = useStore(
    (s) => s.data.output.metadata.predicted_order,
  );
  const metadataValues = type === "known" ? known_order : predicted_order;

  const [searchValue, setSearchValue] = useState("number");
  const [searchTarget, setSearchTarget] = useState("data");
  const [query, setQuery] = useState("");

  const updateSearchInput = (value, target) => {
    setSearchValue(value);
    setSearchTarget(target);
    setQuery("");
  };

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q || !searchValue) return [];

    const found = Object.values(peptidesById)
      .filter((p) => p.origin === type)
      .map((p) => ({
        peptide: p,
        value:
          searchTarget === "data" ? p[searchValue] : p.metadata?.[searchValue],
      }))
      .filter(
        ({ value }) =>
          value != null &&
          value !== "" &&
          String(value).toLowerCase().includes(q),
      );

    found.sort((a, b) => (a.peptide.number ?? 0) - (b.peptide.number ?? 0));
    return found;
  }, [query, searchValue, searchTarget, peptidesById, type]);

  useEffect(() => {
    if (!cy || cy.destroyed()) return;
    cy.nodes().removeClass(`search-match-${type}`);

    const ids = matches.map((m) => m.peptide.id);
    const owned = cy.collection(ids.map((id) => cy.getElementById(id)));
    owned.addClass(`search-match-${type}`);

    return () => {
      if (!cy.destroyed()) owned.removeClass(`search-match-${type}`);
    };
  }, [cy, matches, type]);

  const focusNode = (id) => {
    if (!cy || cy.destroyed()) return;
    cy.elements().unselect();
    const node = cy.getElementById(id);
    if (!node.length) return;

    node.select();
    node.emit("tap");

    cy.animate(
      { center: { eles: node }, zoom: Math.max(cy.zoom(), 1.2) },
      { duration: 250 },
    );
  };

  return (
    <>
      <h4>Search</h4>

      <select
        className="filterSelect"
        id="highlightSelect"
        style={{ width: "100%" }}
        onChange={(e) => {
          const opt = e.target.selectedOptions[0];
          updateSearchInput(opt.value, opt.dataset.target);
        }}
      >
        <option value="number" data-target="data">
          Number
        </option>
        <option value="name" data-target="data">
          Name
        </option>
        {metadataValues.map((value) => (
          <option key={value} value={value} data-target="metadata">
            {value}
          </option>
        ))}
      </select>
      <input
        type="text"
        value={query}
        className="input-area singleLine"
        placeholder={`Enter peptide ${searchValue}…`}
        style={{ width: "100%" }}
        onChange={(e) => setQuery(e.target.value)}
      />
      {query.trim() && (
        <div className="flexRow">
          {matches.length === 0
            ? "No matches"
            : `${matches.length} match${matches.length === 1 ? "" : "es"}`}
        </div>
      )}
      <div className={styles.resultsList}>
        {matches.map(({ peptide, value }) => {
          const text =
            searchValue.key === "name"
              ? peptide.name
              : `${peptide.name}: ${value}`;
          return (
            <div
              className={styles.searchResult}
              key={peptide.id}
              onClick={() => focusNode(peptide.id)}
            >
              <span title={text}>{text}</span>
            </div>
          );
        })}
      </div>
    </>
  );
}
