import { useState, useMemo } from "react";
import { computeFieldChart } from "./metadata";
import IndividualGraph from "./IndividualGraph";
import Button from "@/components/ui/Button";
import styles from "./Metadata.module.css";

import useStore from "@/store";

export default function MetadataGraphs({ data }) {
  const [knownVisible, setKnownVisible] = useState(true);
  const [predictedVisible, setPredictedVisible] = useState(true);

  const peptides = useMemo(() => Object.values(data ?? {}), [data]);
  const known_order = useStore((s) => s.data.output?.metadata?.known_order);
  const predicted_order = useStore(
    (s) => s.data.output?.metadata?.predicted_order,
  );

  const known = useMemo(
    () => computeFieldChart(peptides, known_order, "known", "origin"),
    [peptides, known_order],
  );

  const predicted = useMemo(
    () => computeFieldChart(peptides, predicted_order, "predicted", "origin"),
    [peptides, predicted_order],
  );

  return (
    <div className={styles.gridWrapper}>
      {known_order.length > 0 && (
        <>
          <div className="flexRow">
            <h3>Known peptides</h3>
            <div className="alignRight">
              <Button onClick={() => setKnownVisible((v) => !v)}>
                {knownVisible ? "Hide known" : "Show known"}
              </Button>
            </div>
          </div>
          <div className={styles.graphContainer}>
            {knownVisible &&
              known_order.map((field) => (
                <IndividualGraph
                  key={field}
                  field={field}
                  data={known[field]}
                />
              ))}
          </div>
        </>
      )}

      {known_order.length > 0 && predicted_order.length > 0 && <hr />}
      {predicted_order.length > 0 && (
        <>
          <div className="flexRow">
            <h3>Predicted peptides</h3>
            <div className="alignRight">
              <Button onClick={() => setPredictedVisible((v) => !v)}>
                {predictedVisible ? "Hide predicted" : "Show predicted"}
              </Button>
            </div>
          </div>
          {predictedVisible &&
            predicted_order.map((field) => (
              <IndividualGraph
                key={field}
                field={field}
                data={predicted[field]}
              />
            ))}
        </>
      )}
    </div>
  );
}
