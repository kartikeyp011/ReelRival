export default function ServiceBanner({ health }) {
  if (!health) return null;

  const allOk = health.services?.embed_service && health.services?.llm_service;
  if (allOk) return null;

  return (
    <div style={{
      background: "rgba(239,68,68,0.1)",
      border: "1px solid rgba(239,68,68,0.3)",
      borderRadius: "8px",
      padding: "10px 16px",
      marginBottom: "16px",
      fontSize: "13px",
      color: "#fca5a5",
      display: "flex",
      alignItems: "center",
      gap: "8px",
    }}>
      <span>⚠</span>
      <span>
        GPU services offline —&nbsp;
        {!health.services?.embed_service && "Embedding service down. "}
        {!health.services?.llm_service && "LLM service down. "}
        Restart your Kaggle notebook and update <code style={{background:"rgba(255,255,255,0.1)",padding:"1px 5px",borderRadius:"4px"}}>EMBED_SERVICE_URL</code> in <code style={{background:"rgba(255,255,255,0.1)",padding:"1px 5px",borderRadius:"4px"}}>.env</code>.
      </span>
    </div>
  );
}