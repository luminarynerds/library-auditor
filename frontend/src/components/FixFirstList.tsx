import type { FixFirstItem } from "../api/scans";

interface Props {
  items: FixFirstItem[];
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#d32f2f",
  serious: "#f57c00",
  moderate: "#fbc02d",
  minor: "#888",
};

export default function FixFirstList({ items }: Props) {
  if (items.length === 0) return null;

  return (
    <div style={{ marginBottom: 32 }}>
      <h2>Fix These First</h2>
      <p style={{ color: "#555" }}>These issues have the biggest impact. Fixing them will improve your score the most.</p>
      <ol style={{ paddingLeft: 20 }}>
        {items.map((item, i) => (
          <li key={i} style={{ marginBottom: 16, lineHeight: 1.6 }}>
            <strong>{item.plain_title}</strong>
            <span style={{
              marginLeft: 8, padding: "2px 8px", borderRadius: 4, fontSize: 12, fontWeight: 600,
              background: SEVERITY_COLORS[item.severity] || "#888", color: "#fff",
            }}>
              {item.severity}
            </span>
            <span style={{ marginLeft: 8, color: "#888" }}>({item.count} occurrence{item.count !== 1 ? "s" : ""})</span>
            <br />
            <span style={{ color: "#555" }}>{item.fix_suggestion}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
