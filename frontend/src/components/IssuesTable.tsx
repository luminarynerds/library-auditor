import type { IssueOut } from "../api/scans";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#d32f2f",
  serious: "#f57c00",
  moderate: "#fbc02d",
  minor: "#888",
};

const EFFORT_LABELS: Record<string, { text: string; color: string }> = {
  quick: { text: "Quick fix", color: "#388e3c" },
  developer: { text: "Needs a developer", color: "#f57c00" },
  redesign: { text: "Needs redesign", color: "#d32f2f" },
};

function formatUrl(url: string): { display: string; href: string | null } {
  if (url.includes("(+")) return { display: url, href: null };
  try {
    return { display: new URL(url).pathname, href: url };
  } catch {
    return { display: url, href: null };
  }
}

function IssueCard({ issue, showPage }: { issue: IssueOut; showPage: boolean }) {
  const urlInfo = formatUrl(issue.url);
  const effort = EFFORT_LABELS[issue.effort || "developer"] || EFFORT_LABELS.developer;

  return (
    <div style={{ border: "1px solid #e0e0e0", borderRadius: 8, padding: 16, marginBottom: 12, borderLeft: `4px solid ${SEVERITY_COLORS[issue.severity] || "#888"}` }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 8, marginBottom: 8 }}>
        <div>
          <strong style={{ fontSize: 15 }}>{issue.plain_title.replace("Site-wide: ", "")}</strong>
          <div style={{ display: "flex", gap: 8, marginTop: 4, flexWrap: "wrap" }}>
            <span style={{ padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 600, background: SEVERITY_COLORS[issue.severity] || "#888", color: "#fff" }}>
              {issue.severity}
            </span>
            <span style={{ padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 600, background: effort.color, color: "#fff" }}>
              {effort.text}
            </span>
            {issue.wcag_criterion && (
              <span style={{ padding: "2px 8px", borderRadius: 4, fontSize: 11, background: "#e3f2fd", color: "#1565c0" }}>
                WCAG {issue.wcag_criterion}
              </span>
            )}
          </div>
        </div>
        {showPage && urlInfo.href && (
          <a href={urlInfo.href} target="_blank" rel="noopener noreferrer" style={{ color: "#1976d2", fontSize: 13, wordBreak: "break-all" }}>
            {urlInfo.display}
          </a>
        )}
        {showPage && !urlInfo.href && (
          <span style={{ fontSize: 13, color: "#888" }}>{urlInfo.display}</span>
        )}
      </div>

      {issue.impact_statement && (
        <div style={{ marginBottom: 8, padding: "8px 12px", background: "#fff3e0", borderRadius: 4, fontSize: 13 }}>
          <strong>Why this matters: </strong>{issue.impact_statement}
        </div>
      )}

      <div style={{ marginBottom: 8, fontSize: 13, color: "#333" }}>
        <strong>How to fix: </strong>{issue.fix_suggestion}
      </div>

      {issue.failure_detail && (
        <div style={{ marginBottom: 8, fontSize: 12, color: "#555" }}>
          <strong>Details: </strong>{issue.failure_detail}
        </div>
      )}

      {issue.element_html && (
        <details style={{ marginBottom: 4 }}>
          <summary style={{ fontSize: 12, color: "#888", cursor: "pointer" }}>Show the code</summary>
          <code style={{ display: "block", fontSize: 11, background: "#f5f5f5", padding: 8, borderRadius: 4, marginTop: 4, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
            {issue.element_html}
          </code>
        </details>
      )}

      {issue.help_url && (
        <a href={issue.help_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: "#1976d2" }}>
          Learn more about this issue
        </a>
      )}
    </div>
  );
}

export default function IssuesTable({ issues }: { issues: IssueOut[] }) {
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
          <h3 style={{ color: "#555", fontSize: 16, marginTop: 16, marginBottom: 12 }}>
            Site-wide issues (appear on every page -- fix these once to fix them everywhere)
          </h3>
          {siteWide.map(issue => <IssueCard key={issue.id} issue={issue} showPage={false} />)}
        </>
      )}

      {pageSpecific.length > 0 && (
        <>
          <h3 style={{ color: "#555", fontSize: 16, marginTop: 24, marginBottom: 12 }}>
            Page-specific issues
          </h3>
          {pageSpecific.map(issue => <IssueCard key={issue.id} issue={issue} showPage={true} />)}
        </>
      )}
    </div>
  );
}
