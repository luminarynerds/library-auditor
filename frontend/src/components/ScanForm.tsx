import { useState } from "react";
import { createScan } from "../api/scans";

interface Props {
  onScanCreated: (scanId: string) => void;
}

export default function ScanForm({ onScanCreated }: Props) {
  const [libraryName, setLibraryName] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [accessCode, setAccessCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let url = baseUrl.trim();
      if (!url.startsWith("http")) {
        url = "https://" + url;
      }
      const scan = await createScan({
        library_name: libraryName.trim(),
        base_url: url,
        access_code: accessCode.trim(),
      });
      onScanCreated(scan.id);
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 480, margin: "0 auto" }}>
      <div style={{ marginBottom: 16 }}>
        <label htmlFor="library-name" style={{ display: "block", marginBottom: 4, fontWeight: 600 }}>
          Library Name
        </label>
        <input
          id="library-name"
          type="text"
          value={libraryName}
          onChange={(e) => setLibraryName(e.target.value)}
          placeholder="Springfield Public Library"
          required
          style={{ width: "100%", padding: 8, fontSize: 16, borderRadius: 4, border: "1px solid #ccc" }}
        />
      </div>

      <div style={{ marginBottom: 16 }}>
        <label htmlFor="base-url" style={{ display: "block", marginBottom: 4, fontWeight: 600 }}>
          Website URL
        </label>
        <input
          id="base-url"
          type="text"
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
          placeholder="www.springfieldlibrary.org"
          required
          style={{ width: "100%", padding: 8, fontSize: 16, borderRadius: 4, border: "1px solid #ccc" }}
        />
      </div>

      <div style={{ marginBottom: 16 }}>
        <label htmlFor="access-code" style={{ display: "block", marginBottom: 4, fontWeight: 600 }}>
          Access Code
        </label>
        <input
          id="access-code"
          type="text"
          value={accessCode}
          onChange={(e) => setAccessCode(e.target.value)}
          placeholder="Enter your access code"
          required
          style={{ width: "100%", padding: 8, fontSize: 16, borderRadius: 4, border: "1px solid #ccc" }}
        />
      </div>

      {error && (
        <div role="alert" style={{ color: "#d32f2f", marginBottom: 16, padding: 8, background: "#ffeaea", borderRadius: 4 }}>
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        style={{
          width: "100%",
          padding: 12,
          fontSize: 18,
          fontWeight: 600,
          background: loading ? "#999" : "#1976d2",
          color: "#fff",
          border: "none",
          borderRadius: 4,
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "Starting Scan..." : "Scan My Library"}
      </button>
    </form>
  );
}
