import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getScan, getIssues, getPDFs, getFixFirst } from "../api/scans";
import type { ScanSummary, IssueOut, PDFReportOut, FixFirstItem } from "../api/scans";
import ComplianceScore from "../components/ComplianceScore";
import FixFirstList from "../components/FixFirstList";
import IssuesTable from "../components/IssuesTable";
import PDFInventory from "../components/PDFInventory";

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const [scan, setScan] = useState<ScanSummary | null>(null);
  const [issues, setIssues] = useState<IssueOut[]>([]);
  const [pdfs, setPDFs] = useState<PDFReportOut[]>([]);
  const [fixFirst, setFixFirst] = useState<FixFirstItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([getScan(id), getIssues(id), getPDFs(id), getFixFirst(id)])
      .then(([scanData, issuesData, pdfsData, fixData]) => {
        setScan(scanData);
        setIssues(issuesData);
        setPDFs(pdfsData);
        setFixFirst(fixData);
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div style={{ padding: 32, textAlign: "center" }}>Loading report...</div>;
  if (!scan) return <div style={{ padding: 32, textAlign: "center" }}>Scan not found.</div>;

  return (
    <div style={{ padding: 32, maxWidth: 960, margin: "0 auto", fontFamily: "system-ui, sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h1>{scan.library_name} -- Accessibility Report</h1>
        <Link to="/" style={{ color: "#1976d2" }}>New Scan</Link>
      </div>

      <p style={{ color: "#888" }}>
        Scanned: {scan.base_url} | {new Date(scan.created_at).toLocaleDateString()}
      </p>

      <ComplianceScore
        score={scan.compliance_score}
        pagesFound={scan.pages_found}
        pdfsFound={scan.pdfs_found}
        issueCounts={scan.issue_counts}
      />

      <FixFirstList items={fixFirst} />
      <IssuesTable issues={issues} />
      <PDFInventory pdfs={pdfs} />

      <footer style={{ textAlign: "center", marginTop: 48, padding: 16, borderTop: "1px solid #eee", color: "#888", fontSize: 14 }}>
        The Library Auditor -- Free and open source.
        <br />
        Checks against WCAG 2.1 Level AA (ADA Title II).
        <br />
        Deadline: April 26, 2027 for libraries serving populations under 50,000.
      </footer>
    </div>
  );
}
