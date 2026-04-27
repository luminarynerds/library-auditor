import { useNavigate } from "react-router-dom";
import ScanForm from "../components/ScanForm";

export default function LandingPage() {
  const navigate = useNavigate();

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
    </div>
  );
}
