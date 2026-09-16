import { useMemo, useRef, useState } from "react";
import { useRdkit } from "./useRdkit";
import Button from "@/components/ui/Button";
import styles from "./Selection.module.css";

const svgDataUri = (svg) =>
  `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;

const drawOptions = {
  width: 640,
  height: 480,
  bondLineWidth: 1.1,
  baseFontSize: 0.6,
  addStereoAnnotation: true,
};

export function MoleculeView({ smiles }) {
  const { rdkit, status, error, retry } = useRdkit();
  const [copied, setCopied] = useState(false);
  const dialogRef = useRef(null);

  const svg = useMemo(() => {
    if (status !== "ready") return "";
    const mol = rdkit.get_mol(smiles);
    if (!mol) return "";
    try {
      return mol.get_svg_with_highlights(JSON.stringify(drawOptions));
    } finally {
      mol.delete();
    }
  }, [rdkit, status, smiles]);

  if (status === "loading") {
    return <div className="rdkit-status">Loading chemistry engine…</div>;
  }

  if (status === "error") {
    return (
      <div className="rdkit-status rdkit-error">
        <p>Couldn't load the chemistry engine.</p>
        {error?.message && <p className="rdkit-detail">{error.message}</p>}
        <Button onClick={retry}>Retry</Button>
      </div>
    );
  }

  if (!svg)
    return <div className="rdkit-status">Invalid structure: {smiles}</div>;

  const src = svgDataUri(svg);
  const open = () => dialogRef.current?.showModal();
  const close = () => dialogRef.current?.close();

  const copySmiles = async () => {
    try {
      await navigator.clipboard.writeText(smiles);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      // Clipboard API can reject (insecure context, permissions) — fall back.
      fallbackCopy(smiles);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    }
  };

  function fallbackCopy(text) {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
    } catch {
      /* nothing more we can do */
    }
    ta.remove();
  }

  return (
    <>
      <div className={styles.flexCol}>
        <img
          src={src}
          alt={smiles}
          className={styles.moleculeThumb}
          onClick={open}
          // keyboard access — drop these three lines if you don't need it
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              open();
            }
          }}
        />

        <Button onClick={() => copySmiles(smiles)}>
          {copied ? "Copied!" : "Copy SMILES"}
        </Button>
      </div>

      <dialog
        ref={dialogRef}
        className={styles.moleculeLarge}
        onClick={(e) => {
          if (e.target === dialogRef.current) close();
        }}
      >
        <Button onClick={close} variant="close">
          ×
        </Button>
        <img src={src} alt={smiles} className="molecule-dialog-img" />
      </dialog>
    </>
  );
}
