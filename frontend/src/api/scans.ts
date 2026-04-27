const API_BASE = "/api";

export interface ScanCreate {
  library_name: string;
  base_url: string;
  access_code: string;
  secondary_urls?: string[];
}

export interface ScanSummary {
  id: string;
  library_name: string;
  base_url: string;
  status: string;
  error_message: string | null;
  pages_found: number;
  pdfs_found: number;
  compliance_score: number | null;
  created_at: string;
  completed_at: string | null;
  issue_counts: Record<string, number> | null;
}

export interface IssueOut {
  id: string;
  url: string;
  issue_type: string;
  severity: string;
  axe_rule_id: string | null;
  wcag_criterion: string | null;
  plain_title: string;
  plain_description: string;
  fix_suggestion: string;
  impact_statement: string | null;
  effort: string | null;
  help_url: string | null;
  failure_detail: string | null;
  element_html: string | null;
  element_selector: string | null;
}

export interface PDFReportOut {
  id: string;
  url: string;
  filename: string;
  is_tagged: boolean;
  has_text: boolean;
  page_count: number;
  file_size_bytes: number;
  estimated_cost_low: number;
  estimated_cost_high: number;
}

export interface FixFirstItem {
  plain_title: string;
  severity: string;
  count: number;
  fix_suggestion: string;
  example_url: string;
}

export async function createScan(data: ScanCreate): Promise<ScanSummary> {
  const resp = await fetch(`${API_BASE}/scans`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(err.detail || "Failed to create scan");
  }
  return resp.json();
}

export async function getScan(id: string): Promise<ScanSummary> {
  const resp = await fetch(`${API_BASE}/scans/${id}`);
  if (!resp.ok) throw new Error("Failed to fetch scan");
  return resp.json();
}

export async function getIssues(id: string, page = 1): Promise<IssueOut[]> {
  const resp = await fetch(`${API_BASE}/scans/${id}/issues?page=${page}`);
  if (!resp.ok) throw new Error("Failed to fetch issues");
  return resp.json();
}

export async function getPDFs(id: string, page = 1): Promise<PDFReportOut[]> {
  const resp = await fetch(`${API_BASE}/scans/${id}/pdfs?page=${page}`);
  if (!resp.ok) throw new Error("Failed to fetch PDFs");
  return resp.json();
}

export async function getFixFirst(id: string): Promise<FixFirstItem[]> {
  const resp = await fetch(`${API_BASE}/scans/${id}/fix-first`);
  if (!resp.ok) throw new Error("Failed to fetch fix-first list");
  return resp.json();
}
