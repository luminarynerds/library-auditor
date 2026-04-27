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

function formatUrl(url: string): { display: string; href: string | null } {
  if (url.includes("(+")) {
    // Site-wide: "https://example.com (+9 more pages)"
    return { display: url, href: null };
  }
  try {
    return { display: new URL(url).pathname, href: url };
  } catch {
    return { display: url, href: null };
  }
}

export default function IssuesTable({ issues }: Props) {
  if (issues.length === 0) {
    return <p style={{ color: "#388e3c", fontWeight: 600 }}>No HTML accessibility issues found.</p>;
  }

  const siteWide = issues.filter(i => i.plain_title.startsWith("Site-wide:"));
  const pageSpecific = issues.filter(i => !i.plain_title.startsWith("Site-wide:"));

  return (
    <div style={{ marginBottom: 32 }}>
      <h2>Accessibility Issues</h2>

      {siteWide.length > 0 && (
        <>
          <h3 style={{ color: "#555", fontSize: 16, marginTop: 16 }}>Site-wide issues (appear on every page)</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14, marginBottom: 24 }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #ddd", textAlign: "left" }}>
                <th style={{ padding: 8 }}>Issue</th>
                <th style={{ padding: 8 }}>Severity</th>
                <th style={{ padding: 8 }}>Element</th>
                <th style={{ padding: 8 }}>How to Fix</th>
              </tr>
            </thead>
            <tbody>
              {siteWide.map((issue) => (
                <tr key={issue.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: 8 }}>
                    <strong>{issue.plain_title.replace("Site-wide: ", "")}</strong>
                    <br />
                    <span style={{ color: "#555", fontSize: 13 }}>{issue.plain_description}</span>
                  </td>
                  <td style={{ padding: 8 }}>
                    <span style={{ padding: "2px 8px", borderRadius: 4, fontSize: 12, fontWeight: 600, background: SEVERITY_COLORS[issue.severity] || "#888", color: "#fff" }}>
                      {issue.severity}
                    </span>
                  </td>
                  <td style={{ padding: 8 }}>
                    <code style={{ fontSize: 12, background: "#f5f5f5", padding: "2px 4px", borderRadius: 2 }}>
                      {issue.element_selector?.slice(0, 40) || "—"}
                    </code>
                  </td>
                  <td style={{ padding: 8, color: "#555" }}>{issue.fix_suggestion}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {pageSpecific.length > 0 && (
        <>
          <h3 style={{ color: "#555", fontSize: 16, marginTop: 16 }}>Page-specific issues</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #ddd", textAlign: "left" }}>
                <th style={{ padding: 8 }}>Issue</th>
                <th style={{ padding: 8 }}>Severity</th>
                <th style={{ padding: 8 }}>Page</th>
                <th style={{ padding: 8 }}>Element</th>
                <th style={{ padding: 8 }}>How to Fix</th>
              </tr>
            </thead>
            <tbody>
              {pageSpecific.map((issue) => {
                const urlInfo = formatUrl(issue.url);
                return (
                  <tr key={issue.id} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={{ padding: 8 }}>
                      <strong>{issue.plain_title}</strong>
                    </td>
                    <td style={{ padding: 8 }}>
                      <span style={{ padding: "2px 8px", borderRadius: 4, fontSize: 12, fontWeight: 600, background: SEVERITY_COLORS[issue.severity] || "#888", color: "#fff" }}>
                        {issue.severity}
                      </span>
                    </td>
                    <td style={{ padding: 8 }}>
                      {urlInfo.href ? (
                        <a href={urlInfo.href} target="_blank" rel="noopener noreferrer" style={{ color: "#1976d2", wordBreak: "break-all" }}>
                          {urlInfo.display}
                        </a>
                      ) : (
                        <span style={{ wordBreak: "break-all" }}>{urlInfo.display}</span>
                      )}
                    </td>
                    <td style={{ padding: 8 }}>
                      <code style={{ fontSize: 12, background: "#f5f5f5", padding: "2px 4px", borderRadius: 2 }}>
                        {issue.element_selector?.slice(0, 40) || "—"}
                      </code>
                    </td>
                    <td style={{ padding: 8, color: "#555", fontSize: 13 }}>{issue.fix_suggestion}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
