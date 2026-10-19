import { useState, useRef } from "react";
import useStore from "@/store";
import styles from "./Upload.module.css";

import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import UploadKnown from "./UploadKnown";
import UploadPredicted from "./UploadPredicted";
import Advanced from "./Advanced";
import UploadMonomers from "./UploadMonomers";

async function submit() {
  const input = useStore.getState().data.input;
  const settings = useStore.getState().data.settings;

  if (!input.known?.trim() && !input.predicted?.trim()) {
    throw new Error("Add known or predicted peptides before submitting a job.");
  }
  const res = await fetch("/api/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      input: input,
      config: { edge: settings["edge"], filtering: settings["filtering"] },
    }),
  });
  if (!res.ok) {
    // FastAPI validation errors come back as { detail: [...] }
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail?.[0]?.msg ?? `Request failed (${res.status})`);
  }
  return res.json();
}

export default function UploadCard() {
  const [known, setKnown] = useState(true);
  const [predicted, setPredicted] = useState(false);
  const [monomers, setMonomers] = useState(false);
  const [advanced, setAdvanced] = useState(false);
  const setInfo = useStore((s) => s.setInfo);

  const resetJob = useStore((s) => s.resetJob);

  // Data for submission
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const loadNetwork = useStore((s) => s.loadNetwork);

  // Saving input
  const saveInput = useStore((s) => s.saveInput);

  // Loading a file
  const fileRef = useRef(null);
  const loadFromFile = useStore((s) => s.loadFromFile);

  async function handleSubmit() {
    setLoading(true);
    setError(null);
    try {
      const result = await submit();
      loadNetwork(result.result);
      setInfo("submitSuccess");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) alert("File not found");
    const result = await loadFromFile(file);
    if (!result.ok) alert(`${result.error}`);
  };

  const handleExample = async (name) => {
    try {
      const res = await fetch(`/examples/${name}.json`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      const result = await loadFromFile(
        new File([text], `${name}.json`, { type: "application/json" }),
      );
      setInfo(name);
      if (!result.ok) alert(result.error);
    } catch (err) {
      alert(`Could not load example: ${err.message}`);
    }
  };

  return (
    <Card id="upload" title="upload">
      <div className={styles.toolbar}>
        <div className={styles.buttonGroup}>
          <h4>Examples</h4>
          <div className={styles.exampleButtons}>
            <Button
              onClick={() => handleExample("inputDiversity")}
              variant="example"
              size="medium"
              tooltip="Example showing peptides with diverse structures"
            >
              <span className="upload-icon">↑</span>Diverse peptides
            </Button>
            <Button
              onClick={() => handleExample("inputAntibiotics")}
              variant="example"
              size="medium"
              tooltip="Retrospective example for the discovery of calcium dependent antibiotics"
            >
              <span className="upload-icon">↑</span>Antibiotics
            </Button>
            <Button
              onClick={() => alert("Temp button: Please use other example")}
              variant="example"
              size="medium"
              tooltip="Example showing the discovery of pyoverdines (a class of iron-binding siderophores)"
            >
              <span className="upload-icon">↑</span>Siderophores
            </Button>
          </div>
        </div>
        <div className={styles.buttonGroup}>
          <h4>Upload</h4>
          <div>
            <Button
              onClick={() => {
                const next = !known;
                setKnown(next);
                if (next) {
                  setInfo("knownUpload");
                } else {
                  setInfo("welcome");
                }
              }}
              active={known}
              variant="toggle"
              size="medium"
              tooltip="Upload chemically characterised peptides"
            >
              Known peptides
            </Button>
            <Button
              onClick={() => {
                const next = !predicted;
                setPredicted(next);
                if (next) {
                  setInfo("predictedUpload");
                } else {
                  setInfo("welcome");
                }
              }}
              active={predicted}
              variant="toggle"
              size="medium"
              tooltip="Upload peptides predicted from genomic data"
            >
              Predicted peptides
            </Button>
            <Button
              onClick={() => {
                const next = !monomers;
                setMonomers(next);
                if (next) {
                  setInfo("monomerUpload");
                } else {
                  setInfo("welcome");
                }
              }}
              active={monomers}
              variant="toggle"
              size="medium"
              tooltip="Upload information on monomers"
            >
              Monomers
            </Button>
          </div>
        </div>

        <div className={styles.buttonGroup}>
          <h4>Mode</h4>
          <div>
            <Button
              onClick={() => setAdvanced(false)}
              active={!advanced}
              disabled={!advanced}
              variant="toggle"
              size="medium"
              tooltip="Hide section with advanced features"
            >
              Simple
            </Button>
            <Button
              onClick={() => setAdvanced(true)}
              active={advanced}
              disabled={advanced}
              variant="toggle"
              size="medium"
              tooltip="Open section with advanced features"
            >
              Advanced
            </Button>
          </div>
        </div>
        <div className={styles.buttonGroup}>
          <h4>Input</h4>
          <div className={styles.exampleButtons}>
            <Button
              onClick={() => saveInput()}
              variant="example"
              size="medium"
              tooltip="Save the current input and settings"
            >
              Save
            </Button>
            <Button
              onClick={() => fileRef.current?.click()}
              variant="example"
              size="medium"
              tooltip="Load previously saved input or network"
            >
              Load
            </Button>
            <input
              ref={fileRef}
              type="file"
              accept=".json,application/json"
              onChange={handleFile}
              style={{ display: "none" }}
            />
            <Button
              onClick={() => {
                if (
                  window.confirm(
                    "Clear all data and reset settings? Unsaved data will be lost",
                  )
                ) {
                  setKnown(true);
                  setPredicted(false);
                  setMonomers(false);
                  setAdvanced(false);
                  setInfo("welcome");
                  resetJob();
                }
              }}
              variant="example"
              size="medium"
              tooltip="Clear data input and reset settings"
            >
              Reset
            </Button>
          </div>
        </div>
      </div>
      {known && (
        <>
          <hr />
          <UploadKnown />
        </>
      )}

      {predicted && (
        <>
          <hr />
          <UploadPredicted />
        </>
      )}

      {monomers && (
        <>
          <hr />
          <UploadMonomers advanced={advanced} />
        </>
      )}

      {advanced && (
        <>
          <hr />
          <Advanced />
        </>
      )}
      <hr />
      <div className="flexRow">
        {error && <div className="error">Job failed: {error}</div>}
        <div className="alignRight">
          <Button
            variant="primary"
            size="large"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? "Running" : "Build network"}
          </Button>
        </div>
      </div>
    </Card>
  );
}
