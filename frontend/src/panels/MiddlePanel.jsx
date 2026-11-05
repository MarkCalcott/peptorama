import UploadCard from "@/components/features/upload/UploadCard";
import NetworkCard from "@/components/features/network/NetworkCard";
import ErrorBoundary from "../components/ErrorBoundary";

export default function MiddlePanel() {
  return (
    <div>
      <ErrorBoundary
        fallback={<p>Upload panel did not load. Try refreshing page.</p>}
      >
        <UploadCard />
      </ErrorBoundary>

      <ErrorBoundary
        fallback={<p>Network panel did not load. Try refreshing page.</p>}
      >
        <NetworkCard />
      </ErrorBoundary>
    </div>
  );
}
