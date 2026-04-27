import type { IssueOut } from "../api/scans";

interface Props {
  issues: IssueOut[];
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#d32f2f",
  serious: "#f57c00",
  moderate: "#fbc02d",
  minor: "#888",
};

export default function IssuesTable({ issues }: Props) {
  if (issues.length === 0) {
    return <p style={{ color: "#388e3c", fontWeight: 600 }}>No HTML accessibility issues found.</p>;
  }

  return (
    <div style={{ marginBottom: 32 }}>
      <h2>Accessibility Issues</h2>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
        <thead>
          <tr style={{ borderBottom: "2px solid #ddd", textAlign: "left" }}>
            <th style={{ padding: 8 }}>Issue</th>
            <th style={{ padding: 8 }}>Severity</th>
            <th style={{ padding: 8 }}>Page</th>
            <th style={{ padding: 8 }}>How to Fix</th>
          </tr>
        </thead>
        <tbody>
          {issues.map((issue) => (
            <tr key={issue.id} style={{ borderBottom: "1px solid #eee" }}>
              <td style={{ padding: 8 }}>
                <strong>{issue.plain_title}</strong>
                <br />
                <span style={{ color: "#555", fontSize: 13 }}>{issue.plain_description}</span>
              </td>
              <td style={{ padding: 8 }}>
                <span style={{
                  padding: "2px 8px", borderRadius: 4, fontSize: 12, fontWeight: 600,
                  background: SEVERITY_COLORS[issue.severity] || "#888", color: "#fff",
                }}>
                  {issue.severity}
                </span>
              </td>
              <td style={{ padding: 8 }}>
                <a href={issue.url} target="_blank" rel="noopener noreferrer" style={{ color: "#1976d2", wordBreak: "break-all" }}>
                  {new URL(issue.url).pathname}
                </a>
              </td>
              <td style={{ padding: 8, color: "#555" }}>{issue.fix_suggestion}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
