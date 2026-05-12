export default function ServiceBanner({ health }) {
  if (!health) return null;

  const allOk = health.services?.embed_service && health.services?.llm_service;
  if (allOk) return null;

  return (
    <div className="error-text" style={{ marginBottom: "24px", animation: "pulse 3s infinite" }}>
      <span style={{ fontSize: "18px" }}>⚠</span>
      <span>
        <strong>GPU services offline</strong> —&nbsp;
        {!health.services?.embed_service && "Embedding service down. "}
        {!health.services?.llm_service && "LLM service down. "}
        Restart your Kaggle notebook and update <code style={{background:"rgba(0,0,0,0.3)",padding:"2px 6px",borderRadius:"4px",border:"1px solid rgba(255,255,255,0.1)",fontFamily:"monospace"}}>EMBED_SERVICE_URL</code> in <code style={{background:"rgba(0,0,0,0.3)",padding:"2px 6px",borderRadius:"4px",border:"1px solid rgba(255,255,255,0.1)",fontFamily:"monospace"}}>.env</code>.
      </span>
    </div>
  );
}