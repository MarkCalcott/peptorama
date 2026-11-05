import WarningList from "./WarningList";
import Card from "@/components/ui/Card";
import { INFO_MESSAGES } from "./infoMessages";
import useStore from "@/store";

export default function InfoCard() {
  const info = useStore((s) => s.info) ?? { id: "welcome", params: {} };
  const render = INFO_MESSAGES[info.id] ?? INFO_MESSAGES.welcome;
  const warnings = useStore((s) => s.data.output?.warnings);
  return (
    <>
      <Card id="info" title="Info">
        {render(info.params)}
        {warnings && <WarningList items={warnings} />}
        <p>
          Want to learn more? Read our{" "}
          <a
            href="https://www.biorxiv.org/content/10.64898/2026.11.03.764117v1"
            target="_blank"
            rel="noopener noreferrer"
          >
            preprint article
          </a>{" "}
          or view the{" "}
          <a
            href="https://github.com/MarkCalcott/peptorama"
            target="_blank"
            rel="noopener noreferrer"
          >
            source code
          </a>
          .
        </p>
      </Card>
    </>
  );
}
