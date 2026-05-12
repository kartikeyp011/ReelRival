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

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

        <div style={{ display: "flex", gap: "24px", flexWrap: "wrap" }}>
          <div className="input-group" style={{ minWidth: "300px" }}>
            <label className="input-label">
              Video A
            </label>
            <input
              className="styled-input"
              placeholder="https://youtube.com/watch?v=..."
              value={urlA}
              onChange={e => setUrlA(e.target.value)}
              disabled={loading}
            />
          </div>
          <div className="input-group" style={{ minWidth: "300px" }}>
            <label className="input-label">
              Video B
            </label>
            <input
              className="styled-input"
              placeholder="https://youtube.com/watch?v=..."
              value={urlB}
              onChange={e => setUrlB(e.target.value)}
              disabled={loading}
            />
          </div>
        </div>

        {error && (
          <div className="error-text">
            <span>✗</span> {error}
          </div>
        )}

        <button
          type="submit"
          className="btn-primary"
          disabled={loading}
          style={{ alignSelf: "center", minWidth: "240px", marginTop: "12px" }}
        >
          {loading ? "Analyzing…" : "⚡ Analyze Videos"}
        </button>
      </div>
    </form>
  );
}