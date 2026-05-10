import { useState, useEffect } from "react";
import URLInput from "./components/URLInput";
import VideoCard from "./components/VideoCard";
import ChatWindow from "./components/ChatWindow";
import ServiceBanner from "./components/ServiceBanner";
import { ingestVideos, resetSession, checkHealth } from "./api";

export default function App() {
  const [phase, setPhase] = useState("input");   // "input" | "chat"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [session, setSession] = useState(null);
  const [videoA, setVideoA] = useState(null);
  const [videoB, setVideoB] = useState(null);
  const [health, setHealth] = useState(null);

  // Poll health on mount
  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth({ services: { embed_service: false, llm_service: false } }));
  }, []);

  async function handleIngest(urlA, urlB) {
    setLoading(true);
    setError("");
    try {
      const data = await ingestVideos(urlA, urlB);
      setSession(data.session_id);
      setVideoA(data.video_a);
      setVideoB(data.video_b);
      setPhase("chat");
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Ingestion failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleReset() {
    if (session) await resetSession(session).catch(() => {});
    setPhase("input");
    setSession(null);
    setVideoA(null);
    setVideoB(null);
    setError("");
  }

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      maxWidth: "1100px",
      margin: "0 auto",
      padding: "24px 20px",
    }}>

      {/* Header */}
      <div style={{ marginBottom: "28px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
          <span style={{ fontSize: "22px" }}>⚔️</span>
          <h1 style={{ fontSize: "22px", fontWeight: 700, letterSpacing: "-0.02em" }}>
            ReelRival
          </h1>
          <span style={{
            fontSize: "11px", padding: "2px 8px",
            background: "var(--accent-light)", color: "var(--accent)",
            borderRadius: "999px", fontWeight: 600,
          }}>
            BETA
          </span>
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
          AI-powered YouTube video comparison for creators · Powered by DeepSeek-R1 + RAG
        </p>
      </div>

      <ServiceBanner health={health} />

      {phase === "input" && (
        <div style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)",
          padding: "28px",
        }}>
          <h2 style={{ fontSize: "15px", fontWeight: 600, marginBottom: "18px" }}>
            Compare Two YouTube Videos
          </h2>
          <URLInput onIngest={handleIngest} loading={loading} />
          {loading && (
            <div style={{ marginTop: "16px", color: "var(--text-muted)", fontSize: "13px" }}>
              ⏳ Fetching transcripts, computing embeddings, building index…
            </div>
          )}
          {error && (
            <div style={{ marginTop: "12px", color: "var(--error)", fontSize: "13px" }}>
              ✗ {error}
            </div>
          )}
        </div>
      )}

      {phase === "chat" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px", flex: 1 }}>

          {/* Video cards */}
          <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
            <VideoCard video={videoA} label="Video A" />
            <VideoCard video={videoB} label="Video B" />
          </div>

          {/* Chat */}
          <div style={{
            flex: 1,
            background: "var(--bg)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)",
            overflow: "hidden",
            minHeight: "520px",
            display: "flex",
            flexDirection: "column",
          }}>
            <ChatWindow
              sessionId={session}
              videoA={videoA}
              videoB={videoB}
              onReset={handleReset}
            />
          </div>
        </div>
      )}
    </div>
  );
}