import { useState, useMemo } from "react";
import Card from "@/components/ui/Card";
import useStore from "@/store";

import Button from "@/components/ui/Button";
import styles from "./alignment.module.css";

function getAlignmentInfo(edgeId, peptideIdA, peptideIdB) {
  const monomersA = useStore.getState().peptidesById[peptideIdA];
  const monomersB = useStore.getState().peptidesById[peptideIdB];
  const alignmentMode = useStore.getState().view.monomer.mode;
  const alignmentStereochemistry =
    useStore.getState().view.monomer.stereochemistry;

  const alignmentKey = alignmentMode
    ? `alignment_${alignmentMode}_${alignmentStereochemistry}`
    : null;

  const alignment =
    useStore.getState().edgesById[edgeId][alignmentKey + "_align"];

  if (!alignment) {
    const tanimotoKey = `tanimoto_r${useStore.getState().view.tanimoto.mode}`;
    const similarity = useStore.getState().edgesById[edgeId][tanimotoKey];
    return [null, monomersA, monomersB, similarity];
  }

  const identity = useStore.getState().edgesById[edgeId][alignmentKey + "_id"];

  return [alignment, monomersA, monomersB, identity];
}

function renderAlignment(
  code,
  peptideA,
  peptideB,
  identity,
  type,
  compact = false,
) {
  // Walk the code with two pointers, building alignment columns.

  const KIND_STYLES = {
    match: { aa1: styles.alnMatch, aa2: styles.alnMatch, symbol: "|" },
    mismatch: { aa1: styles.alnMismatch, aa2: styles.alnMismatch, symbol: "·" },
    gapA: { aa1: styles.alnGap, aa2: styles.alnSingleResidue, symbol: "-" },
    gapB: { aa1: styles.alnSingleResidue, aa2: styles.alnGap, symbol: "-" },
  };

  if (!code)
    return (
      <div className={styles.alignmentRow}>
        {type === "edge" && (
          <>
            <h5>{peptideA.number}</h5>
            <div className={styles.tanimoto}>
              {peptideA.monomers.map((monomer, idx) => {
                return (
                  <div
                    className={`${styles.alnCell} ${styles.alnMatch}`}
                    key={idx}
                  >
                    {monomer}
                  </div>
                );
              })}
            </div>
            <hr />
          </>
        )}
        <div className={styles.rowHeader}>
          {peptideB.origin === "known" ? (
            <div className={styles.known}></div>
          ) : (
            <div className={styles.predicted}></div>
          )}

          <h5>{peptideB.number}</h5>
          <div className={styles.tanimoto}>
            {peptideB.monomers.map((monomer, idx) => {
              return (
                <div
                  className={`${styles.alnCell} ${styles.alnMatch}`}
                  key={idx}
                >
                  {monomer}
                </div>
              );
            })}
          </div>
          <div>Similarity: {identity}</div>
        </div>
      </div>
    );

  const reversed = peptideA.number > peptideB.number;
  let monomersA = peptideA.monomers;
  let monomersB = peptideB.monomers;
  if (reversed) {
    monomersA = peptideB.monomers;
    monomersB = peptideA.monomers;
  }

  let i = 0,
    j = 0;
  const columns = [];

  const SWAP_KIND = { gapA: "gapB", gapB: "gapA" };
  const reversal = (col) =>
    columns.push(
      reversed
        ? { a: col.b, b: col.a, kind: SWAP_KIND[col.kind] ?? col.kind }
        : col,
    );

  for (const pos of code) {
    if (pos === "=" || pos === "≠") {
      reversal({
        a: monomersA[i],
        b: monomersB[j],
        kind: pos === "=" ? "match" : "mismatch",
      });
      i++;
      j++;
    } else if (pos === "1") {
      reversal({
        a: monomersA[i],
        b: null,
        kind: "gapB",
      });
      i++;
    } else if (pos === "2") {
      reversal({
        b: monomersB[j],
        a: null,
        kind: "gapA",
      });
      j++;
    }
  }

  return (
    <>
      <div className="pairwiseAlignment">
        {type === "node" && !compact && (
          <h4>
            {peptideB.origin === "known" ? (
              <span className={styles.known}></span>
            ) : (
              <span className={styles.predicted}></span>
            )}
            {peptideB.number}. {peptideB.name}: {Math.round(identity * 100)}%
            identity{" "}
          </h4>
        )}
        {type === "edge" && (
          <h4>
            {peptideA.number}/{peptideB.number}. {peptideA.name} +{" "}
            {peptideB.name}: {Math.round(identity * 100)}% identity
          </h4>
        )}
        <div className={styles.alignmentRow}>
          <div className={styles.monomerCol}>
            {!compact && (
              <>
                <div className={styles.rowHeader}>
                  <h5>{peptideA.number}</h5>
                </div>
                <div> </div>
              </>
            )}

            <div className={styles.rowHeader}>
              {compact && (
                <>
                  {peptideB.origin === "known" ? (
                    <div className={styles.known}></div>
                  ) : (
                    <div className={styles.predicted}></div>
                  )}
                </>
              )}
              <h5>{peptideB.number}</h5>
            </div>
          </div>
          {columns.map((col, idx) => {
            const s = KIND_STYLES[col.kind];
            return (
              <div className={styles.monomerCol} key={idx}>
                {!compact && (
                  <>
                    <div className={`${styles.alnCell} ${s.aa1}`}>
                      {col.a ?? "–"}
                    </div>
                    <div className={styles.alnCell}>{s.symbol}</div>
                  </>
                )}
                <div className={`${styles.alnCell} ${s.aa2}`}>
                  {col.b ?? "–"}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      {!compact && <hr />}
    </>
  );
}

export default function AlignmentCard() {
  const selection = useStore((s) => s.selection);
  const [compact, setCompact] = useState(false);

  const handleAlignment = useMemo(() => {
    if (!selection.element) return "Click nodes or edges to select";

    if (selection.element === "node") {
      const pep1 = selection.selected;
      const pep1Full = useStore.getState().peptidesById[selection.selected];

      if (selection.edgeNeighbours.length === 0)
        return (
          <>
            <h3>
              {pep1Full.number}. {pep1Full.name}
            </h3>
            <div className={styles.alignmentRow}>
              {pep1Full.monomers.map((m, idx) => (
                <div
                  className={`${styles.alnCell} ${styles.alnMatch}`}
                  key={idx}
                >
                  {m}
                </div>
              ))}
            </div>
            <hr />
            <p>No neighbouring nodes</p>
          </>
        );

      return (
        <div>
          <div className="flexRow">
            <h3>
              {pep1Full.number}. Alignments with {pep1Full.name}
            </h3>
            <div className="alignRight">
              <Button onClick={() => setCompact((c) => !c)}>
                {compact ? "Compact" : "Expanded"}
              </Button>
            </div>
          </div>
          {compact && (
            <>
              <div className={styles.alignmentRow}>
                <div className={styles.alnCell}>
                  <h5>{pep1Full.number}</h5>
                </div>
                {pep1Full.monomers.map((m, idx) => (
                  <div
                    className={`${styles.alnCell} ${styles.alnMatch}`}
                    key={idx}
                  >
                    {m}
                  </div>
                ))}
              </div>
              <hr />
            </>
          )}
          {selection.edgeNeighbours.map((edge, idx) => {
            const pep2 = selection.nodeNeighbours[idx];
            return (
              <div key={idx}>
                {renderAlignment(
                  ...getAlignmentInfo(edge, pep1, pep2),
                  selection.element,
                  compact,
                )}
              </div>
            );
          })}
        </div>
      );
    }

    if (selection.element === "edge") {
      const pep1 = selection.nodeNeighbours;
      const pep2 = selection.edgeNeighbours;
      const edge = selection.selected;

      return renderAlignment(
        ...getAlignmentInfo(edge, pep1, pep2),
        selection.element,
      );
    }

    return "No current alignment";
  }, [selection, compact]);

  return (
    <Card id="alignment" title="Alignment">
      {handleAlignment}
    </Card>
  );
}
