import { useState } from "react";

export default function URLInput({ onIngest, loading }) {
  const [urlA, setUrlA] = useState("");
  const [urlB, setUrlB] = useState("");
  const [error, setError] = useState("");

  function isYouTube(url) {
    return url.includes("youtube.com/watch") || url.includes("youtu.be/");
  }

  function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (!urlA.trim() || !urlB.trim()) {
      setError("Please enter both video URLs.");
      return;
    }
    if (!isYouTube(urlA) || !isYouTube(urlB)) {
      setError("Only YouTube URLs are supported.");
      return;
    }
    if (urlA.trim() === urlB.trim()) {
      setError("Please enter two different videos.");
      return;
    }

    onIngest(urlA.trim(), urlB.trim());
  }

  const inputStyle = {
    width: "100%",
    background: "var(--surface-2)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius)",
    padding: "12px 14px",
    color: "var(--text)",
    fontSize: "14px",
    outline: "none",
    transition: "border-color 0.15s",
  };

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>

        {/* URL inputs */}
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: "240px" }}>
            <label style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
              VIDEO A
            </label>
            <input
              style={inputStyle}
              placeholder="https://youtube.com/watch?v=..."
              value={urlA}
              onChange={e => setUrlA(e.target.value)}
              disabled={loading}
              onFocus={e => e.target.style.borderColor = "var(--accent)"}
              onBlur={e => e.target.style.borderColor = "var(--border)"}
            />
          </div>
          <div style={{ flex: 1, minWidth: "240px" }}>
            <label style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
              VIDEO B
            </label>
            <input
              style={inputStyle}
              placeholder="https://youtube.com/watch?v=..."
              value={urlB}
              onChange={e => setUrlB(e.target.value)}
              disabled={loading}
              onFocus={e => e.target.style.borderColor = "var(--accent)"}
              onBlur={e => e.target.style.borderColor = "var(--border)"}
            />
          </div>
        </div>

        {/* Error */}
        {error && (
          <div style={{ fontSize: "13px", color: "var(--error)" }}>
            {error}
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          style={{
            background: loading ? "var(--surface-2)" : "var(--accent)",
            color: loading ? "var(--text-muted)" : "white",
            padding: "12px 28px",
            borderRadius: "var(--radius)",
            fontWeight: 600,
            fontSize: "14px",
            alignSelf: "flex-start",
            transition: "background 0.15s",
            cursor: loading ? "not-allowed" : "pointer",
          }}
          onMouseEnter={e => { if (!loading) e.target.style.background = "var(--accent-hover)"; }}
          onMouseLeave={e => { if (!loading) e.target.style.background = "var(--accent)"; }}
        >
          {loading ? "Analyzing…" : "⚡ Analyze Videos"}
        </button>
      </div>
    </form>
  );
}