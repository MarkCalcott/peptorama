const RDKIT_VERSION = "2025.3.4-1.0.0";
const BASE = `https://unpkg.com/@rdkit/rdkit@${RDKIT_VERSION}/dist`;
const JS_URL = `${BASE}/RDKit_minimal.js`;
const WASM_URL = `${BASE}/RDKit_minimal.wasm`;

const LOAD_TIMEOUT_MS = 15000;

let rdkitPromise = null;

function loadScript(src, timeoutMs) {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[data-rdkit="true"]`);
    if (existing) {
      if (window.initRDKitModule) return resolve();
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () =>
        reject(new Error("RDKit script failed to load")),
      );
      return;
    }

    const s = document.createElement("script");
    s.src = src;
    s.async = true;
    s.dataset.rdkit = "true";

    const timer = setTimeout(() => {
      s.remove();
      reject(new Error(`RDKit script timed out after ${timeoutMs}ms`));
    }, timeoutMs);

    s.onload = () => {
      clearTimeout(timer);
      resolve();
    };
    s.onerror = () => {
      clearTimeout(timer);
      s.remove();
      reject(new Error("RDKit script failed to load"));
    };

    document.head.appendChild(s);
  });
}

export function initRDKit() {
  if (!rdkitPromise) {
    rdkitPromise = (async () => {
      await loadScript(JS_URL, LOAD_TIMEOUT_MS);
      if (!window.initRDKitModule) {
        throw new Error("initRDKitModule not found after script load");
      }
      const RDKit = await window.initRDKitModule({
        locateFile: () => WASM_URL,
      });
      return RDKit;
    })().catch((err) => {
      rdkitPromise = null;
      throw err;
    });
  }
  return rdkitPromise;
}
