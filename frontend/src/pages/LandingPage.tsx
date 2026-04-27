import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { listScans } from "../api/scans";
import type { ScanSummary } from "../api/scans";
import ScanForm from "../components/ScanForm";

const STATUS_COLORS: Record<string, string> = {
  complete: "#388e3c",
  failed: "#d32f2f",
  queued: "#888",
  crawling: "#1976d2",
  auditing: "#1976d2",
  analyzing_pdfs: "#1976d2",
};

export default function LandingPage() {
  const navigate = useNavigate();
  const [recentScans, setRecentScans] = useState<ScanSummary[]>([]);

  useEffect(() => {
    listScans().then(setRecentScans).catch(() => {});
  }, []);

  return (
    <div style={{ padding: 32, maxWidth: 640, margin: "0 auto", fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ textAlign: "center", marginBottom: 8 }}>The Library Auditor</h1>
      <p style={{ textAlign: "center", color: "#555", marginBottom: 32, fontSize: 18 }}>
        Free accessibility scanner for public libraries.
        <br />
        Enter your website, get a plain-language report.
      </p>
      <ScanForm onScanCreated={(id) => navigate(`/scan/${id}`)} />
      <p style={{ textAlign: "center", marginTop: 32, fontSize: 14, color: "#888" }}>
        Checks for ADA Title II / WCAG 2.1 Level AA compliance.
        <br />
        Finds untagged PDFs and estimates remediation costs.
      </p>

      {recentScans.length > 0 && (
        <div style={{ marginTop: 48, borderTop: "1px solid #eee", paddingTop: 24 }}>
          <h2 style={{ fontSize: 18, marginBottom: 16 }}>Recent Scans</h2>
          {recentScans.map((scan) => {
            const isRunning = !["complete", "failed"].includes(scan.status);
            const linkTo = scan.status === "complete" ? `/report/${scan.id}` : `/scan/${scan.id}`;
            return (
              <Link
                key={scan.id}
                to={linkTo}
                style={{
                  display: "block",
                  padding: "12px 16px",
                  marginBottom: 8,
                  border: "1px solid #e0e0e0",
                  borderRadius: 8,
                  textDecoration: "none",
                  color: "inherit",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <strong>{scan.library_name}</strong>
                    <div style={{ fontSize: 13, color: "#888" }}>
                      {scan.base_url} -- {new Date(scan.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    {scan.status === "complete" && scan.compliance_score !== null && (
                      <div style={{
                        fontSize: 20,
                        fontWeight: 700,
                        color: scan.compliance_score >= 80 ? "#388e3c" : scan.compliance_score >= 50 ? "#f57c00" : "#d32f2f",
                      }}>
                        {scan.compliance_score}%
                      </div>
                    )}
                    <span style={{
                      fontSize: 12,
                      fontWeight: 600,
                      color: STATUS_COLORS[scan.status] || "#888",
                    }}>
                      {isRunning ? "Scanning..." : scan.status}
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
