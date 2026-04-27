import type { PDFReportOut } from "../api/scans";

interface Props {
  pdfs: PDFReportOut[];
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function statusLabel(pdf: PDFReportOut): { text: string; color: string } {
  if (pdf.is_tagged) return { text: "Tagged (OK)", color: "#388e3c" };
  if (!pdf.has_text) return { text: "Image Only (Needs OCR)", color: "#d32f2f" };
  return { text: "Untagged (Needs Tagging)", color: "#f57c00" };
}

export default function PDFInventory({ pdfs }: Props) {
  if (pdfs.length === 0) {
    return <p>No PDFs found on your site.</p>;
  }

  const totalCostLow = pdfs.reduce((sum, p) => sum + p.estimated_cost_low, 0);
  const totalCostHigh = pdfs.reduce((sum, p) => sum + p.estimated_cost_high, 0);
  const untaggedCount = pdfs.filter((p) => !p.is_tagged).length;

  return (
    <div style={{ marginBottom: 32 }}>
      <h2>PDF Inventory</h2>
      {untaggedCount > 0 && (
        <p style={{ color: "#d32f2f", fontWeight: 600 }}>
          {untaggedCount} of {pdfs.length} PDFs need remediation.
          Estimated total cost: ${totalCostLow.toFixed(0)} - ${totalCostHigh.toFixed(0)}
        </p>
      )}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
        <thead>
          <tr style={{ borderBottom: "2px solid #ddd", textAlign: "left" }}>
            <th style={{ padding: 8 }}>File</th>
            <th style={{ padding: 8 }}>Status</th>
            <th style={{ padding: 8 }}>Pages</th>
            <th style={{ padding: 8 }}>Size</th>
            <th style={{ padding: 8 }}>Est. Cost</th>
          </tr>
        </thead>
        <tbody>
          {pdfs.map((pdf) => {
            const status = statusLabel(pdf);
            return (
              <tr key={pdf.id} style={{ borderBottom: "1px solid #eee" }}>
                <td style={{ padding: 8 }}>
                  <a href={pdf.url} target="_blank" rel="noopener noreferrer" style={{ color: "#1976d2", wordBreak: "break-all" }}>
                    {pdf.filename}
                  </a>
                </td>
                <td style={{ padding: 8, color: status.color, fontWeight: 600 }}>{status.text}</td>
                <td style={{ padding: 8 }}>{pdf.page_count}</td>
                <td style={{ padding: 8 }}>{formatBytes(pdf.file_size_bytes)}</td>
                <td style={{ padding: 8 }}>
                  {pdf.is_tagged ? "None" : `$${pdf.estimated_cost_low.toFixed(0)} - $${pdf.estimated_cost_high.toFixed(0)}`}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
