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
    <div className="app-container">

      {/* Header */}
      <div className="header">
        <div className="header-title-wrapper">
          <span style={{ fontSize: "48px" }}>⚔️</span>
          <h1 className="header-title">
            ReelRival
          </h1>
          <span className="beta-badge">BETA</span>
        </div>
        <p className="header-subtitle">
          AI-powered YouTube video comparison for creators · Powered by DeepSeek-R1 + RAG
        </p>
      </div>

      <ServiceBanner health={health} />

      {phase === "input" && (
        <div className="glass-panel animate-up" style={{ maxWidth: "1000px", margin: "0 auto", width: "100%" }}>
          <h2 style={{ fontSize: "24px", fontWeight: 600, marginBottom: "32px", textAlign: "center" }}>
            Compare Two YouTube Videos
          </h2>
          <URLInput onIngest={handleIngest} loading={loading} />
          {loading && (
            <div className="status-text" style={{ marginTop: "32px", justifyContent: "center" }}>
              <span style={{ animation: "spin 1s linear infinite", display: "inline-block" }}>⚙️</span> Fetching transcripts, computing embeddings, building index…
            </div>
          )}
          {error && (
            <div className="error-text" style={{ marginTop: "32px", justifyContent: "center" }}>
              <span>✗</span> {error}
            </div>
          )}
        </div>
      )}

      {phase === "chat" && (
        <div className="animate-up" style={{ display: "flex", flexDirection: "column", gap: "32px", flex: 1, animationDelay: "0.1s" }}>

          {/* Video cards */}
          <div style={{ display: "flex", gap: "32px", flexWrap: "wrap" }}>
            <VideoCard video={videoA} label="Video A" />
            <VideoCard video={videoB} label="Video B" />
          </div>

          {/* Chat */}
          <div className="chat-container">
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