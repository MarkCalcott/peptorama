import Topbar from "../components/features/Topbar";
import Panelbar from "../components/features/Panelbar";
import PanelLayout from "./PanelLayout";
import ErrorBoundary from "../components/ErrorBoundary";

export default function Dashboard() {
  return (
    <div>
      <ErrorBoundary
        fallback={<p>Peptorama header did not load. Try refreshing page.</p>}
      >
        <Topbar />
      </ErrorBoundary>

      <ErrorBoundary
        fallback={<p>Panel bar did not load. Try refreshing page.</p>}
      >
        <Panelbar />
      </ErrorBoundary>

      <PanelLayout />
    </div>
  );
}
