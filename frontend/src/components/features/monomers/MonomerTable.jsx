import { useState, useMemo, useRef, useEffect } from "react";
import { validateMonomer } from "./monomerValidation";
import { mergeEditsIntoData, mergeEditsIntoList } from "./edit";

import Button from "@/components/ui/Button";
import styles from "./Monomers.module.css";

const isInbuilt = (m) => m.known === "Inbuilt";
const isUserDefined = (m) => m.known === "User-defined";
const isUnknown = (m) => !isInbuilt(m) && !isUserDefined(m);

export default function MonomerTable({ data, onApply }) {
  const [tableVisible, setTableVisible] = useState(true);

  // Table controls
  const [searchText, setSearchText] = useState("");
  const [statusFilterVal, setStatusFilterVal] = useState("all");
  const [sortCol, setSortCol] = useState("base");
  const [sortDir, setSortDir] = useState(1);
  const [orderedCodes, setOrderedCodes] = useState(null);

  const [edits, setEdits] = useState({});
  const [editingCode, setEditingCode] = useState(null);
  const [prevData, setPrevData] = useState(data);

  if (data !== prevData) {
    setPrevData(data);
    setOrderedCodes(null);
    setEdits({});
  }

  const monomers = useMemo(() => Object.values(data ?? {}), [data]);
  const mergedMonomers = useMemo(
    () => mergeEditsIntoList(monomers, edits),
    [monomers, edits],
  );

  // Sorting function for columns
  function compareBy(col, dir) {
    return (a, b) => {
      if (col === "count") return ((a.count || 0) - (b.count || 0)) * dir;
      if (col === "status") {
        const rank = (m) => (isInbuilt(m) ? 0 : isUserDefined(m) ? 1 : 2);
        return (rank(a) - rank(b)) * dir;
      }
      const va = a[col] ? String(a[col]) : "";
      const vb = b[col] ? String(b[col]) : "";
      return va.localeCompare(vb) * dir;
    };
  }

  // Initial sort
  if (orderedCodes === null && monomers.length) {
    setOrderedCodes(
      [...monomers].sort(compareBy(sortCol, sortDir)).map((m) => m.code),
    );
  }

  const rows = useMemo(() => {
    let list = mergedMonomers;
    if (searchText) {
      const q = searchText.toLowerCase();
      list = list.filter(
        (m) =>
          m.code.toLowerCase().includes(q) ||
          (m.name && m.name.toLowerCase().includes(q)) ||
          (m.category && m.category.toLowerCase().includes(q)) ||
          (m.base && m.base.toLowerCase().includes(q)),
      );
    }
    if (statusFilterVal === "Inbuilt") list = list.filter(isInbuilt);
    else if (statusFilterVal === "User-defined")
      list = list.filter(isUserDefined);
    else if (statusFilterVal === "Unknown") list = list.filter(isUnknown);

    if (orderedCodes) {
      const pos = new Map(orderedCodes.map((c, i) => [c, i]));
      list = [...list].sort(
        (a, b) => (pos.get(a.code) ?? Infinity) - (pos.get(b.code) ?? Infinity),
      );
    }
    return list;
  }, [mergedMonomers, searchText, statusFilterVal, orderedCodes]);

  const editing = editingCode
    ? (mergedMonomers.find((m) => m.code === editingCode) ?? null)
    : null;

  function stageEdit(draft) {
    setEdits((prev) => ({ ...prev, [editingCode]: draft }));
    setEditingCode(null);
  }

  function revertEdit(code) {
    setEdits((prev) => {
      const next = { ...prev };
      delete next[code];
      return next;
    });
  }

  function applyAll() {
    onApply(mergeEditsIntoData(data, edits));
    setEdits({});
    alert(
      "Changes applied to upload section. Build a network to incorporate new monomers.",
    );
  }

  function download(filename, content, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  function exportCsv() {
    const hdr = [
      "code",
      "name",
      "base",
      "exact",
      "stereochemistry",
      "category",
      "smiles",
    ];
    const csvRows = monomers.map((m) =>
      hdr
        .map((h) => `"${(m[h] ?? "").toString().replace(/"/g, '""')}"`)
        .join(","),
    );
    download(
      "monomer_data.csv",
      [hdr.join(","), ...csvRows].join("\n"),
      "text/csv",
    );
  }

  function toggleSort(col) {
    if (sortCol === col) setSortDir((d) => -d);
    else {
      setSortCol(col);
      setSortDir(1);
    }
    setOrderedCodes(
      [...mergedMonomers].sort(compareBy(col, sortDir)).map((m) => m.code),
    );
  }
  const sortArrow = (col) =>
    sortCol === col ? (sortDir === 1 ? "▲" : "▼") : "";

  return (
    <>
      {/* Table controls */}
      <div className="flexRow">
        {tableVisible && (
          <div className="flexRowMedium" style={{ flexWrap: "wrap" }}>
            <div className="flexRowSmall">
              <input
                className="input-area singleLine"
                placeholder="Search monomers…"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
              />
              <select
                className="filterSelect"
                value={statusFilterVal}
                onChange={(e) => setStatusFilterVal(e.target.value)}
              >
                <option value="all">All</option>
                <option value="Inbuilt">Inbuilt</option>
                <option value="User-defined">User-defined</option>
                <option value="Unknown">Unknown</option>
              </select>
            </div>
            <div className="flexRowSmall">
              <Button onClick={exportCsv}>↓ Export CSV</Button>
              {onApply && (
                <Button variant="primary" onClick={applyAll}>
                  Apply changes
                </Button>
              )}
            </div>
          </div>
        )}
        <div className="alignRight">
          <Button onClick={() => setTableVisible((v) => !v)}>
            {tableVisible ? "Hide table" : "Show table"}
          </Button>
        </div>
      </div>

      {/* Table */}
      {tableVisible && (
        <table className="monomer-table">
          <thead>
            <tr>
              {[
                "code",
                "name",
                "base",
                "exact",
                "stereochemistry",
                "category",
                "count",
                "status",
              ].map((col) => (
                <th
                  key={col}
                  onClick={() => toggleSort(col)}
                  className={styles.sortRow}
                >
                  {col} <span className="sort-arrow">{sortArrow(col)}</span>
                </th>
              ))}
              <th>draft changes</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((m) => {
              const colorClass = isInbuilt(m)
                ? styles.swatchCyan
                : isUserDefined(m)
                  ? styles.swatchAmber
                  : styles.swatchRed;
              const dash = <span>—</span>;
              const isDirty = Boolean(edits[m.code]);
              return (
                <tr
                  key={m.code}
                  className={isDirty ? styles.dirtyRow : undefined}
                >
                  <td>{m.code}</td>
                  <td>{m.name || dash}</td>
                  <td>{m.base || dash}</td>
                  <td>{m.exact || dash}</td>
                  <td>{m.stereochemistry}</td>
                  <td>{m.category || dash}</td>
                  <td>{m.count}</td>
                  <td>
                    <span className={`${styles.knownBadge} ${colorClass}`}>
                      {m.known}
                    </span>
                  </td>
                  <td>
                    <div className="flexRowSmall">
                      <Button
                        onClick={() => setEditingCode(m.code)}
                        size="small"
                      >
                        Edit
                      </Button>
                      {isDirty && (
                        <Button onClick={() => revertEdit(m.code)} size="small">
                          Clear
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      <EditMonomerDialog
        key={editingCode ?? "none"}
        monomer={editing}
        onStage={stageEdit}
        onClose={() => setEditingCode(null)}
      />
    </>
  );
}

function EditMonomerDialog({ monomer, onStage, onClose }) {
  const stereo = ["L", "D", "flat"];
  const ref = useRef(null);
  const [draft, setDraft] = useState(monomer);

  useEffect(() => {
    const el = ref.current;
    if (el && monomer && !el.open) el.showModal();
  }, [monomer]);

  if (!monomer || !draft) return <dialog ref={ref} onClose={onClose} />;

  const errors = validateMonomer(draft);
  const hasErrors = Object.keys(errors).length > 0;

  const set = (k) => (e) => setDraft((d) => ({ ...d, [k]: e.target.value }));

  const save = () => {
    if (hasErrors || !draft.code.trim()) {
      alert("Invalid input: fix errors before saving");
      return;
    }
    onStage({
      ...draft,
      name: (draft.name ?? "").trim(),
      known: "User-defined",
    });
  };

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => e.target === ref.current && onClose()}
      className={styles.modal}
    >
      <div className={styles.modalHeader}>
        <h3>Edit: {draft.code}</h3>
      </div>

      <div className={styles.modalLabel}>
        <label>
          <div>Name</div>
          <input
            className={`input-area singleLine wide ${errors.name ? "input-error" : ""}`}
            value={draft.name ?? ""}
            onChange={set("name")}
            placeholder="Unnamed"
          />
        </label>
        {errors.name && <p className="info">{errors.name}</p>}
      </div>

      <div className={styles.modalLabel}>
        <label>
          <div>Base</div>
          <input
            className={`input-area singleLine wide ${errors.base ? "input-error" : ""}`}
            value={draft.base ?? ""}
            onChange={set("base")}
            placeholder="Undetermined"
          />
        </label>
        {errors.base && <p className="info">{errors.base}</p>}
      </div>

      <div className={styles.modalLabel}>
        <label>
          <div>Exact</div>
          <input
            className={`input-area singleLine wide ${errors.exact ? "input-error" : ""}`}
            value={draft.exact ?? ""}
            onChange={set("exact")}
            placeholder="Undetermined"
          />
        </label>
        {errors.exact && <p className="info">{errors.exact}</p>}
      </div>

      <div className={styles.modalLabel}>
        <label>
          <div>Category</div>
          <input
            className={`input-area singleLine wide ${errors.category ? "input-error" : ""}`}
            value={draft.category ?? ""}
            onChange={set("category")}
            placeholder="Undetermined"
          />
        </label>
        {errors.category && <p className="info">{errors.category}</p>}
      </div>

      <div className={styles.modalLabel}>
        <label>
          <div>Stereochemistry</div>

          <select
            className="filterSelect"
            value={draft.stereochemistry ?? ""}
            onChange={set("stereochemistry")}
          >
            {stereo.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
      </div>

      <div className={styles.modalLabel}>
        <label>
          <div>SMILES</div>
          <input
            className={`input-area singleLine wide ${errors.smiles ? "input-error" : ""}`}
            value={draft.smiles ?? ""}
            onChange={set("smiles")}
            placeholder="[*:1]N[C@H](C)C(=O)[*:2]"
          />
        </label>
        {errors.smiles && <p className="info">{errors.smiles}</p>}
      </div>

      <div className="buttonArea">
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={save}>Save</Button>
      </div>
    </dialog>
  );
}
