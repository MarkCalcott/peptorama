import { useState, useRef } from "react";
import Button from "@/components/ui/Button";
import styles from "./Upload.module.css";

import useStore from "@/store";

async function preprocess() {
  const input = useStore.getState().data.input;
  if (!input.known?.trim() && !input.predicted?.trim()) {
    throw new Error("Add known or predicted peptides before preprocessing.");
  }
  const res = await fetch("/api/preprocess", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      known: input.known,
      predicted: input.predicted,
      monomers: input.monomers,
    }),
  });
  if (!res.ok) {
    // FastAPI validation errors come back as { detail: [...] }
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail?.[0]?.msg ?? `Request failed (${res.status})`);
  }
  return res.json();
}

function parseMonomerCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines[0].split(",").map((h) => h.trim().toLowerCase());

  const blankToNull = (raw) => {
    const value = (raw ?? "").replace(/"/g, "").trim();
    return value === "" ? null : value;
  };

  const monomers = {};

  for (const line of lines.slice(1)) {
    if (!line.trim()) continue;

    const cells = line.split(",");
    const row = Object.fromEntries(
      headers.map((h, i) => [h, blankToNull(cells[i])]),
    );
    if (!row.code) continue;

    monomers[row.code] = {
      code: row.code,
      exact: row.exact,
      base: row.base,
      stereochemistry: row.stereochemistry,
      name: row.name,
      smiles: row.smiles,
      category: row.category,
      known: "User-defined",
    };
  }

  return monomers;
}

export default function UploadMonomers() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const hasInputErrors = useStore((s) =>
    Object.values(s.errors).some((e) => e.length > 0),
  );
  const setInfo = useStore((s) => s.setInfo);
  const setOutput = useStore((s) => s.setOutput);
  const setMonomers = useStore((s) => s.setMonomers);
  const fileRef = useRef(null);

  async function handleExtract() {
    setLoading(true);
    setError(null);
    try {
      const result = await preprocess();
      setMonomers(result.monomers);
      setOutput(result);
      setInfo("monomersExtracted");
      useStore.getState().toggleCard("monomers", false, true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleMonomerCSV(file) {
    setLoading(true);
    setError(null);
    try {
      const monomers = await parseMonomerCSV(await file.text());
      setMonomers(monomers);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div>
        <h3>Monomers</h3>
        <div className={styles.buttonGroup}>
          <h4>Upload monomers</h4>
          <div>
            <div className={styles.exampleButtons}>
              <Button
                size="medium"
                variant="primary"
                onClick={handleExtract}
                disabled={loading || hasInputErrors}
                tooltip="Extract monomers from current data input"
              >
                Extract
              </Button>

              <Button
                onClick={() => fileRef.current?.click()}
                size="medium"
                tooltip="Upload monomers in CSV format"
              >
                Import
              </Button>
              <input
                ref={fileRef}
                type="file"
                accept=".csv,.txt,text/csv"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  e.target.value = "";
                  if (file) handleMonomerCSV(file);
                }}
                style={{ display: "none" }}
              />
              <span className="info"></span>

              <Button
                size="medium"
                onClick={() => useStore.getState().setMonomers({})}
                tooltip="Clear current monomer input"
              >
                Clear
              </Button>
            </div>
          </div>
          {error && (
            <div className="error" style={{ marginLeft: "var(--space-lg)" }}>
              Extraction failed: {error}
            </div>
          )}
        </div>
        <div className="flexRow">
          <div className="box" style={{ width: "100%" }}>
            <h4>Monomer definitions</h4>
            <p>
              Peptides are expressed as a string of monomers. These will be
              parsed to extract unique monomers and have some flexibility to
              allow the user to define their own nomenclature.
            </p>
            <p>
              Unique monomers should be separated by a "-" and at least three
              characters long with the first letter capitalised. Monomers will
              be automatically be detected so long peptides contain at least
              three monomers.
            </p>
            <p>Examples of valid peptides are:</p>
            <ul>
              <li>Ala-Thr-Ser</li>
              <li>D-Ala-Thr-L-Ser</li>
              <li>Ala-Adda-Val-FOHOrn-Tyr-Orn</li>
              <li>Gly-N-Me-Tyr-Val-Orn (N-Me-Tyr is a single monomer)</li>
            </ul>
          </div>

          <div className="box" style={{ width: "100%" }}>
            <h4>Additional monomer rules</h4>
            <h5>Defining the base monomer</h5>
            <ul>
              <li>
                Proteinogenic amino acids should use the standard three letter
                code
              </li>
              <li>
                The base amino acid is defined by a capitilised string of at
                least three characters and letters prior to that are not
                included in the base
              </li>

              <ul>
                <li>
                  The base amino acid for Ala, Adda, DAB and Xx1 would be Ala,
                  Adda, DAB and Xx1
                </li>
                <li>
                  The base amino acid for FoOHOrn, ADDA or DAB1 would be Orn,
                  DDA or AB1
                </li>
              </ul>
              <li>
                Stereochemistry can be represented with an L- or D- before the
                monomer, e.g. L-Ala, D-Ser
              </li>
              <ul>
                <li>
                  For SMILES, this will add stereochemistry at the alpha carbon
                  if only the flat monomer is defined. This should be checked
                  for non alpha amino acids.
                </li>
              </ul>
            </ul>
            <h5>Adding modifications</h5>
            <ul>
              <li>Additional modifications can be added in two ways:</li>
              <ul>
                <li>
                  Additional letters before the capitilised base amino acid,
                  e.g. L-FoOHOrn for modified L-Orn.
                </li>
                <li>
                  Separated by dashes and less than two characters, e.g.
                  L-N-Me-Val and L-N-Me-O-Me-Ser for mono- and di-methylated
                  variants of L-Val and L-Ser.
                </li>
              </ul>
              <li>
                Basic Methylation patterns will be added to SMILES strings for
                N-Me, O-Me, and S-Me when it is X-Me-Aaa
              </li>
            </ul>
          </div>
        </div>
      </div>
    </>
  );
}
