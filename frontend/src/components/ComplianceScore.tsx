interface Props {
  score: number | null;
  pagesFound: number;
  pdfsFound: number;
  issueCounts: Record<string, number> | null;
}

function scoreLabel(score: number): string {
  if (score >= 90) return "Excellent -- very few issues found";
  if (score >= 75) return "Good -- some issues to address before the deadline";
  if (score >= 50) return "Needs work -- significant issues found";
  if (score >= 25) return "Poor -- many accessibility barriers for patrons";
  return "Critical -- major accessibility barriers across your site";
}

function Stat({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <div>
      <div style={{ fontSize: 28, fontWeight: 700, color: color || "#333" }}>{value}</div>
      <div style={{ fontSize: 14, color: "#888" }}>{label}</div>
    </div>
  );
}

export default function ComplianceScore({ score, pagesFound, pdfsFound, issueCounts }: Props) {
  const scoreColor = score === null ? "#888" : score >= 75 ? "#388e3c" : score >= 50 ? "#f57c00" : "#d32f2f";
  const totalIssues = issueCounts ? Object.values(issueCounts).reduce((a, b) => a + b, 0) : 0;

  return (
    <div style={{ textAlign: "center", marginBottom: 32 }}>
      <div style={{ fontSize: 64, fontWeight: 700, color: scoreColor }}>
        {score !== null ? `${score}%` : "N/A"}
      </div>
      <div style={{ fontSize: 18, color: "#555" }}>Compliance Score</div>
      {score !== null && (
        <div style={{ fontSize: 14, color: scoreColor, marginTop: 4 }}>
          {scoreLabel(score)}
        </div>
      )}
      <div style={{ display: "flex", justifyContent: "center", gap: 32, marginTop: 16, flexWrap: "wrap" }}>
        <Stat label="Pages Scanned" value={pagesFound} />
        <Stat label="PDFs Found" value={pdfsFound} />
        <Stat label="Total Issues" value={totalIssues} />
        {issueCounts?.critical ? <Stat label="Critical" value={issueCounts.critical} color="#d32f2f" /> : null}
        {issueCounts?.serious ? <Stat label="Serious" value={issueCounts.serious} color="#f57c00" /> : null}
      </div>
      <p style={{ fontSize: 12, color: "#aaa", marginTop: 12 }}>
        Score is based on the number and severity of issues found relative to pages scanned.
        <br />
        Critical issues (10 pts), serious (5 pts), moderate (2 pts), minor (1 pt).
      </p>
    </div>
  );
}
