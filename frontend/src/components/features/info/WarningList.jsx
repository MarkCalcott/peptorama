const SEVERITY_ORDER = { info: 0, warning: 1, error: 2, critical: 3 };

function groupWarnings(warnings = []) {
  const sorted = [...warnings].sort(
    (a, b) => SEVERITY_ORDER[b.level] - SEVERITY_ORDER[a.level],
  );
  return {
    critical: sorted.filter((w) => w.level === "critical"),
    errors: sorted.filter((w) => w.level === "error"),
    info: sorted.filter((w) => w.level === "info" || w.level === "warning"),
  };
}

function Section({ items, className }) {
  return (
    <ul>
      {items.map((w, i) => (
        <li key={i} className={className}>
          {w.message}
        </li>
      ))}
    </ul>
  );
}

export default function WarningList({ items }) {
  const { critical, errors, info } = groupWarnings(items);

  if (!items.length) return null;

  return (
    <>
      <hr />
      {(critical.length > 0 || errors.length > 0) && <h3>Errors</h3>}
      {critical.length > 0 && (
        <div className="error">
          <h4>Must be fixed to run:</h4>
          <Section items={critical} />
        </div>
      )}
      {errors.length > 0 && (
        <div className="warning">
          <h4>Affected data will be dropped:</h4>
          <Section items={errors} />
        </div>
      )}
      {info.length > 0 && (
        <>
          <h4>Information</h4>
          <Section items={info} className="info" />
        </>
      )}
    </>
  );
}
