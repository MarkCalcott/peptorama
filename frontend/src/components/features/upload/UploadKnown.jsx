import { useState } from "react";
import useStore from "../../../store";
import styles from "./Upload.module.css";

const MAX_FILE_BYTES = 1024 * 1024; // For upload hard limit to paste input - to stop overloading browser differs from job limit

const checkErrors = (text, config) => {
  const errors = [];

  // Limits for online jobs
  if (new Blob([text]).size > config.maxInputKB * 1024) {
    errors.push(
      `Input exceeds ${config.maxInputKB} KB limit for known peptides (Reduce input or install locally to modify)`,
    );
  }
  const lines = text.trim().split("\n").filter(Boolean);
  if (lines.length > config.maxPeptides) {
    errors.push(
      `Too many peptides (max ${config.maxPeptides}). (Reduce input or install locally to modify)`,
    );
  }
  const columns = lines.length ? lines[0].split(",").length : 0;
  if (columns > config.maxMetadata) {
    errors.push(
      `Too many metadata columns (max ${config.maxMetadata}). (Reduce input or install locally to modify)`,
    );
  }
  return errors;
};

export default function Known() {
  const known = useStore((s) => s.data.input.known);
  const setInput = useStore((s) => s.setInput);
  const config = useStore((s) => s.config);
  const [errors, setErrors] = useState([]);
  const [isDragging, setIsDragging] = useState(false);

  const inputText = (text) => {
    setInput("known", text);
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
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (!file) return;

    const ext = file.name.split(".").pop().toLowerCase();
    if (!["csv", "txt"].includes(ext)) {
      alert("Only .csv and .txt files are supported");
      return;
    }

    if (file.size > MAX_FILE_BYTES) {
      alert(
        `File is too large (max ${config.maxInputKB} KB online and max 1 MB for local installs)`,
      );
      return;
    }

    const text = await file.text();
    inputText(text);
  };

  return (
    <>
      <h3>Known peptides</h3>
      <p>
        Upload experimentally validated peptides one per line as monomer strings
        separated by dashes or as SMILES strings. Additional metadata can be
        added if separated by commas.
      </p>
      <div className={`flexRow ${styles.container}`}>
        <div className={styles.left}>
          <textarea
            className={`input-area ${isDragging ? "dragging" : ""} ${known.length > 0 && errors.length > 0 ? "input-error" : ""}`}
            value={known}
            onChange={handleChange}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            placeholder="Paste peptides one per line or drop CSV file.&#10;Example: &#10;Gly-L-Ala-B-OH-Tyr, NRP-01&#10;Gly-L-Ala-Leu-D-Ser, NRP-02 &#10;Thr-D-Ala-L-Val-Ser, NRP-03"
          ></textarea>
        </div>
        <div className={styles.right}>
          <div className="box">
            <h4>&#128203; Expected format</h4>
            <div>
              <p>
                Provide peptide sequences as monomer sequence or as SMILES
                strings in CSV file format or paste as comma separated text. Add
                optional columns for name and metadata.
              </p>
              <p>
                Up to&nbsp;{config.maxPeptides}&nbsp;compounds can be analysed
                online with up to&nbsp;{config.maxMetadata}&nbsp;columns. See
                help for local installation with bigger datasets.
              </p>
            </div>
            <table>
              <thead>
                <tr>
                  <th>peptide</th>
                  <th>smiles</th>
                  <th>name</th>
                  <th>bioactive</th>
                  <th>n</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Gly-L-Ala-B-OH-Tyr-&#8230;</td>
                  <td>CC&#8230;</td>
                  <td>NRP-01</td>
                  <td>yes</td>
                  <td>&#8230;</td>
                </tr>
                <tr>
                  <td>Gly-L-Ala-Leu-D-Ser&#8230;</td>
                  <td>CC&#8230;</td>
                  <td>NRP-02</td>
                  <td>no</td>
                  <td>&#8230;</td>
                </tr>
                <tr>
                  <td>Thr-D-Ala-L-Val-Ser&#8230;</td>
                  <td>CC&#8230;</td>
                  <td>NRP-03</td>
                  <td>yes</td>
                  <td>&#8230;</td>
                </tr>
              </tbody>
            </table>
            <div>
              <p className="info">
                Monomers will be extracted automatically as three character
                sequences separated by dashes. Stereochemistry can be added as a
                prefix D- or L-Modifications followed by optional modifications
                as fewer than two characters separated by dashes (e.g.
                L-N-Me-Ala for L-N-methyl-alanine).
              </p>
            </div>
          </div>
        </div>
      </div>
      {known.length > 0 &&
        errors.length > 0 &&
        errors.map((error, i) => (
          <p className="error" key={i}>
            {error}
          </p>
        ))}
    </>
  );
}
