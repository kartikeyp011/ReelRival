export default function VideoCard({ video, label }) {
  if (!video) return null;

  const engagementColor =
    video.engagement_rate >= 5 ? "var(--success)" :
    video.engagement_rate >= 2 ? "var(--warning)" : "var(--error)";

  const fmt = (n) => n?.toLocaleString() ?? "N/A";

  return (
    <div className="glass-panel" style={{ flex: 1, minWidth: "400px", padding: "32px" }}>
      <div className="beta-badge" style={{ display: "inline-block", marginBottom: "20px", fontSize: "12px", padding: "6px 14px" }}>
        {label}
      </div>

      <div style={{
        fontWeight: 700,
        fontSize: "24px",
        marginBottom: "8px",
        overflow: "hidden",
        display: "-webkit-box",
        WebkitLineClamp: 2,
        WebkitBoxOrient: "vertical",
        lineHeight: "1.4",
      }}>
        {video.title}
      </div>

      <div style={{ fontSize: "16px", color: "var(--text-muted)", marginBottom: "28px" }}>
        {video.channel} • {video.publish_date}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        <Stat label="Views" value={fmt(video.view_count)} />
        <Stat label="Likes" value={fmt(video.like_count)} />
        <Stat label="Comments" value={fmt(video.comment_count)} />
        <Stat
          label="Engagement"
          value={`${video.engagement_rate}%`}
          valueColor={engagementColor}
        />
      </div>

      <div style={{
        marginTop: "24px",
        fontSize: "15px",
        display: "flex",
        alignItems: "center",
        gap: "8px",
        color: video.transcript_available ? "var(--success)" : "var(--error)",
        background: video.transcript_available ? "var(--success-bg)" : "var(--error-bg)",
        padding: "10px 16px",
        borderRadius: "var(--radius-sm)",
        fontWeight: 500,
        border: `1px solid ${video.transcript_available ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
      }}>
        {video.transcript_available ? "✓ Transcript Indexed" : "✗ No Transcript"}
      </div>
    </div>
  );
}

function Stat({ label, value, valueColor }) {
  return (
    <div className="stat-card">
      <div className="stat-label">
        {label}
      </div>
      <div className="stat-value" style={{ color: valueColor || "var(--text)" }}>
        {value}
      </div>
    </div>
  );
}