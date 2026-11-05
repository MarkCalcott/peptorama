import Card from "@/components/ui/Card";
import useStore from "@/store";
import NetworkGraph from "./NetworkGraph";
import NetworkBar from "./NetworkBar";
import styles from "./Network.module.css";

export default function NetworkCard() {
  const data = useStore((s) => s.data.output);

  const count = Object.keys(data.edges ?? {}).length;

  return (
    <Card id="network" title="Network">
      {count === 0 && (
        <div className={styles.preload}>
          <p>Build network to view</p>
        </div>
      )}
      {count > 0 && (
        <div className={styles.networkContainer}>
          <NetworkBar />
          <NetworkGraph result={data} />
        </div>
      )}
    </Card>
  );
}
