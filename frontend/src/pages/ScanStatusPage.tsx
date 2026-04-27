import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getScan } from "../api/scans";
import type { ScanSummary } from "../api/scans";

const STATUS_LABELS: Record<string, string> = {
  queued: "Waiting to start...",
  crawling: "Discovering pages and PDFs on your site...",
  auditing: "Checking pages for accessibility issues...",
  analyzing_pdfs: "Analyzing PDF documents...",
  complete: "Scan complete!",
  failed: "Scan failed.",
};

export default function ScanStatusPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [scan, setScan] = useState<ScanSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;

    const poll = async () => {
      try {
        const data = await getScan(id);
        setScan(data);
        if (data.status === "complete") {
          navigate(`/report/${id}`, { replace: true });
          return;
        }
        if (data.status === "failed") {
          return;
        }
      } catch {
        setError("Could not fetch scan status.");
        return;
      }
      setTimeout(poll, 3000);
    };

    poll();
  }, [id, navigate]);

  if (error) {
    return (
      <div style={{ padding: 32, maxWidth: 640, margin: "0 auto", textAlign: "center" }}>
        <p style={{ color: "#d32f2f" }}>{error}</p>
      </div>
    );
  }

  if (!scan) {
    return (
      <div style={{ padding: 32, maxWidth: 640, margin: "0 auto", textAlign: "center" }}>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: 32, maxWidth: 640, margin: "0 auto", fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ textAlign: "center" }}>Scanning: {scan.library_name}</h1>
      <p style={{ textAlign: "center", fontSize: 18, color: "#555" }}>
        {STATUS_LABELS[scan.status] || scan.status}
      </p>

      {scan.status !== "failed" && (
        <div style={{ textAlign: "center", margin: "32px 0" }}>
          <div style={{
            width: 48, height: 48, border: "4px solid #e0e0e0", borderTop: "4px solid #1976d2",
            borderRadius: "50%", animation: "spin 1s linear infinite", margin: "0 auto",
          }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "center", gap: 32, marginTop: 24 }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 32, fontWeight: 700 }}>{scan.pages_found}</div>
          <div style={{ color: "#888" }}>Pages found</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 32, fontWeight: 700 }}>{scan.pdfs_found}</div>
          <div style={{ color: "#888" }}>PDFs found</div>
        </div>
      </div>

      {scan.status === "failed" && (
        <div role="alert" style={{ color: "#d32f2f", textAlign: "center", marginTop: 24, padding: 16, background: "#ffeaea", borderRadius: 4 }}>
          {scan.error_message || "An unexpected error occurred."}
        </div>
      )}
    </div>
  );
}
