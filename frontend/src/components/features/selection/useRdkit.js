import { useCallback, useEffect, useState } from "react";
import { initRDKit } from "./rdkit";

export function useRdkit() {
  const [rdkit, setRdkit] = useState(null);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState("loading");
  const [attempt, setAttempt] = useState(0);

  const retry = useCallback(() => {
    setError(null);
    setStatus("loading");
    setAttempt((n) => n + 1);
  }, []);

  useEffect(() => {
    let active = true;

    initRDKit()
      .then((RDKit) => {
        if (!active) return;
        setRdkit(() => RDKit);
        setStatus("ready");
      })
      .catch((e) => {
        if (!active) return;
        setError(e);
        setStatus("error");
      });

    return () => {
      active = false;
    };
  }, [attempt]);

  return { rdkit, error, status, retry };
}
