import { useState } from "react";
import useStore from "../../../store";
import styles from "./Upload.module.css";
import Button from "../../ui/Button";

const MAX_FILE_BYTES = 1024 * 1024; // For upload hard limit to paste input - to stop overloading browser differs from job limit

const checkErrors = (text, config) => {
  const errors = [];

  // Limits for online jobs
  if (new Blob([text]).size > config.maxPredictedKB * 1024) {
    errors.push(
      `Input exceeds ${config.maxPredictedKB} KB limit for predicted peptides`,
    );
  }
  const lines = text.trim().split("\n").filter(Boolean);
  if (lines.length > config.maxPredictedPeptides) {
    errors.push(`Too many peptides (max ${config.maxPredictedPeptides})`);
  }
  const columns = lines.length ? lines[0].split(",").length : 0;
  if (columns > config.maxPredictedColumns) {
    errors.push(
      `Too many metadata columns (max ${config.maxPredictedColumns})`,
    );
  }
  return errors;
};

// Find all the dropped JSON filenames
const isJson = (name) => /\.json$/i.test(name);
async function collectDropped(transfer) {
  const files = [];
  const items = transfer.items;

  if (items && items.length && items[0].webkitGetAsEntry) {
    const entries = [];
    for (let i = 0; i < items.length; i++) {
      const e = items[i].webkitGetAsEntry && items[i].webkitGetAsEntry();
      if (e) entries.push(e);
    }

    const readAllEntries = async (reader) => {
      const all = [];
      while (true) {
        const batch = await new Promise((res, rej) =>
          reader.readEntries(res, rej),
        );
        if (!batch.length) break;
        all.push(...batch);
      }
      return all;
    };

    const walk = async (entry) => {
      try {
        if (entry.isFile) {
          const f = await new Promise((res, rej) => entry.file(res, rej));
          if (isJson(f.name)) files.push(f);
        } else if (entry.isDirectory) {
          const children = await readAllEntries(entry.createReader());
          for (const c of children) await walk(c);
        }
      } catch (err) {
        console.warn("Skipped entry:", entry.fullPath, err);
      }
    };

    for (const e of entries) await walk(e);
  } else {
    for (const f of transfer.files) if (isJson(f.name)) files.push(f);
  }

  return files;
}

// Process each JSON file to extract predicted peptides
async function processJSON(file, processingSettings) {
  const data = JSON.parse(await file.text());
  const stem = file.name.replace(/\.json$/i, "");
  const lines = [];
  const seen = new Map();
  const split = processingSettings.split;
  const minLength = processingSettings.length.min;
  const maxLength = processingSettings.length.max;

  const hasTE = containsTe(data);

  const addRow = (row) => {
    const base = String(row.sc_number ?? "");
    const addPeptide = (label, peptide, original, ordering) =>
      lines.push(
        `${peptide ?? ""},${stem} ${row.region ?? ""},${original},${stem},${row.region ?? ""},${label},${ordering.join(" ")}`,
      );

    if (row.peptide && split !== "split") {
      addPeptide(base, row.peptide, row.original ?? "", row.ordering || []);
    }

    if (split !== "keep") {
      const segments = splitByTE(row.original ?? "", row.ordering || [], hasTE);
      if (segments.length > 1) {
        segments.forEach((s, i) => {
          const peptide = residueExtract(s.original, minLength, maxLength);
          if (peptide)
            addPeptide(
              base + String.fromCharCode(97 + i),
              peptide,
              s.original,
              s.ordering,
            );
        });
      } else if (row.peptide && split === "split") {
        addPeptide(base, row.peptide, row.original ?? "", row.ordering || []);
      }
    }
  };
  walk(data, addRow, seen, minLength, maxLength);
  return lines;
}

function walk(node, addRow, seen, minLength, maxLength, region = 0) {
  if (Array.isArray(node)) {
    for (const item of node)
      walk(item, addRow, seen, minLength, maxLength, region);
    return;
  }
  if (!node || typeof node !== "object") return;

  const residues = residueExtract(node.polymer, minLength, maxLength);

  if (!seen.get(region)?.has(residues)) {
    addRow({
      region,
      peptide: residues,
      original: node.polymer,
      sc_number: node.sc_number,
      ordering: node.ordering,
      smiles: node.smiles,
    });
    if (!seen.has(region)) seen.set(region, new Set());
    seen.get(region).add(residues);
  }
  for (const [k, v] of Object.entries(node)) {
    if (
      k === "region_predictions" &&
      v &&
      typeof v === "object" &&
      !Array.isArray(v)
    ) {
      for (const [regionKey, regionVal] of Object.entries(v))
        walk(regionVal, addRow, seen, minLength, maxLength, regionKey);
    } else {
      walk(v, addRow, seen, minLength, maxLength, region);
    }
  }
}

function residueExtract(polymer, minLength, maxLength) {
  if (!polymer) return null;
  let monomers = polymer
    .replace(/[()]/g, " ")
    .split(/\s-\s|\s\+\s/)
    .map((s) => s.trim())
    .filter(Boolean)
    .filter((m) => m.toUpperCase() !== "NH2");

  // Don't include X in counting length
  const length = monomers.filter((m) => m !== "X" && m !== "D-X").length;
  if (length < minLength || length > maxLength) return null;

  return monomers.map(normaliseMonomer).join("-");
}

function normaliseMonomer(monomer) {
  // Set prefix
  let prefix = "L-";
  if (monomer.startsWith("D-")) {
    prefix = monomer.slice(0, 2);
    monomer = monomer.slice(2);
  }

  if (monomer === "X") monomer = "Xxx";

  // Ensure capitalisation of suffix
  const parts = monomer.split("-");
  const i = parts.length - 1;
  const str = parts[i];
  if (str === str.toLowerCase()) {
    // For non-capitalised monomers like PKS
    prefix = "";
    parts[i] = str.replace(
      /(cc|oh)?([a-z])([a-z]*)$/i,
      (m, modification, firstLetter, rest) => {
        modification = modification ? modification.toUpperCase() + "-" : "";
        return modification + firstLetter.toUpperCase() + rest;
      },
    );
  } else {
    parts[i] = parts[i][0].toUpperCase() + parts[i].slice(1);
  }

  // Drop all internal dashes if any part besides the stereochemistry suffix is less than 3 residues
  const collapse = parts.slice(0, -1).some((p) => p.length > 3);
  let body = collapse ? parts.join("") : parts.join("-");

  // Pad with number 1 if any parts are below 3 residues
  let n = 1;
  while (body.replace(/-/g, "").length < 3) body += String(n++);

  return prefix + body;
}

// For finding TE domains
function containsTe(data) {
  const set = new Set();
  for (const rec of data.records || []) {
    const cds =
      rec.modules?.["antismash.detection.nrps_pks_domains"]?.cds_results;
    if (!cds) continue;
    for (const [gene, res] of Object.entries(cds))
      if ((res.domain_hmms || []).some((h) => h.hit_id === "Thioesterase"))
        set.add(gene);
  }
  return set;
}

function splitByTE(original, ordering, teSet) {
  const groups = original.split(" + ");
  if (!ordering.length || groups.length !== ordering.length)
    return [{ original, ordering }];

  const segments = [];
  let current = { groups: [], genes: [] };
  for (let i = 0; i < ordering.length; i++) {
    current.groups.push(groups[i]);
    current.genes.push(ordering[i]);
    if (teSet.has(ordering[i]) && i !== ordering.length - 1) {
      segments.push(current);
      current = { groups: [], genes: [] };
    }
  }
  if (current.groups.length) segments.push(current);
  return segments.map((s) => ({
    original: s.groups.join(" + "),
    ordering: s.genes,
  }));
}

export default function Known() {
  const predicted = useStore((s) => s.data.input.predicted);
  const processingSettings = useStore((s) => s.data.settings.processing);
  const setInput = useStore((s) => s.setInput);
  const config = useStore((s) => s.config);
  const errors = useStore((s) => s.errors.known);
  const setStoreErrors = useStore((s) => s.setErrors);
  const setErrors = (errs) => setStoreErrors("known", errs);
  const [processMessage, setProcessMessage] = useState([]);
  const [progress, setProgress] = useState(0);
  const [isDragging, setIsDragging] = useState(false);

  const addProcessMessage = (message) =>
    setProcessMessage((prev) => [...prev, message]);

  const inputText = (text) => {
    setInput("predicted", text);
    setErrors(checkErrors(text, config));
  };

  const handleChange = (e) => {
    inputText(e.target.value);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer) e.dataTransfer.dropEffect = "copy";
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e) => {
    if (
      predicted.length > 1 &&
      !window.confirm("Replace the current input with this file?")
    ) {
      return;
    }
    e.preventDefault();
    setIsDragging(false);

    if (progress !== 0 && progress !== 100) {
      alert(
        "Files are currently being processed. This can take up to a few seconds per file and finding JSON files takes time if large folders are dropped. Please wait a minute or two and then refresh if frozen",
      );
      return;
    }

    const myRunID = useStore.getState().startRun();
    const { isCurrentRun } = useStore.getState();

    addProcessMessage("Previous input cleared and processing started");
    setProcessMessage([]);

    const firstFile = e.dataTransfer.files[0];
    if (!firstFile) {
      addProcessMessage("No files found");
      setProgress(100);
      return;
    }

    if (
      ["csv", "txt"].includes(firstFile.name.split(".").pop().toLowerCase())
    ) {
      const text = await firstFile.text();
      if (firstFile.size > MAX_FILE_BYTES) {
        alert(`File is too large (max ${config.maxInputKB} KB online`);
        addProcessMessage("No file added");
        setProgress(100);
        return;
      }
      inputText(text);
      addProcessMessage("One file added");
      setProgress(100);
      return;
    }
    addProcessMessage("Single .csv or .txt file not detected");
    addProcessMessage("Searching for JSON files");
    setInput("predicted", "");
    setProgress(5);

    const files = await collectDropped(e.dataTransfer);
    const totalFiles = files.length;
    if (!totalFiles) {
      addProcessMessage("The processing ended with no JSON files found");
      setProgress(100);
      return;
    }
    addProcessMessage(`Processing ${totalFiles} JSON files`);
    setProgress(10);

    let processedFiles = 0;
    const lines = ["Peptide,Name,Original,Genome,Region,Candidate,Genes"];
    for (const file of files) {
      if (isCurrentRun(myRunID)) {
        try {
          const newLines = await processJSON(file, processingSettings);
          if (!isCurrentRun(myRunID)) return;
          lines.push(...newLines);
          inputText(lines.join("\n"));
          addProcessMessage(`${file.name}: Added ${newLines.length} peptides`);
        } catch (error) {
          if (!isCurrentRun(myRunID)) return;
          addProcessMessage(`⚠️${file.name}: Error - file not processed`);
          console.log(error);
        }
        if (!isCurrentRun(myRunID)) return;
        processedFiles++;
        setProgress(10 + (processedFiles / totalFiles) * 90);
      }
    }
    addProcessMessage("Finished");
    setProgress(100);
  };

  return (
    <>
      <h3>Predicted peptides</h3>
      <p>
        Drop antiSMASH outputs (JSON files or folders) or use the same format as
        per known peptides.
      </p>
      <div className={`flexRow ${styles.container}`}>
        <div className={styles.left}>
          <textarea
            className={`input-area ${isDragging ? "dragging" : ""} ${predicted.length > 0 && errors.length > 0 ? "input-error" : ""}`}
            value={predicted}
            onChange={handleChange}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            placeholder="Paste peptides one per line or drop antiSMASH file(s) or a CSV file.&#10;Example for monomer sequences: &#10;peptide, name&#10;Gly-L-Ala-B-OH-Tyr, Candidate-01&#10;Gly-L-Ala-Leu-D-Ser, Candidate-02"
          ></textarea>
        </div>
      </div>
      {processMessage.length > 0 && (
        <div>
          <h4>Processing</h4>
          <progress value={progress} max={100}></progress>
          <div className={styles.processedFiles}>
            {processMessage.map((message, i) => (
              <p className="info" key={i}>
                {message}
              </p>
            ))}
          </div>
          {(progress >= 100 && (
            <Button
              onClick={() => {
                setProcessMessage([]);
                setProgress(0);
              }}
            >
              Close summary
            </Button>
          )) || <p className="info">Processing: {Math.floor(progress)}%</p>}
        </div>
      )}
      {predicted.length > 0 &&
        errors.length > 0 &&
        errors.map((error, i) => (
          <p className="error" key={i}>
            {error}
          </p>
        ))}
    </>
  );
}
