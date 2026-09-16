import { useEffect, useMemo } from "react";
import Card from "@/components/ui/Card";
import useStore from "@/store";
import Button from "@/components/ui/Button";

function currentField(method, mode, stereochemistry = null) {
  return method === "tanimoto"
    ? `tanimoto_r${mode}`
    : `alignment_${mode}_${stereochemistry}_id`;
}

export default function EdgeCard() {
  const data = useStore((s) => s.data.output);
  const method = useStore((s) => s.view.current);

  const monomerMode = useStore((s) => s.view.monomer.mode);
  const monomerStereochemistry = useStore(
    (s) => s.view.monomer.stereochemistry,
  );
  const monomerCutoff = useStore((s) => s.view.monomer.cutoff);

  const tanimotoMode = useStore((s) => s.view.tanimoto.mode);
  const tanimotoCutoff = useStore((s) => s.view.tanimoto.cutoff);
  const setView = useStore((s) => s.setView);
  const cy = useStore((s) => s.cy);

  const edgeElements = useMemo(() => {
    if (!cy) return [];

    const edgeField =
      method === "tanimoto"
        ? currentField(method, tanimotoMode)
        : currentField(method, monomerMode, monomerStereochemistry);
    const minEdge =
      method === "tanimoto" ? tanimotoCutoff : monomerCutoff / 100;

    return (data.edges || [])
      .map((e) => (e.data ? e.data : e))
      .filter((d) => typeof d[edgeField] === "number")
      .filter((d) => d[edgeField] >= minEdge)
      .map((d) => ({ data: { ...d, weight: d[edgeField] } }));
  }, [
    cy,
    method,
    tanimotoMode,
    monomerMode,
    monomerStereochemistry,
    tanimotoCutoff,
    monomerCutoff,
  ]);

  useEffect(() => {
    if (!cy || cy.destroyed()) return;
    cy.batch(() => {
      cy.edges().remove();
      cy.add(edgeElements);
    });
  }, [cy, edgeElements]);

  return (
    <Card id="edges" title="Edges">
      {(data.edges.length > 0 && (
        <>
          <h3>Select settings to define edges</h3>
          <div className="box">
            {data.settings.edge.methods.length > 1 && (
              <div>
                <h4>Comparison method</h4>
                <div className="toggleButtonArea">
                  <Button
                    variant="toggle"
                    key="monomer"
                    active={method === "monomer"}
                    onClick={() => setView({ current: "monomer" })}
                  >
                    Monomer
                  </Button>
                  <Button
                    variant="toggle"
                    key="tanimoto"
                    active={method === "tanimoto"}
                    onClick={() => setView({ current: "tanimoto" })}
                  >
                    Tanimoto
                  </Button>
                </div>
              </div>
            )}

            {method === "monomer" &&
              data.settings.edge.monomer.match.length > 1 && (
                <div>
                  <h4>Monomer comparisons</h4>
                  <div className="toggleButtonArea">
                    <Button
                      variant="toggle"
                      key="Base"
                      active={monomerMode === "base"}
                      onClick={() => setView({ monomer: { mode: "base" } })}
                    >
                      Base
                    </Button>
                    <Button
                      variant="toggle"
                      key="Exact"
                      active={monomerMode === "exact"}
                      onClick={() => setView({ monomer: { mode: "exact" } })}
                    >
                      Exact
                    </Button>
                  </div>
                </div>
              )}
            {method === "monomer" &&
              data.settings.edge.monomer.stereochemistry.length > 1 && (
                <div>
                  <h4>Stereochemistry strictness</h4>
                  <div className="toggleButtonArea">
                    {data.settings.edge.monomer.stereochemistry.includes(
                      "relaxed",
                    ) && (
                      <Button
                        variant="toggle"
                        key="relaxed"
                        active={monomerStereochemistry === "relaxed"}
                        onClick={() =>
                          setView({ monomer: { stereochemistry: "relaxed" } })
                        }
                      >
                        Relaxed
                      </Button>
                    )}
                    {data.settings.edge.monomer.stereochemistry.includes(
                      "moderate",
                    ) && (
                      <Button
                        variant="toggle"
                        key="moderate"
                        active={monomerStereochemistry === "moderate"}
                        onClick={() =>
                          setView({ monomer: { stereochemistry: "moderate" } })
                        }
                      >
                        Moderate
                      </Button>
                    )}
                    {data.settings.edge.monomer.stereochemistry.includes(
                      "strict",
                    ) && (
                      <Button
                        variant="toggle"
                        key="strict"
                        active={monomerStereochemistry === "strict"}
                        onClick={() =>
                          setView({ monomer: { stereochemistry: "strict" } })
                        }
                      >
                        Exact
                      </Button>
                    )}
                  </div>
                </div>
              )}
            {method === "monomer" && data.settings.edge.monomer.cutoff > 0 && (
              <>
                <h4>Minimum alignment identity</h4>
                <div className="flexRow" style={{ alignItems: "center" }}>
                  <input
                    className="rangeSlider"
                    type="range"
                    min={data.settings.edge.monomer.cutoff}
                    max="100"
                    step={1}
                    value={monomerCutoff}
                    onChange={(e) =>
                      setView({ monomer: { cutoff: Number(e.target.value) } })
                    }
                    style={{
                      background: `linear-gradient(to right, var(--border-active) 0%, var(--border-active) ${((monomerCutoff - data.settings.edge.monomer.cutoff) / (100 - data.settings.edge.monomer.cutoff)) * 100}%, var(--bg-hover) ${((monomerCutoff - data.settings.edge.monomer.cutoff) / (100 - data.settings.edge.monomer.cutoff)) * 100}%, var(--bg-hover) 100%)`,
                    }}
                  />
                </div>
                <div>{monomerCutoff}% identify</div>
              </>
            )}
            {method === "tanimoto" &&
              data.settings.edge.tanimoto.radius.length > 1 && (
                <div>
                  <h4>Radius</h4>
                  <div className="toggleButtonArea">
                    {data.settings.edge.tanimoto.radius.includes(2) && (
                      <Button
                        variant="toggle"
                        key="Base"
                        active={tanimotoMode === 2}
                        onClick={() => setView({ tanimoto: { mode: 2 } })}
                      >
                        2
                      </Button>
                    )}
                    {data.settings.edge.tanimoto.radius.includes(3) && (
                      <Button
                        variant="toggle"
                        key="Exact"
                        active={tanimotoMode === 3}
                        onClick={() => setView({ tanimoto: { mode: 3 } })}
                      >
                        3
                      </Button>
                    )}
                    {data.settings.edge.tanimoto.radius.includes(4) && (
                      <Button
                        variant="toggle"
                        key="Exact"
                        active={tanimotoMode === 4}
                        onClick={() => setView({ tanimoto: { mode: 4 } })}
                      >
                        4
                      </Button>
                    )}
                  </div>
                </div>
              )}
            {method === "tanimoto" &&
              data.settings.edge.tanimoto.cutoff > 0 && (
                <>
                  <h4>Minimum Tanimoto Similarity</h4>
                  <div className="flexRow" style={{ alignItems: "center" }}>
                    <input
                      className="rangeSlider"
                      type="range"
                      min={data.settings.edge.tanimoto.cutoff}
                      max="1"
                      step={0.01}
                      value={tanimotoCutoff}
                      onChange={(e) =>
                        setView({
                          tanimoto: { cutoff: Number(e.target.value) },
                        })
                      }
                      style={{
                        background: `linear-gradient(to right, var(--border-active) 0%, var(--border-active) ${((tanimotoCutoff - data.settings.edge.tanimoto.cutoff) / (1 - data.settings.edge.tanimoto.cutoff)) * 100}%, var(--bg-hover) ${((tanimotoCutoff - data.settings.edge.tanimoto.cutoff) / (1 - data.settings.edge.tanimoto.cutoff)) * 100}%, var(--bg-hover) 100%)`,
                      }}
                    />
                  </div>
                  <div>Similarity score: {tanimotoCutoff}</div>
                </>
              )}
          </div>
        </>
      )) || (
        <p>Create a network and then use this panel to modify edge settings</p>
      )}
    </Card>
  );
}
